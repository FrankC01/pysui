#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Caching transaction execution."""

import asyncio
from pysui import AsyncGqlClient
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_types.bcs_txne as txeff
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
            self._cache.clearOwnedObjects(),
            self._cache.clearCustom(),
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

    async def build_transaction(self, txn: CachingTransaction):
        """."""
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

    async def execute_transaction(self, txn: CachingTransaction):
        """."""

    async def sign_and_execute_transaction(self, txn: CachingTransaction):
        """."""

    async def apply_effects(self, effects: txeff.TransactionEffects):
        """."""
        self._lastdigest = effects.value.transactionDigest.to_digest_str()
        await self.cache.applyEffects(effects)

    async def wait_for_last_transaction(self):
        """."""
