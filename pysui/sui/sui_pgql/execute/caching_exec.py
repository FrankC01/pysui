#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Caching transaction execution."""

import asyncio
from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction
import pysui.sui.sui_types.bcs_txne as bcs

from .cache import AsyncObjectCache


class AsyncCachingTransactionExecutor:
    """."""

    def __init__(self, client: AsyncGqlClient):
        """."""
        self._client: AsyncGqlClient = client
        self._lastdigest: str = None
        self._cache: AsyncObjectCache = AsyncObjectCache()

    async def reset(self):
        """Reset the cache."""
        return await asyncio.gather(
            self._cache.clearOwnedObjects(),
            self._cache.clearCustom(),
            self.wait_for_last_transaction(),
        )

    async def build_transaction(self, txn: AsyncSuiTransaction):
        """."""

    async def execute_transaction(self, txn: AsyncSuiTransaction):
        """."""

    async def sign_and_execute_transaction(self, txn: AsyncSuiTransaction):
        """."""

    async def apply_effects(self, effects: bcs.TransactionEffects):
        """."""

    async def wait_for_last_transaction(self):
        """."""
