#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared queue item types for serial and parallel executors."""

from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

_SENTINEL: Final = object()


@dataclass
class _QueueItem:
    txn: "AsyncSuiTransaction"
    future: "asyncio.Future[Any]"
    retry_count: int = 0
