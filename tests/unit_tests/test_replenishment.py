#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for gas and balance replenishment callbacks."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_common.executors import ExecutorContext, ExecutionSkipped
from pysui.sui.sui_pgql.execute.serial_exec import GqlSerialTransactionExecutor


class TestCoinReplenishment:
    """Test on_coins_low callback behavior."""

    def test_on_coins_low_callback_signature(self):
        """on_coins_low callback accepts ExecutorContext."""
        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            return None

        # Can be passed to executor
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_coins_low=on_coins_low,
        )
        assert executor._on_coins_low is not None

    @pytest.mark.asyncio
    async def test_on_coins_low_returns_coins(self):
        """on_coins_low returning coins enables continuation."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        returned_coins = ["0xcoin1", "0xcoin2"]

        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            assert isinstance(ctx, ExecutorContext)
            return returned_coins

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_coins_low=on_coins_low,
            min_balance_threshold=1000,
        )

        # Create mock context and call the callback
        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_coins_low(ctx)
        assert result == returned_coins

    @pytest.mark.asyncio
    async def test_on_coins_low_returns_none_halts(self):
        """on_coins_low returning None/[] halts execution."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            return None  # Signal no coins available

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_coins_low=on_coins_low,
            min_balance_threshold=1000,
        )

        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_coins_low(ctx)
        assert result is None

    @pytest.mark.asyncio
    async def test_on_coins_low_receives_correct_context(self):
        """on_coins_low callback receives accurate context data."""
        captured_context = None

        async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
            nonlocal captured_context
            captured_context = ctx
            return None

        mock_client = MagicMock()
        mock_client.config = MagicMock()

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_coins_low=on_coins_low,
        )

        executor._tracked_balance = 5000000
        ctx = executor._build_executor_context()
        await on_coins_low(ctx)

        assert captured_context.sender == "0xsender"
        assert captured_context.gas_coins == []
        assert captured_context.tracked_balance == 5000000


class TestBalanceReplenishment:
    """Test on_balance_low callback behavior."""

    def test_on_balance_low_callback_signature(self):
        """on_balance_low callback accepts ExecutorContext."""
        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            return None

        mock_client = MagicMock()
        mock_client.config = MagicMock()

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_balance_low=on_balance_low,
        )
        assert executor._on_balance_low is not None

    @pytest.mark.asyncio
    async def test_on_balance_low_returns_address(self):
        """on_balance_low returning address enables balance verification."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        funding_wallet = "0xfunding_wallet"

        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            # Can differ from gas_owner
            return funding_wallet

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_balance_low=on_balance_low,
            min_balance_threshold=1000,
        )

        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_balance_low(ctx)
        assert result == funding_wallet

    @pytest.mark.asyncio
    async def test_on_balance_low_returns_none_halts(self):
        """on_balance_low returning None halts execution."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            return None  # Signal balance unavailable

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_balance_low=on_balance_low,
            min_balance_threshold=1000,
        )

        executor._tracked_balance = 500
        ctx = executor._build_executor_context()
        result = await on_balance_low(ctx)
        assert result is None

    @pytest.mark.asyncio
    async def test_on_balance_low_receives_correct_context(self):
        """on_balance_low callback receives accurate context data."""
        captured_context = None

        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            nonlocal captured_context
            captured_context = ctx
            return "0xfunding_address"

        mock_client = MagicMock()
        mock_client.config = MagicMock()

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            on_balance_low=on_balance_low,
        )

        executor._tracked_balance = 5000000
        ctx = executor._build_executor_context()
        await on_balance_low(ctx)

        assert captured_context.sender == "0xsender"
        assert captured_context.gas_owner == "0xsender"  # Default same as sender
        assert captured_context.tracked_balance == 5000000


class TestFundingWalletSeparation:
    """Test that funding wallet can differ from gas_owner."""

    @pytest.mark.asyncio
    async def test_funding_wallet_different_from_gas_owner(self):
        """on_balance_low can return different address than gas_owner."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        gas_owner = "0xgas_owner"
        funding_wallet = "0xfunding_wallet"

        async def on_balance_low(ctx: ExecutorContext) -> str | None:
            # Can return different address for balance check
            return funding_wallet

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender=gas_owner,
            on_balance_low=on_balance_low,
        )

        executor._tracked_balance = 1000
        ctx = executor._build_executor_context()
        balance_addr = await on_balance_low(ctx)

        assert balance_addr != ctx.gas_owner
        assert balance_addr == funding_wallet


class TestReplenishmentViaExecuteTransactions:
    """Behavioral tests: callbacks exercised through execute_transactions, not called directly."""

    def _make_executor_with_mocked_execution(self, executor):
        """Return context-manager patches that make execute_transactions run one tx successfully."""
        from pysui.sui.sui_common.types import TransactionEffects, ExecutionStatus, GasCostSummary

        mock_effects = TransactionEffects(
            transaction_digest="d",
            status=ExecutionStatus(success=True),
            gas_used=GasCostSummary(
                computation_cost=200,
                storage_cost=0,
                storage_rebate=0,
            ),
            lamport_version=1,
            changed_objects=[],
        )

        from unittest.mock import patch
        patches = [
            patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")),
            patch.object(executor._signing_block, "get_signatures", return_value=["sig"]),
            patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)),
            patch.object(executor._cache, "apply_effects", new=AsyncMock()),
            patch.object(executor._cache, "update_gas_coins", new=AsyncMock()),
            patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()),
            patch.object(executor._cache.cache, "getCustom", new=AsyncMock(return_value=[])),
        ]
        return patches, mock_effects

    @pytest.mark.asyncio
    async def test_on_coins_low_returning_none_halts_via_execute(self):
        """on_coins_low returning None causes remaining txs to be ExecutionSkipped."""
        from contextlib import ExitStack
        triggered = []

        async def on_coins_low(ctx):
            triggered.append(ctx.tracked_balance)
            return None

        executor = GqlSerialTransactionExecutor(
            client=MagicMock(),
            sender="0xsender",
            min_balance_threshold=1000,
            on_coins_low=on_coins_low,
        )
        executor._tracked_balance = 1100

        patches, _ = self._make_executor_with_mocked_execution(executor)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered) == 1
        assert triggered[0] == 900
        assert isinstance(results[1], ExecutionSkipped)
        assert "coin replenishment declined" in results[1].reason

    @pytest.mark.asyncio
    async def test_on_balance_low_returning_none_halts_via_execute(self):
        """on_balance_low returning None causes remaining txs to be ExecutionSkipped."""
        from contextlib import ExitStack
        triggered = []

        async def on_balance_low(ctx):
            triggered.append(ctx.tracked_balance)
            return None

        executor = GqlSerialTransactionExecutor(
            client=MagicMock(),
            sender="0xsender",
            min_balance_threshold=1000,
            on_balance_low=on_balance_low,
        )
        executor._tracked_balance = 1100

        patches, _ = self._make_executor_with_mocked_execution(executor)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        assert len(triggered) == 1
        assert isinstance(results[1], ExecutionSkipped)
        assert "balance replenishment declined" in results[1].reason


class TestReplenishmentThreshold:
    """Test balance threshold triggering replenishment."""

    def test_min_balance_threshold_set(self):
        """min_balance_threshold is stored when provided."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        async def on_coins_low(ctx):
            return None

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            min_balance_threshold=5_000_000,
            on_coins_low=on_coins_low,
        )
        assert executor._min_balance_threshold == 5_000_000

    def test_min_balance_threshold_none_by_default(self):
        """min_balance_threshold is None by default (no replenishment)."""
        mock_client = MagicMock()
        mock_client.config = MagicMock()

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
        )
        assert executor._min_balance_threshold is None

    @pytest.mark.asyncio
    async def test_threshold_determines_callback_trigger(self):
        """on_coins_low is triggered when tracked_balance < threshold, not when >=."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from pysui.sui.sui_common.types import TransactionEffects, ExecutionStatus, GasCostSummary

        triggered_at_balances = []

        async def on_coins_low(ctx):
            triggered_at_balances.append(ctx.tracked_balance)
            return None  # halt when triggered

        mock_client = MagicMock()
        mock_client.config = MagicMock()

        executor = GqlSerialTransactionExecutor(
            client=mock_client,
            sender="0xsender",
            min_balance_threshold=1000,
            on_coins_low=on_coins_low,
        )
        # Pre-seed so lazy init is skipped; balance starts just above threshold
        executor._tracked_balance = 1100

        # net cost = 200; 1100 - 200 = 900 < 1000 → triggers
        mock_effects = TransactionEffects(
            transaction_digest="d",
            status=ExecutionStatus(success=True),
            gas_used=GasCostSummary(
                computation_cost=200,
                storage_cost=0,
                storage_rebate=0,
            ),
            lamport_version=1,
            changed_objects=[],
        )

        with patch.object(executor._cache, "build_transaction", new=AsyncMock(return_value="tx")), \
             patch.object(executor._signing_block, "get_signatures", return_value=["sig"]), \
             patch.object(executor, "_execute_raw", new=AsyncMock(return_value=mock_effects)), \
             patch.object(executor._cache, "apply_effects", new=AsyncMock()), \
             patch.object(executor._cache, "update_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache, "invalidate_gas_coins", new=AsyncMock()), \
             patch.object(executor._cache.cache, "getCustom", new=AsyncMock(return_value=[])):
            # Two transactions: tx[0] spends 200, dropping balance to 900 < 1000
            results = await executor.execute_transactions([MagicMock(), MagicMock()])

        # Callback triggered exactly once after tx[0]
        assert len(triggered_at_balances) == 1
        assert triggered_at_balances[0] == 900
        # tx[1] was not attempted
        from pysui.sui.sui_common.executors import ExecutionSkipped
        assert isinstance(results[1], ExecutionSkipped)
