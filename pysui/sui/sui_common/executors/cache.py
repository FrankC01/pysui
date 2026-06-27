#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Transaction Executor Caches."""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Union
from dataclasses import dataclass

from pysui.sui.sui_common.shared_types import ObjectSummary
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented

# ptypes is imported only for type-checker visibility (TYPE_CHECKING guard) to avoid
# a circular import: sui_common (lower layer) must not import sui_pgql (upper layer)
# at runtime. The quoted annotation on MoveFunctionCacheEntry.parameters is required
# as a consequence — runtime hint resolution (e.g. typing.get_type_hints) will not work.
if TYPE_CHECKING:
    import pysui.sui.sui_pgql.pgql_types as ptypes

logger = logging.getLogger(__name__)


@dataclass
class MoveFunctionCacheEntry:
    """Cached Move function definition keyed by package::module::function."""

    package: str
    module: str
    function: str
    parameters: "ptypes.MoveFunctionGQL"


@dataclass
class MoveFunctionEntry:
    """Wrapper pairing a Move function cache entry with its package address."""

    package: str
    function: MoveFunctionCacheEntry


@dataclass
class CacheEntryTypes:
    """Type registry of supported cache categories and their entry shapes."""

    OwnedObject: ObjectSummary
    SharedOrImmutableObject: ObjectSummary
    MoveFunction: MoveFunctionCacheEntry
    Custom: Any


class AbstractAsyncCache(ABC):
    """Base async cache abstraction."""

    @abstractmethod
    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache._get")
    async def _get(
        self, cache_type: str, prop: str
    ) -> Union[ObjectSummary, MoveFunctionCacheEntry]:
        """Fetch a single entry from the underlying cache store."""

    @abstractmethod
    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache._set")
    async def _set(
        self,
        cache_type: str,
        prop: str,
        val: Union[ObjectSummary, MoveFunctionCacheEntry],
    ) -> None:
        """Persist a single entry into the underlying cache store."""

    @abstractmethod
    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache._delete")
    async def _delete(self, cache_type: str, prop: str) -> None:
        """Remove a single entry from the underlying cache store."""

    @abstractmethod
    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache._clear")
    async def _clear(self, cache_type: Union[str, None]) -> None:
        """Clear all entries for one cache type or all types when None."""

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.get_object")
    async def get_object(
        self, id: str
    ) -> Union[ObjectSummary, MoveFunctionCacheEntry, None]:
        """Return cached object entry by id from owned or shared/immutable buckets."""
        res = await self._get("OwnedObject", id)
        if not res:
            res = await self._get("SharedOrImmutableObject", id)

        return res

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.get_objects")
    async def get_objects(
        self, ids: list[str]
    ) -> list[Union[ObjectSummary, MoveFunctionCacheEntry, None]]:
        """Return cached object entries for the given list of object ids."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        return [await self.get_object(x) for x in ids]

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.add_object")
    async def add_object(self, obj: ObjectSummary) -> ObjectSummary:
        """Add an object entry to the appropriate owned or shared/immutable bucket."""
        if obj.owner:
            await self._set("OwnedObject", obj.objectId, obj)
        else:
            await self._set("SharedOrImmutableObject", obj.objectId, obj)

        return obj

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.add_objects")
    async def add_objects(self, objs: list[ObjectSummary]) -> list[ObjectSummary]:
        """Add multiple object entries to the cache."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        return [await self.add_object(x) for x in objs]

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.delete_object")
    async def delete_object(self, oid: str):
        """Remove an object entry from both owned and shared/immutable buckets."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        await self._delete("OwnedObject", oid)
        await self._delete("SharedOrImmutableObject", oid)

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.delete_objects")
    async def delete_objects(self, oids: list[str]):
        """Remove multiple object entries from the cache."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        for oid in oids:
            await self.delete_object(oid)

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.get_move_function_definition")
    async def get_move_function_definition(
        self,
        package,
        module,
        function,
    ) -> MoveFunctionEntry:
        """Return cached Move function entry by package::module::function key."""
        ffull = f"{package}::{module}::{function}"
        return await self._get("MoveFunction", ffull)

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.add_move_function_definition")
    async def add_move_function_definition(
        self, function_definition: MoveFunctionCacheEntry
    ):
        """Cache a Move function definition keyed by package::module::function."""
        ffull = f"{function_definition.package}::{function_definition.module}::{function_definition.function}"
        entry = MoveFunctionEntry(function_definition.package, function_definition)
        await self._set(
            "MoveFunction",
            ffull,
            entry,
        )
        return entry

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.delete_move_function_definition")
    async def delete_move_function_definition(
        self,
        package,
        module,
        function,
    ):
        """Remove a Move function definition from the cache."""
        ffull = f"{package}::{module}::{function}"
        return await self._delete("MoveFunction", ffull)

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.get_custom")
    async def get_custom(self, key: str) -> Any:
        """Return a value from the custom cache bucket."""
        return await self._get("Custom", key)

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.add_custom")
    async def add_custom(self, key: str, value: Any):
        """Set a value in the custom cache bucket."""
        return await self._set("Custom", key, value)

    @instrumented("pysui.sui.sui_common.executors.cache.AbstractAsyncCache.delete_custom")
    async def delete_custom(self, key: str):
        """Remove a value from the custom cache bucket."""
        return await self._delete("Custom", key)


class AsyncInMemoryCache(AbstractAsyncCache):
    """In memory async cache."""

    @sync_instrumented("pysui.sui.sui_common.executors.cache.AsyncInMemoryCache.__init__")
    def __init__(self):
        """."""
        self._cache: dict[
            str, dict[str, Union[ObjectSummary, MoveFunctionCacheEntry, Any]]
        ] = {
            "OwnedObject": {},
            "SharedOrImmutableObject": {},
            "MoveFunction": {},
            "Custom": {},
        }

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncInMemoryCache._get")
    async def _get(
        self, cache_type: str, entry_type: str
    ) -> Union[ObjectSummary, MoveFunctionCacheEntry, Any, None]:
        """Fetch a single entry from the in-memory dict store."""
        res = self._cache.get(cache_type)
        return res.get(entry_type) if res else None

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncInMemoryCache._set")
    async def _set(
        self, cache_type: str, entry_type: str, val: Any
    ) -> Union[ObjectSummary, MoveFunctionCacheEntry, Any, None]:
        """Persist a single entry into the in-memory dict store."""
        self._cache[cache_type][entry_type] = val
        return val

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncInMemoryCache._delete")
    async def _delete(self, cache_type: str, prop: str) -> None:
        """Remove a single entry from the in-memory dict store."""
        self._cache.get(cache_type).pop(prop, None)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncInMemoryCache._clear")
    async def _clear(self, cache_type: Union[str, None]) -> None:
        """Clear all entries for one cache type or all types when None."""
        if cache_type:
            self._cache[cache_type] = {}
        else:
            for _k in self._cache:
                self._cache[_k] = {}


class AsyncObjectCache(AsyncInMemoryCache):
    """Concrete async object cache."""

    @sync_instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.__init__")
    def __init__(self):
        """Initialize the async object cache."""

        super().__init__()

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.clear")
    async def clear(self, cache_type: Union[str, None]):
        """Clear entries for one cache type or all types when None."""
        await self._clear(cache_type)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.getMoveFunctionDefinition")
    async def getMoveFunctionDefinition(
        self, package: str, module: str, function: str
    ) -> MoveFunctionEntry:
        """Return cached Move function definition (camelCase alias)."""
        return await self.get_move_function_definition(package, module, function)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.getObjects")
    async def getObjects(
        self, ids: list[str]
    ) -> list[Union[ObjectSummary, MoveFunctionCacheEntry, None]]:
        """Return cached object entries for the given ids (camelCase alias)."""
        return await self.get_objects(ids)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.deleteObjects")
    async def deleteObjects(self, ids: list[str]):
        """Delete cached object entries for the given ids (camelCase alias)."""
        return await self.delete_objects(ids)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.clearOwnedObjects")
    async def clearOwnedObjects(self):
        """Clear all cached owned-object entries."""
        await self.clear("OwnedObject")

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.clearCustom")
    async def clearCustom(self):
        """Clear all entries from the custom cache bucket."""
        await self.clear("Custom")

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.reset")
    async def reset(self):
        """Reset all cache entries."""
        await self.clear(None)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.getCustom")
    async def getCustom(self, key: str) -> Any:
        """Return a value from the custom cache bucket (camelCase alias)."""
        return await self.get_custom(key)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.setCustom")
    async def setCustom(self, key: str, value: Any):
        """Set a value in the custom cache bucket (camelCase alias)."""
        return await self.add_custom(key, value)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.deleteCustom")
    async def deleteCustom(self, key: str):
        """Remove a value from the custom cache bucket (camelCase alias)."""
        return await self.delete_custom(key)

    @instrumented("pysui.sui.sui_common.executors.cache.AsyncObjectCache.applyEffects")
    async def applyEffects(self, effects) -> None:
        """Apply execution effects to the cache."""
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot

        lamport_version = str(effects.lamport_version)
        deleted: list[str] = []
        added: list[ObjectSummary] = []
        for changed in effects.changed_objects:
            if changed.output_state == sui_prot.ChangedObjectOutputObjectState.DOES_NOT_EXIST:
                deleted.append(changed.object_id)
            elif changed.output_state in (
                sui_prot.ChangedObjectOutputObjectState.OBJECT_WRITE,
                sui_prot.ChangedObjectOutputObjectState.PACKAGE_WRITE,
            ):
                owner = changed.output_owner
                added.append(
                    ObjectSummary(
                        objectId=changed.object_id,
                        version=lamport_version,
                        digest=changed.output_digest or "",
                        owner=None if (owner is None or owner.kind in (sui_prot.OwnerOwnerKind.SHARED, sui_prot.OwnerOwnerKind.CONSENSUS_ADDRESS)) else owner.address,
                        initialSharedVersion=str(owner.version) if owner and owner.kind in (sui_prot.OwnerOwnerKind.SHARED, sui_prot.OwnerOwnerKind.CONSENSUS_ADDRESS) else None,
                    )
                )
        if added or deleted:
            logger.debug("Effects results: Deleted %s Added %s", deleted, added)
            await self.delete_objects(deleted)
            await self.add_objects(added)
