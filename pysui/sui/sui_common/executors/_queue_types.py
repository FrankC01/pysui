#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared queue item types for serial and parallel executors."""

from __future__ import annotations
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Final, Optional

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
    from pysui.sui.sui_common.instrumentation import InstrumentationCollector


class _Sentinel(Enum):
    """Single-member enum used as a typed queue sentinel.

    An enum member narrows under an `is` comparison; a bare object() does not.
    That lets queue consumers type as _QueueItem once the sentinel is ruled out.
    """

    TOKEN = 0


_SENTINEL: Final = _Sentinel.TOKEN


@dataclass
class _QueueItem:
    txn: "AsyncSuiTransaction"
    future: "asyncio.Future[Any]"
    retry_count: int = 0
    collector: Optional["InstrumentationCollector"] = None
