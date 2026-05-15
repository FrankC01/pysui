#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared executor types and context."""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Awaitable, Callable, Literal, Optional, Union
from pysui.sui.sui_common.shared_types import ObjectSummary
from pysui.sui.sui_common.txb_signing import SigningMultiSig


class SerialGasMode(Enum):
    """Gas funding mode for SerialExecutor."""

    COINS = "coins"
    ADDRESS_BALANCE = "address_balance"


class GasStatus(Enum):
    """Execution outcome from SerialQueueProcessor.process()."""

    OK = "ok"
    NEED_FUNDS = "need_funds"
    NEED_FUNDS_AND_RETRY = "need_funds_and_retry"
    TXN_ERROR = "txn_error"


@dataclass
class ExecutorContext:
    """Context passed to gas replenishment callbacks (Parallel Executor)."""

    sender: str
    gas_owner: str
    gas_coins: list[str]
    tracked_balance: int


@dataclass
class SerialExecutorContext:
    """Context passed to on_balance_low callback for SerialExecutor."""

    sender: str
    tracked_balance: int
    min_threshold_balance: int
    client: Any


@dataclass
class ExecutorOptions:
    """Full parameterization for SerialExecutor construction."""

    sender: Union[str, SigningMultiSig]
    gas_mode: SerialGasMode
    initial_coins: list
    min_threshold_balance: int
    on_balance_low: Optional[Callable[[SerialExecutorContext], Awaitable[list | None]]] = None
    max_retries: int = 1
    on_failure: Literal["continue", "exit"] = "continue"


@dataclass
class GasSummary(ObjectSummary):
    """Gas coin with balance for SE internal tracking."""

    balance: int = 0


@dataclass
class ExecutionSkipped:
    """Represents a skipped transaction in a batch."""

    transaction_index: int
    reason: str


class ExecutorError(IntEnum):
    """Error codes for executor failures."""

    BUILDING_ERROR = 1
    EXECUTING_ERROR = 2
    REPLENISHMENT_ERROR = 3
