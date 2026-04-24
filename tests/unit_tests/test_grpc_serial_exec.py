#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for GrpcSerialTransactionExecutor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_common.executors import ExecutionSkipped, ExecutorError, ExecutorContext
from pysui.sui.sui_grpc.grpc_serial_exec import GrpcSerialTransactionExecutor, _grpc_effects_to_common
from pysui.sui.sui_common.types import TransactionEffects


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_grpc_client():
    """Build a mock AsyncGrpcClient."""
    mock_client = MagicMock()
    mock_client.config = MagicMock()
    return mock_client


def _make_executor(**kwargs) -> GrpcSerialTransactionExecutor:
    """Build an executor backed by a plain MagicMock client."""
    executor = GrpcSerialTransactionExecutor(
        client=_make_grpc_client(), sender="0xsender", **kwargs
    )
    executor._tracked_balance = 1_000_000
    return executor


def _make_grpc_effects(
    computation_cost=1000,
    storage_cost=500,
    storage_rebate=200,
    success=True,
    digest="fakedigest",
    lamport=1,
):
    """Build a mock gRPC TransactionEffects protobuf message."""
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot

    gas = MagicMock()
    gas.computation_cost = computation_cost
    gas.storage_cost = storage_cost
    gas.storage_rebate = storage_rebate

    status = MagicMock()
    status.success = success

    mock = MagicMock()
    mock.transaction_digest = digest
    mock.status = status
    mock.gas_used = gas
    mock.lamport_version = lamport
    mock.changed_objects = []
    mock.gas_object = None
    return mock


def _make_common_effects(
    computation_cost=1000,
    storage_cost=500,
    storage_rebate=200,
):
    """Build a protocol-agnostic TransactionEffects directly."""
    from pysui.sui.sui_common.types import ExecutionStatus, GasCostSummary
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

class TestGrpcSerialTransactionExecutor:
    """Test GrpcSerialTransactionExecutor initialization."""

    def test_grpc_executor_creation(self):
        """GrpcSerialTransactionExecutor can be instantiated with required parameters."""
        executor = _make_executor()
        assert executor is not None
        assert executor._default_gas_budget == 50_000_000

    def test_grpc_executor_with_sponsor(self):
        """GrpcSerialTransactionExecutor accepts optional sponsor."""
        executor = _make_executor(sponsor="0xsponsor")
        assert executor is not None

    def test_grpc_executor_custom_gas_budget(self):
        """GrpcSerialTransactionExecutor accepts custom gas budget."""
        executor = _make_executor(default_gas_budget=100_000_000)
        assert executor._default_gas_budget == 100_000_000

    def test_grpc_executor_threshold_requires_callback(self):
        """min_balance_threshold without any callback raises ValueError."""
        with pytest.raises(ValueError, match="min_balance_threshold requires"):
            _make_executor(min_balance_threshold=1_000_000)

    def test_grpc_executor_with_on_coins_low(self):
        """GrpcSerialTransactionExecutor accepts on_coins_low callback."""
        async def on_coins_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=1_000_000, on_coins_low=on_coins_low)
        assert executor._min_balance_threshold == 1_000_000
        assert executor._on_coins_low is not None
        assert executor._on_balance_low is None

    def test_grpc_executor_with_on_balance_low(self):
        """GrpcSerialTransactionExecutor accepts on_balance_low callback."""
        async def on_balance_low(ctx):
            return None

        executor = _make_executor(min_balance_threshold=1_000_000, on_balance_low=on_balance_low)
        assert executor._min_balance_threshold == 1_000_000
        assert executor._on_balance_low is not None
        assert executor._on_coins_low is None

    def test_grpc_executor_with_both_callbacks(self):
        """GrpcSerialTransactionExecutor accepts both callbacks."""
        async def on_coins_low(ctx):
            return None

        async def on_balance_low(ctx):
            return None

        executor = _make_executor(on_coins_low=on_coins_low, on_balance_low=on_balance_low)
        assert executor._on_coins_low is not None
        assert executor._on_balance_low is not None

    def test_grpc_executor_has_execute_transactions(self):
        assert hasattr(GrpcSerialTransactionExecutor, "execute_transactions")

    def test_grpc_executor_has_new_transaction(self):
        assert hasattr(GrpcSerialTransactionExecutor, "new_transaction")

    def test_grpc_executor_has_reset_cache(self):
        assert hasattr(GrpcSerialTransactionExecutor, "reset_cache")

    def test_grpc_executor_build_context(self):
        """_build_executor_context creates ExecutorContext."""
        executor = _make_executor()
        executor._tracked_balance = 500_000
        ctx = executor._build_executor_context()
        assert isinstance(ctx, ExecutorContext)
        assert ctx.sender == "0xsender"
        assert ctx.tracked_balance == 500_000
        assert ctx.gas_coins == []


# ---------------------------------------------------------------------------
# _grpc_effects_to_common conversion tests
# ---------------------------------------------------------------------------

class TestGrpcEffectsToCommon:
    """Test _grpc_effects_to_common conversion."""

    def test_basic_conversion(self):
        """Basic gRPC effects convert to common type correctly."""
        grpc_eff = _make_grpc_effects()
        result = _grpc_effects_to_common(grpc_eff)
        assert isinstance(result, TransactionEffects)
        assert result.transaction_digest == "fakedigest"
        assert result.status.success is True
        assert result.gas_used.computation_cost == 1000
        assert result.gas_used.storage_cost == 500
        assert result.gas_used.storage_rebate == 200
        assert result.lamport_version == 1
        assert result.changed_objects == []
        assert result.gas_object is None

    def test_none_effects_raises(self):
        """None effects raises ValueError."""
        with pytest.raises(ValueError, match="TransactionEffects is None"):
            _grpc_effects_to_common(None)

    def test_gas_cost_defaults_when_none(self):
        """Zero gas costs when gas_used is None."""
        grpc_eff = _make_grpc_effects()
        grpc_eff.gas_used = None
        result = _grpc_effects_to_common(grpc_eff)
        assert result.gas_used.computation_cost == 0
        assert result.gas_used.storage_cost == 0
        assert result.gas_used.storage_rebate == 0

    def test_changed_object_does_not_exist(self):
        """DOES_NOT_EXIST output_state maps correctly."""
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        grpc_eff = _make_grpc_effects()
        co = MagicMock()
        co.object_id = "0xobj1"
        co.output_state = sui_prot.ChangedObjectOutputObjectState.DOES_NOT_EXIST
        co.output_digest = None
        co.output_owner = None
        grpc_eff.changed_objects = [co]
        result = _grpc_effects_to_common(grpc_eff)
        assert len(result.changed_objects) == 1
        assert result.changed_objects[0].output_state == "DoesNotExist"
        assert result.changed_objects[0].object_id == "0xobj1"

    def test_changed_object_object_write(self):
        """OBJECT_WRITE output_state maps correctly."""
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        grpc_eff = _make_grpc_effects()
        co = MagicMock()
        co.object_id = "0xobj2"
        co.output_state = sui_prot.ChangedObjectOutputObjectState.OBJECT_WRITE
        co.output_digest = "somedigest"
        owner = MagicMock()
        owner.kind = sui_prot.OwnerOwnerKind.ADDRESS
        owner.address = "0xowner"
        owner.version = None
        co.output_owner = owner
        grpc_eff.changed_objects = [co]
        result = _grpc_effects_to_common(grpc_eff)
        assert result.changed_objects[0].output_state == "ObjectWrite"
        assert result.changed_objects[0].output_digest == "somedigest"
        assert result.changed_objects[0].output_owner.kind == "AddressOwner"
        assert result.changed_objects[0].output_owner.address == "0xowner"

    def test_unknown_output_state_skipped(self):
        """Unknown output_state entries are skipped."""
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        grpc_eff = _make_grpc_effects()
        co = MagicMock()
        co.object_id = "0xobj3"
        co.output_state = sui_prot.ChangedObjectOutputObjectState.UNKNOWN
        co.output_digest = None
        co.output_owner = None
        grpc_eff.changed_objects = [co]
        result = _grpc_effects_to_common(grpc_eff)
        assert result.changed_objects == []


# ---------------------------------------------------------------------------
# execute_transactions state machine tests
# ---------------------------------------------------------------------------

class TestGrpcExecuteTransactions:
    """End-to-end tests for GrpcSerialTransactionExecutor.execute_transactions."""

    def _patched_executor(self, executor, mock_effects):
        """Context manager patches that stub out I/O on the executor."""
        return (
            patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="fake_tx")),
            patch.object(executor._signing_block, "get_signatures", return_value=["fake_sig"]),
            patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor, "reset_cache", new=AsyncMock()),
        )

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self):
        """execute_transactions with an empty list returns an empty list."""
        executor = _make_executor()
        results = await executor.execute_transactions([])
        assert results == []

    @pytest.mark.asyncio
    async def test_happy_path_single_transaction(self):
        """Single successful transaction returns one TransactionEffects."""
        executor = _make_executor()
        mock_effects = _make_common_effects()

        patches = self._patched_executor(executor, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            results = await executor.execute_transactions([MagicMock()])

        assert len(results) == 1
        assert isinstance(results[0], TransactionEffects)

    @pytest.mark.asyncio
    async def test_happy_path_three_transactions(self):
        """Three successful transactions return three results."""
        executor = _make_executor()
        mock_effects = _make_common_effects()

        patches = self._patched_executor(executor, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            results = await executor.execute_transactions([MagicMock(), MagicMock(), MagicMock()])

        assert len(results) == 3
        assert all(isinstance(r, TransactionEffects) for r in results)

    @pytest.mark.asyncio
    async def test_error_on_build_fills_remaining_skipped(self):
        """If build fails on tx[1], result list has result, error, and ExecutionSkipped."""
        executor = _make_executor()
        mock_effects = _make_common_effects()
        build_error = ValueError("no gas")
        call_count = 0

        async def build_side_effect(tx, signer_block, default_gas_budget=50_000_000):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise build_error
            return "fake_tx"

        patches = self._patched_executor(executor, mock_effects)
        with patches[0] as cache_build, patches[1], patches[2], patches[3], patches[4]:
            cache_build.side_effect = build_side_effect
            results = await executor.execute_transactions([MagicMock(), MagicMock(), MagicMock()])

        assert len(results) == 3
        assert isinstance(results[0], TransactionEffects)
        assert results[1] == (ExecutorError.BUILDING_ERROR, build_error)
        assert isinstance(results[2], ExecutionSkipped)
        assert results[2].transaction_index == 2
        assert results[2].reason == "Halt after error"

    @pytest.mark.asyncio
    async def test_execute_raw_error_returned_as_tuple(self):
        """An execution error is returned as a tuple."""
        executor = _make_executor()

        async def failing_execute(tx_str, sigs):
            raise ValueError("execution failed")

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="fake_tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", side_effect=failing_execute):
            results = await executor.execute_transactions([MagicMock()])

        assert len(results) == 1
        assert results[0][0] == ExecutorError.EXECUTING_ERROR

    @pytest.mark.asyncio
    async def test_result_list_same_length_as_input(self):
        """Result list always has the same length as input list."""
        executor = _make_executor()
        mock_effects = _make_common_effects()

        patches = self._patched_executor(executor, mock_effects)
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            for n in (1, 3, 5):
                results = await executor.execute_transactions([MagicMock()] * n)
                assert len(results) == n
                assert all(isinstance(r, TransactionEffects) for r in results)


# ---------------------------------------------------------------------------
# Replenishment tests
# ---------------------------------------------------------------------------

class TestGrpcReplenishment:
    """Test replenishment callbacks via GrpcSerialTransactionExecutor."""

    @pytest.mark.asyncio
    async def test_on_coins_low_returning_none_halts(self):
        """on_coins_low returning None halts remaining transactions."""
        triggered = []

        async def on_coins_low(ctx):
            triggered.append(ctx.tracked_balance)
            return None

        executor = GrpcSerialTransactionExecutor(
            client=_make_grpc_client(),
            sender="0xsender",
            min_balance_threshold=1000,
            on_coins_low=on_coins_low,
        )
        executor._tracked_balance = 1100

        mock_effects = _make_common_effects(computation_cost=200, storage_cost=0, storage_rebate=0)

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered) == 1
        assert triggered[0] == 900  # 1100 - 200
        assert len(results) == 2
        assert isinstance(results[0], TransactionEffects)
        assert isinstance(results[1], ExecutionSkipped)
        assert "coin replenishment declined" in results[1].reason

    @pytest.mark.asyncio
    async def test_on_balance_low_returning_none_halts(self):
        """on_balance_low returning None halts remaining transactions."""
        triggered = []

        async def on_balance_low(ctx):
            triggered.append(ctx.tracked_balance)
            return None

        executor = GrpcSerialTransactionExecutor(
            client=_make_grpc_client(),
            sender="0xsender",
            min_balance_threshold=1000,
            on_balance_low=on_balance_low,
        )
        executor._tracked_balance = 1100

        mock_effects = _make_common_effects(computation_cost=200, storage_cost=0, storage_rebate=0)

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered) == 1
        assert len(results) == 2
        assert isinstance(results[1], ExecutionSkipped)
        assert "balance replenishment declined" in results[1].reason

    @pytest.mark.asyncio
    async def test_callback_not_triggered_above_threshold(self):
        """Callback is not invoked when balance stays above threshold."""
        callback_called = False

        async def on_coins_low(ctx):
            nonlocal callback_called
            callback_called = True
            return None

        executor = GrpcSerialTransactionExecutor(
            client=_make_grpc_client(),
            sender="0xsender",
            min_balance_threshold=1000,
            on_coins_low=on_coins_low,
        )
        executor._tracked_balance = 100_000

        mock_effects = _make_common_effects(computation_cost=100, storage_cost=0, storage_rebate=0)

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()):
            results = await executor.execute_transactions([MagicMock()])

        assert not callback_called
        assert len(results) == 1
        assert isinstance(results[0], TransactionEffects)

    @pytest.mark.asyncio
    async def test_on_coins_low_success_rearms_balance(self):
        """After successful replenishment, balance is re-armed via _fetch_initial_balance."""
        call_count = 0

        async def on_coins_low(ctx):
            nonlocal call_count
            call_count += 1
            return ["0xcoin1"]

        executor = GrpcSerialTransactionExecutor(
            client=_make_grpc_client(),
            sender="0xsender",
            min_balance_threshold=5000,
            on_coins_low=on_coins_low,
        )
        executor._tracked_balance = 6000

        mock_effects = _make_common_effects(computation_cost=1300, storage_cost=0, storage_rebate=0)

        async def mock_fetch_balance():
            return 50_000

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()), \
             patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()), \
             patch.object(executor, "_fetch_initial_balance", new=mock_fetch_balance):
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert call_count == 1
        assert len(results) == 2
        assert isinstance(results[0], TransactionEffects)
        assert isinstance(results[1], TransactionEffects)
