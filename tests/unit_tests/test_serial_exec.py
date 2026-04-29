#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for GqlSerialTransactionExecutor."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_common.executors import ExecutionSkipped, ExecutorError
from pysui.sui.sui_pgql.pgql_serial_exec import GqlSerialTransactionExecutor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_executor(**kwargs) -> GqlSerialTransactionExecutor:
    """Build an executor backed by a plain MagicMock client."""
    mock_client = MagicMock()
    mock_client.config = MagicMock()
    executor = GqlSerialTransactionExecutor(client=mock_client, sender="0xsender", **kwargs)
    # Pre-seed tracked_balance to avoid fetching during tests (unless explicitly testing that path)
    executor._tracked_balance = 1_000_000
    return executor


def _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200):
    """Build a minimal mock TransactionEffects (common type)."""
    from pysui.sui.sui_common.types import TransactionEffects, ExecutionStatus, GasCostSummary
    return TransactionEffects(
        transaction_digest="fakedigest",
        status=ExecutionStatus(success=True),
        gas_used=GasCostSummary(
            computation_cost=computation_cost,
            storage_cost=storage_cost,
            storage_rebate=storage_rebate,
        ),
        lamport_version=1,
        changed_objects=[],
    )


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

class TestGqlSerialTransactionExecutor:
    """Test GqlSerialTransactionExecutor initialization and structure."""

    def test_serial_executor_creation(self):
        """GqlSerialTransactionExecutor can be instantiated with required parameters."""
        executor = _make_executor()
        assert executor is not None
        assert executor._default_gas_budget == 50_000_000

    def test_serial_executor_with_sponsor(self):
        """GqlSerialTransactionExecutor accepts optional sponsor."""
        executor = _make_executor(sponsor="0xsponsor")
        assert executor is not None

    def test_serial_executor_custom_gas_budget(self):
        """GqlSerialTransactionExecutor accepts custom gas budget."""
        executor = _make_executor(default_gas_budget=100_000_000)
        assert executor._default_gas_budget == 100_000_000

    def test_serial_executor_with_balance_threshold(self):
        """GqlSerialTransactionExecutor accepts min_balance_threshold with a callback."""
        async def on_coins_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=1_000_000, on_coins_low=on_coins_low)
        assert executor._min_balance_threshold == 1_000_000

    def test_serial_executor_threshold_requires_callback(self):
        """min_balance_threshold without any callback raises ValueError."""
        with pytest.raises(ValueError, match="min_balance_threshold requires"):
            _make_executor(min_balance_threshold=1_000_000)

    def test_serial_executor_threshold_with_on_balance_low_only(self):
        """min_balance_threshold with only on_balance_low does not raise."""
        async def on_balance_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=1_000_000, on_balance_low=on_balance_low)
        assert executor._min_balance_threshold == 1_000_000
        assert executor._on_balance_low is not None
        assert executor._on_coins_low is None

    def test_serial_executor_with_callbacks(self):
        """GqlSerialTransactionExecutor accepts callback functions."""
        async def on_coins_low(ctx):
            return None

        async def on_balance_low(ctx):
            return None

        executor = _make_executor(on_coins_low=on_coins_low, on_balance_low=on_balance_low)
        assert executor._on_coins_low is not None
        assert executor._on_balance_low is not None

    def test_serial_executor_has_new_transaction_method(self):
        assert hasattr(GqlSerialTransactionExecutor, "new_transaction")

    def test_serial_executor_has_reset_cache_method(self):
        assert hasattr(GqlSerialTransactionExecutor, "reset_cache")

    def test_serial_executor_has_execute_transactions_method(self):
        assert hasattr(GqlSerialTransactionExecutor, "execute_transactions")

    @pytest.mark.asyncio
    async def test_serial_executor_new_transaction(self):
        """new_transaction returns a CachingTransaction."""
        mock_client = AsyncMock()
        mock_client.config = MagicMock()
        executor = GqlSerialTransactionExecutor(client=mock_client, sender="0xsender")

        mock_client.transaction = AsyncMock(return_value=MagicMock())
        txn = await executor.new_transaction()
        assert txn is not None

    def test_serial_executor_build_context(self):
        """_build_executor_context creates ExecutorContext."""
        from pysui.sui.sui_common.executors import ExecutorContext

        executor = _make_executor()
        executor._tracked_balance = 1000000
        ctx = executor._build_executor_context()
        assert isinstance(ctx, ExecutorContext)
        assert ctx.sender == "0xsender"
        assert ctx.gas_coins == []
        assert ctx.tracked_balance == 1000000

    def test_serial_executor_context_coins_are_copy(self):
        """Gas coins in _build_executor_context are empty (base class doesn't provide them)."""
        executor = _make_executor()
        executor._tracked_balance = 0
        ctx = executor._build_executor_context()
        # Base class returns empty gas_coins list by default
        assert ctx.gas_coins == []


# ---------------------------------------------------------------------------
# End-to-end state machine tests (#26)
# ---------------------------------------------------------------------------

class TestExecuteTransactionsStateMachine:
    """End-to-end tests for execute_transactions state machine with mocked cache."""

    def _patched_executor(self, executor, mock_effects):
        """Context manager that patches all heavy I/O on the executor."""
        return (
            patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="fake_tx")),
            patch.object(executor._signing_block, "get_signatures", return_value=["fake_sig"]),
            patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor, "reset_cache", new=AsyncMock()),
        )

    @pytest.mark.asyncio
    async def test_happy_path_three_transactions(self):
        """Three successful transactions return three results."""
        from pysui.sui.sui_common.types import TransactionEffects
        executor = _make_executor()
        mock_effects = _mock_effects()

        patches = self._patched_executor(executor, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            txns = [MagicMock(), MagicMock(), MagicMock()]
            results = await executor.execute_transactions(txns)

        assert len(results) == 3
        assert all(isinstance(r, TransactionEffects) for r in results)

    @pytest.mark.asyncio
    async def test_error_on_second_tx_fills_remaining_skipped(self):
        """If tx[1] fails, result list has result, error, and ExecutionSkipped for tx[2]."""
        from pysui.sui.sui_common.types import TransactionEffects
        executor = _make_executor()
        mock_effects = _mock_effects()
        build_error = ValueError("no gas")
        call_count = 0

        async def build_side_effect(tx, signer_block, default_gas_budget=50_000_000):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise build_error
            return "fake_tx"

        patches = self._patched_executor(executor, mock_effects)
        with patches[0] as cache_build, patches[1], patches[2], patches[3], patches[4] as reset_mock:
            # Override cache's build_transaction to fail on second call
            cache_build.side_effect = build_side_effect

            txns = [MagicMock(), MagicMock(), MagicMock()]
            results = await executor.execute_transactions(txns)

        assert len(results) == 3
        assert isinstance(results[0], TransactionEffects)
        assert results[1] == (ExecutorError.BUILDING_ERROR, build_error)
        assert isinstance(results[2], ExecutionSkipped)
        assert results[2].transaction_index == 2
        assert results[2].reason == "Halt after error"

    @pytest.mark.asyncio
    async def test_error_on_execute_raw(self):
        """A transaction error is returned as a tuple."""
        executor = _make_executor()
        executor._tracked_balance = 5_000_000  # simulate already initialized

        async def failing_execute(tx_str, sigs):
            raise ValueError("execution failed")

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="fake_tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", side_effect=failing_execute):
            results = await executor.execute_transactions([MagicMock()])

        assert len(results) == 1
        assert results[0][0] == ExecutorError.EXECUTING_ERROR

    @pytest.mark.asyncio
    async def test_execute_transactions_returns_list_same_length(self):
        """Result list always has the same length as the input list."""
        from pysui.sui.sui_common.types import TransactionEffects
        executor = _make_executor()
        mock_effects = _mock_effects()

        patches = self._patched_executor(executor, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            for n in (1, 3, 5):
                results = await executor.execute_transactions([MagicMock()] * n)
                assert len(results) == n
                # All should be successful TransactionEffects
                assert all(isinstance(r, TransactionEffects) for r in results)

    @pytest.mark.asyncio
    async def test_execute_transactions_empty_list_returns_empty(self):
        """execute_transactions with an empty list returns an empty list immediately."""
        executor = _make_executor()
        results = await executor.execute_transactions([])
        assert results == []


# ---------------------------------------------------------------------------
# Replenishment threshold behavioral tests (#27)
# ---------------------------------------------------------------------------

class TestReplenishmentThresholdBehavior:
    """Behavioral tests verifying threshold-triggered callback invocation.

    Note: These tests are disabled pending refactor of replenishment logic.
    The base class handles replenishment callbacks, and comprehensive testing
    of that interaction requires deeper mocking of the base class behavior.
    """

    @pytest.mark.asyncio
    async def test_callback_triggered_when_balance_drops_below_threshold(self):
        """on_coins_low is invoked after a transaction drops balance below threshold."""
        from pysui.sui.sui_common.types import TransactionEffects
        callback_called = False

        async def on_coins_low(ctx):
            nonlocal callback_called
            callback_called = True
            return None  # halt

        executor = _make_executor(min_balance_threshold=5_000, on_coins_low=on_coins_low)
        # Pre-seed tracked_balance just above threshold; effects will cost 1300 net
        executor._tracked_balance = 6_000

        # Net cost = 1000 + 500 - 200 = 1300 → balance drops to 4700 < 5000
        mock_effects = _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200)

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert callback_called, "on_coins_low should have been called"
        assert len(results) == 2
        assert isinstance(results[0], TransactionEffects)
        assert isinstance(results[1], ExecutionSkipped)
        assert results[1].reason == "coin replenishment declined"

    @pytest.mark.asyncio
    async def test_callback_not_triggered_when_balance_above_threshold(self):
        """on_coins_low is NOT invoked when balance stays above threshold."""
        from pysui.sui.sui_common.types import TransactionEffects
        callback_called = False

        async def on_coins_low(ctx):
            nonlocal callback_called
            callback_called = True
            return None

        executor = _make_executor(min_balance_threshold=1_000, on_coins_low=on_coins_low)
        executor._tracked_balance = 100_000  # well above threshold

        mock_effects = _mock_effects(computation_cost=100, storage_cost=50, storage_rebate=20)

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()):
            results = await executor.execute_transactions([MagicMock()])

        assert not callback_called
        assert len(results) == 1
        assert isinstance(results[0], TransactionEffects)

    @pytest.mark.asyncio
    async def test_callback_not_called_again_after_successful_replenishment(self):
        """After a successful on_coins_low replenishment, callback is not re-called next iteration."""
        from pysui.sui.sui_common.types import TransactionEffects
        call_count = 0

        async def on_coins_low(ctx):
            nonlocal call_count
            call_count += 1
            return ["0xcoin1"]  # return a new coin — replenishment succeeds

        executor = _make_executor(min_balance_threshold=5_000, on_coins_low=on_coins_low)
        executor._tracked_balance = 6_000

        # Net cost 1300 → balance drops to 4700 after tx[0], triggers callback
        mock_effects = _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200)

        async def mock_fetch_balance():
            return 50_000  # re-armed balance after replenishment

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()), \
             patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()), \
             patch.object(executor, "_fetch_initial_balance", new=mock_fetch_balance):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert call_count == 1, "callback should be called exactly once"
        assert len(results) == 2
        assert isinstance(results[0], TransactionEffects)
        assert isinstance(results[1], TransactionEffects)  # tx[1] should succeed, not be skipped
