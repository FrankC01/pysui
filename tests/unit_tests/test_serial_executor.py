#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for SerialExecutor and SerialQueueProcessor."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_common.executors import (
    ExecutionSkipped,
    ExecutorError,
    GasSummary,
)
from pysui.sui.sui_common.executors.exec_types import (
    ExecutorOptions,
    SerialGasMode,
    GasStatus,
    SerialExecutorContext,
)
from pysui.sui.sui_common.executors.serial_executor import SerialExecutor


_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_executor(gas_mode=SerialGasMode.COINS, **option_kwargs) -> SerialExecutor:
    """Build a SerialExecutor with a MagicMock client — no network, no async init."""
    mock_client = MagicMock()
    mock_client.config = MagicMock()
    options = ExecutorOptions(
        sender="0xsender",
        gas_mode=gas_mode,
        initial_coins=[],
        min_threshold_balance=10_000_000,
        **option_kwargs,
    )
    return SerialExecutor(client=mock_client, options=options)


def _mock_executed_tx(computation_cost=1000, storage_cost=500, storage_rebate=200):
    """Build a minimal mock ExecutedTransaction."""
    gas = MagicMock()
    gas.computation_cost = computation_cost
    gas.storage_cost = storage_cost
    gas.storage_rebate = storage_rebate
    effects = MagicMock()
    effects.gas_used = gas
    effects.gas_object = None
    effects.changed_objects = []
    executed_tx = MagicMock()
    executed_tx.effects = effects
    executed_tx.objects = None
    return executed_tx


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

class TestSerialExecutorConstruction:
    """Test SerialExecutor init (sync, no network)."""

    def test_executor_created(self):
        ex = _make_executor()
        assert ex is not None

    def test_executor_not_dead_initially(self):
        ex = _make_executor()
        assert ex._dead is False

    def test_executor_task_none_initially(self):
        ex = _make_executor()
        assert ex._task is None

    def test_executor_has_queue_processor(self):
        ex = _make_executor()
        assert ex._qp is not None

    def test_executor_has_empty_queue(self):
        ex = _make_executor()
        assert ex._queue.empty()

    def test_coins_mode_executor(self):
        ex = _make_executor(gas_mode=SerialGasMode.COINS)
        assert ex._options.gas_mode == SerialGasMode.COINS

    def test_address_balance_mode_executor(self):
        ex = _make_executor(gas_mode=SerialGasMode.ADDRESS_BALANCE)
        assert ex._options.gas_mode == SerialGasMode.ADDRESS_BALANCE

    def test_executor_has_new_transaction_method(self):
        assert hasattr(SerialExecutor, "new_transaction")

    def test_executor_has_submit_method(self):
        assert hasattr(SerialExecutor, "submit")

    def test_executor_has_close_method(self):
        assert hasattr(SerialExecutor, "close")


# ---------------------------------------------------------------------------
# Submit tests
# ---------------------------------------------------------------------------

class TestSubmit:
    """Test submit() — Future creation and dead-executor gate."""

    @pytest.mark.asyncio
    async def test_submit_single_returns_future(self):
        ex = _make_executor()
        executed_tx = _mock_executed_tx()
        with patch.object(ex._qp, "process", new=AsyncMock(return_value=(GasStatus.OK, executed_tx))):
            ex._task = asyncio.create_task(ex._processor_loop())
            fut = ex.submit(MagicMock())
            assert isinstance(fut, asyncio.Future)
            result = await fut
            await ex.close()
        assert result is executed_tx

    @pytest.mark.asyncio
    async def test_submit_list_returns_list_of_futures(self):
        ex = _make_executor()
        executed_tx = _mock_executed_tx()
        with patch.object(ex._qp, "process", new=AsyncMock(return_value=(GasStatus.OK, executed_tx))):
            ex._task = asyncio.create_task(ex._processor_loop())
            futs = ex.submit([MagicMock(), MagicMock(), MagicMock()])
            assert isinstance(futs, list)
            assert len(futs) == 3
            results = await asyncio.gather(*futs)
            await ex.close()
        assert all(r is executed_tx for r in results)

    @pytest.mark.asyncio
    async def test_submit_to_dead_executor_returns_skipped(self):
        ex = _make_executor()
        ex._dead = True
        fut = ex.submit(MagicMock())
        result = fut.result()
        assert isinstance(result, ExecutionSkipped)

    @pytest.mark.asyncio
    async def test_submit_list_to_dead_executor_all_skipped(self):
        ex = _make_executor()
        ex._dead = True
        futs = ex.submit([MagicMock(), MagicMock()])
        results = [f.result() for f in futs]
        assert all(isinstance(r, ExecutionSkipped) for r in results)

    @pytest.mark.asyncio
    async def test_txn_error_continue_does_not_kill_executor(self):
        ex = _make_executor(on_failure="continue")
        error_result = (ExecutorError.EXECUTING_ERROR, ValueError("failed"))
        with patch.object(ex._qp, "process", new=AsyncMock(return_value=(GasStatus.TXN_ERROR, error_result))):
            ex._task = asyncio.create_task(ex._processor_loop())
            fut = ex.submit(MagicMock())
            result = await fut
            await ex.close()
        assert result is error_result
        assert ex._dead is False

    @pytest.mark.asyncio
    async def test_txn_error_exit_kills_executor(self):
        ex = _make_executor(on_failure="exit")
        error_result = (ExecutorError.EXECUTING_ERROR, ValueError("failed"))
        process_mock = AsyncMock(side_effect=[(GasStatus.TXN_ERROR, error_result)])
        with patch.object(ex._qp, "process", new=process_mock):
            ex._task = asyncio.create_task(ex._processor_loop())
            futs = ex.submit([MagicMock(), MagicMock()])
            results = await asyncio.gather(*futs)
            await ex.close()
        assert results[0] is error_result
        assert isinstance(results[1], ExecutionSkipped)
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_need_funds_no_callback_hard_stop(self):
        ex = _make_executor()  # no on_balance_low
        executed_tx = _mock_executed_tx()
        process_mock = AsyncMock(side_effect=[(GasStatus.NEED_FUNDS, executed_tx)])
        with patch.object(ex._qp, "process", new=process_mock):
            ex._task = asyncio.create_task(ex._processor_loop())
            futs = ex.submit([MagicMock(), MagicMock()])
            results = await asyncio.gather(*futs)
            await ex.close()
        assert results[0] is executed_tx
        assert isinstance(results[1], ExecutionSkipped)
        assert ex._dead is True


# ---------------------------------------------------------------------------
# SerialQueueProcessor unit tests
# ---------------------------------------------------------------------------

class TestSerialQueueProcessor:
    """Test SerialQueueProcessor state management (no network)."""

    def test_seed_funds_coins_mode_sets_gas_summary(self):
        ex = _make_executor(gas_mode=SerialGasMode.COINS)
        summary = GasSummary(objectId="0x1", version="1", digest="d", balance=100_000_000)
        ex._qp.seed_funds(gas_summary=summary)
        assert ex._qp._gas_summary is summary
        assert ex._qp._tracked_balance == 100_000_000

    def test_seed_funds_address_balance_mode_no_summary(self):
        ex = _make_executor(gas_mode=SerialGasMode.ADDRESS_BALANCE)
        ex._qp.seed_funds(tracked_balance=50_000_000)
        assert ex._qp._gas_summary is None
        assert ex._qp._tracked_balance == 50_000_000

    def test_update_tracked_balance_deducts_net_gas(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        effects = MagicMock()
        effects.gas_used.computation_cost = 1000
        effects.gas_used.storage_cost = 500
        effects.gas_used.storage_rebate = 200
        ex._qp._update_tracked_balance(effects)
        assert ex._qp._tracked_balance == 1_000_000 - (1000 + 500 - 200)

    def test_update_tracked_balance_clamps_to_zero(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 100
        effects = MagicMock()
        effects.gas_used.computation_cost = 10_000
        effects.gas_used.storage_cost = 5_000
        effects.gas_used.storage_rebate = 0
        ex._qp._update_tracked_balance(effects)
        assert ex._qp._tracked_balance == 0

    def test_update_tracked_balance_from_accumulator_merge(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        acc = MagicMock()
        acc.operation = "MERGE"
        acc.value = 500_000
        changed_obj = MagicMock()
        changed_obj.output_state = "ACCUMULATOR_WRITE"
        changed_obj.accumulator_write = acc
        executed_tx = MagicMock()
        executed_tx.effects.changed_objects = [changed_obj]
        ex._qp._update_tracked_balance_from_accumulator(executed_tx)
        assert ex._qp._tracked_balance == 1_500_000

    def test_update_tracked_balance_from_accumulator_split(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        acc = MagicMock()
        acc.operation = "SPLIT"
        acc.value = 300_000
        changed_obj = MagicMock()
        changed_obj.output_state = "ACCUMULATOR_WRITE"
        changed_obj.accumulator_write = acc
        executed_tx = MagicMock()
        executed_tx.effects.changed_objects = [changed_obj]
        ex._qp._update_tracked_balance_from_accumulator(executed_tx)
        assert ex._qp._tracked_balance == 700_000

    def test_update_tracked_balance_from_accumulator_split_clamps_to_zero(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 100
        acc = MagicMock()
        acc.operation = "SPLIT"
        acc.value = 1_000_000
        changed_obj = MagicMock()
        changed_obj.output_state = "ACCUMULATOR_WRITE"
        changed_obj.accumulator_write = acc
        executed_tx = MagicMock()
        executed_tx.effects.changed_objects = [changed_obj]
        ex._qp._update_tracked_balance_from_accumulator(executed_tx)
        assert ex._qp._tracked_balance == 0

    def test_update_tracked_balance_from_accumulator_no_accumulator_entry(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        changed_obj = MagicMock()
        changed_obj.output_state = "OWNED"
        executed_tx = MagicMock()
        executed_tx.effects.changed_objects = [changed_obj]
        ex._qp._update_tracked_balance_from_accumulator(executed_tx)
        assert ex._qp._tracked_balance == 1_000_000

    def test_update_tracked_balance_from_accumulator_none_tx(self):
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        ex._qp._update_tracked_balance_from_accumulator(None)
        assert ex._qp._tracked_balance == 1_000_000


# ---------------------------------------------------------------------------
# Replenishment tests
# ---------------------------------------------------------------------------

class TestReplenishment:
    """Test _replenish() — callback invocation and SerialExecutorContext shape."""

    @pytest.mark.asyncio
    async def test_replenish_no_callback_returns_false(self):
        ex = _make_executor()
        result = await ex._replenish()
        assert result is False

    @pytest.mark.asyncio
    async def test_replenish_callback_none_returns_false(self):
        async def callback(ctx):
            return None
        ex = _make_executor(on_balance_low=callback)
        result = await ex._replenish()
        assert result is False

    @pytest.mark.asyncio
    async def test_replenish_callback_empty_list_returns_false(self):
        async def callback(ctx):
            return []
        ex = _make_executor(on_balance_low=callback)
        result = await ex._replenish()
        assert result is False

    @pytest.mark.asyncio
    async def test_replenish_passes_serial_executor_context(self):
        captured = None
        async def callback(ctx):
            nonlocal captured
            captured = ctx
            return None
        ex = _make_executor(on_balance_low=callback)
        ex._qp._tracked_balance = 500_000
        await ex._replenish()
        assert isinstance(captured, SerialExecutorContext)
        assert captured.sender == "0xsender"
        assert captured.tracked_balance == 500_000
        assert captured.min_threshold_balance == 10_000_000

    @pytest.mark.asyncio
    async def test_replenish_context_client_is_executor_client(self):
        captured = None
        async def callback(ctx):
            nonlocal captured
            captured = ctx
            return None
        ex = _make_executor(on_balance_low=callback)
        await ex._replenish()
        assert captured.client is ex._client

    @pytest.mark.asyncio
    async def test_replenish_add_funds_exception_returns_false(self):
        async def callback(ctx):
            return ["0xcoin1"]
        ex = _make_executor(on_balance_low=callback)
        with patch.object(ex._qp, "add_funds", new=AsyncMock(side_effect=ValueError("bad coin"))):
            result = await ex._replenish()
        assert result is False


# ---------------------------------------------------------------------------
# Hard stop tests
# ---------------------------------------------------------------------------

class TestHardStop:
    """Test _hard_stop() — marks dead, drains queued items to ExecutionSkipped."""

    @pytest.mark.asyncio
    async def test_hard_stop_marks_dead(self):
        ex = _make_executor()
        await ex._hard_stop("test reason")
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_hard_stop_drains_queued_items(self):
        from pysui.sui.sui_common.executors.serial_executor import _QueueItem
        ex = _make_executor()
        loop = asyncio.get_running_loop()
        fut1 = loop.create_future()
        fut2 = loop.create_future()
        ex._queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut1))
        ex._queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut2))
        await ex._hard_stop("test reason")
        assert fut1.done()
        assert fut2.done()
        assert isinstance(fut1.result(), ExecutionSkipped)
        assert isinstance(fut2.result(), ExecutionSkipped)

    @pytest.mark.asyncio
    async def test_hard_stop_reason_in_skipped(self):
        from pysui.sui.sui_common.executors.serial_executor import _QueueItem
        ex = _make_executor()
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        ex._queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut))
        await ex._hard_stop("specific halt reason")
        assert fut.result().reason == "specific halt reason"

    @pytest.mark.asyncio
    async def test_hard_stop_empty_queue_no_error(self):
        ex = _make_executor()
        await ex._hard_stop("no items")
        assert ex._dead is True
