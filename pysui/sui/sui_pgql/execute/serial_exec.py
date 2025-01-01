#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
import base64
import logging
import time
from enum import IntEnum
from typing import Any, Coroutine, Optional, Union

ser_txn_exc_logger = logging.getLogger("serial_exec")

from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_txb_signing import SignerBlock, SigningMultiSig
import pysui.sui.sui_pgql.pgql_types as ptypes
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as bcst
from .caching_exec import AsyncCachingTransactionExecutor

from .caching_txn import CachingTransaction


class ExecutorError(IntEnum):
    BUILDING_ERROR = 1
    SIGNING_ERROR = 2
    EXECUTING_ERROR = 3


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
        *,
        client: AsyncGqlClient,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
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
        self._signing_block = SignerBlock(sender=sender, sponsor=sponsor)
        self._default_gas_budget: int = default_gas_budget

    async def new_transaction(
        self,
    ) -> Coroutine[Any, Any, CachingTransaction]:
        """Create a new caching transaction for transaction block building."""
        ser_txn_exc_logger.debug("Generate new transaction")
        return CachingTransaction(client=self._client)

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
        """Reset (empty) the internal cache."""
        return await self._cache.reset()

    async def wait_for_last_transaction(self):
        """Waits for committed results of last execution."""
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
        return await self._cache.build_transaction(transaction, self._signing_block)

    def _sign_transaction(self, tx_str: str) -> list[str]:
        """Sign the transaction.

        :param tx_str: base64 encoded TransactionData str
        :type tx_str: str
        :raises ValueError: if using multi-sign erroneously
        :return: list of base64 encoded signatures
        :rtype: list[str]
        """
        return self._signing_block.get_signatures(
            config=self._client.config, tx_bytes=tx_str
        )

    async def execute_transactions(
        self,
        transactions: list[CachingTransaction],
    ) -> list[Union[ptypes.ExecutionResultGQL, Exception]]:
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

            # Buillding is non-recoverable
            tx_str = await asyncio.gather(
                self._build_transaction(tx), return_exceptions=True
            )
            if not isinstance(tx_str[0], str):
                ser_txn_exc_logger.critical(f"tx build {tx_str[0].args}")
                exe_res.append((ExecutorError.BUILDING_ERROR, tx_str[0]))
                continue
            tx_str: str = tx_str[0]
            ser_txn_exc_logger.debug(f"Signing {tx_str}")
            try:
                ser_txn_exc_logger.debug("Cache transaction execution")
                # Sign the transaction
                sig_list = self._sign_transaction(tx_str)
                results = await asyncio.gather(
                    self._cache.execute_transaction(tx_str, sig_list)
                )
                if not isinstance(results[0], ptypes.ExecutionResultGQL):
                    ser_txn_exc_logger.critical(f"tx execution {results[0].args}")
                    exe_res.append((ExecutorError.EXECUTING_ERROR, results[0]))
                    continue
                results: ptypes.ExecutionResultGQL = results[0]
                await self.apply_effects(results.bcs)
                end_time = time.time()
                ser_txn_exc_logger.info(f"tx execution time {end_time-start_time}")
                exe_res.append(results)
            except ValueError as ve:
                ser_txn_exc_logger.critical(f"tx signing non-recoverable {ve.args}")
                exe_res.append((ExecutorError.SIGNING_ERROR, ve))

        return exe_res
