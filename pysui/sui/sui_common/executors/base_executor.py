#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Base executor ABCs for protocol-agnostic serial transaction execution."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Union

from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.executors.exec_types import ExecutorContext, ExecutionSkipped, ExecutorError
from pysui.sui.sui_common.types import TransactionEffects
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig

logger = logging.getLogger(__name__)


class _BaseExecutor(ABC):
    """Base class owning the cache, signer, and balance for all executors."""

    def __init__(
        self,
        *,
        cache: _BaseCachingExecutor,
        signer_block: SignerBlock,
        default_gas_budget: int = 50_000_000,
        min_balance_threshold: Optional[int] = None,
    ) -> None:
        self._cache = cache
        self._signing_block = signer_block
        self._tracked_balance: int = 0
        self._default_gas_budget = default_gas_budget
        self._min_balance_threshold = min_balance_threshold

    async def reset_cache(self) -> None:
        """Reset the underlying executor cache."""
        await self._cache.reset()

    async def _apply_effects(self, effects: TransactionEffects) -> None:
        await self._cache.apply_effects(effects)


class _BaseSerialExecutor(_BaseExecutor, ABC):
    """ABC for serial transaction executors. Subclasses implement _execute_raw and _fetch_initial_balance."""

    def __init__(
        self,
        *,
        client,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
        default_gas_budget: int = 50_000_000,
        min_balance_threshold: Optional[int] = None,
        on_coins_low: Optional[Callable[[ExecutorContext], Awaitable[Optional[list[str]]]]] = None,
        on_balance_low: Optional[Callable[[ExecutorContext], Awaitable[Optional[str]]]] = None,
    ) -> None:
        # Build signer_block from sender/sponsor
        signer_block = SignerBlock(
            sender=sender if isinstance(sender, SigningMultiSig) else sender,
            sponsor=sponsor if isinstance(sponsor, SigningMultiSig) else sponsor,
        )
        cache = self._create_caching_executor(client, sender if isinstance(sender, str) else sender.signing_address)
        super().__init__(
            cache=cache,
            signer_block=signer_block,
            default_gas_budget=default_gas_budget,
            min_balance_threshold=min_balance_threshold,
        )
        self._client = client
        self._on_coins_low = on_coins_low
        self._on_balance_low = on_balance_low
        self._queue: asyncio.Queue = asyncio.Queue()
        self._last_digest: Optional[str] = None

    @abstractmethod
    def _create_caching_executor(self, client, gas_owner: str) -> _BaseCachingExecutor:
        """Create the protocol-specific caching executor."""

    @abstractmethod
    async def _execute_raw(self, tx_str: str, sigs: list[str]) -> TransactionEffects:
        """Execute a signed transaction and return common TransactionEffects."""

    @abstractmethod
    async def _fetch_initial_balance(self) -> int:
        """Fetch the current gas balance for the sender."""

    def _build_executor_context(self) -> ExecutorContext:
        return ExecutorContext(
            sender=self._signing_block.sender_str,
            gas_owner=self._signing_block.sender_str,
            gas_coins=[],
            tracked_balance=self._tracked_balance,
        )

    async def _try_replenish_coins(self) -> bool:
        """Returns True if replenishment was attempted and succeeded (coins invalidated for re-fetch)."""
        if self._on_coins_low is None:
            return False
        ctx = self._build_executor_context()
        new_coins = await self._on_coins_low(ctx)
        if new_coins:
            await self._cache.invalidate_gas_coins()
            return True
        return False

    async def _try_build_with_replenishment(
        self, tx
    ) -> tuple[Optional[str], Optional[ExecutorError], Optional[Exception]]:
        """Attempt to build a transaction, retrying once after coin replenishment on failure."""
        try:
            tx_str = await self._cache.build_transaction(tx, self._signing_block, self._default_gas_budget)
            return tx_str, None, None
        except Exception as exc:
            logger.warning("build_transaction failed: %s", exc)
            replenished = await self._try_replenish_coins()
            if not replenished:
                return None, ExecutorError.BUILDING_ERROR, exc
            try:
                tx_str = await self._cache.build_transaction(tx, self._signing_block, self._default_gas_budget)
                return tx_str, None, None
            except Exception as exc2:
                return None, ExecutorError.BUILDING_ERROR, exc2

    def _update_tracked_balance(self, effects: TransactionEffects) -> None:
        """Deduct net gas cost of executed transaction from tracked balance."""
        gas = effects.gas_used
        net_gas = gas.computation_cost + gas.storage_cost - gas.storage_rebate
        self._tracked_balance = max(0, self._tracked_balance - net_gas)

    async def _check_balance_threshold(
        self,
        idx: int,
        txns: list,
        results: list,
        effects: TransactionEffects,
    ) -> bool:
        """Check balance against threshold and invoke replenishment callback if needed.

        Returns True if the caller should return results immediately.
        """
        if self._min_balance_threshold is None or self._tracked_balance >= self._min_balance_threshold:
            return False
        halt_reason = None
        ctx = self._build_executor_context()
        if self._on_coins_low is not None:
            new_coins = await self._on_coins_low(ctx)
            if new_coins:
                await self._cache.invalidate_gas_coins()
                refreshed = await self._fetch_initial_balance()
                if refreshed is not None:
                    self._tracked_balance = refreshed
            else:
                halt_reason = "coin replenishment declined"
        elif self._on_balance_low is not None:
            new_addr = await self._on_balance_low(ctx)
            if new_addr:
                refreshed = await self._fetch_initial_balance()
                if refreshed is not None:
                    self._tracked_balance = refreshed
            else:
                halt_reason = "balance replenishment declined"
        if halt_reason:
            results.append(effects)
            for remaining_idx in range(idx + 1, len(txns)):
                results.append(ExecutionSkipped(transaction_index=remaining_idx, reason=halt_reason))
            return True
        return False

    async def execute_transactions(
        self,
        txns: list,
    ) -> list[Union[TransactionEffects, tuple[ExecutorError, Exception], ExecutionSkipped]]:
        """Execute a list of transactions serially, handling replenishment and halting on errors."""
        if self._tracked_balance == 0:
            self._tracked_balance = await self._fetch_initial_balance()

        results: list[Union[TransactionEffects, tuple[ExecutorError, Exception], ExecutionSkipped]] = []
        halt = False

        for idx, tx in enumerate(txns):
            if halt:
                results.append(ExecutionSkipped(transaction_index=idx, reason="Halt after error"))
                continue
            tx_str, build_err, exc = await self._try_build_with_replenishment(tx)
            if build_err is not None:
                results.append((build_err, exc))
                halt = True
                continue
            try:
                sigs = self._signing_block.get_signatures(config=self._client.config, tx_bytes=tx_str)
                effects = await self._execute_raw(tx_str, sigs)
                self._last_digest = effects.transaction_digest
                await self._apply_effects(effects)
                self._update_tracked_balance(effects)
                if await self._check_balance_threshold(idx, txns, results, effects):
                    return results
                results.append(effects)
            except Exception as exc:
                logger.warning("execute_raw failed: %s", exc)
                results.append((ExecutorError.EXECUTING_ERROR, exc))
                halt = True

        return results

    async def new_transaction(self, **kwargs):
        """Create a new transaction pre-wired for this executor's deferred-mode cache.

        The transaction is constructed with ``mode=DEFERRED`` and
        ``object_cache`` pointed at this executor's persistent object cache, so
        object references that hit the cache are resolved without an on-chain
        fetch, and cache misses produce ``UnresolvedObjectArg`` placeholders
        that the caching executor resolves at build time.
        """
        from pysui.sui.sui_common.txb_tx_argparse import TxnArgMode  # local: breaks circular import
        kwargs["mode"] = TxnArgMode.DEFERRED
        kwargs["object_cache"] = self._cache.cache
        return await self._client.transaction(**kwargs)
