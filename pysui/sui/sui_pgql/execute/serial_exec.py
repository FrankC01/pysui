#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
import base64
from functools import partialmethod, partial
from typing import Any, Coroutine, Optional, Union

from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_txb_signing import SigningMultiSig
import pysui.sui.sui_pgql.pgql_types as ptypes
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
        signer: Union[str, SigningMultiSig],
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
        self._signer = signer
        self._default_gas_budget: int = default_gas_budget

    async def new_transaction(
        self,
    ) -> Coroutine[Any, Any, CachingTransaction]:
        """."""
        return CachingTransaction(client=self._client, sender=self._signer)

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

    async def _build_transaction(
        self, transaction: CachingTransaction
    ) -> Coroutine[Any, Any, str]:
        """Builds a TransactionData construct"""
        gcoin: bcs.ObjectReference = await self._cache.cache.getCustom("gasCoin")
        if gcoin:
            transaction.set_gas_payment(gcoin)
        transaction.set_gas_budget_if_notset(self._default_gas_budget)
        return await self._cache.build_transaction(transaction)

    async def build_transaction(self, transaction: CachingTransaction) -> str:
        """Builds the TransactionKind bytes ready for signing and execution.

        :param txn: The transaction to build
        :type txn: CachingTransaction
        :return: The build TransactionData base64 str
        :rtype: str
        """
        return await (
            await self._queue.run_task(partial(self._build_transaction, transaction))
        )

    async def execute_transaction(
        self,
        transaction: Union[str, CachingTransaction],
        **kwargs,
    ) -> ptypes.ExecutionResultGQL:
        """."""

        async def task():
            # Ensure tx is built
            txn_str = (
                transaction
                if isinstance(transaction, str)
                else await self.build_transaction(transaction)
            )
            # Sign the transaction
            sig_list: list[str] = []
            if isinstance(self._signer, str):
                sig_list.append(
                    self._client.config.active_group.keypair_for_address(
                        address=self._signer
                    ).new_sign_secure(txn_str)
                )
            else:
                if self._signer._can_sign_msg:
                    sig_list.append(
                        self._signer.multi_sig.sign(txn_str, self.signer.pub_keys)
                    )
                else:
                    raise ValueError("BaseMultiSig can not sign for execution")
            try:
                # TODO: Clean up using legacy pysui Signature type
                results: ptypes.ExecutionResultGQL = (
                    await self._cache.execute_transaction(
                        txn_str, [x.value for x in sig_list], **kwargs
                    )
                )
                await self.apply_effects(results.bcs)
                return results

            except ValueError as exc:
                await self.reset_cache()
                raise exc

        return await (await self._queue.run_task(task))

    async def apply_effects(self, effects_str: str):
        """Apply transaction effects."""
        tx_effects = bcst.TransactionEffects.deserialize(base64.b64decode(effects_str))
        return await asyncio.gather(
            self._cache_gas_coin(tx_effects),
            self._cache.apply_effects(tx_effects),
            return_exceptions=True,
        )

    async def reset_cache(self) -> None:
        """."""
        return await self._cache.reset()

    async def wait_for_last_transaction(self):
        """."""
        return await self._cache.wait_for_last_transaction()
