#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
from functools import partialmethod
from typing import Optional

from pysui import AsyncGqlClient
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as bcst
from .caching_exec import AsyncCachingTransactionExecutor
from .queue import SerialQueue


def _get_gascoin_from_effects(effects: bcst.TransactionEffects) -> bcs.ObjectReference:
    """."""
    if effects.enum_name != "V2":
        raise ValueError(f"Expect V2 effects, found {effects.enum_name}")
    v2effects: bcst.TransactionEffectsV2 = effects.value
    gas_object_change = v2effects.changedObjects[v2effects.gasObjectIndex.value]
    if not gas_object_change:
        raise ValueError("Gas object not found in effects")

    gas_address, effchange = gas_object_change
    if effchange.outputState.enum_name != "ObjectWrite":
        raise ValueError("Unexpected gas object state")

    edigest, _eowner = effchange.outputState.value
    return bcs.ObjectReference(gas_address, v2effects.lamportVersion, edigest)


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
        self._default_gas_budget: int = default_gas_budget or 50_000_000

    async def _cache_gas_coin(self, effects: bcst.TransactionEffects):
        """Retrive gas coin information from effects."""
        if effects.enum_name != "V2":
            return None
        gascoin = _get_gascoin_from_effects(effects)
        if gascoin:
            self._cache.cache.setCustom("gasCoin", gascoin)
        else:
            self._cache.cache.deleteCustom("gasCoin")

    async def apply_effects(self, effects: bcst.TransactionEffects):
        """Apply transaction effects."""
        return await asyncio.gather(
            self._cache_gas_coin(effects),
            self._cache.apply_effects(effects),
            return_exceptions=True,
        )

    async def _build_transaction(self, txn):
        gcoin = await self._cache.cache.getCustom("gasCoin")

    async def buildTransaction(self, txn):
        """."""
        return self._queue.run_task(partialmethod(self._build_transaction, txn))

    def reset_cache(self):
        """."""
        return self._cache.reset()

    def wait_for_txn(self):
        """."""

    def execute_txn(self):
        """."""
