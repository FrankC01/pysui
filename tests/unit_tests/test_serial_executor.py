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
    GasMode,
    GasStatus,
    ExecutorContext,
)
from pysui.sui.sui_common.executors.serial_executor import SerialExecutor


_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_executor(gas_mode=GasMode.COINS, **option_kwargs) -> SerialExecutor:
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
        ex = _make_executor(gas_mode=GasMode.COINS)
        assert ex._options.gas_mode == GasMode.COINS

    def test_address_balance_mode_executor(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        assert ex._options.gas_mode == GasMode.ADDRESS_BALANCE

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
        assert results[1].reason == "Transaction error with on_failure=exit"
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
        assert results[1].reason == "on_balance_low declined or failed"
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_need_funds_with_successful_replenishment(self):
        """NEED_FUNDS triggers replenishment; executor stays alive when callback succeeds."""
        executed_tx = _mock_executed_tx()
        async def callback(ctx):
            return [MagicMock(object_type=_SUI_COIN_TYPE, balance=20_000_000)]
        ex = _make_executor(on_balance_low=callback)
        with patch.object(ex._qp, "process", new=AsyncMock(return_value=(GasStatus.NEED_FUNDS, executed_tx))):
            with patch.object(ex._qp, "add_funds", new=AsyncMock()):
                ex._task = asyncio.create_task(ex._processor_loop())
                fut = ex.submit(MagicMock())
                result = await fut
                await ex.close()
        assert result is executed_tx
        assert ex._dead is False

    @pytest.mark.asyncio
    async def test_need_funds_and_retry_exhausted_hard_stops(self):
        """NEED_FUNDS_AND_RETRY with max_retries=0 immediately hard-stops."""
        error_result = (ExecutorError.EXECUTING_ERROR, ValueError("insufficient gas"))
        ex = _make_executor(max_retries=0)
        process_mock = AsyncMock(return_value=(GasStatus.NEED_FUNDS_AND_RETRY, error_result))
        with patch.object(ex._qp, "process", new=process_mock):
            ex._task = asyncio.create_task(ex._processor_loop())
            futs = ex.submit([MagicMock(), MagicMock()])
            results = await asyncio.gather(*futs)
            await ex.close()
        assert results[0] is error_result
        assert isinstance(results[1], ExecutionSkipped)
        assert results[1].reason == "Max retries exhausted"
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_need_funds_and_retry_succeeds_after_replenishment(self):
        """NEED_FUNDS_AND_RETRY eventually resolves OK after successful replenishment."""
        executed_tx = _mock_executed_tx()
        error_result = (ExecutorError.EXECUTING_ERROR, ValueError("insufficient gas"))
        async def callback(ctx):
            return [MagicMock(object_type=_SUI_COIN_TYPE, balance=20_000_000)]
        ex = _make_executor(max_retries=1, on_balance_low=callback)
        process_mock = AsyncMock(side_effect=[
            (GasStatus.NEED_FUNDS_AND_RETRY, error_result),
            (GasStatus.OK, executed_tx),
        ])
        with patch.object(ex._qp, "process", new=process_mock):
            with patch.object(ex._qp, "add_funds", new=AsyncMock()):
                ex._task = asyncio.create_task(ex._processor_loop())
                fut = ex.submit(MagicMock())
                result = await fut
                await ex.close()
        assert result is executed_tx
        assert ex._dead is False

    @pytest.mark.asyncio
    async def test_serial_ordering_transactions_execute_in_submission_order(self):
        """Transactions execute in the order they are submitted."""
        execution_order = []

        async def ordered_process(txn):
            execution_order.append(id(txn))
            return (GasStatus.OK, _mock_executed_tx())

        ex = _make_executor()
        txn1 = MagicMock()
        txn2 = MagicMock()
        txn3 = MagicMock()
        with patch.object(ex._qp, "process", new=ordered_process):
            ex._task = asyncio.create_task(ex._processor_loop())
            futs = ex.submit([txn1, txn2, txn3])
            await asyncio.gather(*futs)
            await ex.close()
        assert execution_order == [id(txn1), id(txn2), id(txn3)]


# ---------------------------------------------------------------------------
# SerialQueueProcessor unit tests
# ---------------------------------------------------------------------------

class TestSerialQueueProcessor:
    """Test SerialQueueProcessor state management (no network)."""

    def test_seed_funds_coins_mode_sets_gas_summary(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        summary = GasSummary(objectId="0x1", version="1", digest="d", balance=100_000_000)
        ex._qp.seed_funds(gas_summary=summary)
        assert ex._qp._gas_summary is summary
        assert ex._qp._tracked_balance == 100_000_000

    def test_seed_funds_address_balance_mode_no_summary(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
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

    def test_update_tracked_balance_gas_used_none(self):
        """When effects.gas_used is None, tracked balance is unchanged."""
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        effects = MagicMock()
        effects.gas_used = None
        ex._qp._update_tracked_balance(effects)
        assert ex._qp._tracked_balance == 1_000_000

    def test_update_tracked_balance_from_accumulator_accumulator_write_none(self):
        """When accumulator_write is None, balance is unchanged."""
        ex = _make_executor()
        ex._qp._tracked_balance = 1_000_000
        changed_obj = MagicMock()
        changed_obj.output_state = "ACCUMULATOR_WRITE"
        changed_obj.accumulator_write = None
        executed_tx = MagicMock()
        executed_tx.effects.changed_objects = [changed_obj]
        ex._qp._update_tracked_balance_from_accumulator(executed_tx)
        assert ex._qp._tracked_balance == 1_000_000


# ---------------------------------------------------------------------------
# Replenishment tests
# ---------------------------------------------------------------------------

class TestReplenishment:
    """Test _replenish() — callback invocation and ExecutorContext shape."""

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
        assert isinstance(captured, ExecutorContext)
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

    @pytest.mark.asyncio
    async def test_replenish_returns_true_on_success(self):
        """_replenish() returns True when callback provides coins and add_funds succeeds."""
        returned_coins = [MagicMock(object_type=_SUI_COIN_TYPE, balance=20_000_000)]
        async def callback(ctx):
            return returned_coins
        ex = _make_executor(on_balance_low=callback)
        with patch.object(ex._qp, "add_funds", new=AsyncMock()) as mock_add_funds:
            result = await ex._replenish()
        assert result is True
        mock_add_funds.assert_called_once_with(returned_coins)


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

    @pytest.mark.asyncio
    async def test_hard_stop_idempotent(self):
        """Second _hard_stop() call is a no-op — does not raise or double-set futures."""
        from pysui.sui.sui_common.executors.serial_executor import _QueueItem
        ex = _make_executor()
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        ex._queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut))
        await ex._hard_stop("first call")
        await ex._hard_stop("second call")
        assert ex._dead is True
        assert isinstance(fut.result(), ExecutionSkipped)


# ---------------------------------------------------------------------------
# SerialQueueProcessor.process() direct tests
# ---------------------------------------------------------------------------

class TestSerialQueueProcessorProcess:
    """Direct tests of SerialQueueProcessor.process() — no patching of process() itself."""

    @pytest.mark.asyncio
    async def test_process_build_error_returns_txn_error(self):
        """Build failure returns (GasStatus.TXN_ERROR, (ExecutorError.BUILDING_ERROR, exc))."""
        ex = _make_executor()
        build_exc = ValueError("build failed")
        ex._qp._cache.build_transaction = AsyncMock(side_effect=build_exc)
        txn = MagicMock()
        status, result = await ex._qp.process(txn)
        assert status == GasStatus.TXN_ERROR
        assert result[0] == ExecutorError.BUILDING_ERROR
        assert result[1] is build_exc

    @pytest.mark.asyncio
    async def test_process_execute_error_returns_txn_error(self):
        """ExecuteTransaction non-ok returns (GasStatus.TXN_ERROR, ...)."""
        ex = _make_executor()
        ex._qp._cache.build_transaction = AsyncMock(
            return_value={"tx_bytestr": "abc", "sig_array": ["sig"]}
        )
        bad_result = MagicMock()
        bad_result.is_ok.return_value = False
        bad_result.result_string = "network error"
        ex._client.execute = AsyncMock(return_value=bad_result)
        txn = MagicMock()
        status, result = await ex._qp.process(txn)
        assert status == GasStatus.TXN_ERROR
        assert result[0] == ExecutorError.EXECUTING_ERROR

    @pytest.mark.asyncio
    async def test_process_insufficient_gas_returns_need_funds_and_retry(self):
        """Insufficient gas error returns NEED_FUNDS_AND_RETRY."""
        ex = _make_executor()
        ex._qp._cache.build_transaction = AsyncMock(
            return_value={"tx_bytestr": "abc", "sig_array": ["sig"]}
        )
        bad_result = MagicMock()
        bad_result.is_ok.return_value = False
        bad_result.result_string = "insufficient gas"
        ex._client.execute = AsyncMock(return_value=bad_result)
        txn = MagicMock()
        status, result = await ex._qp.process(txn)
        assert status == GasStatus.NEED_FUNDS_AND_RETRY
        assert result[0] == ExecutorError.EXECUTING_ERROR

    @pytest.mark.asyncio
    async def test_process_success_returns_ok(self):
        """Successful execution returns (GasStatus.OK, executed_tx) when balance is above threshold."""
        ex = _make_executor(gas_mode=GasMode.COINS)
        ex._qp.seed_funds(gas_summary=GasSummary(objectId="0x1", version="1", digest="d", balance=20_000_000))
        ex._qp._cache.build_transaction = AsyncMock(
            return_value={"tx_bytestr": "abc", "sig_array": ["sig"]}
        )
        ex._qp._cache.apply_effects = AsyncMock()
        ex._qp._cache.update_gas_coins = AsyncMock()
        ex._qp._cache.invalidate_gas_coins = AsyncMock()
        executed_tx = _mock_executed_tx()
        ok_result = MagicMock()
        ok_result.is_ok.return_value = True
        ok_result.result_data = executed_tx
        ex._client.execute = AsyncMock(return_value=ok_result)
        txn = MagicMock()
        status, result = await ex._qp.process(txn)
        assert status == GasStatus.OK
        assert result is executed_tx

    @pytest.mark.asyncio
    async def test_process_low_balance_returns_need_funds(self):
        """When balance drops below threshold after success, returns NEED_FUNDS."""
        ex = _make_executor(gas_mode=GasMode.COINS)
        # balance > 0 but below threshold of 10_000_000
        ex._qp.seed_funds(gas_summary=GasSummary(objectId="0x1", version="1", digest="d", balance=5_000_000))
        ex._qp._cache.build_transaction = AsyncMock(
            return_value={"tx_bytestr": "abc", "sig_array": ["sig"]}
        )
        ex._qp._cache.apply_effects = AsyncMock()
        ex._qp._cache.update_gas_coins = AsyncMock()
        ex._qp._cache.invalidate_gas_coins = AsyncMock()
        executed_tx = _mock_executed_tx()
        ok_result = MagicMock()
        ok_result.is_ok.return_value = True
        ok_result.result_data = executed_tx
        ex._client.execute = AsyncMock(return_value=ok_result)
        txn = MagicMock()
        status, result = await ex._qp.process(txn)
        assert status == GasStatus.NEED_FUNDS
        assert result is executed_tx


# ---------------------------------------------------------------------------
# _update_gas_summary() direct tests
# ---------------------------------------------------------------------------

class TestUpdateGasSummary:
    """Tests for SerialQueueProcessor._update_gas_summary()."""

    def test_updates_version_and_digest_from_gas_object(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        ex._qp.seed_funds(
            gas_summary=GasSummary(objectId="0x1", version="1", digest="old", balance=5_000_000)
        )
        go = MagicMock()
        go.output_version = 2
        go.output_digest = "newdigest"
        effects = MagicMock()
        effects.gas_object = go
        tx = MagicMock()
        tx.effects = effects
        tx.objects = None
        ex._qp._update_gas_summary(tx)
        assert ex._qp._gas_summary.version == "2"
        assert ex._qp._gas_summary.digest == "newdigest"

    def test_updates_balance_from_objects_scan(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        ex._qp.seed_funds(
            gas_summary=GasSummary(objectId="0x1", version="1", digest="d", balance=5_000_000)
        )
        go = MagicMock()
        go.output_version = 2
        go.output_digest = "d2"
        effects = MagicMock()
        effects.gas_object = go
        obj_entry = MagicMock()
        obj_entry.object_id = "0x1"
        obj_entry.version = 2
        obj_entry.balance = 4_998_700
        objs = MagicMock()
        objs.objects = [obj_entry]
        tx = MagicMock()
        tx.effects = effects
        tx.objects = objs
        ex._qp._update_gas_summary(tx)
        assert ex._qp._gas_summary.balance == 4_998_700

    def test_no_change_when_gas_summary_none(self):
        """ADDRESS_BALANCE mode has no gas_summary — _update_gas_summary is a no-op."""
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        tx = MagicMock()
        tx.effects.gas_object = MagicMock()
        tx.objects = None
        ex._qp._update_gas_summary(tx)
        assert ex._qp._gas_summary is None

    def test_no_change_when_executed_tx_none(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        ex._qp.seed_funds(
            gas_summary=GasSummary(objectId="0x1", version="1", digest="d", balance=5_000_000)
        )
        ex._qp._update_gas_summary(None)
        assert ex._qp._gas_summary.version == "1"

    def test_no_change_when_no_gas_object_in_effects(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        ex._qp.seed_funds(
            gas_summary=GasSummary(objectId="0x1", version="1", digest="d", balance=5_000_000)
        )
        effects = MagicMock()
        effects.gas_object = None
        tx = MagicMock()
        tx.effects = effects
        tx.objects = None
        ex._qp._update_gas_summary(tx)
        assert ex._qp._gas_summary.version == "1"
        assert ex._qp._gas_summary.digest == "d"
