#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Base caching executor ABC for protocol-agnostic transaction caching."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pysui.sui.sui_common.executors.cache import AsyncObjectCache, ObjectSummary, deleted_object_ids
from pysui.sui.sui_common.types import TransactionEffects
from pysui.sui.sui_common.instrumentation import count, instrumented, sync_instrumented

if TYPE_CHECKING:
    from pysui.sui.sui_common.executors.object_registry import AbstractObjectRegistry

logger = logging.getLogger(__name__)


class _BaseCachingExecutor:
    """Protocol-agnostic base for caching transaction executors."""

    @sync_instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.__init__")
    def __init__(
        self,
        client=None,
        gas_owner: Optional[str] = None,
        use_account_gas: bool = False,
    ) -> None:
        self._client = client
        self._gas_owner = gas_owner
        self._use_account_gas = use_account_gas
        self.cache: AsyncObjectCache = AsyncObjectCache()

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.build_transaction")
    async def build_transaction(
        self,
        txn,
        signer_block,
        gas_objects_override: Optional[list] = None,
    ) -> dict:
        """Resolve deferred object inputs then build and sign, injecting gas from cache."""
        txn.inject_cache(self.cache)
        use_gas: Optional[list]
        if gas_objects_override is not None:
            use_gas = gas_objects_override
        else:
            gas_objects = await self.cache.get_custom("gasCoins")
            use_gas = gas_objects or None
        return await txn.build_and_sign(
            use_gas_objects=use_gas,
            use_account_for_gas=self._use_account_gas and not use_gas,
        )

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.apply_effects")
    async def apply_effects(self, effects: TransactionEffects) -> None:
        """Apply transaction effects to the cache."""
        await self.cache.apply_effects(effects)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.reset")
    async def reset(self) -> None:
        """Reset the cache state."""
        await self.cache.reset()

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.update_gas_coins")
    async def update_gas_coins(self, coins: list[str]) -> None:
        """Update the cached gas coins list."""
        await self.cache.add_custom("gasCoins", coins)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.invalidate_gas_coins")
    async def invalidate_gas_coins(self) -> None:
        """Invalidate cached gas coin entries."""
        await self.cache.add_custom("gasCoins", None)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.sync_to_registry")
    async def sync_to_registry(
        self, registry: "AbstractObjectRegistry", effects: TransactionEffects
    ) -> None:
        """Push known object versions into the shared registry and tombstone deletions.

        Higher version always wins — stale writes are silently dropped by the registry.
        Deleted objects are already gone from the cache by the time this runs, so their
        ids come from the effects directly; without that the registry would keep serving
        a version for an object that no longer exists.
        Called by the parallel executor after each transaction's effects are applied.
        """
        from pysui.sui.sui_common.executors.object_registry import ObjectVersionEntry

        # Only owned objects change version after execution; shared objects use
        # initialSharedVersion which is stable and doesn't need registry tracking.
        owned = self.cache._cache.get("OwnedObject", {})
        entries: list[ObjectVersionEntry] = [
            ObjectVersionEntry(object_id=oid, version=cached.version, digest=cached.digest)
            for oid, cached in owned.items()
        ]
        if entries:
            await registry.upsert_many(entries)
        for oid in deleted_object_ids(effects=effects):
            await registry.tombstone(oid)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.seed_from_registry")
    async def seed_from_registry(
        self, registry: "AbstractObjectRegistry", object_ids: list[str]
    ) -> None:
        """Seed this executor's cache with known object versions from the shared registry.

        Read-side counterpart to sync_to_registry. Only the requested ids are pulled so a
        short-lived per-transaction cache does not inherit the whole process-wide registry.
        Tombstoned entries are skipped: they carry no usable version or digest.
        Emits executor.ocs.seed_hit / seed_miss / seed_tombstone counts per requested id.
        """
        if not object_ids:
            return
        entries = await registry.get_many(object_ids)
        for oid in object_ids:
            entry = entries.get(oid)
            if entry is None:
                count("executor.ocs.seed_miss")
                continue
            if entry.is_tombstone:
                count("executor.ocs.seed_tombstone")
                continue
            count("executor.ocs.seed_hit")
            # Bucket named explicitly: add_object routes on owner truthiness, and the
            # registry tracks only owned objects without carrying an owner to route on.
            await self.cache.add_object_to(
                bucket="OwnedObject",
                obj=ObjectSummary(
                    objectId=entry.object_id,
                    version=entry.version,
                    digest=entry.digest,
                    owner=self._gas_owner,
                    initialSharedVersion=None,
                ),
            )
