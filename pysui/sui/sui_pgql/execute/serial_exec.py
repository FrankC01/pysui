#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
from functools import partialmethod, partial
from typing import Any, Coroutine, Optional, Union

from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_txb_signing import SigningMultiSig
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as bcst
from .caching_exec import AsyncCachingTransactionExecutor
from .queue import SerialQueue
from .caching_txn import CachingTransaction


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
        self,
        client: AsyncGqlClient,
        sender: Union[str, SigningMultiSig],
        default_gas_budget: Optional[int] = 50_000_000,
    ):
        """SerialTransactionExecutor Creates a new executor.

        :param client: Asynchronous GraphQL client
        :type client: AsyncGqlClient
        :param default_gas_budget: Set gas budget, defaults to 50_000_000
        :type default_gas_budget: Optional[int], optional
        """
        self._queue: SerialQueue = SerialQueue()
        self._cache: AsyncCachingTransactionExecutor = AsyncCachingTransactionExecutor(
            client
        )
        self._client = client
        self._sender = sender
        self._default_gas_budget: int = default_gas_budget

    async def new_transaction(
        self,
    ) -> Coroutine[Any, Any, CachingTransaction]:
        """."""
        return CachingTransaction(client=self._client, sender=self._sender)

    async def _cache_gas_coin(
        self, effects: bcst.TransactionEffects
    ) -> Coroutine[Any, Any, None]:
        """Retrive gas coin information from effects."""
        if effects.enum_name != "V2":
            return None
        gascoin = _get_gascoin_from_effects(effects)
        if gascoin:
            await self._cache.cache.setCustom("gasCoin", gascoin)
        else:
            await self._cache.cache.deleteCustom("gasCoin")

    async def apply_effects(self, effects: bcst.TransactionEffects):
        """Apply transaction effects."""
        return await asyncio.gather(
            self._cache_gas_coin(effects),
            self._cache.apply_effects(effects),
            return_exceptions=True,
        )

    async def _build_transaction(
        self, txn: CachingTransaction
    ) -> Coroutine[Any, Any, str]:
        """Builds a TransactionData construct"""
        gcoin: bcs.ObjectReference = await self._cache.cache.getCustom("gasCoin")
        if gcoin:
            txn.set_gas_payment(gcoin)
        txn.set_gas_budget_if_notset(self._default_gas_budget)
        return await self._cache.build_transaction(txn)

    async def build_transaction(self, txn: CachingTransaction) -> str:
        """Builds the TransactionKind bytes ready for signing and execution.

        :param txn: The transaction to build
        :type txn: CachingTransaction
        :return: The build TransactionData base64 str
        :rtype: str
        """
        return await (await self._queue.run_task(partial(self._build_transaction, txn)))

    def reset_cache(self) -> None:
        """."""
        return self._cache.reset()

    async def wait_for_txn(self):
        """."""

    async def execute_txn(self, transaction: Union[str, CachingTransaction]):
        """."""
