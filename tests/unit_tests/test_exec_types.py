#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for executor types and context objects."""

import pytest
from pysui.sui.sui_common.executors import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
)
import pysui.sui.sui_bcs.bcs as bcs


class TestExecutorContext:
    """Test ExecutorContext dataclass."""

    def test_executor_context_creation(self):
        """ExecutorContext is created with all required fields."""
        coins = [
            bcs.ObjectReference(
                bcs.Address.from_str("0x1"),
                1,
                bcs.Digest.from_bytes(b"\x00" * 32),
            )
        ]
        ctx = ExecutorContext(
            sender="0xsender",
            gas_owner="0xgas_owner",
            gas_coins=coins,
            tracked_balance=1000000,
        )
        assert ctx.sender == "0xsender"
        assert ctx.gas_owner == "0xgas_owner"
        assert ctx.gas_coins == coins
        assert ctx.tracked_balance == 1000000

    def test_executor_context_empty_coins(self):
        """ExecutorContext can be created with empty coins list."""
        ctx = ExecutorContext(
            sender="0xsender",
            gas_owner="0xgas_owner",
            gas_coins=[],
            tracked_balance=0,
        )
        assert ctx.gas_coins == []
        assert ctx.tracked_balance == 0


class TestExecutionSkipped:
    """Test ExecutionSkipped dataclass."""

    def test_execution_skipped_creation(self):
        """ExecutionSkipped is created with transaction_index and reason."""
        skipped = ExecutionSkipped(transaction_index=2, reason="prior transaction failed")
        assert skipped.transaction_index == 2
        assert skipped.reason == "prior transaction failed"

    def test_execution_skipped_various_reasons(self):
        """ExecutionSkipped works with different reason strings."""
        reasons = [
            "prior transaction failed",
            "coin replenishment failed",
            "coin replenishment declined",
            "balance below threshold",
            "balance verification failed",
            "balance replenishment declined",
            "replenishment callback raised",
            "balance initialization failed",
        ]
        for i, reason in enumerate(reasons):
            skipped = ExecutionSkipped(transaction_index=i, reason=reason)
            assert skipped.reason == reason


class TestExecutorError:
    """Test ExecutorError enum."""

    def test_executor_error_values(self):
        """ExecutorError has expected enum values."""
        assert ExecutorError.BUILDING_ERROR.value == 1
        assert ExecutorError.EXECUTING_ERROR.value == 2
        assert ExecutorError.REPLENISHMENT_ERROR.value == 3

    def test_executor_error_name(self):
        """ExecutorError enum names are correct."""
        assert ExecutorError.BUILDING_ERROR.name == "BUILDING_ERROR"
        assert ExecutorError.EXECUTING_ERROR.name == "EXECUTING_ERROR"
        assert ExecutorError.REPLENISHMENT_ERROR.name == "REPLENISHMENT_ERROR"

    def test_executor_error_in_tuple(self):
        """ExecutorError can be part of error tuples."""
        error_tuple = (ExecutorError.BUILDING_ERROR, ValueError("test error"))
        assert isinstance(error_tuple[0], ExecutorError)
        assert isinstance(error_tuple[1], ValueError)

    def test_replenishment_error_in_tuple(self):
        """REPLENISHMENT_ERROR can be part of error tuples."""
        error_tuple = (ExecutorError.REPLENISHMENT_ERROR, RuntimeError("callback failed"))
        assert error_tuple[0] == ExecutorError.REPLENISHMENT_ERROR
        assert isinstance(error_tuple[1], RuntimeError)


class TestSerialGasMode:
    """Test SerialGasMode enum."""

    def test_coins_value(self):
        from pysui.sui.sui_common.executors.exec_types import SerialGasMode
        assert SerialGasMode.COINS.value == "coins"

    def test_address_balance_value(self):
        from pysui.sui.sui_common.executors.exec_types import SerialGasMode
        assert SerialGasMode.ADDRESS_BALANCE.value == "address_balance"

    def test_enum_has_two_members(self):
        from pysui.sui.sui_common.executors.exec_types import SerialGasMode
        assert len(SerialGasMode) == 2

    def test_enum_name_coins(self):
        from pysui.sui.sui_common.executors.exec_types import SerialGasMode
        assert SerialGasMode.COINS.name == "COINS"

    def test_enum_name_address_balance(self):
        from pysui.sui.sui_common.executors.exec_types import SerialGasMode
        assert SerialGasMode.ADDRESS_BALANCE.name == "ADDRESS_BALANCE"


class TestGasStatus:
    """Test GasStatus enum."""

    def test_ok_value(self):
        from pysui.sui.sui_common.executors.exec_types import GasStatus
        assert GasStatus.OK.value == "ok"

    def test_need_funds_value(self):
        from pysui.sui.sui_common.executors.exec_types import GasStatus
        assert GasStatus.NEED_FUNDS.value == "need_funds"

    def test_need_funds_and_retry_value(self):
        from pysui.sui.sui_common.executors.exec_types import GasStatus
        assert GasStatus.NEED_FUNDS_AND_RETRY.value == "need_funds_and_retry"

    def test_txn_error_value(self):
        from pysui.sui.sui_common.executors.exec_types import GasStatus
        assert GasStatus.TXN_ERROR.value == "txn_error"

    def test_enum_has_four_members(self):
        from pysui.sui.sui_common.executors.exec_types import GasStatus
        assert len(GasStatus) == 4


class TestSerialExecutorContext:
    """Test SerialExecutorContext dataclass."""

    def test_creation_with_all_fields(self):
        from pysui.sui.sui_common.executors.exec_types import SerialExecutorContext
        ctx = SerialExecutorContext(
            sender="0xsender",
            tracked_balance=5_000_000,
            min_threshold_balance=10_000_000,
            client=None,
        )
        assert ctx.sender == "0xsender"
        assert ctx.tracked_balance == 5_000_000
        assert ctx.min_threshold_balance == 10_000_000
        assert ctx.client is None

    def test_client_field_accepts_any(self):
        from pysui.sui.sui_common.executors.exec_types import SerialExecutorContext
        mock_client = object()
        ctx = SerialExecutorContext(
            sender="0xaddr",
            tracked_balance=0,
            min_threshold_balance=1,
            client=mock_client,
        )
        assert ctx.client is mock_client

    def test_zero_balances(self):
        from pysui.sui.sui_common.executors.exec_types import SerialExecutorContext
        ctx = SerialExecutorContext(
            sender="0x0",
            tracked_balance=0,
            min_threshold_balance=0,
            client=None,
        )
        assert ctx.tracked_balance == 0
        assert ctx.min_threshold_balance == 0


class TestExecutorOptions:
    """Test ExecutorOptions dataclass."""

    def test_required_fields(self):
        from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, SerialGasMode
        opts = ExecutorOptions(
            sender="0xsender",
            gas_mode=SerialGasMode.COINS,
            initial_coins=[],
            min_threshold_balance=10_000_000,
        )
        assert opts.sender == "0xsender"
        assert opts.gas_mode == SerialGasMode.COINS
        assert opts.initial_coins == []
        assert opts.min_threshold_balance == 10_000_000

    def test_defaults(self):
        from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, SerialGasMode
        opts = ExecutorOptions(
            sender="0xsender",
            gas_mode=SerialGasMode.COINS,
            initial_coins=[],
            min_threshold_balance=1,
        )
        assert opts.on_balance_low is None
        assert opts.max_retries == 1
        assert opts.on_failure == "continue"

    def test_on_balance_low_callback(self):
        from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, SerialGasMode
        async def callback(ctx):
            return None
        opts = ExecutorOptions(
            sender="0xsender",
            gas_mode=SerialGasMode.ADDRESS_BALANCE,
            initial_coins=[],
            min_threshold_balance=10_000_000,
            on_balance_low=callback,
        )
        assert opts.on_balance_low is callback

    def test_on_failure_exit(self):
        from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, SerialGasMode
        opts = ExecutorOptions(
            sender="0xsender",
            gas_mode=SerialGasMode.COINS,
            initial_coins=[],
            min_threshold_balance=1,
            on_failure="exit",
        )
        assert opts.on_failure == "exit"

    def test_address_balance_mode(self):
        from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, SerialGasMode
        opts = ExecutorOptions(
            sender="0xsender",
            gas_mode=SerialGasMode.ADDRESS_BALANCE,
            initial_coins=[],
            min_threshold_balance=50_000_000,
        )
        assert opts.gas_mode == SerialGasMode.ADDRESS_BALANCE
        assert opts.min_threshold_balance == 50_000_000

    def test_initial_coins_list(self):
        from pysui.sui.sui_common.executors.exec_types import ExecutorOptions, SerialGasMode
        coins = ["0xcoin1", "0xcoin2"]
        opts = ExecutorOptions(
            sender="0xsender",
            gas_mode=SerialGasMode.COINS,
            initial_coins=coins,
            min_threshold_balance=1,
        )
        assert opts.initial_coins == coins
