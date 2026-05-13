#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared executor types and context."""

from dataclasses import dataclass
from enum import IntEnum
from pysui.sui.sui_common.shared_types import ObjectSummary


@dataclass
class ExecutorContext:
    """Context passed to gas replenishment callbacks."""

    sender: str
    gas_owner: str
    gas_coins: list[str]
    tracked_balance: int


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
