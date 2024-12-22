#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
import base64
import logging
import time
from typing import Any, Coroutine, Optional, Union

ser_txn_exc_logger = logging.getLogger("serial_exec")

from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_txb_signing import SigningMultiSig
import pysui.sui.sui_pgql.pgql_types as ptypes
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as bcst
from .caching_exec import AsyncCachingTransactionExecutor

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
    ser_txn_exc_logger.debug("Have gas coin from effects")
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
        ser_txn_exc_logger.debug("Generate new transaction")
        return CachingTransaction(client=self._client, sender=self._signer)

    async def _cache_gas_coin(
        self, effects: bcst.TransactionEffects
    ) -> Coroutine[Any, Any, None]:
        """Retrive gas coin information from effects."""
        ser_txn_exc_logger.debug("Gas Coin Caching from effects")
        if effects.enum_name != "V2":
            ser_txn_exc_logger.debug("Effects != V2")
            return None
        gascoin = _get_gascoin_from_effects(effects)
        if gascoin:
            ser_txn_exc_logger.debug(
                f"Have gas coin with version {gascoin.SequenceNumber}"
            )
            await self._cache.cache.setCustom("gasCoin", gascoin)
        else:
            ser_txn_exc_logger.debug("DON'T Have gas coin")
            await self._cache.cache.deleteCustom("gasCoin")

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

    async def _build_transaction(self, transaction: CachingTransaction) -> str:
        """Builds TransactionData for execution."""
        ser_txn_exc_logger.debug("in _build_transaction")
        gcoin: bcs.ObjectReference = await self._cache.cache.getCustom("gasCoin")
        if gcoin:
            ser_txn_exc_logger.debug(
                f"Have gas coin {gcoin.SequenceNumber}, setting gas payment in txn"
            )
            transaction.set_gas_payment(gcoin)
        else:
            ser_txn_exc_logger.debug("No gas coin")
        transaction.set_gas_budget_if_notset(self._default_gas_budget)
        ser_txn_exc_logger.debug("Calling cache build transaction")
        return await self._cache.build_transaction(transaction)

    def _sign_transaction(self, tx_str: str) -> list[str]:
        """Sign the transaction.

        :param tx_str: base64 encoded TransactionData str
        :type tx_str: str
        :raises ValueError: if using multi-sign erroneously
        :return: list of base64 encoded signatures
        :rtype: list[str]
        """
        sig_list: list[str] = []
        if isinstance(self._signer, str):
            sig_list.append(
                self._client.config.active_group.keypair_for_address(
                    address=self._signer
                ).new_sign_secure(tx_str)
            )
        else:
            if self._signer._can_sign_msg:
                sig_list.append(
                    self._signer.multi_sig.sign(tx_str, self.signer.pub_keys)
                )
            else:
                raise ValueError("BaseMultiSig can not sign for execution")
        return [x.value for x in sig_list]

    async def execute_transactions(
        self,
        transactions: list[CachingTransaction],
        **kwargs,
    ) -> list[ptypes.ExecutionResultGQL]:
        """Serially execute one or more transactions

        :param transactions: The transactions to execute
        :type transactions: list[CachingTransaction]
        :raises ValueError: _description_
        :raises exc: _description_
        :return: The transaction execution results
        :rtype: list[ptypes.ExecutionResultGQL]
        """
        exe_res: list[ptypes.ExecutionResultGQL] = []
        for tx in transactions:
            start_time = time.time()
            ser_txn_exc_logger.debug("Building transaction")
            tx_str = await self._build_transaction(tx)
            ser_txn_exc_logger.debug(f"Signing {tx_str}")

            try:
                ser_txn_exc_logger.debug("Cache transaction execution")
                # Sign the transaction
                sig_list = self._sign_transaction(tx_str)
                results: ptypes.ExecutionResultGQL = (
                    await self._cache.execute_transaction(tx_str, sig_list, **kwargs)
                )
                await self.apply_effects(results.bcs)
                end_time = time.time()
                ser_txn_exc_logger.info(f"tx execution {end_time-start_time}")
                exe_res.append(results)

            except ValueError as exc:
                ser_txn_exc_logger.debug("Error callingi cache execute")
                await self.reset_cache()
                raise exc

        return exe_res
