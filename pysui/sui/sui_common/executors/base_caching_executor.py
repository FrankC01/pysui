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

if TYPE_CHECKING:
    from pysui.sui.sui_common.executors.object_registry import AbstractObjectRegistry

logger = logging.getLogger(__name__)


class _BaseCachingExecutor:
    """Protocol-agnostic base for caching transaction executors."""

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

    def _from_cache_to_builder(
        self,
        unres: bcs.UnresolvedObjectArg,
        cachm: ObjectSummary,
    ) -> tuple[bcs.BuilderArg, bcs.CallArg]:
        """Convert a cache entry + unresolved arg to resolved (BuilderArg, CallArg)."""
        co_addy: bcs.Address = bcs.Address.from_str(unres.ObjectStr)
        barg: bcs.BuilderArg = bcs.BuilderArg("Object", co_addy)
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

    async def _resolve_object_inputs(self, txn) -> None:
        """Resolve all UnresolvedObjectArg inputs via the SuiCommand object-fetch path.

        Cache hits are resolved without a network round-trip. Cache misses are
        batch-fetched via ``GetMultipleObjectSummary`` whose result is ``list[ObjectSummary]``.
        All fetched entries are written back to the per-executor cache so subsequent
        transactions in the same batch avoid redundant fetches.
        """
        from pysui.sui.sui_common.sui_commands import GetMultipleObjectSummary

        unresolved: dict[int, bcs.UnresolvedObjectArg] = txn.builder.get_unresolved_inputs()
        if not unresolved:
            return

        fetch_ids: dict[int, str] = {}
        resolved: dict[int, tuple[bcs.BuilderArg, bcs.CallArg]] = {}

        for idx, unobj in unresolved.items():
            cached = await self.cache.get_object(unobj.ObjectStr)
            if cached:
                logger.debug("cache hit: %s", unobj.ObjectStr)
                resolved[idx] = self._from_cache_to_builder(unobj, cached)
            else:
                logger.debug("cache miss: %s — will fetch", unobj.ObjectStr)
                fetch_ids[idx] = unobj.ObjectStr

        if fetch_ids:
            result = await self._client.execute(
                command=GetMultipleObjectSummary(object_ids=list(fetch_ids.values()))
            )
            if not result.is_ok():
                raise ValueError(f"Failed to fetch objects for resolution: {result.result_string}")

            entries: list[ObjectSummary] = result.result_data
            inv_fetch: dict[str, int] = {v: k for k, v in fetch_ids.items()}

            for entry in entries:
                idx = inv_fetch.get(entry.objectId)
                if idx is None:
                    continue
                await self.cache.add_object(entry)
                resolved[idx] = self._from_cache_to_builder(unresolved[idx], entry)

        txn.builder.resolved_object_inputs(resolved)

    async def build_transaction(
        self,
        txn,
        signer_block,
        gas_objects_override: Optional[list] = None,
    ) -> dict:
        """Resolve deferred object inputs then build and sign, injecting gas from cache."""
        await self._resolve_object_inputs(txn)
        if gas_objects_override is not None:
            use_gas = gas_objects_override
        else:
            gas_objects = await self.cache.getCustom("gasCoins")
            use_gas = gas_objects or None
        return await txn.build_and_sign(
            use_gas_objects=use_gas,
            use_account_for_gas=self._use_account_gas and not use_gas,
        )

    async def apply_effects(self, effects: TransactionEffects) -> None:
        """Apply transaction effects to the cache."""
        await self.cache.applyEffects(effects)

    async def reset(self) -> None:
        """Reset the cache state."""
        await self.cache.reset()

    async def update_gas_coins(self, coins: list[str]) -> None:
        """Update the cached gas coins list."""
        await self.cache.setCustom("gasCoins", coins)

    async def invalidate_gas_coins(self) -> None:
        """Invalidate cached gas coin entries."""
        await self.cache.setCustom("gasCoins", None)

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
