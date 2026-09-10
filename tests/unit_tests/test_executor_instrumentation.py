#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for Task #104 — instrumentation collector propagation into executor
background tasks (SerialExecutor and ParallelExecutor).

A collector activated around submit() must be visible to instrumentation calls made
while that item is processed in the executor's background worker/task, even though
submit() itself returns before processing happens, and the background worker/task was
started with no collector active. No live node required.
"""

import asyncio
from contextlib import asynccontextmanager

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pysui.sui.sui_common.instrumentation import InstrumentationCollector, active_collector
from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, GasMode
from pysui.sui.sui_common.executors.parallel_executor import ParallelExecutor
from pysui.sui.sui_common.executors.serial_executor import SerialExecutor


_PARALLEL_CE_PATH = "pysui.sui.sui_common.executors.base_parallel_executor._BaseCachingExecutor"


class _RecordingCollector(InstrumentationCollector):
    """Test collector — records measure() labels it observes."""

    def __init__(self) -> None:
        self.labels: list[str] = []

    @asynccontextmanager
    async def measure(self, label: str):
        self.labels.append(label)
        yield


def _make_client():
    client = MagicMock()
    client.config = MagicMock()
    client.transaction = AsyncMock()
    return client


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


def _txn_mock(unresolved_ids=None):
    txn = MagicMock()
    txn.builder.get_unresolved_inputs.return_value = (
        {i: MagicMock(ObjectStr=oid) for i, oid in enumerate(unresolved_ids)}
        if unresolved_ids else {}
    )
    return txn


class TestParallelExecutorCollectorPropagation:
    """A collector active around submit() must reach _build_worker's per-item work."""

    @pytest.mark.asyncio
    async def test_collector_active_around_submit_records_labels(self):
        client = _make_client()
        options = ExecutorOptions(
            sender="0xsender",
            gas_mode=GasMode.ADDRESS_BALANCE,
            initial_coins=[],
            min_threshold_balance=10_000_000,
        )
        ex = ParallelExecutor(client=client, options=options)

        executed_tx = _mock_executed_tx()
        client.execute = AsyncMock(return_value=_ok_result(executed_tx))

        ce = MagicMock()
        ce.build_transaction = AsyncMock(return_value={"tx_bytestr": "abc", "sig_array": ["sig"]})
        ce.apply_effects = AsyncMock()
        ce.sync_to_registry = AsyncMock()
        ce.seed_from_registry = AsyncMock()
        ce.update_gas_coins = AsyncMock()

        collector = _RecordingCollector()
        with patch(_PARALLEL_CE_PATH, return_value=ce):
            # Background worker is started with no collector active — exactly the
            # scenario Task #104 fixes (collector must not need to be active at
            # construction/worker-start time, only at submit() time).
            ex._build_task = asyncio.create_task(ex._build_worker())
            async with active_collector(collector):
                fut = ex.submit(_txn_mock())
            result = await fut
            await ex.close()

        assert result is executed_tx
        assert "executor.parallel.object_resolve" in collector.labels


class TestSerialExecutorCollectorPropagation:
    """A collector active around submit() must reach _process_item's work."""

    @pytest.mark.asyncio
    async def test_collector_active_around_submit_records_labels(self):
        client = _make_client()
        options = ExecutorOptions(
            sender="0xsender",
            gas_mode=GasMode.ADDRESS_BALANCE,
            initial_coins=[],
            min_threshold_balance=10_000_000,
        )
        ex = SerialExecutor(client=client, options=options)

        executed_tx = _mock_executed_tx()
        client.execute = AsyncMock(return_value=_ok_result(executed_tx))

        ce = MagicMock()
        ce.build_transaction = AsyncMock(return_value={"tx_bytestr": "abc", "sig_array": ["sig"]})
        ce.apply_effects = AsyncMock()

        collector = _RecordingCollector()
        # SerialQueueProcessor builds its _cache at __init__ time (before any patch
        # could apply), so replace it directly rather than patching the class.
        ex._qp._cache = ce

        # Background processor loop is started with no collector active — same
        # construction-time-vs-submit-time scenario as the parallel executor test.
        ex._task = asyncio.create_task(ex._processor_loop())
        async with active_collector(collector):
            fut = ex.submit(_txn_mock())
        result = await fut
        await ex.close()

        assert result is executed_tx
        assert "executor.serial.object_resolve" in collector.labels
