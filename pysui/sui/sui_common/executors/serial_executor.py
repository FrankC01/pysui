#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Concrete serial transaction executor — protocol-agnostic."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.executors.exec_types import (
    ExecutionSkipped,
    ExecutorError,
    GasSummary,
    GasMode,
    GasStatus,
    ExecutorOptions,
)
from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
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


class SerialQueueProcessor:
    """Owns gas state and full execution lifecycle for SerialExecutor.

    Mode-aware: COINS mode manages a master gas coin (_gas_summary);
    ADDRESS_BALANCE mode uses use_account_for_gas and tracks total address balance.
    Never calls on_balance_low — that is the coroutine's responsibility.
    """

    def __init__(
        self,
        *,
        client,
        signer_block: SignerBlock,
        gas_mode: GasMode,
        min_threshold_balance: int,
    ) -> None:
        self._client = client
        self._signing_block = signer_block
        self._gas_mode = gas_mode
        self._min_threshold_balance = min_threshold_balance
        self._gas_summary: GasSummary | None = None
        self._tracked_balance: int = 0
        self._cache = _BaseCachingExecutor(
            client=client,
            gas_owner=signer_block.sender_str,
            use_account_gas=(gas_mode == GasMode.ADDRESS_BALANCE),
        )

    def seed_funds(
        self,
        *,
        gas_summary: GasSummary | None = None,
        tracked_balance: int = 0,
    ) -> None:
        """Set initial gas state after executor initialization PTBs complete.

        Called synchronously by the client factory after async init is done.
        COINS mode: gas_summary is the merged fat coin.
        ADDRESS_BALANCE mode: gas_summary is None; tracked_balance is the queried address balance.
        """
        self._gas_summary = gas_summary
        self._tracked_balance = tracked_balance if gas_summary is None else gas_summary.balance

    @property
    def sender_str(self) -> str:
        return self._signing_block.sender_str

    @property
    def tracked_balance(self) -> int:
        return self._tracked_balance

    async def add_funds(self, coins: list) -> None:
        """Merge new coins into gas state after on_balance_low returns candidates.

        COINS mode: merges candidates into the master gas coin, updates _gas_summary.
        ADDRESS_BALANCE mode: sends primary candidate to account balance, updates _tracked_balance.
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
        if total < self._min_threshold_balance:
            raise ValueError(
                f"add_funds: provided coins total {total} < min_threshold_balance {self._min_threshold_balance}"
            )

        if self._gas_mode == GasMode.COINS:
            await self._merge_into_gas_coin(candidates)
        else:
            await self._send_funds_to_account(candidates, self._tracked_balance)

    async def _merge_into_gas_coin(self, candidates: list) -> None:
        """COINS mode: merge candidates into master gas coin, update _gas_summary."""
        merge_tx = await self._new_transaction()
        await merge_tx.merge_coins(merge_to=merge_tx.gas, merge_from=candidates)
        gas_obj = sui_prot.Object(
            object_id=self._gas_summary.objectId,
            version=int(self._gas_summary.version),
            digest=self._gas_summary.digest,
            balance=self._gas_summary.balance,
        )
        build_dict = await merge_tx.build_and_sign(use_gas_objects=[gas_obj])
        result = await self._client.execute(command=cmd.ExecuteTransaction(**build_dict))
        if not result.is_ok():
            raise ValueError(f"add_funds: merge failed: {result.result_string}")
        await self._refresh_coins_balance(result.result_data)

    async def _send_funds_to_account(self, candidates: list, existing_balance: int = 0) -> None:
        executed_tx = await send_funds_to_account(
            client=self._client,
            sender=self._signing_block.sender_str,
            candidates=candidates,
            existing_balance=existing_balance,
            min_threshold_balance=self._min_threshold_balance,
            new_transaction_fn=self._new_transaction,
        )
        self._update_tracked_balance_from_accumulator(executed_tx)

    async def process(self, txn) -> tuple:
        """Full execution lifecycle. Returns (GasStatus, result).

        result is ExecutedTransaction on success, or (ExecutorError, Exception) on failure.
        Never raises — all failures are returned as (GasStatus.TXN_ERROR, error_tuple).
        """
        gas_objects_override = None
        if self._gas_mode == GasMode.COINS and self._gas_summary is not None:
            gas_objects_override = [
                sui_prot.Object(
                    object_id=self._gas_summary.objectId,
                    version=int(self._gas_summary.version),
                    digest=self._gas_summary.digest,
                    balance=self._gas_summary.balance,
                )
            ]

        try:
            signed_tx = await self._cache.build_transaction(
                txn, self._signing_block, gas_objects_override
            )
        except Exception as exc:
            logger.warning("SerialQueueProcessor: build_transaction failed: %s", exc)
            return GasStatus.TXN_ERROR, (ExecutorError.BUILDING_ERROR, exc)

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
            logger.warning("SerialQueueProcessor: execute failed: %s", exc)
            error_str = str(exc).lower()
            if "insufficient gas" in error_str or "insufficient_gas" in error_str:
                return GasStatus.NEED_FUNDS_AND_RETRY, (ExecutorError.EXECUTING_ERROR, exc)
            return GasStatus.TXN_ERROR, (ExecutorError.EXECUTING_ERROR, exc)

        await self._cache.apply_effects(executed_tx.effects)
        self._update_gas_summary(executed_tx)
        self._update_tracked_balance(executed_tx.effects)

        if self._gas_mode == GasMode.COINS:
            if executed_tx.effects and executed_tx.effects.gas_object:
                go = executed_tx.effects.gas_object
                if go.object_id:
                    await self._cache.update_gas_coins([go.object_id])
                else:
                    await self._cache.invalidate_gas_coins()
            else:
                await self._cache.invalidate_gas_coins()

        if self._tracked_balance > 0 and self._tracked_balance < self._min_threshold_balance:
            return GasStatus.NEED_FUNDS, executed_tx

        return GasStatus.OK, executed_tx

    def _update_gas_summary(self, executed_tx: "sui_prot.ExecutedTransaction") -> None:
        """Update _gas_summary version/digest/balance from ExecutedTransaction."""
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
            target_version = int(self._gas_summary.version) if self._gas_summary.version else None
            for obj in executed_tx.objects.objects:
                if obj.object_id == self._gas_summary.objectId:
                    if target_version is None or obj.version == target_version:
                        if obj.balance is not None:
                            self._gas_summary.balance = obj.balance
                        break

    def _update_tracked_balance(self, effects: "sui_prot.TransactionEffects") -> None:
        self._tracked_balance = update_tracked_balance(effects, self._tracked_balance)

    def _update_tracked_balance_from_accumulator(
        self, executed_tx: "sui_prot.ExecutedTransaction"
    ) -> None:
        self._tracked_balance = update_tracked_balance_from_accumulator(executed_tx, self._tracked_balance)

    async def _refresh_coins_balance(self, executed_tx) -> None:
        """COINS mode: update _gas_summary from tx result, then set _tracked_balance."""
        self._update_gas_summary(executed_tx)
        if self._gas_summary:
            self._tracked_balance = self._gas_summary.balance

    async def _new_transaction(self, **kwargs):
        """Create a new DEFERRED transaction using this processor's cache."""
        kwargs["mode"] = TxnArgMode.DEFERRED
        kwargs["object_cache"] = self._cache.cache
        return await self._client.transaction(**kwargs)


class SerialExecutor:
    """Serial transaction executor using asyncio.Queue + background coroutine.

    Obtain via ``await client.serial_executor(options=ExecutorOptions(...))``.
    Do not instantiate directly — the client factory performs async initialization.

    submit() is the unified entry point for single or batch submission.
    Each transaction resolves to one of:
    - ExecutedTransaction: success
    - (ExecutorError, Exception): failure
    - ExecutionSkipped: not attempted due to hard stop
    """

    def __init__(self, *, client, options: ExecutorOptions) -> None:
        self._client = client
        self._options = options
        self._dead: bool = False
        self._closing: bool = False
        self._task: asyncio.Task[None] | None = None
        self._queue: asyncio.Queue[_QueueItem | object] = asyncio.Queue()
        signer_block = SignerBlock(sender=options.sender)
        self._qp = SerialQueueProcessor(
            client=client,
            signer_block=signer_block,
            gas_mode=options.gas_mode,
            min_threshold_balance=options.min_threshold_balance,
        )

    async def _initialize(self) -> None:
        """Async initialization: fetch/validate coins, seed gas management, start processor."""
        sender = self._qp.sender_str
        gas_mode = self._options.gas_mode
        threshold = self._options.min_threshold_balance

        selected = await acquire_coins(
            client=self._client,
            sender=sender,
            initial_coins=self._options.initial_coins,
            threshold=threshold,
        )

        # Step 3: Identify primary (fattest — already first after sort)
        primary = selected[0]
        rest = selected[1:]

        # Step 4: Seed gas management BEFORE any PTB so post-tx update methods work uniformly
        if gas_mode == GasMode.COINS:
            fat_coin = GasSummary(
                objectId=primary.object_id,
                version=str(primary.version),
                digest=primary.digest,
                balance=primary.balance or 0,
            )
            self._qp.seed_funds(gas_summary=fat_coin)

            # Step 5a: Merge rest into primary if needed
            if rest:
                merge_tx = await self._qp._new_transaction()
                await merge_tx.merge_coins(merge_to=merge_tx.gas, merge_from=rest)
                gas_obj = sui_prot.Object(
                    object_id=primary.object_id,
                    version=primary.version,
                    digest=primary.digest,
                    balance=primary.balance or 0,
                )
                build_dict = await merge_tx.build_and_sign(use_gas_objects=[gas_obj])
                merge_result = await self._client.execute(
                    command=cmd.ExecuteTransaction(**build_dict)
                )
                if not merge_result.is_ok():
                    raise ValueError(f"Initialization merge failed: {merge_result.result_string}")
                await self._qp._refresh_coins_balance(merge_result.result_data)

        else:
            # ADDRESS_BALANCE: query existing balance once to seed, then send_funds
            bal_result = await self._client.execute(
                command=cmd.GetAddressCoinBalance(owner=sender)
            )
            if not bal_result.is_ok():
                raise ValueError(f"Failed to query address balance: {bal_result.result_string}")
            existing_balance = bal_result.result_data.balance.address_balance
            self._qp.seed_funds(tracked_balance=existing_balance)

            # Step 5b: Only send funds if existing balance is below threshold
            if existing_balance < threshold:
                await self._qp._send_funds_to_account(selected, existing_balance)

        self._task = asyncio.create_task(self._processor_loop())

    def submit(self, txn) -> "asyncio.Future | list[asyncio.Future]":
        """Submit one or more transactions for serial execution.

        :param txn: A single AsyncSuiTransaction or a list of them.
        :return: A single Future for a single transaction; list of Futures for a list.
        """
        if isinstance(txn, list):
            return [self._submit_one(t) for t in txn]
        return self._submit_one(txn)

    def _submit_one(self, txn) -> asyncio.Future:
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        if self._dead:
            future.set_result(
                ExecutionSkipped(transaction_index=-1, reason="Executor is dead")
            )
            return future
        self._queue.put_nowait(_QueueItem(txn=txn, future=future))
        return future

    async def close(self) -> None:
        """Signal shutdown and wait for the processor coroutine to finish."""
        if not self._closing:
            self._closing = True
            self._queue.put_nowait(_SENTINEL)
        if self._task is not None:
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def new_transaction(self, **kwargs):
        """Create a new DEFERRED transaction using this executor's object cache."""
        return await self._qp._new_transaction(**kwargs)

    async def _processor_loop(self) -> None:
        """Background coroutine: dequeues and processes transactions one at a time."""
        while True:
            item = await self._queue.get()
            if item is _SENTINEL:
                self._queue.task_done()
                break
            await self._process_item(item)
            self._queue.task_done()

    async def _process_item(self, item: _QueueItem) -> None:
        """Process one queue item through its full lifecycle including retry."""
        status, result = await self._qp.process(item.txn)

        match status:
            case GasStatus.OK:
                item.future.set_result(result)

            case GasStatus.TXN_ERROR:
                item.future.set_result(result)
                if self._options.on_failure == "exit":
                    await self._hard_stop("Transaction error with on_failure=exit")

            case GasStatus.NEED_FUNDS:
                item.future.set_result(result)
                if not await self._replenish():
                    await self._hard_stop("on_balance_low declined or failed")

            case GasStatus.NEED_FUNDS_AND_RETRY:
                while True:
                    if item.retry_count >= self._options.max_retries:
                        item.future.set_result(result)
                        await self._hard_stop("Max retries exhausted")
                        return
                    if not await self._replenish():
                        item.future.set_result(result)
                        await self._hard_stop("on_balance_low declined on retry")
                        return
                    item.retry_count += 1
                    status, result = await self._qp.process(item.txn)
                    if status != GasStatus.NEED_FUNDS_AND_RETRY:
                        break

                # Dispatch on final retry outcome
                item.future.set_result(result)
                if status == GasStatus.NEED_FUNDS:
                    if not await self._replenish():
                        await self._hard_stop("on_balance_low declined after retry")
                elif status == GasStatus.TXN_ERROR and self._options.on_failure == "exit":
                    await self._hard_stop("Transaction error after retry with on_failure=exit")

            case _:
                item.future.set_result(result)

    async def _replenish(self) -> bool:
        """Call on_balance_low; pass returned coins to QP.add_funds(). Returns False on hard stop."""
        return await run_replenishment(
            on_balance_low=self._options.on_balance_low,
            sender=self._qp.sender_str,
            tracked_balance=self._qp.tracked_balance,
            min_threshold_balance=self._options.min_threshold_balance,
            client=self._client,
            add_funds_fn=self._qp.add_funds,
            label="SerialExecutor",
        )

    async def _hard_stop(self, reason: str) -> None:
        """Mark executor dead and drain remaining queued items to ExecutionSkipped."""
        if self._dead:
            return
        self._dead = True
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                if item is not _SENTINEL:
                    item.future.set_result(
                        ExecutionSkipped(transaction_index=-1, reason=reason)
                    )
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        self._queue.put_nowait(_SENTINEL)
        if self._task is not None and not self._task.done():
            self._task.cancel()
