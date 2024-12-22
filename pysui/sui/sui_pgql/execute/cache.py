#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Transaction Executor Caches."""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Any, Union
from dataclasses import dataclass

import pysui.sui.sui_types.bcs_txne as bcs
import pysui.sui.sui_pgql.pgql_types as ptypes

logger = logging.getLogger("serial_exec")


@dataclass
class ObjectCacheEntry:
    objectId: str
    version: str
    digest: str
    owner: Union[str, None] = None
    initialSharedVersion: Union[str, None] = None


@dataclass
class MoveFunctionCacheEntry:
    package: str
    module: str
    function: str
    parameters: ptypes.MoveFunctionGQL  # OpenMoveTypeSignature


@dataclass
class MoveFunctionEntry:
    package: str
    function: MoveFunctionCacheEntry


@dataclass
class CacheEntryTypes:
    OwnedObject: ObjectCacheEntry
    SharedOrImmutableObject: ObjectCacheEntry
    MoveFunction: MoveFunctionCacheEntry
    Custom: Any


class AbstractAsyncCache(ABC):
    """Base async cache abstraction."""

    @abstractmethod
    async def _get(
        self, cache_type: str, prop: str
    ) -> Union[ObjectCacheEntry, MoveFunctionCacheEntry]:
        pass

    @abstractmethod
    async def _set(
        self,
        cache_type: str,
        prop: str,
        val: Union[ObjectCacheEntry, MoveFunctionCacheEntry],
    ) -> None:
        pass

    @abstractmethod
    async def _delete(self, cache_type: str, prop: str) -> None:
        pass

    @abstractmethod
    async def _clear(self, cache_type: Union[str, None]) -> None:
        pass

    async def get_object(
        self, id: str
    ) -> Union[ObjectCacheEntry, MoveFunctionCacheEntry, None]:
        res = await self._get("OwnedObject", id)
        if not res:
            res = await self._get("SharedOrImmutableObject", id)

        return res if res else None

    async def get_objects(
        self, ids: list[str]
    ) -> list[Union[ObjectCacheEntry, MoveFunctionCacheEntry, None]]:
        return await asyncio.gather(*[self.get_object(x) for x in ids])

    async def add_object(self, obj: ObjectCacheEntry) -> ObjectCacheEntry:
        if obj.owner:
            await self._set("OwnedObject", obj.objectId, obj)
        else:
            await self._set("SharedOrImmutableObject", obj.objectId, obj)

        return obj

    async def add_objects(self, objs: list[ObjectCacheEntry]) -> list[ObjectCacheEntry]:
        return await asyncio.gather(*[self.add_object(x) for x in objs])

    async def delete_object(self, oid: str):
        await asyncio.gather(
            self._delete("OwnedObject", oid),
            self._delete("SharedOrImmutableObject", oid),
        )

    async def delete_objects(self, oids: list[str]):
        await asyncio.gather(*[self.delete_object(oid) for oid in oids])

    async def get_move_function_definition(
        self,
        package,
        module,
        function,
    ) -> MoveFunctionEntry:
        ffull = f"{package}::{module}::{function}"
        return await self._get("MoveFunction", ffull)

    async def add_move_function_definition(
        self, function_definition: MoveFunctionCacheEntry
    ):
        ffull = f"{function_definition.package}::{function_definition.module}::{function_definition.function}"
        entry = MoveFunctionEntry(function_definition.package, function_definition)
        await self._set(
            "MoveFunction",
            ffull,
            entry,
        )
        return entry

    async def delete_move_function_definition(
        self,
        package,
        module,
        function,
    ):
        ffull = f"{package}::{module}::{function}"
        return await self._delete("MoveFunction", ffull)

    async def get_custom(self, key: str) -> Any:
        return await self._get("Custom", key)

    async def add_custom(self, key: str, value: Any):
        return await self._set("Custom", key, value)

    async def delete_custom(self, key: str):
        return await self._delete("Custom", key)


class AsyncInMemoryCache(AbstractAsyncCache):
    """In memory async cache."""

    def __init__(self):
        """."""
        self._cache: dict[
            str, dict[str, Union[ObjectCacheEntry, MoveFunctionCacheEntry, Any]]
        ] = {
            "OwnedObject": {},
            "SharedOrImmutableObject": {},
            "MoveFunction": {},
            "Custom": {},
        }

    async def _get(
        self, cache_type: str, entry_type: str
    ) -> Union[ObjectCacheEntry, MoveFunctionCacheEntry, Any, None]:
        res = self._cache.get(cache_type)
        return res.get(entry_type) if res else None

    async def _set(
        self, cache_type: str, entry_type: str, val: Any
    ) -> Union[ObjectCacheEntry, MoveFunctionCacheEntry, Any, None]:
        self._cache[cache_type][entry_type] = val
        return val

    async def _delete(self, cache_type: str, prop: str) -> None:
        self._cache.get(cache_type).pop(prop, None)

    async def _clear(self, cache_type: Union[str, None]) -> None:
        if cache_type:
            self._cache[cache_type] = {}
        else:
            for _k in self._cache.keys():
                self._cache[_k] = {}


class AsyncObjectCache(AsyncInMemoryCache):
    """Concrete async object cache."""

    def __init__(self):

        super().__init__()

    async def clear(self, cache_type: Union[str, None]):
        await self._clear(cache_type)

    async def getMoveFunctionDefinition(
        self, package: str, module: str, function: str
    ) -> MoveFunctionEntry:
        return self.get_move_function_definition(package, module, function)

    async def getObjects(
        self, ids: list[str]
    ) -> list[Union[ObjectCacheEntry, MoveFunctionCacheEntry, None]]:
        return await self.get_objects(ids)

    async def deleteObjects(self, ids: list[str]):
        return await self.delete_objects(ids)

    async def clearOwnedObjects(self):
        await self.clear("OwnedObject")

    async def clearCustom(self):
        await self.clear("Custom")

    async def getCustom(self, key: str) -> Any:
        return await self.get_custom(key)

    async def setCustom(self, key: str, value: Any):
        return await self.add_custom(key, value)

    async def deleteCustom(self, key: str):
        return await self.delete_custom(key)

    async def applyEffects(self, effects: bcs.TransactionEffects):
        if effects.enum_name != "V2":
            raise ValueError(
                f"Unsupported transaction effects version {effects.enum_name}"
            )
        ev2: bcs.TransactionEffectsV2 = effects.value
        lamport_version = ev2.lamportVersion
        changed_objects: list = ev2.changedObjects
        deleted: list[str] = []
        added: list[ObjectCacheEntry] = []
        for address, change in changed_objects:
            addy = address.to_address_str()
            out_state = change.outputState
            if out_state.enum_name == "NotExist":
                deleted.append(addy)
            elif out_state.enum_name == "ObjectWrite":
                digest, owner = out_state.value
                added.append(
                    ObjectCacheEntry(
                        address.to_address_str(),
                        lamport_version,
                        digest.to_digest_str(),
                        owner.value.to_address_str(),
                        (
                            str(owner.value)
                            if owner.enum_name == "SharedInitialVersion"
                            else None
                        ),
                    )
                )
            else:
                pass
        if added or deleted:
            logger.debug(f"Effects results: Deleted {deleted} Added {added}")
            await asyncio.gather(self.delete_objects(deleted), self.add_objects(added))
