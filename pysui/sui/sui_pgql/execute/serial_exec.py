#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

from typing import Optional

from pysui import AsyncGqlClient
import pysui.sui.sui_types.bcs_txne as bcs
from .caching_exec import AsyncCachingTransactionExecutor
from .queue import SerialQueue


def gas_coin_from_effects(effects: bcs.TransactionEffects):
    """."""
    if effects.enum_name != "V2":
        raise ValueError(f"Expected V2 effects found {effects.enum_name}")


class SerialTransactionExecutor:
    """."""

    def __init__(
        self, client: AsyncGqlClient, default_gas_budget: Optional[int] = None
    ):
        """."""
        self._queue: SerialQueue = SerialQueue()
        self._cache: AsyncCachingTransactionExecutor = AsyncCachingTransactionExecutor(
            client
        )
        self._default_gas_budget: int = (
            default_gas_budget if default_gas_budget else 50_000_000
        )

    async def apply_effects(self):
        """."""

    async def _cache_gas_coin(self):
        """."""

    async def buildTransaction(self):
        """."""

    def reset_cache(self):
        """."""
        return self._cache.reset()

    def wait_for_txn(self):
        """."""

    def execute_txn(self):
        """."""
