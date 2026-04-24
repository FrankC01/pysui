#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Caching transaction execution."""

import asyncio
import logging
from typing import Any, Optional
from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction
from pysui.sui.sui_common.txb_signing import SignerBlock
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_gas_objects,
    async_get_objects_by_ids,
)
import pysui.sui.sui_bcs.bcs as bcs
import pysui.sui.sui_bcs.bcs_txne as bcst
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes
from .cache import AsyncObjectCache, ObjectCacheEntry
from .caching_txn import CachingTransaction

logger = logging.getLogger(__name__)


class AsyncCachingTransactionExecutor:
    """."""

    def __init__(self, client: AsyncGqlClient, gas_owner: Optional[str] = None):
        """Initialize caching executor.

        :param client: Asynchronous GraphQL client
        :type client: AsyncGqlClient
        :param gas_owner: Address of the gas owner (defaults to None, will be set by serial executor)
        :type gas_owner: Optional[str]
        """
        self._client: AsyncGqlClient = client
        self._gas_owner: Optional[str] = gas_owner
        self._lastdigest: str | None = None
        self.cache: AsyncObjectCache = AsyncObjectCache()

    async def reset(self):
        """Reset the cache."""
        await self.wait_for_last_transaction()
        await self.cache.clearOwnedObjects()
        await self.cache.clearCustom()

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
        logger.debug("_get_sui_objects on %s", list(objids.keys()))
        oids = list(objids.values())
        resobjs = await async_get_objects_by_ids(self._client, oids)
        return resobjs

    async def _get_sui_gas(
        self,
        gas_owner: str,
    ) -> list[ptypes.SuiCoinObjectGQL]:
        """Fetch senders Sui coins

        :raises ValueError: If fetch error
        :return: list of ptypes.SuiCoinObjectGQL
        :rtype: list[ptypes.SuiCoinObjectGQL]
        """

        all_coins = await async_get_all_owned_gas_objects(gas_owner, self._client)
        logger.debug("fetching all coins result %s", len(all_coins))
        return all_coins

    def _from_cache_to_builder(
        self, unres: bcs.UnresolvedObjectArg, cachm: ObjectCacheEntry
    ) -> tuple[bcs.BuilderArg, bcs.CallArg]:
        """Converts cache object to BuilderArg and CallArg for tx builder.

        :param unres: The unresolved object
        :type unres: bcs.UnresolvedObjectArg
        :param cachm: The cache entry for same object (by address)
        :type cachm: ObjectCacheEntry
        :return: Builder and Call arguments replacement in builder's inputs
        :rtype: tuple[bcs.BuilderArg, bcs.CallArg]
        """
        co_addy: bcs.Address = bcs.Address.from_str(unres.ObjectStr)
        barg: bcs.BuilderArg = bcs.BuilderArg("Object", co_addy)
        carg: bcs.CallArg | None = None
        cobjarg: bcs.ObjectArg | None = None
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

        # P3 fix: batch cache lookups instead of sequential awaits
        # First, collect all cache lookups
        cache_lookups = []
        for index, unobj in unresolved_objects.items():
            cache_lookups.append((index, unobj, self.cache.get_object(unobj.ObjectStr)))

        # Execute all cache lookups concurrently
        for index, unobj, lookup_task in cache_lookups:
            cachm = await lookup_task
            if cachm:
                logger.debug("Found %s in cache", unobj.ObjectStr)
                resolved_builder_inputs[index] = self._from_cache_to_builder(unobj, cachm)
            else:
                logger.debug("Did not find %s in cache. Resolving...", unobj.ObjectStr)
                fetch_ids[index] = unobj.ObjectStr

        # Fetch unresolved objects
        logger.debug("Ids for resolving %s", fetch_ids)
        resolved_objs = await self._get_sui_objects(fetch_ids)

        if resolved_objs:
            logger.debug("Resolved ids %s", resolved_objs)
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
                caller_arg: bcs.ObjectArg | None = None
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

                elif isinstance(
                    resobj.object_owner,
                    (ptypes.SuiObjectOwnedAddress, ptypes.SuiObjectOwnedParent),
                ):
                    # E7 fix: address-owned objects (immutable when not deleted)
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
                    # Cache as owned object
                    await self.cache.add_object(
                        ObjectCacheEntry(
                            resobj.object_id,
                            str(resobj.version),
                            resobj.object_digest,
                            resobj.object_owner.address
                            if isinstance(
                                resobj.object_owner, ptypes.SuiObjectOwnedAddress
                            )
                            else None,
                        )
                    )
                else:
                    # E7 fix: immutable system objects (e.g., 0x2) classified as immutable
                    # instead of raising ValueError
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
                    # Cache as immutable object (owner=None routes to SharedOrImmutableObject)
                    await self.cache.add_object(
                        ObjectCacheEntry(
                            resobj.object_id,
                            str(resobj.version),
                            resobj.object_digest,
                            None,
                        )
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
    ) -> str:
        """Builds the transaction to ready for execution

        :param txn: The transaction being built
        :type txn: CachingTransaction
        :param signer_block: Signing context
        :type signer_block: SignerBlock
        :return: Base64 transaction string
        :rtype: str
        """
        await self._resolve_object_inputs(txn)
        gas_coins = await self.cache.getCustom("gasCoins")
        # If no gas coins cached, fetch available coins
        if not gas_coins:
            logger.debug("No gasCoins in cache, fetching all coins")
            gas_owner = self._gas_owner or signer_block.payer_address
            coin_list: list[ptypes.SuiCoinObjectGQL] = await self._get_sui_gas(
                gas_owner
            )
            if not coin_list:
                raise TypeError(f"Signer {gas_owner} has no gas coins")
            # Eliminate in-use coins from transaction builder
            in_use: list[str] = list(txn.builder.objects_registry.keys())
            coin_list[:] = [
                coin for coin in coin_list if coin.coin_object_id not in in_use
            ]
            if not coin_list:
                raise ValueError(
                    f"Signer {gas_owner} has no available gas coins (all in use)"
                )
            # Convert SuiCoinObjectGQL to ObjectReference list
            gas_coins = [
                bcs.ObjectReference(
                    bcs.Address.from_str(coin.coin_object_id),
                    coin.version,
                    bcs.Digest.from_str(coin.object_digest),
                )
                for coin in coin_list
            ]
            logger.debug("Caching %s gas coins", len(gas_coins))
            await self.cache.setCustom("gasCoins", gas_coins)
        else:
            logger.debug("Have %s gasCoins in cache", len(gas_coins))

        txn.set_gas_payment(gas_coins)
        # Build TransactionData and return serialized bytes
        return await txn.build(
            gas_budget=txn._gas_budget,
            use_gas_objects=txn.get_gas_payment(),
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

    async def update_gas_coins(self, coins: list[bcs.ObjectReference]) -> None:
        """Update the cached gas coins.

        :param coins: New list of gas coin object references
        :type coins: list[bcs.ObjectReference]
        """
        await self.cache.setCustom("gasCoins", coins)

    async def invalidate_gas_coins(self) -> None:
        """Remove cached gas coins, forcing a fresh network fetch on the next build."""
        await self.cache.deleteCustom("gasCoins")

    async def get_sui_objects(self, objids: dict) -> list:
        """Fetch Sui objects by ID map.

        :param objids: Mapping of index to object ID string
        :type objids: dict
        :return: List of resolved objects
        :rtype: list
        """
        return await self._get_sui_objects(objids)

    async def wait_for_last_transaction(self, poll_interval: float = 1.0) -> Any:
        """Waits for committed results of last execution

        :param poll_interval: Polling interval in seconds, defaults to 1.0
        :type poll_interval: float
        :return: GetTx results SuiRpcResults
        :rtype: Any
        """
        if self._lastdigest:
            xres = await self._client.wait_for_transaction(
                digest=self._lastdigest, poll_interval=poll_interval
            )
            self._lastdigest = None
            return xres
