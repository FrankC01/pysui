#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Caching transaction execution."""

import asyncio
import logging
import base64
from typing import Any, Coroutine
from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction
from pysui.sui.sui_pgql.pgql_txb_signing import SignerBlock
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as bcst
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes
from .cache import AsyncObjectCache, ObjectCacheEntry
from .caching_txn import CachingTransaction

logger = logging.getLogger("serial_exec")


class AsyncCachingTransactionExecutor:
    """."""

    def __init__(self, client: AsyncGqlClient):
        """Initialize caching executor."""
        self._client: AsyncGqlClient = client
        self._lastdigest: str = None
        self.cache: AsyncObjectCache = AsyncObjectCache()

    async def reset(self):
        """Reset the cache."""
        return await asyncio.gather(
            self.cache.clearOwnedObjects(),
            self.cache.clearCustom(),
            self.wait_for_last_transaction(),
        )

    async def _get_sui_objects(self, objids: dict) -> list:
        """Fetch unresolved Sui objects

        :param objids: Input index and object ids
        :type objids: dict
        :raises ValueError: If fetch error
        :return: list of ptypes.ObjectReadGQL
        :rtype: list
        """
        resobjs = []
        if objids == {}:
            logger.debug("_get_sui_objects has no entries")
            return resobjs
        logger.debug(f"_get_sui_objects on {objids.keys()}")
        oids = list(objids.values())
        result = await self._client.execute_query_node(
            with_node=qn.GetMultipleObjects(object_ids=oids)
        )
        while result.is_ok():
            resobjs.extend(result.result_data.data)
            if result.result_data.next_cursor.hasNextPage:
                result = await self.client.execute_query_node(
                    with_node=qn.GetMultipleObjects(
                        object_ids=oids,
                        next_page=result.result_data.next_cursor,
                    )
                )
            else:
                break
        if result.is_err():
            raise ValueError(result.result_string)

        return resobjs

    async def _get_sui_gas(
        self,
        gas_owner: str,
    ) -> Coroutine[Any, Any, list[ptypes.SuiCoinObjectGQL]]:
        """Fetch senders Sui coins

        :raises ValueError: If fetch error
        :return: list of ptypes.ObjectReadGQL
        :rtype: Coroutine[Any, Any, bcs.ObjectReference]
        """

        all_coins: list[ptypes.SuiCoinObjectGQL] = []

        result = await self._client.execute_query_node(
            with_node=qn.GetCoins(owner=gas_owner)
        )
        while result.is_ok():
            all_coins.extend(result.result_data.data)
            if result.result_data.next_cursor.hasNextPage:
                result = await self._client.execute_query_node(
                    with_node=qn.GetCoins(
                        owner=gas_owner,
                        next_page=result.result_data.next_cursor,
                    )
                )
            else:
                break
        logger.debug(f"fetching all coins result {len(all_coins)}")
        return all_coins

    async def _smash_gas(
        self, txn: CachingTransaction, signer_block: SignerBlock
    ) -> Coroutine[Any, Any, ptypes.SuiCoinObjectGQL]:
        """Smashes all available sui for signer."""
        # Get object references
        in_use: list[str] = list(txn.builder.objects_registry.keys())
        # Get all gas
        coin_list: list[ptypes.SuiCoinObjectGQL] = await self._get_sui_gas(
            signer_block.payer_address
        )
        if not coin_list:
            raise TypeError(f"Signer {signer_block.payer_address} has no gas coins")
        # Eliminate in use
        coin_list[:] = [coin for coin in coin_list if coin.coin_object_id not in in_use]

        # If noting available, throw exception
        if not coin_list:
            logger.debug("_smash_gas has no available coins")
            raise ValueError(
                f"Signer {signer_block.payer_address} has no available gas coins"
            )
        # If one return it
        if len(coin_list) == 1:
            ret_coin = coin_list[0]
            logger.debug(f"_smash_gas has 1 coin, returning version {ret_coin.version}")
            return ret_coin
        # Otherwise smash lowest to highesst and return it
        coin_list.sort(key=lambda x: int(x.balance), reverse=True)
        tx = AsyncSuiTransaction(client=self._client)

        use_as_gas = coin_list.pop(0)
        logger.debug(f"_smash_gas merging coins to version {use_as_gas.version}")
        await tx.merge_coins(merge_to=tx.gas, merge_from=coin_list)
        res = await self._client.execute_query_node(
            with_node=qn.ExecuteTransaction(
                **await tx.build_and_sign(use_gas_objects=[use_as_gas])
            )
        )
        if res.is_err():
            raise ValueError(f"Failed smashing coins with {res.result_string}")

        # Deserialize tx effects and get updated gas coin information
        tx_effects = bcst.TransactionEffects.deserialize(
            base64.b64decode(res.result_data.bcs)
        ).value
        _, effchange = tx_effects.changedObjects[tx_effects.gasObjectIndex.value]
        edigest, _ = effchange.outputState.value

        use_as_gas.version = tx_effects.lamportVersion
        use_as_gas.object_digest = edigest.to_digest_str()
        logger.debug(f"Merge gas returning version {use_as_gas.version}")
        return use_as_gas

    def _from_cache_to_builder(
        self, unres: bcs.UnresolvedObjectArg, cachm: ObjectCacheEntry
    ) -> tuple[bcs.BuilderArg, bcs.CallArg]:
        """Converts cach object to BuilderArg and CallArg for tx builder.

        :param unres: The unresolved object
        :type unres: bcs.UnresolvedObjectArg
        :param cachm: The cache entry for same object (by address)
        :type cachm: ObjectCacheEntry
        :return: Builder and Call arguments replacement in builder's inputs
        :rtype: tuple[bcs.BuilderArg, bcs.CallArg]
        """
        co_addy: bcs.Address = bcs.Address.from_str(unres.ObjectStr)
        barg: bcs.BuilderArg = bcs.BuilderArg("Object", co_addy)
        carg: bcs.CallArg = None
        cobjarg: bcs.ObjectArg = None
        # Shared object arg
        if cachm.initialSharedVersion is not None:
            carg = bcs.CallArg(
                "Object",
                bcs.ObjectArg(
                    "SharedObject",
                    bcs.SharedObjectReference(
                        co_addy,
                        int(cachm.initialSharedVersion),
                        unres.RefType == 2,
                    ),
                ),
            )

        else:
            carg = bcs.CallArg(
                "Object",
                bcs.ObjectArg(
                    "Recieving" if unres.IsReceiving else "ImmOrOwnedObject",
                    bcs.ObjectReference(
                        co_addy,
                        int(cachm.version),
                        bcs.Digest.from_str(cachm.digest),
                    ),
                ),
            )
        return (barg, carg)

    async def _resolve_object_inputs(self, txn: CachingTransaction):
        """Resolves unresolved object references in builder

        :param txn: The transaction
        :type txn: CachingTransaction
        """
        logger.debug("_resolving_object_inputs")
        # Get builder unresolved as index, Unresolved map
        fetch_ids: dict[int, str] = {}
        resolved_builder_inputs: dict[int, tuple[bcs.BuilderArg, bcs.CallArg]] = {}
        unresolved_objects: dict[int, bcs.UnresolvedObjectArg] = (
            txn.builder.get_unresolved_inputs()
        )

        # Bang up against cache by id
        for index, unobj in unresolved_objects.items():
            if cachm := await self.cache.get_object(unobj.ObjectStr):
                logger.debug(f"Found {unobj.ObjectStr} in cache")
                resolved_builder_inputs[index] = self._from_cache_to_builder(
                    unobj, cachm
                )
            else:
                logger.debug(f"Did not find {unobj.ObjectStr} in cache. Resolving...")
                fetch_ids[index] = unobj.ObjectStr

        # Fetch unresolved objects
        logger.debug(f"Ids for resolving {fetch_ids}")
        resolved_objs = await self._get_sui_objects(fetch_ids)

        if resolved_objs:
            logger.debug(f"Resolved ids {resolved_objs}")
            inv_unrids = {
                value.ObjectStr: key for key, value in unresolved_objects.items()
            }
            # Validate and cache results (may contain deletes)
            for resobj in resolved_objs:
                if isinstance(resobj, ptypes.ObjectReadDeletedGQL):
                    raise ValueError(f"Object {resobj.object_id} deleted")
                # Get the unresolved details
                unentry: bcs.UnresolvedObjectArg = unresolved_objects[
                    inv_unrids[resobj.object_id]
                ]

                # Build relevant cache type and BuilderArg
                res_obj_addy: bcs.Address = bcs.Address.from_str(resobj.object_id)
                builder_arg = bcs.BuilderArg("Object", res_obj_addy)
                caller_arg: bcs.ObjectArg = None
                caller_shared: bool = False
                # Build CallArg
                if isinstance(resobj.object_owner, ptypes.SuiObjectOwnedShared):
                    # centry.initialSharedVersion = str(resobj.object_owner.initial_version)
                    caller_shared = True
                    caller_arg = bcs.CallArg(
                        "Object",
                        bcs.ObjectArg(
                            "SharedObject",
                            bcs.SharedObjectReference(
                                res_obj_addy,
                                resobj.object_owner.initial_version,
                                unentry.RefType == 2,
                            ),
                        ),
                    )
                    # Read only shared objects are not reported in effects with
                    # initial version, we wedge it into the cache here
                    await self.cache.add_object(
                        ObjectCacheEntry(
                            resobj.object_id,
                            str(resobj.version),
                            resobj.object_digest,
                            None,
                            str(resobj.object_owner.initial_version),
                        )
                    )

                elif not isinstance(
                    resobj.object_owner,
                    (ptypes.SuiObjectOwnedAddress, ptypes.SuiObjectOwnedParent),
                ):
                    raise ValueError(f"{resobj.object_id} is immutable")
                # await self.cache.add_object(centry)
                if not caller_shared:
                    oref = bcs.ObjectReference(
                        res_obj_addy,
                        resobj.version,
                        bcs.Digest.from_str(resobj.object_digest),
                    )
                    caller_arg = bcs.CallArg(
                        "Object",
                        bcs.ObjectArg(
                            "Recieving" if unentry.IsReceiving else "ImmOrOwnedObject",
                            oref,
                        ),
                    )
                # Setup resolving
                resolved_builder_inputs[inv_unrids[resobj.object_id]] = (
                    builder_arg,
                    caller_arg,
                )
        else:
            logger.debug("No ids for resolving.")

        # Hydrate the transaction with resolved objects
        txn.builder.resolved_object_inputs(resolved_builder_inputs)

    async def build_transaction(
        self, txn: CachingTransaction, signer_block: SignerBlock
    ) -> Coroutine[Any, Any, str]:
        """Builds the transaction to ready for execution

        :param txn: The transaction being built
        :type txn: CachingTransaction
        :return: Base64 transaction string
        :rtype: Coroutine[Any, Any, str]
        """
        await self._resolve_object_inputs(txn)
        gas_pay = await self.cache.getCustom("gasCoin")
        # Smash gas coins if no payment set
        if not gas_pay:
            logger.debug("No gasCoin in cache")
            gas_object: ptypes.SuiCoinObjectGQL = await self._smash_gas(
                txn, signer_block
            )
            gas_pay = bcs.ObjectReference(
                bcs.Address.from_str(gas_object.coin_object_id),
                gas_object.version,
                bcs.Digest.from_str(gas_object.object_digest),
            )
            logger.debug(f"Setting gas coin to oid {gas_object.coin_object_id}")
            await self.cache.setCustom("gasCoin", gas_pay)
            txn.set_gas_payment(gas_pay)
        else:
            logger.debug("Have gasCoin in cache")
            txn.set_gas_payment(gas_pay)
        # Build TransactionData and return serialized bytes
        return await txn.build(
            gas_budget=txn._gas_budget,
            use_gas_object=txn.get_gas_payment(),
            signer_block=signer_block,
        )

    async def execute_transaction(
        self, txn_str: str, txn_sigs: list[str]
    ) -> ptypes.ExecutionResultGQL:
        """Executes the transaction.

        :param txn_str: Base64 TransactionData string
        :type txn_str: str
        :param txn_sigs: List of Base64 signatures
        :type txn_sigs: list[str]
        :raises ValueError: HTTP failure
        :return: The results of the execution
        :rtype: ptypes.ExecutionResultGQL
        """
        result = await self._client.execute_query_node(
            with_node=qn.ExecuteTransaction(
                tx_bytestr=txn_str,
                sig_array=txn_sigs,
            )
        )

        if result.is_ok():
            return result.result_data
        else:
            raise ValueError(f"{result.result_string}")

    async def apply_effects(self, effects: bcst.TransactionEffects):
        """Apply the transaction execution effects to cache.

        :param effects: The execution transaction effects
        :type effects: bcst.TransactionEffects
        """
        self._lastdigest = effects.value.transactionDigest.to_digest_str()
        await self.cache.applyEffects(effects)

    async def wait_for_last_transaction(self) -> Any:
        """Waits for committed results of last execution

        :return: GetTx results SuiRpcResults
        :rtype: Any
        """
        if self._lastdigest:
            xres = await self._client.wait_for_transaction(
                digest=self._lastdigest, poll_interval=1
            )
            self._lastdigest = None
            return xres
