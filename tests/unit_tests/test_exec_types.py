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
