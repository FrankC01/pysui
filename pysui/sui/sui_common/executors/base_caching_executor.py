#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Base caching executor ABC for protocol-agnostic transaction caching."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pysui.sui.sui_common.executors.cache import AsyncObjectCache, ObjectSummary
from pysui.sui.sui_common.types import TransactionEffects
import pysui.sui.sui_bcs.bcs as bcs
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented

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
        if gas_objects_override is not None:
            use_gas = gas_objects_override
        else:
            gas_objects = await self.cache.getCustom("gasCoins")
            use_gas = gas_objects or None
        return await txn.build_and_sign(
            use_gas_objects=use_gas,
            use_account_for_gas=self._use_account_gas and not use_gas,
        )

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.apply_effects")
    async def apply_effects(self, effects: TransactionEffects) -> None:
        """Apply transaction effects to the cache."""
        await self.cache.applyEffects(effects)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.reset")
    async def reset(self) -> None:
        """Reset the cache state."""
        await self.cache.reset()

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.update_gas_coins")
    async def update_gas_coins(self, coins: list[str]) -> None:
        """Update the cached gas coins list."""
        await self.cache.setCustom("gasCoins", coins)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.invalidate_gas_coins")
    async def invalidate_gas_coins(self) -> None:
        """Invalidate cached gas coin entries."""
        await self.cache.setCustom("gasCoins", None)

    @instrumented("pysui.sui.sui_common.executors.base_caching_executor._BaseCachingExecutor.sync_to_registry")
    async def sync_to_registry(self, registry: "AbstractObjectRegistry") -> None:
        """Push known object versions from the per-executor cache into the shared registry.

        Higher version always wins — stale writes are silently dropped by the registry.
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
