#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Concrete parallel transaction executor — protocol-agnostic."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

from pysui.sui.sui_common.txb_signing import SignerBlock
from pysui.sui.sui_common.executors.exec_types import (
    ExecutionSkipped,
    ExecutorError,
    GasMode,
    ExecutorOptions,
)
from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.executors.conflict_tracker import ConflictTracker
from pysui.sui.sui_common.executors.gas_pool import GasCoin, GasCoinPool
from pysui.sui.sui_common.executors.object_registry import (
    AbstractObjectRegistry,
    get_object_registry,
)
from pysui.sui.sui_common.executors.gas_utils import (
    _SUI_COIN_TYPE,
    acquire_coins,
    send_funds_to_account,
    update_tracked_balance,
    update_tracked_balance_from_accumulator,
    run_replenishment,
)
from pysui.sui.sui_common.executors._queue_types import _SENTINEL, _QueueItem
from pysui.sui.sui_common.validators import valid_sui_address
from pysui.sui.sui_common.txb_tx_argparse import TxnArgMode
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.sui_commands as cmd

logger = logging.getLogger(__name__)


class _BaseParallelExecutor:
    """Protocol-agnostic concrete parallel transaction executor.

    Obtain via ``await client.parallel_executor(options=ExecutorOptions(...))``.
    Do not instantiate directly — the client factory performs async initialization.

    submit() is the entry point. Returns asyncio.Future(s).

    Two gas modes:
    - GasMode.COINS: GasCoinPool; one coin checked out per in-flight transaction.
    - GasMode.ADDRESS_BALANCE: no coin pool; use_account_for_gas path.

    Conflict tracking serializes transactions sharing owned object inputs,
    preventing equivocation while allowing concurrent execution of non-conflicting txns.
    """

    def __init__(self, *, client, options: ExecutorOptions) -> None:
        self._client = client
        self._options = options
        self._dead: bool = False
        self._closing: bool = False
        self._build_task: asyncio.Task[None] | None = None
        self._build_queue: asyncio.Queue[_QueueItem | object] = asyncio.Queue()
        self._in_flight: set[asyncio.Task[None]] = set()
        self._semaphore = asyncio.Semaphore(options.max_concurrent)
        self._conflict_tracker = ConflictTracker()
        self._registry: AbstractObjectRegistry = get_object_registry()
        self._tracked_balance: int = 0
        self._signing_block = SignerBlock(sender=options.sender)

        if options.gas_mode == GasMode.COINS:
            self._gas_pool: GasCoinPool | None = GasCoinPool()
        else:
            self._gas_pool = None

    async def _initialize(self) -> None:
        """Async init: seed gas state, start build worker. Called by client factory."""
        sender = self._signing_block.sender_str
        gas_mode = self._options.gas_mode
        threshold = self._options.min_threshold_balance

        selected = await acquire_coins(
            client=self._client,
            sender=sender,
            initial_coins=self._options.initial_coins,
            threshold=threshold,
        )

        if gas_mode == GasMode.COINS:
            gas_coins = [
                GasCoin(
                    object_id=o.object_id,
                    version=str(o.version),
                    digest=o.digest,
                    balance=o.balance or 0,
                )
                for o in selected
            ]
            await self._gas_pool.replenish(gas_coins)
            self._tracked_balance = sum(c.balance for c in gas_coins)
        else:
            bal_result = await self._client.execute(
                command=cmd.GetAddressCoinBalance(owner=sender)
            )
            if not bal_result.is_ok():
                raise ValueError(f"Failed to query address balance: {bal_result.result_string}")
            existing_balance = bal_result.result_data.balance.address_balance
            self._tracked_balance = existing_balance
            if existing_balance < threshold:
                await self._send_funds_to_account(selected, existing_balance)

        self._build_task = asyncio.create_task(self._build_worker())

    async def _add_funds(self, coins: list) -> None:
        """Merge new coins into gas state after on_balance_low returns candidates.

        COINS mode: adds coins directly to GasCoinPool.
        ADDRESS_BALANCE mode: sends primary candidate via send_funds PTB.
        """
        if not coins:
            raise ValueError("add_funds: coin list is empty")

        if isinstance(coins[0], str):
            if not all(valid_sui_address(c) for c in coins):
                raise ValueError("add_funds: one or more entries are not valid object IDs")
            result = await self._client.execute(
                command=cmd.GetMultipleObjects(object_ids=list(coins))
            )
            if not result.is_ok():
                raise ValueError(f"add_funds: failed to fetch coin objects: {result.result_string}")
            candidates = [o for o in result.result_data if o.object_type == _SUI_COIN_TYPE]
        else:
            candidates = [o for o in coins if o.object_type == _SUI_COIN_TYPE]

        if not candidates:
            raise ValueError("add_funds: no SUI coins in provided list")

        total = sum(o.balance or 0 for o in candidates)
        if total < self._options.min_threshold_balance:
            raise ValueError(
                f"add_funds: provided coins total {total} < min_threshold_balance {self._options.min_threshold_balance}"
            )

        if self._options.gas_mode == GasMode.COINS:
            gas_coins = [
                GasCoin(
                    object_id=o.object_id,
                    version=str(o.version),
                    digest=o.digest,
                    balance=o.balance or 0,
                )
                for o in candidates
            ]
            await self._gas_pool.replenish(gas_coins)
            self._tracked_balance += sum(c.balance for c in gas_coins)
        else:
            await self._send_funds_to_account(candidates, self._tracked_balance)

    async def _send_funds_to_account(self, candidates: list, existing_balance: int = 0) -> None:
        executed_tx = await send_funds_to_account(
            client=self._client,
            sender=self._signing_block.sender_str,
            candidates=candidates,
            existing_balance=existing_balance,
            min_threshold_balance=self._options.min_threshold_balance,
            new_transaction_fn=self._new_transaction,
        )
        self._update_tracked_balance_from_accumulator(executed_tx)

    async def _new_transaction(self, **kwargs):
        """Internal: create a DEFERRED transaction without shared cache injection."""
        kwargs["mode"] = TxnArgMode.DEFERRED
        return await self._client.transaction(**kwargs)

    def _submit_one(self, txn) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        if self._dead:
            future.set_result(
                ExecutionSkipped(transaction_index=-1, reason="Executor is dead")
            )
            return future
        self._build_queue.put_nowait(_QueueItem(txn=txn, future=future))
        return future

    async def _build_worker(self) -> None:
        """Serial background coroutine: acquire conflict + gas, dispatch execute tasks."""
        while True:
            try:
                item = await self._build_queue.get()
            except asyncio.CancelledError:
                break
            if item is _SENTINEL:
                self._build_queue.task_done()
                break

            if self._dead:
                item.future.set_result(
                    ExecutionSkipped(transaction_index=-1, reason="Executor is dead")
                )
                self._build_queue.task_done()
                continue

            # Conflict acquisition — blocks until all object IDs are free
            try:
                unresolved = item.txn.builder.get_unresolved_inputs()
                conflict_ids: set[str] = {
                    u.ObjectStr for u in unresolved.values()
                    if hasattr(u, "ObjectStr")
                }
            except (AttributeError, TypeError):
                conflict_ids = set()
            reservation = await self._conflict_tracker.acquire(conflict_ids)

            # Bound concurrency — block here if max_concurrent tasks are running
            await self._semaphore.acquire()

            # Gas checkout — blocks if pool is empty (back-pressure in COINS mode)
            gas_coin: GasCoin | None = None
            if self._options.gas_mode == GasMode.COINS:
                gas_coin = await self._gas_pool.checkout()

            # Per-transaction caching executor (isolated; not shared across tasks)
            caching_exec = _BaseCachingExecutor(
                client=self._client,
                gas_owner=self._signing_block.sender_str,
                use_account_gas=(self._options.gas_mode == GasMode.ADDRESS_BALANCE),
            )
            if gas_coin is not None:
                await caching_exec.update_gas_coins([gas_coin.object_id])

            task = asyncio.create_task(
                self._execute_item(item, gas_coin, reservation, caching_exec)
            )
            self._in_flight.add(task)
            task.add_done_callback(self._in_flight.discard)

            self._build_queue.task_done()

    async def _execute_item(
        self,
        item: _QueueItem,
        gas_coin: GasCoin | None,
        reservation,
        caching_exec: _BaseCachingExecutor,
    ) -> None:
        """Parallel execute task: build+execute transaction, update gas, release conflict."""
        semaphore_held = True
        try:
            async with reservation:
                while True:
                    # Ensure gas coin is reflected in cache (after retry re-checkout)
                    if gas_coin is not None:
                        await caching_exec.update_gas_coins([gas_coin.object_id])

                    gas_objects_override = None
                    if gas_coin is not None:
                        gas_objects_override = [
                            sui_prot.Object(
                                object_id=gas_coin.object_id,
                                version=int(gas_coin.version),
                                digest=gas_coin.digest,
                                balance=gas_coin.balance,
                            )
                        ]

                    try:
                        signed_tx = await caching_exec.build_transaction(
                            item.txn, self._signing_block, gas_objects_override
                        )
                    except Exception as exc:
                        logger.warning("_BaseParallelExecutor: build failed: %s", exc)
                        if gas_coin is not None:
                            await self._gas_pool.checkin(gas_coin, retire=True)
                            gas_coin = None
                        if not item.future.done():
                            item.future.set_result((ExecutorError.BUILDING_ERROR, exc))
                        return

                    try:
                        exec_result = await self._client.execute(
                            command=cmd.ExecuteTransaction(
                                tx_bytestr=signed_tx["tx_bytestr"],
                                sig_array=signed_tx["sig_array"],
                            )
                        )
                        if not exec_result.is_ok():
                            raise ValueError(f"ExecuteTransaction failed: {exec_result.result_string}")
                        executed_tx: sui_prot.ExecutedTransaction = exec_result.result_data
                    except Exception as exc:
                        error_str = str(exc).lower()
                        is_gas_error = (
                            "insufficient gas" in error_str or
                            "insufficient_gas" in error_str
                        )

                        if is_gas_error and item.retry_count < self._options.max_retries:
                            if gas_coin is not None:
                                await self._gas_pool.checkin(gas_coin, retire=True)
                                gas_coin = None
                            if not await self._replenish():
                                item.future.set_result((ExecutorError.EXECUTING_ERROR, exc))
                                await self._hard_stop("on_balance_low declined on gas retry")
                                return
                            item.retry_count += 1
                            if self._options.gas_mode == GasMode.COINS:
                                self._semaphore.release()
                                semaphore_held = False
                                gas_coin = await self._gas_pool.checkout()
                                await self._semaphore.acquire()
                                semaphore_held = True
                            continue

                        if gas_coin is not None:
                            await self._gas_pool.checkin(gas_coin, retire=True)
                            gas_coin = None
                        if not item.future.done():
                            item.future.set_result((ExecutorError.EXECUTING_ERROR, exc))
                        if is_gas_error:
                            await self._hard_stop("gas retries exhausted")
                        elif self._options.on_failure == "exit":
                            await self._hard_stop("transaction error with on_failure=exit")
                        return

                    await caching_exec.apply_effects(executed_tx.effects)
                    await caching_exec.sync_to_registry(self._registry)

                    if self._options.gas_mode == GasMode.COINS and gas_coin is not None:
                        updated = self._update_gas_coin(executed_tx, gas_coin)
                        await self._gas_pool.checkin(updated)
                        gas_coin = None

                    # Gas cost always deducted; accumulator tracks MERGE/SPLIT in ADDRESS_BALANCE
                    self._update_tracked_balance(executed_tx.effects)
                    if self._options.gas_mode == GasMode.ADDRESS_BALANCE:
                        self._update_tracked_balance_from_accumulator(executed_tx)

                    if not item.future.done():
                        item.future.set_result(executed_tx)

                    if self._tracked_balance < self._options.min_threshold_balance:
                        if not await self._replenish():
                            await self._hard_stop("on_balance_low declined after success")

                    return

        finally:
            if gas_coin is not None:
                await self._gas_pool.checkin(gas_coin, retire=True)
            if semaphore_held:
                self._semaphore.release()

    def _update_gas_coin(
        self, executed_tx: "sui_prot.ExecutedTransaction", gas_coin: GasCoin
    ) -> GasCoin:
        """Return updated GasCoin with version/digest/balance from ExecutedTransaction."""
        new_version = gas_coin.version
        new_digest = gas_coin.digest
        new_balance = gas_coin.balance

        effects = executed_tx.effects
        if effects and effects.gas_object:
            go = effects.gas_object
            if go.output_version is not None:
                new_version = str(go.output_version)
            if go.output_digest is not None:
                new_digest = go.output_digest

        if executed_tx.objects:
            target_version = int(new_version) if new_version else None
            for obj in executed_tx.objects.objects:
                if obj.object_id == gas_coin.object_id:
                    if target_version is None or obj.version == target_version:
                        if obj.balance is not None:
                            new_balance = obj.balance
                        break

        return GasCoin(
            object_id=gas_coin.object_id,
            version=new_version,
            digest=new_digest,
            balance=new_balance,
        )

    def _update_tracked_balance(self, effects: "sui_prot.TransactionEffects") -> None:
        self._tracked_balance = update_tracked_balance(effects, self._tracked_balance)

    def _update_tracked_balance_from_accumulator(
        self, executed_tx: "sui_prot.ExecutedTransaction"
    ) -> None:
        self._tracked_balance = update_tracked_balance_from_accumulator(executed_tx, self._tracked_balance)

    async def _replenish(self) -> bool:
        """Call on_balance_low; pass returned coins to _add_funds(). Returns False on hard stop."""
        return await run_replenishment(
            on_balance_low=self._options.on_balance_low,
            sender=self._signing_block.sender_str,
            tracked_balance=self._tracked_balance,
            min_threshold_balance=self._options.min_threshold_balance,
            client=self._client,
            add_funds_fn=self._add_funds,
            label="_BaseParallelExecutor",
        )

    async def _hard_stop(self, reason: str) -> None:
        """Mark executor dead and drain build queue items to ExecutionSkipped."""
        if self._dead:
            return
        self._dead = True
        while not self._build_queue.empty():
            try:
                item = self._build_queue.get_nowait()
                if item is not _SENTINEL:
                    item.future.set_result(
                        ExecutionSkipped(transaction_index=-1, reason=reason)
                    )
                self._build_queue.task_done()
            except asyncio.QueueEmpty:
                break
        self._build_queue.put_nowait(_SENTINEL)
        if self._build_task is not None and not self._build_task.done():
            self._build_task.cancel()
