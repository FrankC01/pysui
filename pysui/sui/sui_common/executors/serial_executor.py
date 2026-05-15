#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Concrete serial transaction executor — protocol-agnostic."""

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.executors.exec_types import (
    ExecutionSkipped,
    ExecutorError,
    GasSummary,
    SerialGasMode,
    GasStatus,
    ExecutorOptions,
    SerialExecutorContext,
)
from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.validators import valid_sui_address
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.sui_commands as cmd

logger = logging.getLogger(__name__)

_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"

_SEND_FUNDS_GAS_OVERHEAD = 3_000_000  # gas budget estimate for the split+send_funds PTB in Option B


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
        gas_mode: SerialGasMode,
        min_threshold_balance: int,
    ) -> None:
        self._client = client
        self._signing_block = signer_block
        self._gas_mode = gas_mode
        self._min_threshold_balance = min_threshold_balance
        self._gas_summary: Optional[GasSummary] = None
        self._tracked_balance: int = 0
        self._cache = _BaseCachingExecutor(
            client=client,
            gas_owner=signer_block.sender_str,
            use_account_gas=(gas_mode == SerialGasMode.ADDRESS_BALANCE),
        )

    def seed_funds(
        self,
        *,
        gas_summary: Optional[GasSummary] = None,
        tracked_balance: int = 0,
    ) -> None:
        """Set initial gas state after executor initialization PTBs complete.

        Called synchronously by the client factory after async init is done.
        COINS mode: gas_summary is the merged fat coin.
        ADDRESS_BALANCE mode: gas_summary is None; tracked_balance is the queried address balance.
        """
        self._gas_summary = gas_summary
        self._tracked_balance = tracked_balance if gas_summary is None else gas_summary.balance

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

        if self._gas_mode == SerialGasMode.COINS:
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
        """ADDRESS_BALANCE mode: send primary coin to account balance via send_funds.

        Option A: use non-primary coin as gas.
        Option B: no separate gas coin but primary has surplus — split and send, primary pays gas.
        Fallback: fetch another coin via GetGas (on_balance_low context only).
        Balance updated from accumulator write in tx result — no network call.
        """
        sorted_candidates = sorted(candidates, key=lambda o: o.balance or 0, reverse=True)
        primary = sorted_candidates[0]
        not_primary = sorted_candidates[1:]

        send_tx = await self._new_transaction()

        if not_primary:
            # Option A: use non-primary as gas coin; send primary whole
            gas_coin = not_primary[0]
            await send_tx.move_call(
                target="0x2::coin::send_funds",
                type_arguments=["0x2::sui::SUI"],
                arguments=[primary, self._signing_block.sender_str],
            )
            gas_obj = sui_prot.Object(
                object_id=gas_coin.object_id,
                version=gas_coin.version,
                digest=gas_coin.digest,
                balance=gas_coin.balance or 0,
            )
            build_dict = await send_tx.build_and_sign(use_gas_objects=[gas_obj])

        elif primary.balance > (self._min_threshold_balance - existing_balance) + _SEND_FUNDS_GAS_OVERHEAD:
            # Option B: split deficit from primary; primary (residual ~3M) pays gas
            amount_to_send = self._min_threshold_balance - existing_balance
            what_we_send = await send_tx.split_coin(coin=send_tx.gas, amounts=[amount_to_send])
            await send_tx.move_call(
                target="0x2::coin::send_funds",
                type_arguments=["0x2::sui::SUI"],
                arguments=[what_we_send, self._signing_block.sender_str],
            )
            gas_obj = sui_prot.Object(
                object_id=primary.object_id,
                version=primary.version,
                digest=primary.digest,
                balance=primary.balance or 0,
            )
            build_dict = await send_tx.build_and_sign(use_gas_objects=[gas_obj])

        else:
            # Fallback: fetch another coin from chain (on_balance_low context only)
            result = await self._client.execute_for_all(
                command=cmd.GetGas(owner=self._signing_block.sender_str)
            )
            if not result.is_ok():
                raise ValueError(f"send_funds: failed to fetch gas coins: {result.result_string}")
            other_coins = [
                o for o in result.result_data.objects
                if o.object_id != primary.object_id
            ]
            if not other_coins:
                raise ValueError("send_funds: no gas coin available — hard stop")
            gas_coin = other_coins[0]
            await send_tx.move_call(
                target="0x2::coin::send_funds",
                type_arguments=["0x2::sui::SUI"],
                arguments=[primary, self._signing_block.sender_str],
            )
            gas_obj = sui_prot.Object(
                object_id=gas_coin.object_id,
                version=gas_coin.version,
                digest=gas_coin.digest,
                balance=gas_coin.balance or 0,
            )
            build_dict = await send_tx.build_and_sign(use_gas_objects=[gas_obj])

        result = await self._client.execute(command=cmd.ExecuteTransaction(**build_dict))
        if not result.is_ok():
            raise ValueError(f"send_funds: transaction failed: {result.result_string}")
        self._update_tracked_balance_from_accumulator(result.result_data)

    async def process(self, txn) -> tuple:
        """Full execution lifecycle. Returns (GasStatus, result).

        result is ExecutedTransaction on success, or (ExecutorError, Exception) on failure.
        Never raises — all failures are returned as (GasStatus.TXN_ERROR, error_tuple).
        """
        gas_objects_override = None
        if self._gas_mode == SerialGasMode.COINS and self._gas_summary is not None:
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

        if self._gas_mode == SerialGasMode.COINS:
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
        """Deduct net gas cost from tracked balance."""
        gas = effects.gas_used
        net_gas = (gas.computation_cost or 0) + (gas.storage_cost or 0) - (gas.storage_rebate or 0)
        self._tracked_balance = max(0, self._tracked_balance - net_gas)

    def _update_tracked_balance_from_accumulator(
        self, executed_tx: "sui_prot.ExecutedTransaction"
    ) -> None:
        """ADDRESS_BALANCE mode: update _tracked_balance from accumulator write in tx result.

        MERGE operation (send_funds): adds value to _tracked_balance.
        SPLIT operation (redeem_funds): subtracts value from _tracked_balance.
        No network call — derives balance from tx result only.
        """
        if executed_tx is None or executed_tx.effects is None:
            return
        for changed_obj in executed_tx.effects.changed_objects:
            output_state = str(changed_obj.output_state)
            if "ACCUMULATOR" in output_state:
                acc = changed_obj.accumulator_write
                if acc is not None:
                    if "MERGE" in str(acc.operation):
                        self._tracked_balance += acc.value
                    elif "SPLIT" in str(acc.operation):
                        self._tracked_balance = max(0, self._tracked_balance - acc.value)
                break

    async def _refresh_coins_balance(self, executed_tx) -> None:
        """COINS mode: update _gas_summary from tx result, then set _tracked_balance."""
        self._update_gas_summary(executed_tx)
        if self._gas_summary:
            self._tracked_balance = self._gas_summary.balance

    async def _new_transaction(self, **kwargs):
        """Create a new DEFERRED transaction using this processor's cache."""
        from pysui.sui.sui_common.txb_tx_argparse import TxnArgMode
        kwargs["mode"] = TxnArgMode.DEFERRED
        kwargs["object_cache"] = self._cache.cache
        return await self._client.transaction(**kwargs)


_SENTINEL = object()


@dataclass
class _QueueItem:
    txn: object
    future: asyncio.Future
    retry_count: int = 0


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
        self._task: Optional[asyncio.Task] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        signer_block = SignerBlock(sender=options.sender)
        self._qp = SerialQueueProcessor(
            client=client,
            signer_block=signer_block,
            gas_mode=options.gas_mode,
            min_threshold_balance=options.min_threshold_balance,
        )

    async def _initialize(self) -> None:
        """Async initialization: fetch/validate coins, seed gas management, start processor."""
        sender = self._qp._signing_block.sender_str
        gas_mode = self._options.gas_mode
        threshold = self._options.min_threshold_balance

        # Step 1: Acquire candidate coins — provided or self-heal via GetGas
        if self._options.initial_coins:
            coins = self._options.initial_coins
            if isinstance(coins[0], str):
                if not all(valid_sui_address(c) for c in coins):
                    raise ValueError("initial_coins: one or more entries are not valid object IDs")
                result = await self._client.execute(
                    command=cmd.GetMultipleObjects(object_ids=list(coins))
                )
                if not result.is_ok():
                    raise ValueError(f"Failed to fetch initial coins: {result.result_string}")
                obj_list = [o for o in result.result_data if o.object_type == _SUI_COIN_TYPE]
            else:
                obj_list = [o for o in coins if o.object_type == _SUI_COIN_TYPE]
        else:
            # Empty or None — self-heal
            result = await self._client.execute_for_all(command=cmd.GetGas(owner=sender))
            if not result.is_ok():
                raise ValueError(f"Failed to fetch gas coins: {result.result_string}")
            obj_list = result.result_data.objects

        if not obj_list:
            raise ValueError(f"No SUI coins found for sender {sender}")

        # Step 2: Working set — sort descending, accumulate until threshold met
        sorted_coins = sorted(obj_list, key=lambda o: o.balance or 0, reverse=True)
        selected = []
        running = 0
        for o in sorted_coins:
            selected.append(o)
            running += o.balance or 0
            if running >= threshold:
                break
        if running < threshold:
            raise ValueError(
                f"Insufficient balance {running} < min_threshold_balance {threshold}"
            )

        # Step 3: Identify primary (fattest — already first after sort)
        primary = selected[0]
        rest = selected[1:]

        # Step 4: Seed gas management BEFORE any PTB so post-tx update methods work uniformly
        if gas_mode == SerialGasMode.COINS:
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
        self._queue.put_nowait(_SENTINEL)
        if self._task is not None:
            await self._task

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
        if self._options.on_balance_low is None:
            logger.warning("SerialExecutor: balance low but no on_balance_low callback — hard stop")
            return False
        ctx = SerialExecutorContext(
            sender=self._qp._signing_block.sender_str,
            tracked_balance=self._qp._tracked_balance,
            min_threshold_balance=self._options.min_threshold_balance,
            client=self._client,
        )
        coins = await self._options.on_balance_low(ctx)
        if not coins:
            logger.warning("SerialExecutor: on_balance_low returned None/[] — hard stop")
            return False
        try:
            await self._qp.add_funds(coins)
        except Exception as exc:
            logger.warning("SerialExecutor: add_funds failed: %s — hard stop", exc)
            return False
        return True

    async def _hard_stop(self, reason: str) -> None:
        """Mark executor dead and drain remaining queued items to ExecutionSkipped."""
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
