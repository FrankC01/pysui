#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Step 5 unit tests — new_transaction deferred-mode wiring.

Verifies that SerialExecutor.new_transaction and
_BaseParallelExecutor.new_transaction inject mode=DEFERRED (and
object_cache for the serial case) before delegating to client.transaction().
No network access; all clients are MagicMock.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pysui.sui.sui_common.txb_tx_argparse import TxnArgMode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_grpc_client():
    mock_client = MagicMock()
    mock_client.config = MagicMock()
    mock_client.transaction = AsyncMock()
    return mock_client


def _make_grpc_serial_executor(**kwargs):
    from pysui.sui.sui_common.executors.serial_executor import SerialExecutor
    from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, GasMode
    client = _make_grpc_client()
    options = ExecutorOptions(
        sender="0xsender",
        gas_mode=GasMode.COINS,
        initial_coins=[],
        min_threshold_balance=10_000_000,
    )
    ex = SerialExecutor(client=client, options=options)
    return ex, client


def _make_grpc_parallel_executor(**kwargs):
    from pysui.sui.sui_common.executors.parallel_executor import ParallelExecutor
    from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, GasMode
    client = _make_grpc_client()
    options = ExecutorOptions(
        sender="0xsender",
        gas_mode=GasMode.COINS,
        initial_coins=[],
        min_threshold_balance=10_000_000,
    )
    ex = ParallelExecutor(client=client, options=options)
    return ex, client


# ---------------------------------------------------------------------------
# Serial executor — new_transaction wiring
# ---------------------------------------------------------------------------

class TestSerialNewTransaction:
    """SerialExecutor.new_transaction injects mode=DEFERRED and object_cache."""

    @pytest.mark.asyncio
    async def test_new_transaction_injects_deferred_mode(self):
        """new_transaction passes mode=DEFERRED to client.transaction()."""
        ex, client = _make_grpc_serial_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction()

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["mode"] == TxnArgMode.DEFERRED

    @pytest.mark.asyncio
    async def test_new_transaction_injects_object_cache(self):
        """new_transaction passes object_cache=self._cache.cache to client.transaction()."""
        ex, client = _make_grpc_serial_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction()

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["object_cache"] is ex._qp._cache.cache

    @pytest.mark.asyncio
    async def test_new_transaction_passes_caller_kwargs_through(self):
        """Extra kwargs from the caller are forwarded to client.transaction()."""
        ex, client = _make_grpc_serial_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction(compress_inputs=True)

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["compress_inputs"] is True
        assert call_kwargs["mode"] == TxnArgMode.DEFERRED

    @pytest.mark.asyncio
    async def test_new_transaction_returns_client_result(self):
        """new_transaction returns whatever client.transaction() returns."""
        ex, client = _make_grpc_serial_executor()
        sentinel = MagicMock(name="txn")
        client.transaction.return_value = sentinel

        result = await ex.new_transaction()

        assert result is sentinel

    @pytest.mark.asyncio
    async def test_new_transaction_overrides_caller_mode(self):
        """Executor enforces DEFERRED even if caller explicitly passes a mode."""
        ex, client = _make_grpc_serial_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction(mode=TxnArgMode.EAGER)

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["mode"] == TxnArgMode.DEFERRED

    @pytest.mark.asyncio
    async def test_new_transaction_defined_on_base_not_concrete(self):
        """new_transaction is defined directly on SerialExecutor."""
        from pysui.sui.sui_common.executors.serial_executor import SerialExecutor
        assert "new_transaction" in SerialExecutor.__dict__


# ---------------------------------------------------------------------------
# Parallel executor — new_transaction wiring
# ---------------------------------------------------------------------------

class TestParallelNewTransaction:
    """_BaseParallelExecutor.new_transaction injects mode=DEFERRED but no object_cache."""

    @pytest.mark.asyncio
    async def test_new_transaction_injects_deferred_mode(self):
        """new_transaction passes mode=DEFERRED to client.transaction()."""
        ex, client = _make_grpc_parallel_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction()

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["mode"] == TxnArgMode.DEFERRED

    @pytest.mark.asyncio
    async def test_new_transaction_does_not_inject_object_cache(self):
        """Parallel executor does not wire a shared object_cache (per-tx caches managed internally)."""
        ex, client = _make_grpc_parallel_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction()

        call_kwargs = client.transaction.call_args.kwargs
        assert "object_cache" not in call_kwargs

    @pytest.mark.asyncio
    async def test_new_transaction_passes_caller_kwargs_through(self):
        """Extra kwargs from the caller are forwarded to client.transaction()."""
        ex, client = _make_grpc_parallel_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction(compress_inputs=False)

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["compress_inputs"] is False
        assert call_kwargs["mode"] == TxnArgMode.DEFERRED

    @pytest.mark.asyncio
    async def test_new_transaction_returns_client_result(self):
        """new_transaction returns whatever client.transaction() returns."""
        ex, client = _make_grpc_parallel_executor()
        sentinel = MagicMock(name="par_txn")
        client.transaction.return_value = sentinel

        result = await ex.new_transaction()

        assert result is sentinel

    @pytest.mark.asyncio
    async def test_new_transaction_overrides_caller_mode(self):
        """Executor enforces DEFERRED even if caller explicitly passes a mode."""
        ex, client = _make_grpc_parallel_executor()
        client.transaction.return_value = MagicMock()

        await ex.new_transaction(mode=TxnArgMode.EAGER)

        call_kwargs = client.transaction.call_args.kwargs
        assert call_kwargs["mode"] == TxnArgMode.DEFERRED

    @pytest.mark.asyncio
    async def test_new_transaction_defined_on_base_not_concrete(self):
        """new_transaction is defined on ParallelExecutor (the shell), not _BaseParallelExecutor."""
        from pysui.sui.sui_common.executors.base_parallel_executor import _BaseParallelExecutor
        from pysui.sui.sui_common.executors.parallel_executor import ParallelExecutor

        for klass in ParallelExecutor.__mro__:
            if "new_transaction" in klass.__dict__:
                owner = klass
                break
        else:
            owner = None
        assert owner is ParallelExecutor
