#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Caching transaction execution."""

import asyncio
from typing import Any, Coroutine
from pysui import AsyncGqlClient
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as bcst
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes
from .cache import AsyncObjectCache, ObjectCacheEntry
from .caching_txn import CachingTransaction


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
        return all_coins

    async def _smash_gas(
        self, txn: CachingTransaction
    ) -> Coroutine[Any, Any, ptypes.SuiCoinObjectGQL]:
        """Smashes all available sui for signer."""
        # Get object references
        in_use: list[str] = list(txn.builder.objects_registry.keys())
        # Get all gas
        coin_list: list[ptypes.SuiCoinObjectGQL] = await self._get_sui_gas(
            txn.signer_block.payer_address
        )
        if not coin_list:
            raise TypeError(f"Signer {txn.signer_block.payer_address} has no gas coins")
        # Eliminate in use
        coin_list[:] = [coin for coin in coin_list if coin.coin_object_id not in in_use]
        # available_list: list[ptypes.SuiCoinObjectGQL] = []
        # for coin in coin_list:
        #     if coin.coin_object_id not in in_use:
        #         available_list.append(coin)

        # If noting available, throw exception
        if not coin_list:
            raise TypeError(
                f"Signer {txn.signer_block.payer_address} has no available gas coins"
            )
        # If one return it
        if len(coin_list) == 1:
            return coin_list[0]
        # Otherwise smash and return it
        tx = AsyncSuiTransaction(client=self._client)
        use_as_gas = coin_list.pop(0)
        await tx.merge_coins(merge_to=tx.gas, merge_from=coin_list)
        res = await self._client.execute_query_node(
            with_node=qn.ExecuteTransaction(
                **await tx.build_and_sign(use_gas_objects=[use_as_gas])
            )
        )
        if res.is_err():
            raise ValueError(f"Failed smashing coins with {res.result_string}")
        return use_as_gas

    async def _resolve_object_inputs(self, txn: CachingTransaction):
        """Resolves unresolved object references in builder

        :param txn: The transaction
        :type txn: CachingTransaction
        """
        # print("Resolving objects")
        # Get builder unresolved as index, Unresolved map
        unresolved_objects: dict[int, bcs.UnresolvedObjectArg] = (
            txn.builder.get_unresolved_inputs()
        )

        # Bang up against cache by id
        fetch_ids: dict[int, str] = {}
        by_id: dict[str, ObjectCacheEntry] = {}
        for index, unobj in unresolved_objects.items():
            if cachm := await self.cache.get_object(unobj.ObjectStr):
                by_id[cachm.objectId] = cachm
            else:
                fetch_ids[index] = unobj.ObjectStr
        # Fetch unresolved objects
        resolved_objs = await self._get_sui_objects(fetch_ids)
        inv_unrids = {value.ObjectStr: key for key, value in unresolved_objects.items()}
        resolved_builder_inputs: dict[int, tuple[bcs.BuilderArg, bcs.CallArg]] = {}
        # Validate and cache results (may contain deletes)
        for resobj in resolved_objs:
            if isinstance(resobj, ptypes.ObjectReadDeletedGQL):
                raise ValueError(f"Object {resobj.object_id} deleted")
            # Get the unresolved details
            unentry: bcs.UnresolvedObjectArg = unresolved_objects[
                inv_unrids[resobj.object_id]
            ]
            # Build relevant cache type and BuilderArg
            centry = ObjectCacheEntry(
                resobj.object_id, str(resobj.version), resobj.object_digest
            )
            builder_arg = bcs.BuilderArg(
                "Object", bcs.Address.from_str(resobj.object_id)
            )
            caller_arg: bcs.ObjectArg = None
            caller_shared: bool = False
            # Build CallArg
            if isinstance(resobj.object_owner, ptypes.SuiObjectOwnedShared):
                centry.initialSharedVersion = str(resobj.object_owner.initial_version)
                caller_shared = True
                caller_arg = bcs.CallArg(
                    "Object",
                    bcs.ObjectArg(
                        "SharedObject",
                        bcs.SharedObjectReference(
                            bcs.Address.from_str(resobj.object_id),
                            bcs.U64(resobj.object_owner.initial_version),
                            unentry.RefType == 2,
                        ),
                    ),
                )

            elif isinstance(resobj.object_owner, ptypes.SuiObjectOwnedAddress):
                centry.owner = resobj.object_owner.address_id
            elif isinstance(resobj.object_owner, ptypes.SuiObjectOwnedParent):
                centry.owner = resobj.object_owner.parent_id
            else:
                raise ValueError(f"{resobj.object_id} is immutable")
            await self.cache.add_object(centry)
            if not caller_shared:
                oref = bcs.ObjectReference(
                    bcs.Address.from_str(resobj.object_id),
                    resobj.version,
                    bcs.Digest.from_str(resobj.object_digest),
                )
                caller_arg = bcs.CallArg(
                    "Object",
                    bcs.ObjectArg(
                        "Recieving" if unentry.IsReceiving else "ImmOrOwnedObject", oref
                    ),
                )
            # Setup resolving
            resolved_builder_inputs[inv_unrids[resobj.object_id]] = (
                builder_arg,
                caller_arg,
            )

        # Hydrate the transaction
        txn.builder.resolved_object_inputs(resolved_builder_inputs)

    async def build_transaction(
        self, txn: CachingTransaction
    ) -> Coroutine[Any, Any, str]:
        """."""
        await self._resolve_object_inputs(txn)
        # Smash gas coins if no payment set
        if not txn.get_gas_payment():
            gas_list: ptypes.SuiCoinObjectGQL = await self._smash_gas(txn)
            txn.set_gas_payment(
                bcs.ObjectReference(
                    bcs.Address.from_str(gas_list.coin_object_id),
                    gas_list.version,
                    bcs.Digest.from_str(gas_list.object_digest),
                )
            )
        # Build TransactionData and return serialized bytes
        return await txn.build(
            gas_budget=txn._gas_budget, use_gas_object=txn.get_gas_payment()
        )

    async def execute_transaction(
        self,
        txn_str: str,
        txn_sigs: list[str],
        **kwargs,
    ) -> ptypes.ExecutionResultGQL:
        """."""
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

    # async def sign_and_execute_transaction(self, txn: CachingTransaction):
    #     """."""

    async def apply_effects(self, effects: bcst.TransactionEffects):
        """."""
        self._lastdigest = effects.value.transactionDigest.to_digest_str()
        await self.cache.applyEffects(effects)

    async def wait_for_last_transaction(self) -> Any:
        """."""
        if self._lastdigest:
            _xres = await self._client.wait_for_transaction(self._lastdigest)
            self._lastdigest = None
