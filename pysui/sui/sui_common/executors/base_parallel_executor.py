#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Base ABC for protocol-agnostic parallel transaction execution."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Optional, Union

from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.executors.conflict_tracker import ConflictTracker
from pysui.sui.sui_common.executors.exec_types import ExecutorContext, ExecutionSkipped, ExecutorError
from pysui.sui.sui_common.executors.gas_pool import GasCoin, GasCoinPool
from pysui.sui.sui_common.executors.object_registry import (
    AbstractObjectRegistry,
    ObjectVersionEntry,
    get_object_registry,
)
from pysui.sui.sui_common.executors.queue import ParallelQueue
from pysui.sui.sui_common.types import TransactionEffects
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig

logger = logging.getLogger(__name__)

GasMode = str  # "coins" | "addressBalance"


class _BaseParallelExecutor(ABC):
    """Protocol-agnostic ABC for parallel transaction execution.

    Two gas modes are supported:
    - "coins": each in-flight transaction checks out an exclusive gas coin from
      the pool. The pool is replenished automatically when it drops to the
      low-water mark. The user must seed the pool via ``_refill_coin_pool`` or
      provide an initial set of coins.
    - "addressBalance": no gas coin pool. Concurrency is bounded only by
      ``max_tasks``; the Sui node selects gas from the sender's accumulated
      balance. An optional ``on_balance_low`` callback fires when the tracked
      balance drops below ``min_balance_threshold``.

    Conflict tracking (owned-object serialisation):
      All unresolved object inputs in each transaction are treated as potential
      conflict IDs. This is conservative — shared objects also acquire a slot —
      but it is always correct and prevents equivocation for owned objects.
      Future versions may refine this via registry ownership lookup.

    Subclasses must implement:
      - ``_create_caching_executor``  — create a per-transaction cache
      - ``_execute_single``           — sign+execute one transaction
      - ``_refill_coin_pool``         — mint new gas coins (coins mode only)
      - ``_fetch_balance``            — fetch the current gas balance
    """

    def __init__(
        self,
        *,
        client,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
        gas_mode: GasMode = "coins",
        max_tasks: int = 4,
        default_gas_budget: int = 50_000_000,
        min_balance_threshold: Optional[int] = None,
        low_water_mark: int = 5,
        min_balance_per_coin: Optional[int] = None,
        on_balance_low: Optional[Callable[[ExecutorContext], Awaitable[Optional[str]]]] = None,
        registry: Optional[AbstractObjectRegistry] = None,
    ) -> None:
        if gas_mode not in ("coins", "addressBalance"):
            raise ValueError(f"gas_mode must be 'coins' or 'addressBalance', got {gas_mode!r}")
        if gas_mode == "addressBalance" and min_balance_threshold is not None and on_balance_low is None:
            raise ValueError("addressBalance mode with min_balance_threshold requires on_balance_low")

        self._client = client
        self._gas_mode: GasMode = gas_mode
        self._default_gas_budget = default_gas_budget
        self._min_balance_threshold = min_balance_threshold
        self._on_balance_low = on_balance_low

        sender_addr = sender if isinstance(sender, str) else sender.signing_address
        self._signing_block = SignerBlock(
            sender=sender,
            sponsor=sponsor,
        )

        self._gas_owner = (
            sponsor if isinstance(sponsor, str)
            else sponsor.signing_address if isinstance(sponsor, SigningMultiSig)
            else sender_addr
        )

        self._parallel_queue = ParallelQueue(max_tasks=max_tasks)
        self._conflict_tracker = ConflictTracker()
        self._registry: AbstractObjectRegistry = registry or get_object_registry()

        if gas_mode == "coins":
            self._gas_pool: Optional[GasCoinPool] = GasCoinPool(
                low_water_mark=low_water_mark,
                min_balance_per_coin=min_balance_per_coin,
            )
            self._refill_lock = asyncio.Lock()
        else:
            self._gas_pool = None
            self._refill_lock = asyncio.Lock()

        self._tracked_balance: int = 0
        self._balance_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Abstract protocol-specific hooks
    # ------------------------------------------------------------------

    @abstractmethod
    def _create_caching_executor(self) -> _BaseCachingExecutor:
        """Create a fresh per-transaction caching executor."""

    @abstractmethod
    async def _execute_single(
        self,
        tx_str: str,
        sigs: list[str],
        caching_exec: _BaseCachingExecutor,
    ) -> TransactionEffects:
        """Sign-and-execute one transaction, returning protocol-agnostic effects."""

    @abstractmethod
    async def _refill_coin_pool(self, n: int) -> list[GasCoin]:
        """Mint ``n`` fresh gas coins and return them.

        Must NOT use the parallel executor's own path — use a plain one-off
        transaction outside the caching executor to avoid circular dependency.
        """

    @abstractmethod
    async def _fetch_balance(self) -> int:
        """Return the current gas balance for the gas owner."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_executor_context(self) -> ExecutorContext:
        return ExecutorContext(
            sender=self._signing_block.sender_str,
            gas_owner=self._gas_owner,
            gas_coins=[],
            tracked_balance=self._tracked_balance,
        )

    async def _maybe_trigger_refill(self) -> None:
        """Start a background refill task if the pool is low and no refill is running."""
        if self._gas_pool is None or not self._gas_pool.is_low():
            return
        if self._refill_lock.locked():
            return
        asyncio.ensure_future(self._do_refill())

    async def _do_refill(self) -> None:
        """Refill the gas coin pool. Serialised by _refill_lock."""
        assert self._gas_pool is not None
        async with self._refill_lock:
            if not self._gas_pool.is_low():
                return
            try:
                target = self._gas_pool._low_water_mark * 3
                new_coins = await self._refill_coin_pool(target)
                if new_coins:
                    await self._gas_pool.replenish(new_coins)
                    logger.info("parallel_exec: refilled pool with %d coins", len(new_coins))
            except Exception as exc:
                logger.warning("parallel_exec: coin refill failed: %s", exc)

    async def _deduct_gas(self, effects: TransactionEffects) -> None:
        """Thread-safely deduct net gas from tracked balance."""
        gas = effects.gas_used
        net = gas.computation_cost + gas.storage_cost - gas.storage_rebate
        async with self._balance_lock:
            self._tracked_balance = max(0, self._tracked_balance - net)

    async def _check_balance_threshold(self) -> Optional[str]:
        """Fire on_balance_low if tracked balance is below threshold. Returns halt reason or None."""
        if self._min_balance_threshold is None or self._on_balance_low is None:
            return None
        async with self._balance_lock:
            if self._tracked_balance >= self._min_balance_threshold:
                return None
        ctx = self._build_executor_context()
        result = await self._on_balance_low(ctx)
        if result:
            refreshed = await self._fetch_balance()
            async with self._balance_lock:
                self._tracked_balance = refreshed
            return None
        return "balance replenishment declined"

    # ------------------------------------------------------------------
    # Per-transaction task
    # ------------------------------------------------------------------

    async def _execute_transaction_task(
        self,
        tx,
        gas_budget: int,
    ) -> TransactionEffects:
        """Execute a single transaction with conflict tracking and gas management."""
        caching_exec = self._create_caching_executor()

        # Coins mode: checkout gas coin before conflict acquisition so that
        # a slow refill doesn't hold the conflict lock.
        gas_coin: Optional[GasCoin] = None
        if self._gas_mode == "coins":
            assert self._gas_pool is not None
            gas_coin = await self._gas_pool.checkout()
            logger.debug("parallel_exec: checked out gas coin %s", gas_coin.object_id)
            # Seed the per-tx cache with this coin so the tx builder picks it up
            await caching_exec.update_gas_coins([gas_coin.object_id])

        # Extract conflict IDs conservatively from unresolved inputs
        try:
            unresolved = tx.builder.get_unresolved_inputs()
            conflict_ids: set[str] = {u.ObjectStr for u in unresolved.values()}
        except AttributeError:
            # tx does not expose builder.get_unresolved_inputs — no conflict tracking
            conflict_ids = set()

        try:
            async with await self._conflict_tracker.acquire(conflict_ids):
                tx_str = await caching_exec.build_transaction(
                    tx, self._signing_block, gas_budget
                )
                sigs = self._signing_block.get_signatures(
                    config=self._client.config, tx_bytes=tx_str
                )
                effects = await self._execute_single(tx_str, sigs, caching_exec)
                await caching_exec.apply_effects(effects)
                await caching_exec.sync_to_registry(self._registry)

        except Exception:
            # Return gas coin to pool even on failure so the pool doesn't drain
            if gas_coin is not None:
                assert self._gas_pool is not None
                await self._gas_pool.checkin(gas_coin, retire=True)
            raise

        # Post-execution: deduct gas and checkin coin at updated version
        await self._deduct_gas(effects)

        if gas_coin is not None and effects.gas_object is not None:
            assert self._gas_pool is not None
            go = effects.gas_object
            updated_coin = GasCoin(
                object_id=go.object_id,
                version=str(effects.lamport_version),
                digest=go.output_digest or gas_coin.digest,
                balance=max(0, gas_coin.balance - (
                    effects.gas_used.computation_cost
                    + effects.gas_used.storage_cost
                    - effects.gas_used.storage_rebate
                )),
            )
            await self._gas_pool.checkin(updated_coin)
        elif gas_coin is not None:
            assert self._gas_pool is not None
            await self._gas_pool.checkin(gas_coin, retire=True)

        await self._maybe_trigger_refill()
        return effects

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute_transactions(
        self,
        transactions: list,
        gas_budget: Optional[int] = None,
    ) -> list[Union[TransactionEffects, tuple[ExecutorError, Exception]]]:
        """Execute a list of transactions in parallel.

        Returns a list of the same length as ``transactions``. Each element is:
        - ``TransactionEffects``: transaction succeeded
        - ``(ExecutorError, Exception)``: transaction failed

        Ordering within the list matches ``transactions``; per-object conflict
        tracking ensures owned objects are never equivocated across concurrent txs.

        :param transactions: Transactions to execute
        :param gas_budget: Per-transaction gas budget; defaults to constructor value
        :return: Results in input order
        """
        if self._tracked_balance == 0:
            self._tracked_balance = await self._fetch_balance()

        budget = gas_budget if gas_budget is not None else self._default_gas_budget

        async def _run_one(tx) -> Union[TransactionEffects, tuple[ExecutorError, Exception]]:
            try:
                return await self._parallel_queue.run_task(
                    lambda: self._execute_transaction_task(tx, budget)  # type: ignore[arg-type, return-value]
                )
            except Exception as exc:
                logger.warning("parallel_exec: transaction failed: %s", exc)
                return (ExecutorError.EXECUTING_ERROR, exc)

        results = await asyncio.gather(*[_run_one(tx) for tx in transactions])
        return list(results)

    async def reset_pool(self) -> None:
        """Drain the gas coin pool (coins mode only)."""
        if self._gas_pool is not None:
            await self._gas_pool.reset()

    async def seed_coin_pool(self, coins: list[GasCoin]) -> None:
        """Add coins to the gas pool directly (coins mode only).

        Call this before ``execute_transactions`` to seed the pool without
        running an automatic refill.
        """
        if self._gas_pool is None:
            raise RuntimeError("seed_coin_pool is only valid in coins gas mode")
        await self._gas_pool.replenish(coins)

    async def new_transaction(self, **kwargs):
        """Create a new transaction pre-wired for deferred object resolution.

        The transaction is constructed with ``mode=DEFERRED`` so that object
        references produce ``UnresolvedObjectArg`` placeholders rather than
        triggering an eager on-chain fetch.  The per-transaction object cache is
        managed internally by the executor and wired at execution time, so no
        shared ``object_cache`` is injected here.
        """
        from pysui.sui.sui_common.txb_tx_argparse import TxnArgMode  # local: breaks circular import
        kwargs["mode"] = TxnArgMode.DEFERRED
        return await self._client.transaction(**kwargs)
