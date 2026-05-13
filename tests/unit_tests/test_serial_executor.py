#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for PysuiSerialExecutor."""

import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_common.executors import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    GasSummary,
)
from pysui.sui.sui_common.executors.serial_executor import PysuiSerialExecutor


_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_executor(**kwargs) -> PysuiSerialExecutor:
    """Build an executor backed by a plain MagicMock client."""
    mock_client = MagicMock()
    mock_client.config = MagicMock()
    executor = PysuiSerialExecutor(client=mock_client, sender="0xsender", **kwargs)
    executor._tracked_balance = 1_000_000
    return executor


def _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200):
    """Build a minimal mock TransactionEffects (proto shape)."""
    gas = MagicMock()
    gas.computation_cost = computation_cost
    gas.storage_cost = storage_cost
    gas.storage_rebate = storage_rebate

    eff = MagicMock()
    eff.transaction_digest = "fakedigest"
    eff.gas_used = gas
    eff.gas_object = None
    eff.changed_objects = []
    eff.lamport_version = 1
    return eff


def _mock_executed_tx(computation_cost=1000, storage_cost=500, storage_rebate=200):
    """Build a mock ExecutedTransaction wrapping mock TransactionEffects."""
    effects = _mock_effects(computation_cost, storage_cost, storage_rebate)
    executed_tx = MagicMock()
    executed_tx.effects = effects
    executed_tx.objects = None
    return executed_tx, effects


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

class TestPysuiSerialExecutor:
    """Test PysuiSerialExecutor initialization and structure."""

    def test_executor_creation(self):
        executor = _make_executor()
        assert executor is not None

    def test_executor_with_sponsor(self):
        executor = _make_executor(sponsor="0xsponsor")
        assert executor is not None

    def test_executor_with_balance_threshold(self):
        async def on_coins_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=1_000_000, on_coins_low=on_coins_low)
        assert executor._min_balance_threshold == 1_000_000

    def test_executor_threshold_with_on_balance_low_only(self):
        async def on_balance_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=1_000_000, on_balance_low=on_balance_low)
        assert executor._min_balance_threshold == 1_000_000
        assert executor._on_balance_low is not None
        assert executor._on_coins_low is None

    def test_executor_with_both_callbacks(self):
        async def on_coins_low(ctx):
            return None

        async def on_balance_low(ctx):
            return None

        executor = _make_executor(on_coins_low=on_coins_low, on_balance_low=on_balance_low)
        assert executor._on_coins_low is not None
        assert executor._on_balance_low is not None

    def test_executor_has_new_transaction_method(self):
        assert hasattr(PysuiSerialExecutor, "new_transaction")

    def test_executor_has_reset_cache_method(self):
        assert hasattr(PysuiSerialExecutor, "reset_cache")

    def test_executor_has_execute_transactions_method(self):
        assert hasattr(PysuiSerialExecutor, "execute_transactions")

    def test_executor_has_with_coins_classmethod(self):
        assert hasattr(PysuiSerialExecutor, "with_coins")

    @pytest.mark.asyncio
    async def test_executor_new_transaction(self):
        mock_client = AsyncMock()
        mock_client.config = MagicMock()
        executor = PysuiSerialExecutor(client=mock_client, sender="0xsender")
        mock_client.transaction = AsyncMock(return_value=MagicMock())
        txn = await executor.new_transaction()
        assert txn is not None

    def test_executor_build_context(self):
        executor = _make_executor()
        executor._tracked_balance = 1000000
        ctx = executor._build_executor_context()
        assert isinstance(ctx, ExecutorContext)
        assert ctx.sender == "0xsender"
        assert ctx.gas_coins == []
        assert ctx.tracked_balance == 1000000


# ---------------------------------------------------------------------------
# State machine tests
# ---------------------------------------------------------------------------

class TestExecuteTransactionsStateMachine:
    """End-to-end tests for execute_transactions state machine."""

    def _patched_executor(self, executor, mock_executed_tx):
        return (
            patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value={"tx_bytestr": "fake_tx", "sig_array": ["fake_sig"]})),
            patch.object(executor._signing_block, "get_signatures", return_value=["fake_sig"]),
            patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_executed_tx)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor, "reset_cache", new=AsyncMock()),
        )

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self):
        executor = _make_executor()
        results = await executor.execute_transactions([])
        assert results == []

    @pytest.mark.asyncio
    async def test_happy_path_single_transaction(self):
        executor = _make_executor()
        mock_executed_tx, mock_effects = _mock_executed_tx()
        patches = self._patched_executor(executor, mock_executed_tx)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            results = await executor.execute_transactions([MagicMock()])
        assert len(results) == 1
        assert results[0] is mock_executed_tx

    @pytest.mark.asyncio
    async def test_happy_path_three_transactions(self):
        executor = _make_executor()
        mock_executed_tx, mock_effects = _mock_executed_tx()
        patches = self._patched_executor(executor, mock_executed_tx)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            results = await executor.execute_transactions([MagicMock(), MagicMock(), MagicMock()])
        assert len(results) == 3
        assert all(r is mock_executed_tx for r in results)

    @pytest.mark.asyncio
    async def test_error_on_build_fills_remaining_skipped(self):
        executor = _make_executor()
        mock_executed_tx, mock_effects = _mock_executed_tx()
        build_error = ValueError("no gas")
        call_count = 0

        async def build_side_effect(tx, signer_block, gas_objects_override=None):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise build_error
            return {"tx_bytestr": "fake_tx", "sig_array": ["fake_sig"]}

        patches = self._patched_executor(executor, mock_executed_tx)
        with patches[0] as cache_build, patches[1], patches[2], patches[3], patches[4]:
            cache_build.side_effect = build_side_effect
            results = await executor.execute_transactions([MagicMock(), MagicMock(), MagicMock()])

        assert len(results) == 3
        assert results[0] is mock_executed_tx
        assert results[1] == (ExecutorError.BUILDING_ERROR, build_error)
        assert isinstance(results[2], ExecutionSkipped)
        assert results[2].transaction_index == 2
        assert results[2].reason == "Halt after error"

    @pytest.mark.asyncio
    async def test_error_on_execute_raw(self):
        executor = _make_executor()

        async def failing_execute(tx_str, sigs):
            raise ValueError("execution failed")

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value={"tx_bytestr": "fake_tx", "sig_array": ["sig"]})), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", side_effect=failing_execute):
            results = await executor.execute_transactions([MagicMock()])

        assert len(results) == 1
        assert results[0][0] == ExecutorError.EXECUTING_ERROR

    @pytest.mark.asyncio
    async def test_result_list_same_length_as_input(self):
        executor = _make_executor()
        mock_executed_tx, mock_effects = _mock_executed_tx()
        patches = self._patched_executor(executor, mock_executed_tx)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            for n in (1, 3, 5):
                results = await executor.execute_transactions([MagicMock()] * n)
                assert len(results) == n
                assert all(r is mock_executed_tx for r in results)


# ---------------------------------------------------------------------------
# Replenishment callback tests
# ---------------------------------------------------------------------------

class TestCoinReplenishment:
    """Test on_coins_low callback behavior."""

    def test_on_coins_low_callback_signature(self):
        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            return None

        executor = _make_executor(on_coins_low=on_coins_low)
        assert executor._on_coins_low is not None

    @pytest.mark.asyncio
    async def test_on_coins_low_returns_coins(self):
        returned_coins = ["0xcoin1", "0xcoin2"]

        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            assert isinstance(ctx, ExecutorContext)
            return returned_coins

        executor = _make_executor(on_coins_low=on_coins_low, min_balance_threshold=1000)
        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_coins_low(ctx)
        assert result == returned_coins

    @pytest.mark.asyncio
    async def test_on_coins_low_returns_none_signals_halt(self):
        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            return None

        executor = _make_executor(on_coins_low=on_coins_low, min_balance_threshold=1000)
        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_coins_low(ctx)
        assert result is None

    @pytest.mark.asyncio
    async def test_on_coins_low_receives_correct_context(self):
        captured_context = None

        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            nonlocal captured_context
            captured_context = ctx
            return None

        executor = _make_executor(on_coins_low=on_coins_low)
        executor._tracked_balance = 5000000
        ctx = executor._build_executor_context()
        await on_coins_low(ctx)
        assert captured_context.sender == "0xsender"
        assert captured_context.gas_coins == []
        assert captured_context.tracked_balance == 5000000


class TestBalanceReplenishment:
    """Test on_balance_low callback behavior."""

    def test_on_balance_low_callback_signature(self):
        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            return None

        executor = _make_executor(on_balance_low=on_balance_low)
        assert executor._on_balance_low is not None

    @pytest.mark.asyncio
    async def test_on_balance_low_returns_address(self):
        funding_wallet = "0xfunding_wallet"

        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            return funding_wallet

        executor = _make_executor(on_balance_low=on_balance_low, min_balance_threshold=1000)
        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_balance_low(ctx)
        assert result == funding_wallet

    @pytest.mark.asyncio
    async def test_on_balance_low_receives_correct_context(self):
        captured_context = None

        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            nonlocal captured_context
            captured_context = ctx
            return "0xfunding_address"

        executor = _make_executor(on_balance_low=on_balance_low)
        executor._tracked_balance = 5000000
        ctx = executor._build_executor_context()
        await on_balance_low(ctx)
        assert captured_context.sender == "0xsender"
        assert captured_context.tracked_balance == 5000000


# ---------------------------------------------------------------------------
# Replenishment via execute_transactions
# ---------------------------------------------------------------------------

class TestReplenishmentViaExecuteTransactions:
    """Behavioral tests: callbacks exercised through execute_transactions."""

    def _make_patched_executor(self, executor, computation_cost=200):
        mock_executed_tx, mock_effects = _mock_executed_tx(computation_cost=computation_cost, storage_cost=0, storage_rebate=0)
        patches = [
            patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value={"tx_bytestr": "tx", "sig_array": ["sig"]})),
            patch.object(executor._signing_block, "get_signatures", return_value=["sig"]),
            patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_executed_tx)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor._cache, "update_gas_coins", new=AsyncMock()),
            patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()),
            patch.object(executor._cache.cache, "getCustom", new=AsyncMock(return_value=[])),
        ]
        return patches, mock_executed_tx, mock_effects

    @pytest.mark.asyncio
    async def test_on_coins_low_returning_none_halts(self):
        triggered = []

        async def on_coins_low(ctx):
            triggered.append(ctx.tracked_balance)
            return None

        executor = _make_executor(min_balance_threshold=1000, on_coins_low=on_coins_low)
        executor._tracked_balance = 1100

        patches, mock_executed_tx, mock_effects = self._make_patched_executor(executor)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered) == 1
        assert triggered[0] == 900
        assert results[0] is mock_executed_tx
        assert isinstance(results[1], ExecutionSkipped)
        assert "coin replenishment declined" in results[1].reason

    @pytest.mark.asyncio
    async def test_on_balance_low_returning_none_halts(self):
        triggered = []

        async def on_balance_low(ctx):
            triggered.append(ctx.tracked_balance)
            return None

        executor = _make_executor(min_balance_threshold=1000, on_balance_low=on_balance_low)
        executor._tracked_balance = 1100

        patches, _, __ = self._make_patched_executor(executor)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered) == 1
        assert isinstance(results[1], ExecutionSkipped)
        assert "balance replenishment declined" in results[1].reason

    @pytest.mark.asyncio
    async def test_callback_not_triggered_above_threshold(self):
        callback_called = False

        async def on_coins_low(ctx):
            nonlocal callback_called
            callback_called = True
            return None

        executor = _make_executor(min_balance_threshold=1000, on_coins_low=on_coins_low)
        executor._tracked_balance = 100_000

        patches, mock_executed_tx, mock_effects = self._make_patched_executor(executor)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            results = await executor.execute_transactions([MagicMock()])

        assert not callback_called
        assert len(results) == 1
        assert results[0] is mock_executed_tx


# ---------------------------------------------------------------------------
# Threshold tests
# ---------------------------------------------------------------------------

class TestReplenishmentThreshold:
    """Test balance threshold triggering replenishment."""

    def test_min_balance_threshold_set(self):
        async def on_coins_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=5_000_000, on_coins_low=on_coins_low)
        assert executor._min_balance_threshold == 5_000_000

    def test_min_balance_threshold_none_by_default(self):
        executor = _make_executor()
        assert executor._min_balance_threshold is None

    @pytest.mark.asyncio
    async def test_threshold_determines_callback_trigger(self):
        triggered_at_balances = []

        async def on_coins_low(ctx):
            triggered_at_balances.append(ctx.tracked_balance)
            return None

        executor = _make_executor(min_balance_threshold=1000, on_coins_low=on_coins_low)
        executor._tracked_balance = 1100

        mock_executed_tx, mock_effects = _mock_executed_tx(computation_cost=200, storage_cost=0, storage_rebate=0)
        patches = [
            patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value={"tx_bytestr": "tx", "sig_array": ["sig"]})),
            patch.object(executor._signing_block, "get_signatures", return_value=["sig"]),
            patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_executed_tx)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor._cache, "update_gas_coins", new=AsyncMock()),
            patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()),
            patch.object(executor._cache.cache, "getCustom", new=AsyncMock(return_value=[])),
        ]
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered_at_balances) == 1
        assert triggered_at_balances[0] == 900
        assert isinstance(results[1], ExecutionSkipped)
