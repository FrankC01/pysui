#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Base executor ABCs for protocol-agnostic serial transaction execution."""

import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Literal, Optional, Union

from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.executors.exec_types import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    GasSummary,
)
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
import pysui.sui.sui_common.sui_commands as cmd

logger = logging.getLogger(__name__)

_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"


class _BaseExecutor(ABC):
    """Base class owning the cache, signer, and balance for all executors."""

    def __init__(
        self,
        *,
        cache: _BaseCachingExecutor,
        signer_block: SignerBlock,
        min_balance_threshold: Optional[int] = None,
    ) -> None:
        self._cache = cache
        self._signing_block = signer_block
        self._tracked_balance: int = 0
        self._min_balance_threshold = min_balance_threshold

    async def reset_cache(self) -> None:
        """Reset the underlying executor cache."""
        await self._cache.reset()

    async def _apply_effects(self, effects: "sui_prot.TransactionEffects") -> None:
        await self._cache.apply_effects(effects)


class _BaseSerialExecutor(_BaseExecutor, ABC):
    """ABC for serial transaction executors. Subclasses implement _execute_raw and _fetch_initial_balance."""

    def __init__(
        self,
        *,
        client,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
        min_balance_threshold: Optional[int] = None,
        on_coins_low: Optional[
            Callable[[ExecutorContext], Awaitable[Optional[list[str]]]]
        ] = None,
        on_balance_low: Optional[
            Callable[[ExecutorContext], Awaitable[Optional[str]]]
        ] = None,
        on_failure: Literal["continue", "exit"] = "continue",
    ) -> None:
        # Build signer_block from sender/sponsor
        signer_block = SignerBlock(sender=sender, sponsor=sponsor)
        use_account_gas = on_balance_low is not None and on_coins_low is None
        self._use_account_gas = use_account_gas
        cache = self._create_caching_executor(
            client,
            sender if isinstance(sender, str) else sender.signing_address,
            use_account_gas=use_account_gas,
        )
        super().__init__(
            cache=cache,
            signer_block=signer_block,
            min_balance_threshold=min_balance_threshold,
        )
        self._client = client
        self._on_coins_low = on_coins_low
        self._on_balance_low = on_balance_low
        self._on_failure: Literal["continue", "exit"] = on_failure
        self._last_digest: Optional[str] = None
        self._gas_summary: Optional[GasSummary] = None

    @abstractmethod
    def _create_caching_executor(self, client, gas_owner: str, use_account_gas: bool = False) -> _BaseCachingExecutor:
        """Create the protocol-specific caching executor."""

    @abstractmethod
    async def _execute_raw(
        self, tx_str: str, sigs: list[str]
    ) -> "sui_prot.ExecutedTransaction":
        """Execute a signed transaction and return ExecutedTransaction."""

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
    ) -> tuple[Optional[dict], Optional[ExecutorError], Optional[Exception]]:
        """Attempt to build and sign a transaction, retrying once with coin replenishment on failure."""
        gas_objects = None
        if self._gas_summary is not None:
            gas_objects = [
                sui_prot.Object(
                    object_id=self._gas_summary.objectId,
                    version=int(self._gas_summary.version),
                    digest=self._gas_summary.digest,
                    balance=self._gas_summary.balance,
                )
            ]
        try:
            signed_tx = await self._cache.build_transaction(
                tx, self._signing_block, gas_objects
            )
            return signed_tx, None, None
        except Exception as exc:
            logger.warning("build_transaction failed: %s", exc)
            return None, ExecutorError.BUILDING_ERROR, exc

    def _update_tracked_balance(self, effects: "sui_prot.TransactionEffects") -> None:
        """Deduct net gas cost of executed transaction from tracked balance."""
        gas = effects.gas_used
        net_gas = (gas.computation_cost or 0) + (gas.storage_cost or 0) - (gas.storage_rebate or 0)
        self._tracked_balance = max(0, self._tracked_balance - net_gas)

    async def _check_balance_threshold(
        self,
        idx: int,
        txns: list,
        results: list,
        executed_tx: "sui_prot.ExecutedTransaction",
    ) -> bool:
        """Check balance against threshold and invoke replenishment callback if needed.

        Returns True if the caller should return results immediately.
        """
        if (
            self._min_balance_threshold is None
            or self._tracked_balance >= self._min_balance_threshold
        ):
            return False
        halt_reason = None
        ctx = self._build_executor_context()
        if self._on_coins_low is not None:
            new_coins = await self._on_coins_low(ctx)
            if not new_coins:
                halt_reason = "coin replenishment declined"
            else:
                gas_id = self._gas_summary.objectId
                candidates: list = []
                if isinstance(new_coins[0], str):
                    filtered_ids = [c for c in new_coins if c != gas_id]
                    if not filtered_ids:
                        halt_reason = "coin replenishment declined"
                    else:
                        fetch_result = await self._client.execute(
                            command=cmd.GetMultipleObjects(object_ids=filtered_ids)
                        )
                        if not fetch_result.is_ok():
                            halt_reason = f"coin replenishment fetch failed: {fetch_result.result_string}"
                        else:
                            candidates = [
                                o for o in fetch_result.result_data
                                if o.object_type == _SUI_COIN_TYPE
                            ]
                            if not candidates:
                                halt_reason = "coin replenishment: no SUI coins in returned objects"
                else:
                    candidates = [
                        o for o in new_coins
                        if o.object_id != gas_id and o.object_type == _SUI_COIN_TYPE
                    ]
                    if not candidates:
                        halt_reason = "coin replenishment declined"
                if halt_reason is None:
                    accumulated = sum(o.balance or 0 for o in candidates)
                    current = self._gas_summary.balance
                    if accumulated + current < self._min_balance_threshold:
                        halt_reason = f"coin replenishment: insufficient balance {accumulated + current} < {self._min_balance_threshold}"
                    else:
                        merge_tx = await self.new_transaction()
                        await merge_tx.merge_coins(merge_to=merge_tx.gas, merge_from=candidates)
                        gas_objects = [
                            sui_prot.Object(
                                object_id=self._gas_summary.objectId,
                                version=int(self._gas_summary.version),
                                digest=self._gas_summary.digest,
                                balance=self._gas_summary.balance,
                            )
                        ]
                        build_dict = await merge_tx.build_and_sign(use_gas_objects=gas_objects)
                        merge_result = await self._client.execute(
                            command=cmd.ExecuteTransaction(**build_dict)
                        )
                        if not merge_result.is_ok():
                            halt_reason = f"coin replenishment merge failed: {merge_result.result_string}"
                        else:
                            self._update_gas_summary(merge_result.result_data)
                            self._tracked_balance = self._gas_summary.balance
        elif self._on_balance_low is not None:
            new_addr = await self._on_balance_low(ctx)
            if new_addr:
                refreshed = await self._fetch_initial_balance()
                if refreshed is not None:
                    self._tracked_balance = refreshed
            else:
                halt_reason = "balance replenishment declined"
        if halt_reason:
            results.append(executed_tx)
            for remaining_idx in range(idx + 1, len(txns)):
                results.append(
                    ExecutionSkipped(
                        transaction_index=remaining_idx, reason=halt_reason
                    )
                )
            return True
        return False

    def _update_gas_summary(self, executed_tx: "sui_prot.ExecutedTransaction") -> None:
        """Update GasSummary version/digest/balance in-place from ExecutedTransaction objects."""
        if self._gas_summary is None or executed_tx is None:
            return
        effects = executed_tx.effects
        if effects and effects.gas_object:
            go = effects.gas_object
            if go.output_version is not None:
                self._gas_summary.version = str(go.output_version)
            if go.output_digest is not None:
                self._gas_summary.digest = go.output_digest
        if executed_tx.objects:
            target_version = (
                int(self._gas_summary.version) if self._gas_summary.version else None
            )
            for obj in executed_tx.objects.objects:
                if obj.object_id == self._gas_summary.objectId:
                    if target_version is None or obj.version == target_version:
                        if obj.balance is not None:
                            self._gas_summary.balance = obj.balance
                        break

    async def execute_transactions(
        self,
        txns: list,
    ) -> "list[Union[sui_prot.ExecutedTransaction, tuple[ExecutorError, Exception], ExecutionSkipped]]":
        """Execute a list of transactions serially, handling replenishment and halting on errors."""
        if self._tracked_balance == 0:
            self._tracked_balance = await self._fetch_initial_balance()

        results: list[
            Union[sui_prot.ExecutedTransaction, tuple[ExecutorError, Exception], ExecutionSkipped]
        ] = []
        halt = False

        for idx, tx in enumerate(txns):
            if halt:
                results.append(
                    ExecutionSkipped(transaction_index=idx, reason="Halt after error")
                )
                continue
            signed_tx, build_err, exc = await self._try_build_with_replenishment(tx)
            if build_err is not None:
                results.append((build_err, exc))
                halt = True
                continue
            try:
                executed_tx = await self._execute_raw(
                    signed_tx["tx_bytestr"], signed_tx["sig_array"]
                )
                self._last_digest = executed_tx.effects.transaction_digest
                await self._apply_effects(executed_tx.effects)
                self._update_tracked_balance(executed_tx.effects)
                if await self._check_balance_threshold(idx, txns, results, executed_tx):
                    return results
                results.append(executed_tx)
            except Exception as exc:
                logger.warning("execute_raw failed: %s", exc)
                results.append((ExecutorError.EXECUTING_ERROR, exc))
                if self._on_failure == "exit":
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
        from pysui.sui.sui_common.txb_tx_argparse import (
            TxnArgMode,
        )  # local: breaks circular import

        kwargs["mode"] = TxnArgMode.DEFERRED
        kwargs["object_cache"] = self._cache.cache
        return await self._client.transaction(**kwargs)
