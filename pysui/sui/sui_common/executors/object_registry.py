#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Process-wide singleton object version registry for parallel executor coordination."""

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional

import logging

logger = logging.getLogger(__name__)


@dataclass
class ObjectVersionEntry:
    """Cached version/digest for a single Sui object."""

    object_id: str
    version: str
    digest: str
    last_used_ns: int = field(default_factory=time.monotonic_ns)
    is_tombstone: bool = False
    tombstone_expires_ns: int = 0


class AbstractObjectRegistry(ABC):
    """Interface for a process-wide object version cache."""

    @abstractmethod
    async def get(self, object_id: str) -> Optional[ObjectVersionEntry]: ...

    @abstractmethod
    async def get_many(self, object_ids: list[str]) -> dict[str, ObjectVersionEntry]: ...

    @abstractmethod
    async def upsert(self, entry: ObjectVersionEntry) -> None: ...

    @abstractmethod
    async def upsert_many(self, entries: list[ObjectVersionEntry]) -> None: ...

    @abstractmethod
    async def tombstone(self, object_id: str, ttl_seconds: float = 30.0) -> None: ...

    @abstractmethod
    async def evict(self, object_id: str) -> None: ...

    @abstractmethod
    async def reset(self) -> None: ...

    @abstractmethod
    def size(self) -> int: ...


class InMemoryObjectRegistry(AbstractObjectRegistry):
    """LRU-bounded in-memory object registry with tombstone support.

    A single instance is shared across all parallel executors in the process.
    Use get_object_registry() to obtain the singleton; use
    _set_object_registry_for_tests() only in pytest fixtures.
    """

    DEFAULT_MAX_ENTRIES: int = 50_000
    DEFAULT_TOMBSTONE_TTL_SECONDS: float = 30.0

    def __init__(self, *, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        self._entries: OrderedDict[str, ObjectVersionEntry] = OrderedDict()
        self._max = max_entries
        self._lock = asyncio.Lock()

    async def get(self, object_id: str) -> Optional[ObjectVersionEntry]:
        async with self._lock:
            return self._get_unlocked(object_id)

    async def get_many(self, object_ids: list[str]) -> dict[str, ObjectVersionEntry]:
        async with self._lock:
            result: dict[str, ObjectVersionEntry] = {}
            for oid in object_ids:
                entry = self._get_unlocked(oid)
                if entry is not None:
                    result[oid] = entry
            return result

    async def upsert(self, entry: ObjectVersionEntry) -> None:
        async with self._lock:
            self._upsert_unlocked(entry)

    async def upsert_many(self, entries: list[ObjectVersionEntry]) -> None:
        async with self._lock:
            for entry in entries:
                self._upsert_unlocked(entry)

    async def tombstone(self, object_id: str, ttl_seconds: float = DEFAULT_TOMBSTONE_TTL_SECONDS) -> None:
        async with self._lock:
            expires_ns = time.monotonic_ns() + int(ttl_seconds * 1_000_000_000)
            entry = ObjectVersionEntry(
                object_id=object_id,
                version="",
                digest="",
                is_tombstone=True,
                tombstone_expires_ns=expires_ns,
            )
            self._upsert_unlocked(entry)

    async def evict(self, object_id: str) -> None:
        async with self._lock:
            self._entries.pop(object_id, None)

    async def reset(self) -> None:
        async with self._lock:
            self._entries.clear()

    def size(self) -> int:
        return len(self._entries)

    def _get_unlocked(self, object_id: str) -> Optional[ObjectVersionEntry]:
        entry = self._entries.get(object_id)
        if entry is None:
            return None
        if entry.is_tombstone and time.monotonic_ns() > entry.tombstone_expires_ns:
            del self._entries[object_id]
            return None
        self._entries.move_to_end(object_id)
        entry.last_used_ns = time.monotonic_ns()
        return entry

    def _upsert_unlocked(self, entry: ObjectVersionEntry) -> None:
        existing = self._entries.get(entry.object_id)
        if existing and not entry.is_tombstone and not existing.is_tombstone:
            # Higher version wins — skip stale writes
            if existing.version >= entry.version:
                return
        self._entries[entry.object_id] = entry
        self._entries.move_to_end(entry.object_id)
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)


# --- Singleton machinery ---

_REGISTRY: Optional[AbstractObjectRegistry] = None
_REGISTRY_INIT_LOCK = threading.Lock()


def get_object_registry() -> AbstractObjectRegistry:
    """Return the process-wide singleton registry, creating it on first call."""
    global _REGISTRY
    if _REGISTRY is None:
        with _REGISTRY_INIT_LOCK:
            if _REGISTRY is None:
                _REGISTRY = InMemoryObjectRegistry()
    return _REGISTRY


def _set_object_registry_for_tests(registry: Optional[AbstractObjectRegistry]) -> None:
    """Replace or clear the singleton. Call in pytest teardown to restore isolation."""
    global _REGISTRY
    _REGISTRY = registry
