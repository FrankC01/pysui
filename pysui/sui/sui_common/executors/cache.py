#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Transaction Executor Caches."""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Union
from dataclasses import dataclass

# ptypes is imported only for type-checker visibility (TYPE_CHECKING guard) to avoid
# a circular import: sui_common (lower layer) must not import sui_pgql (upper layer)
# at runtime. The quoted annotation on MoveFunctionCacheEntry.parameters is required
# as a consequence — runtime hint resolution (e.g. typing.get_type_hints) will not work.
if TYPE_CHECKING:
    import pysui.sui.sui_pgql.pgql_types as ptypes

logger = logging.getLogger(__name__)


@dataclass
class ObjectCacheEntry:
    """Cached object reference with version, digest, and owner metadata."""

    objectId: str
    version: str
    digest: str
    owner: str | None = None
    initialSharedVersion: str | None = None


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
        """Fetch a single entry from the underlying cache store."""
        pass

    @abstractmethod
    async def _set(
        self,
        cache_type: str,
        prop: str,
        val: Union[ObjectCacheEntry, MoveFunctionCacheEntry],
    ) -> None:
        """Persist a single entry into the underlying cache store."""
        pass

    @abstractmethod
    async def _delete(self, cache_type: str, prop: str) -> None:
        """Remove a single entry from the underlying cache store."""
        pass

    @abstractmethod
    async def _clear(self, cache_type: Union[str, None]) -> None:
        """Clear all entries for one cache type or all types when None."""
        pass

    async def get_object(
        self, id: str
    ) -> Union[ObjectCacheEntry, MoveFunctionCacheEntry, None]:
        """Return cached object entry by id from owned or shared/immutable buckets."""
        res = await self._get("OwnedObject", id)
        if not res:
            res = await self._get("SharedOrImmutableObject", id)

        return res if res else None

    async def get_objects(
        self, ids: list[str]
    ) -> list[Union[ObjectCacheEntry, MoveFunctionCacheEntry, None]]:
        """Return cached object entries for the given list of object ids."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        return [await self.get_object(x) for x in ids]

    async def add_object(self, obj: ObjectCacheEntry) -> ObjectCacheEntry:
        """Add an object entry to the appropriate owned or shared/immutable bucket."""
        if obj.owner:
            await self._set("OwnedObject", obj.objectId, obj)
        else:
            await self._set("SharedOrImmutableObject", obj.objectId, obj)

        return obj

    async def add_objects(self, objs: list[ObjectCacheEntry]) -> list[ObjectCacheEntry]:
        """Add multiple object entries to the cache."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        return [await self.add_object(x) for x in objs]

    async def delete_object(self, oid: str):
        """Remove an object entry from both owned and shared/immutable buckets."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        await self._delete("OwnedObject", oid)
        await self._delete("SharedOrImmutableObject", oid)

    async def delete_objects(self, oids: list[str]):
        """Remove multiple object entries from the cache."""
        # P2 fix: replace asyncio.gather on in-memory dict ops with direct iteration
        for oid in oids:
            await self.delete_object(oid)

    async def get_move_function_definition(
        self,
        package,
        module,
        function,
    ) -> MoveFunctionEntry:
        """Return cached Move function entry by package::module::function key."""
        ffull = f"{package}::{module}::{function}"
        return await self._get("MoveFunction", ffull)

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

    async def delete_move_function_definition(
        self,
        package,
        module,
        function,
    ):
        """Remove a Move function definition from the cache."""
        ffull = f"{package}::{module}::{function}"
        return await self._delete("MoveFunction", ffull)

    async def get_custom(self, key: str) -> Any:
        """Return a value from the custom cache bucket."""
        return await self._get("Custom", key)

    async def add_custom(self, key: str, value: Any):
        """Set a value in the custom cache bucket."""
        return await self._set("Custom", key, value)

    async def delete_custom(self, key: str):
        """Remove a value from the custom cache bucket."""
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
        """Fetch a single entry from the in-memory dict store."""
        res = self._cache.get(cache_type)
        return res.get(entry_type) if res else None

    async def _set(
        self, cache_type: str, entry_type: str, val: Any
    ) -> Union[ObjectCacheEntry, MoveFunctionCacheEntry, Any, None]:
        """Persist a single entry into the in-memory dict store."""
        self._cache[cache_type][entry_type] = val
        return val

    async def _delete(self, cache_type: str, prop: str) -> None:
        """Remove a single entry from the in-memory dict store."""
        self._cache.get(cache_type).pop(prop, None)

    async def _clear(self, cache_type: Union[str, None]) -> None:
        """Clear all entries for one cache type or all types when None."""
        if cache_type:
            self._cache[cache_type] = {}
        else:
            for _k in self._cache:
                self._cache[_k] = {}


class AsyncObjectCache(AsyncInMemoryCache):
    """Concrete async object cache."""

    def __init__(self):
        """Initialize the async object cache."""

        super().__init__()

    async def clear(self, cache_type: Union[str, None]):
        """Clear entries for one cache type or all types when None."""
        await self._clear(cache_type)

    async def getMoveFunctionDefinition(
        self, package: str, module: str, function: str
    ) -> MoveFunctionEntry:
        """Return cached Move function definition (camelCase alias)."""
        return await self.get_move_function_definition(package, module, function)

    async def getObjects(
        self, ids: list[str]
    ) -> list[Union[ObjectCacheEntry, MoveFunctionCacheEntry, None]]:
        """Return cached object entries for the given ids (camelCase alias)."""
        return await self.get_objects(ids)

    async def deleteObjects(self, ids: list[str]):
        """Delete cached object entries for the given ids (camelCase alias)."""
        return await self.delete_objects(ids)

    async def clearOwnedObjects(self):
        """Clear all cached owned-object entries."""
        await self.clear("OwnedObject")

    async def clearCustom(self):
        """Clear all entries from the custom cache bucket."""
        await self.clear("Custom")

    async def reset(self):
        """Reset all cache entries."""
        await self.clear(None)

    async def getCustom(self, key: str) -> Any:
        """Return a value from the custom cache bucket (camelCase alias)."""
        return await self.get_custom(key)

    async def setCustom(self, key: str, value: Any):
        """Set a value in the custom cache bucket (camelCase alias)."""
        return await self.add_custom(key, value)

    async def deleteCustom(self, key: str):
        """Remove a value from the custom cache bucket (camelCase alias)."""
        return await self.delete_custom(key)

    async def applyEffects(self, effects) -> None:
        """Apply execution effects to the cache using the protocol-agnostic common type."""
        from pysui.sui.sui_common.types import TransactionEffects as TxEffects

        lamport_version = str(effects.lamport_version)
        deleted: list[str] = []
        added: list[ObjectCacheEntry] = []
        for changed in effects.changed_objects:
            if changed.output_state == "DoesNotExist":
                deleted.append(changed.object_id)
            elif changed.output_state in ("ObjectWrite", "PackageWrite"):
                owner = changed.output_owner
                added.append(
                    ObjectCacheEntry(
                        objectId=changed.object_id,
                        version=lamport_version,
                        digest=changed.output_digest or "",
                        owner=None if (owner is None or owner.kind == "SharedInitialVersion") else owner.address,
                        initialSharedVersion=str(owner.initial_shared_version) if owner and owner.kind == "SharedInitialVersion" else None,
                    )
                )
        if added or deleted:
            logger.debug("Effects results: Deleted %s Added %s", deleted, added)
            await self.delete_objects(deleted)
            await self.add_objects(added)
