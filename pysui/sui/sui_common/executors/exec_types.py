#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared executor types and context."""

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pysui.sui.sui_bcs.bcs as bcs


@dataclass
class ExecutorContext:
    """Context passed to gas replenishment callbacks."""

    sender: str
    gas_owner: str
    gas_coins: "list[bcs.ObjectReference]"
    tracked_balance: int


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
