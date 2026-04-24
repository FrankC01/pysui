#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for SerialTransactionExecutor."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_common.executors import ExecutionSkipped, ExecutorError
from pysui.sui.sui_pgql.execute.serial_exec import SerialTransactionExecutor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_executor(**kwargs) -> SerialTransactionExecutor:
    """Build an executor backed by a plain MagicMock client."""
    mock_client = MagicMock()
    mock_client.config = MagicMock()
    return SerialTransactionExecutor(client=mock_client, sender="0xsender", **kwargs)


def _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200):
    """Build a minimal mock TransactionEffects that satisfies serial_exec's access pattern."""
    gas_used = MagicMock()
    gas_used.computationCost = computation_cost
    gas_used.storageCost = storage_cost
    gas_used.storageRebate = storage_rebate

    v2 = MagicMock()
    v2.gasUsed = gas_used
    v2.transactionDigest.to_digest_str.return_value = "fakedigest"
    v2.changedObjects = []
    v2.lamportVersion = 1
    v2.gasObjectIndex.value = 0

    effects = MagicMock()
    effects.enum_name = "V2"
    effects.value = v2
    return effects


def _mock_execution_result():
    """Build a minimal mock ExecutionResultGQL."""
    from pysui.sui.sui_pgql.pgql_types import ExecutionResultGQL
    result = MagicMock(spec=ExecutionResultGQL)
    result.effects_bcs = base64.b64encode(b"fake_effects").decode()
    return result


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

class TestSerialTransactionExecutor:
    """Test SerialTransactionExecutor initialization and structure."""

    def test_serial_executor_creation(self):
        """SerialTransactionExecutor can be instantiated with required parameters."""
        executor = _make_executor()
        assert executor is not None
        assert executor._default_gas_budget == 50_000_000

    def test_serial_executor_with_sponsor(self):
        """SerialTransactionExecutor accepts optional sponsor."""
        executor = _make_executor(sponsor="0xsponsor")
        assert executor is not None

    def test_serial_executor_custom_gas_budget(self):
        """SerialTransactionExecutor accepts custom gas budget."""
        executor = _make_executor(default_gas_budget=100_000_000)
        assert executor._default_gas_budget == 100_000_000

    def test_serial_executor_with_balance_threshold(self):
        """SerialTransactionExecutor accepts min_balance_threshold with a callback."""
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
        """SerialTransactionExecutor accepts callback functions."""
        async def on_coins_low(ctx):
            return None

        async def on_balance_low(ctx):
            return None

        executor = _make_executor(on_coins_low=on_coins_low, on_balance_low=on_balance_low)
        assert executor._on_coins_low is not None
        assert executor._on_balance_low is not None

    def test_serial_executor_has_new_transaction_method(self):
        assert hasattr(SerialTransactionExecutor, "new_transaction")

    def test_serial_executor_has_reset_cache_method(self):
        assert hasattr(SerialTransactionExecutor, "reset_cache")

    def test_serial_executor_has_wait_for_last_transaction_method(self):
        assert hasattr(SerialTransactionExecutor, "wait_for_last_transaction")

    def test_serial_executor_has_execute_transactions_method(self):
        assert hasattr(SerialTransactionExecutor, "execute_transactions")

    @pytest.mark.asyncio
    async def test_serial_executor_new_transaction(self):
        """new_transaction returns a CachingTransaction."""
        mock_client = AsyncMock()
        mock_client.config = MagicMock()
        executor = SerialTransactionExecutor(client=mock_client, sender="0xsender")

        with patch("pysui.sui.sui_pgql.execute.serial_exec.CachingTransaction") as mock_txn:
            mock_txn.return_value = MagicMock()
            txn = await executor.new_transaction()
            assert txn is not None

    def test_serial_executor_build_context(self):
        """_build_executor_context creates ExecutorContext."""
        from pysui.sui.sui_common.executors import ExecutorContext

        executor = _make_executor()
        ctx = executor._build_executor_context([], 1000000)
        assert isinstance(ctx, ExecutorContext)
        assert ctx.sender == "0xsender"
        assert ctx.gas_coins == []
        assert ctx.tracked_balance == 1000000

    def test_serial_executor_context_coins_are_copy(self):
        """Gas coins passed to _build_executor_context are defensively copied."""
        executor = _make_executor()
        original = [MagicMock()]
        ctx = executor._build_executor_context(original, 0)
        ctx.gas_coins.clear()
        assert len(original) == 1  # original not mutated


# ---------------------------------------------------------------------------
# End-to-end state machine tests (#26)
# ---------------------------------------------------------------------------

class TestExecuteTransactionsStateMachine:
    """End-to-end tests for execute_transactions state machine with mocked cache."""

    def _patched_executor(self, executor, mock_result, mock_effects):
        """Context manager that patches all heavy I/O on the executor."""
        return (
            patch.object(executor, "_build_transaction", new=AsyncMock(return_value="fake_tx")),
            patch.object(executor, "_sign_transaction", return_value=["fake_sig"]),
            patch.object(executor._cache, "execute_transaction", new=AsyncMock(return_value=mock_result)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor._cache, "update_gas_coins", new=AsyncMock()),
            patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()),
            patch.object(executor, "reset_cache", new=AsyncMock()),
            patch("pysui.sui.sui_pgql.execute.serial_exec.bcst.TransactionEffects.deserialize", return_value=mock_effects),
            patch("pysui.sui.sui_pgql.execute.serial_exec._get_gascoin_from_effects", return_value=MagicMock()),
        )

    @pytest.mark.asyncio
    async def test_happy_path_three_transactions(self):
        """Three successful transactions return three results."""
        executor = _make_executor()
        mock_result = _mock_execution_result()
        mock_effects = _mock_effects()

        patches = self._patched_executor(executor, mock_result, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
            txns = [MagicMock(), MagicMock(), MagicMock()]
            results = await executor.execute_transactions(txns)

        assert len(results) == 3
        assert all(r is mock_result for r in results)

    @pytest.mark.asyncio
    async def test_error_on_second_tx_fills_remaining_skipped(self):
        """If tx[1] fails, result list has result, error, and ExecutionSkipped for tx[2]."""
        executor = _make_executor()
        mock_result = _mock_execution_result()
        mock_effects = _mock_effects()
        build_error = ValueError("no gas")
        call_count = 0

        async def build_side_effect(tx):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise build_error
            return "fake_tx"

        patches = self._patched_executor(executor, mock_result, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
            # Override build to fail on second call
            executor._build_transaction = build_side_effect
            reset_mock = executor.reset_cache

            txns = [MagicMock(), MagicMock(), MagicMock()]
            results = await executor.execute_transactions(txns)

        assert len(results) == 3
        assert results[0] is mock_result
        assert results[1] == (ExecutorError.BUILDING_ERROR, build_error)
        assert isinstance(results[2], ExecutionSkipped)
        assert results[2].transaction_index == 2
        assert results[2].reason == "prior transaction failed"
        reset_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_resets_tracked_balance(self):
        """A transaction error resets _tracked_balance to None so next call re-fetches."""
        executor = _make_executor()
        executor._tracked_balance = 5_000_000  # simulate already initialized

        async def failing_build(tx):
            raise ValueError("fail")

        with patch.object(executor, "_build_transaction", side_effect=failing_build), \
             patch.object(executor, "reset_cache", new=AsyncMock()):
            results = await executor.execute_transactions([MagicMock()])

        assert executor._tracked_balance is None
        assert len(results) == 1
        assert results[0][0] == ExecutorError.BUILDING_ERROR

    @pytest.mark.asyncio
    async def test_execute_transactions_returns_list_same_length(self):
        """Result list always has the same length as the input list."""
        executor = _make_executor()
        mock_result = _mock_execution_result()
        mock_effects = _mock_effects()

        patches = self._patched_executor(executor, mock_result, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
            for n in (1, 3, 5):
                results = await executor.execute_transactions([MagicMock()] * n)
                assert len(results) == n

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
    """Behavioral tests verifying threshold-triggered callback invocation."""

    @pytest.mark.asyncio
    async def test_callback_triggered_when_balance_drops_below_threshold(self):
        """on_coins_low is invoked after a transaction drops balance below threshold."""
        callback_called = False

        async def on_coins_low(ctx):
            nonlocal callback_called
            callback_called = True
            return None  # halt

        executor = _make_executor(min_balance_threshold=5_000, on_coins_low=on_coins_low)
        # Pre-seed tracked_balance just above threshold; effects will cost 1300 net
        executor._tracked_balance = 6_000

        mock_result = _mock_execution_result()
        # Net cost = 1000 + 500 - 200 = 1300 → balance drops to 4700 < 5000
        mock_effects = _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200)

        with patch.object(executor, "_build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor, "_sign_transaction", return_value=["sig"]), \
             patch.object(executor._cache, "execute_transaction", new=AsyncMock(return_value=mock_result)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()), \
             patch.object(executor._cache, "update_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache.cache, "getCustom", new=AsyncMock(return_value=[])), \
             patch("pysui.sui.sui_pgql.execute.serial_exec.bcst.TransactionEffects.deserialize", return_value=mock_effects), \
             patch("pysui.sui.sui_pgql.execute.serial_exec._get_gascoin_from_effects", return_value=MagicMock()):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert callback_called, "on_coins_low should have been called"
        assert len(results) == 2
        assert results[0] is mock_result
        assert isinstance(results[1], ExecutionSkipped)
        assert results[1].reason == "coin replenishment declined"

    @pytest.mark.asyncio
    async def test_callback_not_triggered_when_balance_above_threshold(self):
        """on_coins_low is NOT invoked when balance stays above threshold."""
        callback_called = False

        async def on_coins_low(ctx):
            nonlocal callback_called
            callback_called = True
            return None

        executor = _make_executor(min_balance_threshold=1_000, on_coins_low=on_coins_low)
        executor._tracked_balance = 100_000  # well above threshold

        mock_result = _mock_execution_result()
        mock_effects = _mock_effects(computation_cost=100, storage_cost=50, storage_rebate=20)

        with patch.object(executor, "_build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor, "_sign_transaction", return_value=["sig"]), \
             patch.object(executor._cache, "execute_transaction", new=AsyncMock(return_value=mock_result)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()), \
             patch.object(executor._cache, "update_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()), \
             patch("pysui.sui.sui_pgql.execute.serial_exec.bcst.TransactionEffects.deserialize", return_value=mock_effects), \
             patch("pysui.sui.sui_pgql.execute.serial_exec._get_gascoin_from_effects", return_value=MagicMock()):
            results = await executor.execute_transactions([MagicMock()])

        assert not callback_called
        assert len(results) == 1
        assert results[0] is mock_result

    @pytest.mark.asyncio
    async def test_callback_not_called_again_after_successful_replenishment(self):
        """After a successful on_coins_low replenishment, callback is not re-called next iteration."""
        call_count = 0

        async def on_coins_low(ctx):
            nonlocal call_count
            call_count += 1
            return ["0xcoin1"]  # return a new coin

        executor = _make_executor(min_balance_threshold=5_000, on_coins_low=on_coins_low)
        executor._tracked_balance = 6_000

        mock_result = _mock_execution_result()
        # Net cost 1300 → balance drops to 4700 after tx[0], triggers callback
        mock_effects = _mock_effects(computation_cost=1000, storage_cost=500, storage_rebate=200)

        # After replenishment, _refresh_tracked_balance returns 50_000
        async def mock_refresh():
            return 50_000

        from pysui.sui.sui_pgql.pgql_types import ObjectReadGQL
        mock_coin_obj = MagicMock(spec=ObjectReadGQL)
        mock_coin_obj.coin_object_id = "0xcoin1"
        mock_coin_obj.version = 1
        mock_coin_obj.object_digest = "a" * 44

        with patch.object(executor, "_build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor, "_sign_transaction", return_value=["sig"]), \
             patch.object(executor._cache, "execute_transaction", new=AsyncMock(return_value=mock_result)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()), \
             patch.object(executor._cache, "update_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache.cache, "getCustom", new=AsyncMock(return_value=[])), \
             patch.object(executor._cache, "get_sui_objects", new=AsyncMock(return_value=[mock_coin_obj])), \
             patch.object(executor, "_refresh_tracked_balance", new=mock_refresh), \
             patch("pysui.sui.sui_pgql.execute.serial_exec.bcst.TransactionEffects.deserialize", return_value=mock_effects), \
             patch("pysui.sui.sui_pgql.execute.serial_exec._get_gascoin_from_effects", return_value=MagicMock()), \
             patch("pysui.sui.sui_pgql.execute.serial_exec.bcs.ObjectReference"), \
             patch("pysui.sui.sui_pgql.execute.serial_exec.bcs.Address.from_str"), \
             patch("pysui.sui.sui_pgql.execute.serial_exec.bcs.Digest.from_str"):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert call_count == 1, "callback should be called exactly once"
        assert len(results) == 2
        assert results[0] is mock_result
        assert results[1] is mock_result  # tx[1] should succeed, not be skipped


# ---------------------------------------------------------------------------
# _get_gascoin_from_effects unit tests (C10)
# ---------------------------------------------------------------------------

class TestGetGascoinFromEffects:
    """Unit tests for the module-level _get_gascoin_from_effects function."""

    def _make_v2_effects(self, output_state_enum="ObjectWrite"):
        digest_mock = MagicMock()
        owner_mock = MagicMock()
        out_state = MagicMock()
        out_state.enum_name = output_state_enum
        out_state.value = (digest_mock, owner_mock)
        change = MagicMock()
        change.outputState = out_state
        addr = MagicMock()
        v2 = MagicMock()
        v2.changedObjects = [(addr, change)]
        v2.gasObjectIndex.value = 0
        v2.lamportVersion = 5
        effects = MagicMock()
        effects.enum_name = "V2"
        effects.value = v2
        return effects, addr, digest_mock

    def test_raises_on_non_v2_effects(self):
        from pysui.sui.sui_pgql.execute.serial_exec import _get_gascoin_from_effects
        effects = MagicMock()
        effects.enum_name = "V1"
        with pytest.raises(ValueError, match="Expect V2 effects"):
            _get_gascoin_from_effects(effects)

    def test_raises_when_gas_object_not_found(self):
        from pysui.sui.sui_pgql.execute.serial_exec import _get_gascoin_from_effects
        v2 = MagicMock()
        v2.changedObjects = [None]
        v2.gasObjectIndex.value = 0
        effects = MagicMock()
        effects.enum_name = "V2"
        effects.value = v2
        with pytest.raises(ValueError, match="Gas object not found"):
            _get_gascoin_from_effects(effects)

    def test_raises_on_unexpected_output_state(self):
        from pysui.sui.sui_pgql.execute.serial_exec import _get_gascoin_from_effects
        effects, _, _ = self._make_v2_effects(output_state_enum="NotExist")
        with pytest.raises(ValueError, match="Unexpected gas object state"):
            _get_gascoin_from_effects(effects)

    def test_returns_object_reference_on_success(self):
        from pysui.sui.sui_pgql.execute.serial_exec import _get_gascoin_from_effects
        effects, addr, digest_mock = self._make_v2_effects()
        with patch("pysui.sui.sui_pgql.execute.serial_exec.bcs.ObjectReference") as mock_ref:
            mock_ref.return_value = "obj_ref"
            result = _get_gascoin_from_effects(effects)
        assert result == "obj_ref"
        mock_ref.assert_called_once_with(addr, 5, digest_mock)
