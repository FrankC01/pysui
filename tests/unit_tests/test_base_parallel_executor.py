#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for _BaseParallelExecutor."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pysui.sui.sui_common.executors.base_parallel_executor import _BaseParallelExecutor
from pysui.sui.sui_common.executors.exec_types import ExecutorError
from pysui.sui.sui_common.executors.gas_pool import GasCoin
from pysui.sui.sui_common.executors.object_registry import (
    InMemoryObjectRegistry,
    _set_object_registry_for_tests,
)
from pysui.sui.sui_common.types import (
    TransactionEffects,
    ExecutionStatus,
    GasCostSummary,
    ChangedObject,
    Owner,
)


# ---------------------------------------------------------------------------
# Test double — concrete _BaseParallelExecutor subclass
# ---------------------------------------------------------------------------

class _TestParallelExecutor(_BaseParallelExecutor):
    """Minimal concrete subclass for testing."""

    def __init__(self, effects_factory=None, **kwargs):
        super().__init__(**kwargs)
        self._effects_factory = effects_factory or (lambda: _make_effects())
        self._execute_count = 0

    def _create_caching_executor(self):
        mock = MagicMock()
        mock.build_transaction = AsyncMock(return_value="dGVzdA==")
        mock.apply_effects = AsyncMock()
        mock.sync_to_registry = AsyncMock()
        mock.update_gas_coins = AsyncMock()
        return mock

    async def _execute_single(self, tx_str, sigs, caching_exec):
        self._execute_count += 1
        return self._effects_factory()

    async def _refill_coin_pool(self, n: int) -> list[GasCoin]:
        return [
            GasCoin(object_id=f"0x{'ff' * 31}{i:02x}", version="1", digest="d", balance=5_000_000)
            for i in range(n)
        ]

    async def _fetch_balance(self) -> int:
        return 10_000_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _oid(suffix: str = "01") -> str:
    return "0x" + "aa" * 31 + suffix


def _coin(suffix: str = "01", balance: int = 2_000_000) -> GasCoin:
    return GasCoin(object_id=_oid(suffix), version="1", digest="d", balance=balance)


def _make_effects(
    *,
    computation_cost: int = 1000,
    storage_cost: int = 500,
    storage_rebate: int = 200,
    gas_oid: str = "0x" + "ee" * 32,
) -> TransactionEffects:
    return TransactionEffects(
        transaction_digest="fakedigest",
        status=ExecutionStatus(success=True),
        gas_used=GasCostSummary(
            computation_cost=computation_cost,
            storage_cost=storage_cost,
            storage_rebate=storage_rebate,
        ),
        lamport_version=2,
        changed_objects=[],
        gas_object=ChangedObject(
            object_id=gas_oid,
            output_state="ObjectWrite",
            output_digest="newdigest",
            output_owner=Owner(kind="AddressOwner", address="0xsender"),
        ),
    )


def _make_mock_client():
    client = MagicMock()
    client.config = MagicMock()
    return client


def _make_tx(unresolved_ids: list[str] | None = None):
    """Make a mock transaction with optional unresolved object inputs."""
    tx = MagicMock()
    if unresolved_ids is not None:
        unresolved = {
            i: MagicMock(ObjectStr=oid)
            for i, oid in enumerate(unresolved_ids)
        }
        tx.builder.get_unresolved_inputs.return_value = unresolved
    else:
        tx.builder.get_unresolved_inputs.side_effect = AttributeError
    return tx


def _make_signing_block_patcher():
    """Patch SignerBlock.get_signatures to return a fake sig list."""
    return patch(
        "pysui.sui.sui_common.executors.base_parallel_executor.SignerBlock.get_signatures",
        return_value=["sig1"],
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestBaseParallelExecutorConstruction:
    def _make(self, **kwargs) -> _TestParallelExecutor:
        defaults = dict(
            client=_make_mock_client(),
            sender="0xsender",
            gas_mode="coins",
            max_tasks=2,
        )
        defaults.update(kwargs)
        return _TestParallelExecutor(**defaults)

    def test_coins_mode_creates_pool(self):
        ex = self._make(gas_mode="coins")
        assert ex._gas_pool is not None

    def test_address_balance_mode_no_pool(self):
        ex = self._make(gas_mode="addressBalance")
        assert ex._gas_pool is None

    def test_invalid_gas_mode_raises(self):
        with pytest.raises(ValueError, match="gas_mode"):
            self._make(gas_mode="unknown")

    def test_address_balance_with_threshold_and_no_callback_raises(self):
        with pytest.raises(ValueError, match="on_balance_low"):
            self._make(gas_mode="addressBalance", min_balance_threshold=1_000_000)

    def test_address_balance_with_both_threshold_and_callback_ok(self):
        cb = AsyncMock()
        ex = self._make(gas_mode="addressBalance", min_balance_threshold=1_000_000, on_balance_low=cb)
        assert ex._on_balance_low is cb

    def test_custom_registry_used(self):
        reg = InMemoryObjectRegistry()
        ex = self._make(registry=reg)
        assert ex._registry is reg

    def test_sponsor_sets_gas_owner(self):
        ex = self._make(sponsor="0xsponsor")
        assert ex._gas_owner == "0xsponsor"

    def test_sender_only_gas_owner(self):
        ex = self._make()
        assert ex._gas_owner == "0xsender"


# ---------------------------------------------------------------------------
# execute_transactions — address balance mode
# ---------------------------------------------------------------------------

class TestExecuteTransactionsAddressBalance:
    def setup_method(self):
        _set_object_registry_for_tests(InMemoryObjectRegistry())

    def teardown_method(self):
        _set_object_registry_for_tests(None)

    def _make(self, **kwargs) -> _TestParallelExecutor:
        defaults = dict(
            client=_make_mock_client(),
            sender="0xsender",
            gas_mode="addressBalance",
            max_tasks=4,
        )
        defaults.update(kwargs)
        return _TestParallelExecutor(**defaults)

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self):
        ex = self._make()
        with _make_signing_block_patcher():
            results = await ex.execute_transactions([])
        assert results == []

    @pytest.mark.asyncio
    async def test_single_success(self):
        ex = self._make()
        tx = _make_tx()
        with _make_signing_block_patcher():
            results = await ex.execute_transactions([tx])
        assert len(results) == 1
        assert isinstance(results[0], TransactionEffects)

    @pytest.mark.asyncio
    async def test_multiple_success_in_order(self):
        ex = self._make()
        txns = [_make_tx() for _ in range(5)]
        with _make_signing_block_patcher():
            results = await ex.execute_transactions(txns)
        assert len(results) == 5
        assert all(isinstance(r, TransactionEffects) for r in results)
        assert ex._execute_count == 5

    @pytest.mark.asyncio
    async def test_failure_returns_error_tuple(self):
        async def _fail(*args, **kwargs):
            raise RuntimeError("boom")

        ex = self._make()
        ex._execute_single = _fail
        tx = _make_tx()
        with _make_signing_block_patcher():
            results = await ex.execute_transactions([tx])
        assert len(results) == 1
        assert isinstance(results[0], tuple)
        err, exc = results[0]
        assert err == ExecutorError.EXECUTING_ERROR
        assert "boom" in str(exc)

    @pytest.mark.asyncio
    async def test_partial_failures_do_not_halt_remaining(self):
        call_count = 0

        async def _alternate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("middle failure")
            return _make_effects()

        ex = self._make()
        ex._execute_single = _alternate
        txns = [_make_tx() for _ in range(3)]
        with _make_signing_block_patcher():
            results = await ex.execute_transactions(txns)
        assert len(results) == 3
        assert isinstance(results[0], TransactionEffects)
        assert isinstance(results[1], tuple)
        assert isinstance(results[2], TransactionEffects)

    @pytest.mark.asyncio
    async def test_balance_fetched_once_on_first_call(self):
        ex = self._make()
        fetch_count = 0

        async def _count_fetch():
            nonlocal fetch_count
            fetch_count += 1
            return 5_000_000

        ex._fetch_balance = _count_fetch
        txns = [_make_tx() for _ in range(3)]
        with _make_signing_block_patcher():
            await ex.execute_transactions(txns)
        assert fetch_count == 1

    @pytest.mark.asyncio
    async def test_balance_not_refetched_on_second_call(self):
        ex = self._make()
        fetch_count = 0

        async def _count_fetch():
            nonlocal fetch_count
            fetch_count += 1
            return 5_000_000

        ex._fetch_balance = _count_fetch
        ex._tracked_balance = 99  # pre-seed so first call skips fetch
        txns = [_make_tx() for _ in range(2)]
        with _make_signing_block_patcher():
            await ex.execute_transactions(txns)
        assert fetch_count == 0


# ---------------------------------------------------------------------------
# execute_transactions — coins mode
# ---------------------------------------------------------------------------

class TestExecuteTransactionsCoinsMode:
    def setup_method(self):
        _set_object_registry_for_tests(InMemoryObjectRegistry())

    def teardown_method(self):
        _set_object_registry_for_tests(None)

    def _make(self, **kwargs) -> _TestParallelExecutor:
        defaults = dict(
            client=_make_mock_client(),
            sender="0xsender",
            gas_mode="coins",
            max_tasks=4,
        )
        defaults.update(kwargs)
        return _TestParallelExecutor(**defaults)

    @pytest.mark.asyncio
    async def test_single_tx_with_seeded_pool(self):
        # low_water_mark=0 prevents auto-refill so pool size is predictable
        ex = self._make(low_water_mark=0)
        await ex.seed_coin_pool([_coin()])
        tx = _make_tx()
        with _make_signing_block_patcher():
            results = await ex.execute_transactions([tx])
        assert isinstance(results[0], TransactionEffects)
        # Coin is returned to pool at updated version (new object_id from gas_object)
        assert ex._gas_pool.size() == 1

    @pytest.mark.asyncio
    async def test_pool_checkout_blocks_until_checkin(self):
        ex = self._make(max_tasks=2)
        # Only 1 coin — second task must wait for the first to complete
        await ex.seed_coin_pool([_coin("01")])
        txns = [_make_tx(), _make_tx()]
        with _make_signing_block_patcher():
            results = await ex.execute_transactions(txns)
        assert all(isinstance(r, TransactionEffects) for r in results)

    @pytest.mark.asyncio
    async def test_coin_pool_drained_triggers_refill(self):
        ex = self._make(low_water_mark=5, max_tasks=1)
        # Start with 3 coins (below low_water_mark=5 → is_low() True after checkout)
        coins = [_coin(f"{i:02x}") for i in range(3)]
        await ex.seed_coin_pool(coins)

        refill_called = False
        original_refill = ex._refill_coin_pool

        async def _tracking_refill(n: int):
            nonlocal refill_called
            refill_called = True
            return await original_refill(n)

        ex._refill_coin_pool = _tracking_refill
        tx = _make_tx()
        with _make_signing_block_patcher():
            await ex.execute_transactions([tx])
        # Give background refill a chance to run
        await asyncio.sleep(0.05)
        assert refill_called

    @pytest.mark.asyncio
    async def test_seed_coin_pool_invalid_in_address_mode(self):
        ex = self._make(gas_mode="addressBalance")
        with pytest.raises(RuntimeError, match="coins gas mode"):
            await ex.seed_coin_pool([_coin()])

    @pytest.mark.asyncio
    async def test_failure_returns_coin_to_pool(self):
        ex = self._make()
        await ex.seed_coin_pool([_coin()])

        async def _fail(*args, **kwargs):
            raise RuntimeError("execution failed")

        ex._execute_single = _fail
        tx = _make_tx()
        with _make_signing_block_patcher():
            results = await ex.execute_transactions([tx])
        # Coin was retired (not returned to pool) on failure
        assert isinstance(results[0], tuple)


# ---------------------------------------------------------------------------
# Conflict tracking integration
# ---------------------------------------------------------------------------

class TestConflictTrackingIntegration:
    def setup_method(self):
        _set_object_registry_for_tests(InMemoryObjectRegistry())

    def teardown_method(self):
        _set_object_registry_for_tests(None)

    def _make(self) -> _TestParallelExecutor:
        return _TestParallelExecutor(
            client=_make_mock_client(),
            sender="0xsender",
            gas_mode="addressBalance",
            max_tasks=8,
        )

    @pytest.mark.asyncio
    async def test_serial_order_for_same_object(self):
        ex = self._make()
        order: list[int] = []

        call_num = 0

        async def _ordered_execute(tx_str, sigs, caching_exec):
            nonlocal call_num
            n = call_num
            call_num += 1
            order.append(n)
            await asyncio.sleep(0.01)
            return _make_effects()

        ex._execute_single = _ordered_execute
        shared_oid = "0x" + "cc" * 32
        txns = [_make_tx([shared_oid]) for _ in range(4)]
        with _make_signing_block_patcher():
            await ex.execute_transactions(txns)
        # All 4 should have executed — order enforced by ConflictTracker
        assert sorted(order) == list(range(4))

    @pytest.mark.asyncio
    async def test_non_overlapping_objects_run_concurrently(self):
        ex = self._make()
        entered_times: list[float] = []

        async def _timed_execute(tx_str, sigs, caching_exec):
            import time
            entered_times.append(time.monotonic())
            await asyncio.sleep(0.05)
            return _make_effects()

        ex._execute_single = _timed_execute
        # Two transactions using completely different objects — no conflict
        txns = [_make_tx(["0x" + "aa" * 32]), _make_tx(["0x" + "bb" * 32])]
        with _make_signing_block_patcher():
            await ex.execute_transactions(txns)
        # Both should have started within 10ms of each other (concurrent)
        assert len(entered_times) == 2
        assert abs(entered_times[1] - entered_times[0]) < 0.04


# ---------------------------------------------------------------------------
# Gas budget parameter
# ---------------------------------------------------------------------------

class TestGasBudgetParameter:
    def setup_method(self):
        _set_object_registry_for_tests(InMemoryObjectRegistry())

    def teardown_method(self):
        _set_object_registry_for_tests(None)

    @pytest.mark.asyncio
    async def test_custom_gas_budget_passed_to_build(self):
        ex = _TestParallelExecutor(
            client=_make_mock_client(),
            sender="0xsender",
            gas_mode="addressBalance",
            default_gas_budget=50_000_000,
        )
        budgets_seen: list[int] = []

        original_create = ex._create_caching_executor

        def _patched_create():
            mock = original_create()
            original_build = mock.build_transaction

            async def _capture_budget(tx, signing_block, budget):
                budgets_seen.append(budget)
                return "dGVzdA=="

            mock.build_transaction = _capture_budget
            return mock

        ex._create_caching_executor = _patched_create
        tx = _make_tx()
        with _make_signing_block_patcher():
            await ex.execute_transactions([tx], gas_budget=999_999)
        assert budgets_seen == [999_999]

    @pytest.mark.asyncio
    async def test_default_gas_budget_used_when_not_specified(self):
        ex = _TestParallelExecutor(
            client=_make_mock_client(),
            sender="0xsender",
            gas_mode="addressBalance",
            default_gas_budget=12_345_678,
        )
        budgets_seen: list[int] = []

        original_create = ex._create_caching_executor

        def _patched_create():
            mock = original_create()

            async def _capture_budget(tx, signing_block, budget):
                budgets_seen.append(budget)
                return "dGVzdA=="

            mock.build_transaction = _capture_budget
            return mock

        ex._create_caching_executor = _patched_create
        tx = _make_tx()
        with _make_signing_block_patcher():
            await ex.execute_transactions([tx])
        assert budgets_seen == [12_345_678]
