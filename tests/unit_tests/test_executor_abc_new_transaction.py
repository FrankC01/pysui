#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Step 5 unit tests — ABC new_transaction deferred-mode wiring.

Verifies that _BaseSerialExecutor.new_transaction and
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
    from pysui.sui.sui_grpc.grpc_serial_exec import GrpcSerialTransactionExecutor
    client = _make_grpc_client()
    ex = GrpcSerialTransactionExecutor(client=client, sender="0xsender", **kwargs)
    ex._tracked_balance = 1_000_000
    return ex, client


def _make_grpc_parallel_executor(**kwargs):
    from pysui.sui.sui_grpc.grpc_parallel_exec import GrpcParallelTransactionExecutor
    client = _make_grpc_client()
    ex = GrpcParallelTransactionExecutor(client=client, sender="0xsender", **kwargs)
    return ex, client


# ---------------------------------------------------------------------------
# Serial executor — new_transaction wiring
# ---------------------------------------------------------------------------

class TestSerialNewTransaction:
    """_BaseSerialExecutor.new_transaction injects mode=DEFERRED and object_cache."""

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
        assert call_kwargs["object_cache"] is ex._cache.cache

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
        """new_transaction is resolved from _BaseSerialExecutor, not GrpcSerialTransactionExecutor."""
        from pysui.sui.sui_common.executors.base_executor import _BaseSerialExecutor
        from pysui.sui.sui_grpc.grpc_serial_exec import GrpcSerialTransactionExecutor

        for klass in GrpcSerialTransactionExecutor.__mro__:
            if "new_transaction" in klass.__dict__:
                owner = klass
                break
        else:
            owner = None
        assert owner is _BaseSerialExecutor


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
    async def test_new_transaction_defined_on_base_not_concrete(self):
        """new_transaction is resolved from _BaseParallelExecutor, not GrpcParallelTransactionExecutor."""
        from pysui.sui.sui_common.executors.base_parallel_executor import _BaseParallelExecutor
        from pysui.sui.sui_grpc.grpc_parallel_exec import GrpcParallelTransactionExecutor

        for klass in GrpcParallelTransactionExecutor.__mro__:
            if "new_transaction" in klass.__dict__:
                owner = klass
                break
        else:
            owner = None
        assert owner is _BaseParallelExecutor
