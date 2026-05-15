#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for _BaseParallelExecutor — concrete two-queue design."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pysui.sui.sui_common.executors.base_parallel_executor import _BaseParallelExecutor
from pysui.sui.sui_common.executors.parallel_executor import ParallelExecutor
from pysui.sui.sui_common.executors._queue_types import _QueueItem
from pysui.sui.sui_common.executors.exec_types import (
    ExecutorOptions,
    GasMode,
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
)
from pysui.sui.sui_common.executors.gas_pool import GasCoin


_CE_PATH = "pysui.sui.sui_common.executors.base_parallel_executor._BaseCachingExecutor"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client():
    client = MagicMock()
    client.config = MagicMock()
    client.transaction = AsyncMock()
    return client


def _make_executor(gas_mode=GasMode.COINS, **option_kwargs) -> ParallelExecutor:
    client = _make_client()
    options = ExecutorOptions(
        sender="0xsender",
        gas_mode=gas_mode,
        initial_coins=[],
        min_threshold_balance=10_000_000,
        **option_kwargs,
    )
    return ParallelExecutor(client=client, options=options)


def _gas_coin(suffix="01", balance=5_000_000) -> GasCoin:
    return GasCoin(object_id=f"0x{'aa' * 31}{suffix}", version="1", digest="d", balance=balance)


def _mock_executed_tx(computation_cost=1000, storage_cost=500, storage_rebate=200):
    gas = MagicMock()
    gas.computation_cost = computation_cost
    gas.storage_cost = storage_cost
    gas.storage_rebate = storage_rebate
    effects = MagicMock()
    effects.gas_used = gas
    effects.gas_object = None
    effects.changed_objects = []
    tx = MagicMock()
    tx.effects = effects
    tx.objects = None
    return tx


def _ok_result(data):
    r = MagicMock()
    r.is_ok.return_value = True
    r.result_data = data
    return r


def _ce_mock(signed_tx=None):
    ce = MagicMock()
    ce.build_transaction = AsyncMock(
        return_value=signed_tx or {"tx_bytestr": "abc", "sig_array": ["sig"]}
    )
    ce.apply_effects = AsyncMock()
    ce.sync_to_registry = AsyncMock()
    ce.update_gas_coins = AsyncMock()
    return ce


def _txn_mock(unresolved_ids=None):
    txn = MagicMock()
    txn.builder.get_unresolved_inputs.return_value = (
        {i: MagicMock(ObjectStr=oid) for i, oid in enumerate(unresolved_ids)}
        if unresolved_ids else {}
    )
    return txn


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:

    def test_coins_mode_creates_gas_pool(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        assert ex._gas_pool is not None

    def test_address_balance_mode_no_gas_pool(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        assert ex._gas_pool is None

    def test_dead_starts_false(self):
        ex = _make_executor()
        assert ex._dead is False

    def test_build_task_starts_none(self):
        ex = _make_executor()
        assert ex._build_task is None

    def test_build_queue_empty_initially(self):
        ex = _make_executor()
        assert ex._build_queue.empty()

    def test_semaphore_created_with_max_concurrent(self):
        ex = _make_executor(max_concurrent=5)
        assert ex._semaphore._value == 5

    def test_tracked_balance_starts_zero(self):
        ex = _make_executor()
        assert ex._tracked_balance == 0

    def test_has_submit_method(self):
        assert hasattr(ParallelExecutor, "submit")

    def test_has_close_method(self):
        assert hasattr(ParallelExecutor, "close")

    def test_has_new_transaction_method(self):
        assert hasattr(ParallelExecutor, "new_transaction")


# ---------------------------------------------------------------------------
# submit() — Future creation and dead-executor gate
# ---------------------------------------------------------------------------

class TestSubmit:

    @pytest.mark.asyncio
    async def test_submit_single_returns_future(self):
        ex = _make_executor()
        fut = ex.submit(_txn_mock())
        assert isinstance(fut, asyncio.Future)

    @pytest.mark.asyncio
    async def test_submit_list_returns_list_of_futures(self):
        ex = _make_executor()
        futs = ex.submit([_txn_mock(), _txn_mock(), _txn_mock()])
        assert isinstance(futs, list)
        assert len(futs) == 3
        assert all(isinstance(f, asyncio.Future) for f in futs)

    @pytest.mark.asyncio
    async def test_submit_to_dead_executor_returns_skipped(self):
        ex = _make_executor()
        ex._dead = True
        fut = ex.submit(_txn_mock())
        assert fut.done()
        assert isinstance(fut.result(), ExecutionSkipped)

    @pytest.mark.asyncio
    async def test_submit_list_to_dead_executor_all_skipped(self):
        ex = _make_executor()
        ex._dead = True
        futs = ex.submit([_txn_mock(), _txn_mock()])
        assert all(f.done() for f in futs)
        assert all(isinstance(f.result(), ExecutionSkipped) for f in futs)

    @pytest.mark.asyncio
    async def test_submit_single_success_address_balance(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()
        assert result is executed_tx

    @pytest.mark.asyncio
    async def test_submit_single_success_coins_mode(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        await ex._gas_pool.replenish([_gas_coin()])
        ex._tracked_balance = 20_000_000
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()
        assert result is executed_tx

    @pytest.mark.asyncio
    async def test_submit_list_all_succeed(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            futs = ex.submit([_txn_mock(), _txn_mock(), _txn_mock()])
            results = await asyncio.gather(*futs)
            await ex.close()
        assert all(r is executed_tx for r in results)

    @pytest.mark.asyncio
    async def test_build_error_sets_building_error(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        ce = _ce_mock()
        ce.build_transaction = AsyncMock(side_effect=ValueError("build failed"))
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()
        assert isinstance(result, tuple)
        err, exc = result
        assert err == ExecutorError.BUILDING_ERROR
        assert "build failed" in str(exc)

    @pytest.mark.asyncio
    async def test_execute_error_continue_does_not_kill_executor(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE, on_failure="continue")
        bad_result = MagicMock()
        bad_result.is_ok.return_value = False
        bad_result.result_string = "network error"
        ex._client.execute = AsyncMock(return_value=bad_result)
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            # Capture _dead before close() — close() always sets it True as part of normal shutdown
            dead_before_close = ex._dead
            await ex.close()
        assert isinstance(result, tuple)
        assert result[0] == ExecutorError.EXECUTING_ERROR
        assert dead_before_close is False

    @pytest.mark.asyncio
    async def test_execute_error_exit_kills_executor(self):
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE, on_failure="exit")
        bad_result = MagicMock()
        bad_result.is_ok.return_value = False
        bad_result.result_string = "network error"
        ex._client.execute = AsyncMock(return_value=bad_result)
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()
        assert result[0] == ExecutorError.EXECUTING_ERROR
        assert ex._dead is True
        # Submit after dead returns ExecutionSkipped immediately
        fut2 = ex.submit(_txn_mock())
        assert isinstance(fut2.result(), ExecutionSkipped)

    @pytest.mark.asyncio
    async def test_coins_mode_gas_coin_available_after_success(self):
        ex = _make_executor(gas_mode=GasMode.COINS)
        await ex._gas_pool.replenish([_gas_coin()])
        # Seed tracked_balance above threshold so post-success balance check doesn't trigger hard_stop
        ex._tracked_balance = 20_000_000
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            await fut
            await ex.close()
        # Pool should not be empty after success — coin was checked back in
        assert ex._gas_pool.size() == 1

    @pytest.mark.asyncio
    async def test_build_error_coins_mode_retires_gas_coin(self):
        """Build failure in COINS mode retires the gas coin — pool is empty after."""
        ex = _make_executor(gas_mode=GasMode.COINS)
        await ex._gas_pool.replenish([_gas_coin()])
        ce = _ce_mock()
        ce.build_transaction = AsyncMock(side_effect=ValueError("build failed"))
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()
        assert isinstance(result, tuple)
        assert result[0] == ExecutorError.BUILDING_ERROR
        assert ex._gas_pool.size() == 0

    @pytest.mark.asyncio
    async def test_gas_error_retries_exhausted_hard_stops(self):
        """Gas error with max_retries=0 skips retry and triggers hard stop."""
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE, max_retries=0)
        bad_result = MagicMock()
        bad_result.is_ok.return_value = False
        bad_result.result_string = "insufficient gas"
        ex._client.execute = AsyncMock(return_value=bad_result)
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()
        assert isinstance(result, tuple)
        assert result[0] == ExecutorError.EXECUTING_ERROR
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_submit_success_calls_apply_effects_and_sync(self):
        """After successful execution, apply_effects and sync_to_registry are called."""
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock())
            await fut
            await ex.close()
        ce.apply_effects.assert_called_once_with(executed_tx.effects)
        ce.sync_to_registry.assert_called_once_with(ex._registry)


# ---------------------------------------------------------------------------
# _hard_stop()
# ---------------------------------------------------------------------------

class TestHardStop:

    @pytest.mark.asyncio
    async def test_hard_stop_marks_dead(self):
        ex = _make_executor()
        await ex._hard_stop("test reason")
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_hard_stop_drains_queued_items(self):
        ex = _make_executor()
        loop = asyncio.get_running_loop()
        fut1 = loop.create_future()
        fut2 = loop.create_future()
        ex._build_queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut1))
        ex._build_queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut2))
        await ex._hard_stop("test reason")
        assert fut1.done()
        assert fut2.done()
        assert isinstance(fut1.result(), ExecutionSkipped)
        assert isinstance(fut2.result(), ExecutionSkipped)

    @pytest.mark.asyncio
    async def test_hard_stop_reason_in_skipped(self):
        ex = _make_executor()
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        ex._build_queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut))
        await ex._hard_stop("specific reason")
        assert fut.result().reason == "specific reason"

    @pytest.mark.asyncio
    async def test_hard_stop_empty_queue_no_error(self):
        ex = _make_executor()
        await ex._hard_stop("no items")
        assert ex._dead is True

    @pytest.mark.asyncio
    async def test_hard_stop_idempotent(self):
        ex = _make_executor()
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        ex._build_queue.put_nowait(_QueueItem(txn=MagicMock(), future=fut))
        await ex._hard_stop("first call")
        # Second call must not raise or double-set the already-resolved future
        await ex._hard_stop("second call")
        assert ex._dead is True


# ---------------------------------------------------------------------------
# _replenish()
# ---------------------------------------------------------------------------

class TestReplenishment:

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
    async def test_replenish_passes_correct_context(self):
        captured = None
        async def callback(ctx):
            nonlocal captured
            captured = ctx
            return None
        ex = _make_executor(on_balance_low=callback)
        ex._tracked_balance = 3_000_000
        await ex._replenish()
        assert isinstance(captured, ExecutorContext)
        assert captured.sender == "0xsender"
        assert captured.tracked_balance == 3_000_000
        assert captured.min_threshold_balance == 10_000_000
        assert captured.client is ex._client

    @pytest.mark.asyncio
    async def test_replenish_add_funds_exception_returns_false(self):
        async def callback(ctx):
            return ["0xcoin1"]
        ex = _make_executor(on_balance_low=callback)
        with patch.object(ex, "_add_funds", new=AsyncMock(side_effect=ValueError("bad coin"))):
            result = await ex._replenish()
        assert result is False

    @pytest.mark.asyncio
    async def test_replenish_returns_true_on_success(self):
        """_replenish() returns True when callback provides coins and add_funds succeeds."""
        returned_coins = [_gas_coin()]
        async def callback(ctx):
            return returned_coins
        ex = _make_executor(on_balance_low=callback)
        with patch.object(ex, "_add_funds", new=AsyncMock()) as mock_add_funds:
            result = await ex._replenish()
        assert result is True
        mock_add_funds.assert_called_once_with(returned_coins)


# ---------------------------------------------------------------------------
# _update_tracked_balance()
# ---------------------------------------------------------------------------

class TestUpdateTrackedBalance:

    def test_deducts_net_gas(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        effects = MagicMock()
        effects.gas_used.computation_cost = 1000
        effects.gas_used.storage_cost = 500
        effects.gas_used.storage_rebate = 200
        ex._update_tracked_balance(effects)
        assert ex._tracked_balance == 1_000_000 - (1000 + 500 - 200)

    def test_clamps_to_zero(self):
        ex = _make_executor()
        ex._tracked_balance = 100
        effects = MagicMock()
        effects.gas_used.computation_cost = 10_000
        effects.gas_used.storage_cost = 5_000
        effects.gas_used.storage_rebate = 0
        ex._update_tracked_balance(effects)
        assert ex._tracked_balance == 0

    def test_rebate_reduces_deduction(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        effects = MagicMock()
        effects.gas_used.computation_cost = 500
        effects.gas_used.storage_cost = 300
        effects.gas_used.storage_rebate = 800
        ex._update_tracked_balance(effects)
        # net = 500 + 300 - 800 = 0 → balance unchanged
        assert ex._tracked_balance == 1_000_000

    def test_gas_used_none_no_change(self):
        """When effects.gas_used is None, tracked balance is unchanged."""
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        effects = MagicMock()
        effects.gas_used = None
        ex._update_tracked_balance(effects)
        assert ex._tracked_balance == 1_000_000


# ---------------------------------------------------------------------------
# _update_tracked_balance_from_accumulator()
# ---------------------------------------------------------------------------

class TestUpdateTrackedBalanceFromAccumulator:

    def _make_accumulator_tx(self, operation, value):
        acc = MagicMock()
        acc.operation = operation
        acc.value = value
        changed_obj = MagicMock()
        changed_obj.output_state = "ACCUMULATOR_WRITE"
        changed_obj.accumulator_write = acc
        tx = MagicMock()
        tx.effects.changed_objects = [changed_obj]
        return tx

    def test_merge_increases_balance(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        tx = self._make_accumulator_tx("MERGE", 500_000)
        ex._update_tracked_balance_from_accumulator(tx)
        assert ex._tracked_balance == 1_500_000

    def test_split_decreases_balance(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        tx = self._make_accumulator_tx("SPLIT", 300_000)
        ex._update_tracked_balance_from_accumulator(tx)
        assert ex._tracked_balance == 700_000

    def test_split_clamps_to_zero(self):
        ex = _make_executor()
        ex._tracked_balance = 100
        tx = self._make_accumulator_tx("SPLIT", 1_000_000)
        ex._update_tracked_balance_from_accumulator(tx)
        assert ex._tracked_balance == 0

    def test_no_accumulator_entry_no_change(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        changed_obj = MagicMock()
        changed_obj.output_state = "OWNED"
        tx = MagicMock()
        tx.effects.changed_objects = [changed_obj]
        ex._update_tracked_balance_from_accumulator(tx)
        assert ex._tracked_balance == 1_000_000

    def test_none_tx_no_change(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        ex._update_tracked_balance_from_accumulator(None)
        assert ex._tracked_balance == 1_000_000

    def test_empty_changed_objects_no_change(self):
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        tx = MagicMock()
        tx.effects.changed_objects = []
        ex._update_tracked_balance_from_accumulator(tx)
        assert ex._tracked_balance == 1_000_000

    def test_accumulator_write_none_no_change(self):
        """When accumulator_write is None on an ACCUMULATOR_WRITE object, balance unchanged."""
        ex = _make_executor()
        ex._tracked_balance = 1_000_000
        changed_obj = MagicMock()
        changed_obj.output_state = "ACCUMULATOR_WRITE"
        changed_obj.accumulator_write = None
        tx = MagicMock()
        tx.effects.changed_objects = [changed_obj]
        ex._update_tracked_balance_from_accumulator(tx)
        assert ex._tracked_balance == 1_000_000


# ---------------------------------------------------------------------------
# _update_gas_coin()
# ---------------------------------------------------------------------------

class TestUpdateGasCoin:

    def _make_executed_tx_with_gas_object(self, output_version=2, output_digest="newdigest"):
        go = MagicMock()
        go.output_version = output_version
        go.output_digest = output_digest
        effects = MagicMock()
        effects.gas_object = go
        tx = MagicMock()
        tx.effects = effects
        tx.objects = None
        return tx

    def test_updates_version_and_digest_from_gas_object(self):
        ex = _make_executor()
        coin = _gas_coin(balance=5_000_000)
        tx = self._make_executed_tx_with_gas_object(output_version=2, output_digest="newdigest")
        updated = ex._update_gas_coin(tx, coin)
        assert updated.version == "2"
        assert updated.digest == "newdigest"

    def test_updates_balance_from_objects_scan(self):
        ex = _make_executor()
        coin = _gas_coin(suffix="01", balance=5_000_000)
        go = MagicMock()
        go.output_version = 2
        go.output_digest = "newdigest"
        effects = MagicMock()
        effects.gas_object = go
        obj_entry = MagicMock()
        obj_entry.object_id = coin.object_id
        obj_entry.version = 2
        obj_entry.balance = 4_998_700
        objects = MagicMock()
        objects.objects = [obj_entry]
        tx = MagicMock()
        tx.effects = effects
        tx.objects = objects
        updated = ex._update_gas_coin(tx, coin)
        assert updated.balance == 4_998_700

    def test_falls_back_to_original_when_no_gas_object(self):
        ex = _make_executor()
        coin = _gas_coin(balance=5_000_000)
        effects = MagicMock()
        effects.gas_object = None
        tx = MagicMock()
        tx.effects = effects
        tx.objects = None
        updated = ex._update_gas_coin(tx, coin)
        assert updated.version == coin.version
        assert updated.digest == coin.digest
        assert updated.balance == coin.balance

    def test_object_id_preserved(self):
        ex = _make_executor()
        coin = _gas_coin(suffix="01")
        tx = self._make_executed_tx_with_gas_object()
        updated = ex._update_gas_coin(tx, coin)
        assert updated.object_id == coin.object_id

    def test_balance_unchanged_when_objects_is_none(self):
        ex = _make_executor()
        coin = _gas_coin(balance=5_000_000)
        tx = self._make_executed_tx_with_gas_object()
        # tx.objects is None — balance should stay at original
        updated = ex._update_gas_coin(tx, coin)
        assert updated.balance == coin.balance


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------

class TestClose:

    @pytest.mark.asyncio
    async def test_close_with_none_build_task(self):
        """close() is safe when build task has not been started."""
        ex = _make_executor()
        await ex.close()

    @pytest.mark.asyncio
    async def test_close_double_close_is_safe(self):
        """Second close() call does not raise or deadlock."""
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        ex._build_task = asyncio.create_task(ex._build_worker())
        await ex.close()
        await ex.close()

    @pytest.mark.asyncio
    async def test_close_marks_dead(self):
        """close() sets _dead True as part of normal PE shutdown."""
        ex = _make_executor()
        ex._build_task = asyncio.create_task(ex._build_worker())
        await ex.close()
        assert ex._dead is True


# ---------------------------------------------------------------------------
# ConflictTracking
# ---------------------------------------------------------------------------

class TestConflictTracking:

    @pytest.mark.asyncio
    async def test_conflict_ids_extracted_from_txn_inputs(self):
        """Txn inputs with ObjectStr are extracted for conflict tracking."""
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        txn = _txn_mock(unresolved_ids=["0xobj1", "0xobj2"])
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(txn)
            result = await fut
            await ex.close()
        assert result is executed_tx
        txn.builder.get_unresolved_inputs.assert_called()

    @pytest.mark.asyncio
    async def test_txn_with_no_unresolved_inputs_succeeds(self):
        """Txn with no unresolved inputs completes normally (empty conflict set)."""
        ex = _make_executor(gas_mode=GasMode.ADDRESS_BALANCE)
        executed_tx = _mock_executed_tx()
        ex._client.execute = AsyncMock(return_value=_ok_result(executed_tx))
        ce = _ce_mock()
        with patch(_CE_PATH, return_value=ce):
            ex._build_task = asyncio.create_task(ex._build_worker())
            fut = ex.submit(_txn_mock(unresolved_ids=None))
            result = await fut
            await ex.close()
        assert result is executed_tx
