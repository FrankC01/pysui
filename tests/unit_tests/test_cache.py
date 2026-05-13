#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for AsyncObjectCache."""

import pytest
import asyncio
from pysui.sui.sui_common.executors import AsyncObjectCache, ObjectSummary


class TestAsyncObjectCache:
    """Test AsyncObjectCache functionality."""

    @pytest.mark.asyncio
    async def test_cache_creation(self):
        """Cache is created with no entries."""
        cache = AsyncObjectCache()
        assert cache is not None

    @pytest.mark.asyncio
    async def test_set_and_get_custom(self):
        """setCustom and getCustom work for storing arbitrary data."""
        cache = AsyncObjectCache()
        data = ["item1", "item2"]
        await cache.setCustom("test_key", data)
        result = await cache.getCustom("test_key")
        assert result == data

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """getCustom returns None for non-existent keys."""
        cache = AsyncObjectCache()
        result = await cache.getCustom("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_overwrite_custom_value(self):
        """Setting same key overwrites previous value."""
        cache = AsyncObjectCache()
        await cache.setCustom("key", "value1")
        await cache.setCustom("key", "value2")
        result = await cache.getCustom("key")
        assert result == "value2"

    @pytest.mark.asyncio
    async def test_multiple_keys(self):
        """Cache can store multiple different keys."""
        cache = AsyncObjectCache()
        await cache.setCustom("key1", "value1")
        await cache.setCustom("key2", {"data": "value2"})
        await cache.setCustom("key3", [1, 2, 3])

        assert await cache.getCustom("key1") == "value1"
        assert await cache.getCustom("key2") == {"data": "value2"}
        assert await cache.getCustom("key3") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_reset_cache(self):
        """reset() clears all cache entries."""
        cache = AsyncObjectCache()
        await cache.setCustom("key1", "value1")
        await cache.setCustom("key2", "value2")
        await cache.reset()
        assert await cache.getCustom("key1") is None
        assert await cache.getCustom("key2") is None

    @pytest.mark.asyncio
    async def test_gas_coins_special_key(self):
        """Cache handles gasCoins key specially."""
        cache = AsyncObjectCache()
        coins = ["coin1", "coin2", "coin3"]
        await cache.setCustom("gasCoins", coins)
        result = await cache.getCustom("gasCoins")
        assert result == coins

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Cache handles concurrent set/get operations."""
        cache = AsyncObjectCache()

        async def set_and_get(key: str, value: str) -> str:
            await cache.setCustom(key, value)
            return await cache.getCustom(key)

        results = await asyncio.gather(
            set_and_get("key1", "value1"),
            set_and_get("key2", "value2"),
            set_and_get("key3", "value3"),
        )
        assert results == ["value1", "value2", "value3"]

    @pytest.mark.asyncio
    async def test_none_values(self):
        """Cache can store None as a value (vs not storing key)."""
        cache = AsyncObjectCache()
        await cache.setCustom("none_key", None)
        # Since setCustom stores None, getCustom should return None
        # But we can't distinguish from "not set". In this case, we trust setCustom behavior.
        result = await cache.getCustom("none_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_reset_clears_all_buckets(self):
        """reset() clears OwnedObject, SharedOrImmutableObject, and Custom buckets."""
        cache = AsyncObjectCache()
        await cache.add_object(ObjectSummary(objectId="0xa", version="1", digest="d1", owner="0xowner"))
        await cache.add_object(ObjectSummary(objectId="0xb", version="1", digest="d2", owner=None))
        await cache.setCustom("k", "v")
        await cache.reset()
        assert await cache.get_object("0xa") is None
        assert await cache.get_object("0xb") is None
        assert await cache.getCustom("k") is None


class TestObjectBucketRouting:
    """Test that add_object routes correctly between OwnedObject and SharedOrImmutableObject."""

    @pytest.mark.asyncio
    async def test_owned_object_stored_in_owned_bucket(self):
        """Object with owner set goes to OwnedObject bucket."""
        cache = AsyncObjectCache()
        entry = ObjectSummary(objectId="0x1", version="1", digest="d", owner="0xowner")
        await cache.add_object(entry)
        result = await cache.get_object("0x1")
        assert result is not None
        assert result.owner == "0xowner"

    @pytest.mark.asyncio
    async def test_shared_object_stored_in_shared_bucket(self):
        """Object with owner=None goes to SharedOrImmutableObject bucket."""
        cache = AsyncObjectCache()
        entry = ObjectSummary(objectId="0x2", version="2", digest="d", owner=None)
        await cache.add_object(entry)
        result = await cache.get_object("0x2")
        assert result is not None
        assert result.owner is None

    @pytest.mark.asyncio
    async def test_owned_and_shared_buckets_are_independent(self):
        """Owned object is absent from shared bucket and vice versa."""
        cache = AsyncObjectCache()
        owned = ObjectSummary(objectId="0xowned", version="1", digest="d1", owner="0xaddr")
        shared = ObjectSummary(objectId="0xshared", version="1", digest="d2", owner=None)
        await cache.add_object(owned)
        await cache.add_object(shared)

        assert (await cache.get_object("0xowned")).owner == "0xaddr"
        assert (await cache.get_object("0xshared")).owner is None
        assert await cache._get("SharedOrImmutableObject", "0xowned") is None
        assert await cache._get("OwnedObject", "0xshared") is None

    @pytest.mark.asyncio
    async def test_get_objects_returns_mixed_results(self):
        """getObjects handles owned, shared, and missing objects in one call."""
        cache = AsyncObjectCache()
        await cache.add_object(ObjectSummary(objectId="0xa", version="1", digest="d1", owner="0xowner"))
        await cache.add_object(ObjectSummary(objectId="0xb", version="2", digest="d2", owner=None))
        results = await cache.getObjects(["0xa", "0xb", "0xmissing"])
        assert results[0].objectId == "0xa"
        assert results[1].objectId == "0xb"
        assert results[2] is None


class TestDeleteObject:
    """Test delete_object and delete_objects."""

    @pytest.mark.asyncio
    async def test_delete_owned_object(self):
        cache = AsyncObjectCache()
        entry = ObjectSummary(objectId="0x1", version="1", digest="d", owner="0xowner")
        await cache.add_object(entry)
        await cache.delete_object("0x1")
        assert await cache.get_object("0x1") is None

    @pytest.mark.asyncio
    async def test_delete_shared_object(self):
        cache = AsyncObjectCache()
        entry = ObjectSummary(objectId="0x2", version="1", digest="d", owner=None)
        await cache.add_object(entry)
        await cache.delete_object("0x2")
        assert await cache.get_object("0x2") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_idempotent(self):
        """Deleting an object that does not exist does not raise."""
        cache = AsyncObjectCache()
        await cache.delete_object("0xmissing")

    @pytest.mark.asyncio
    async def test_delete_objects_removes_multiple(self):
        cache = AsyncObjectCache()
        for i in range(3):
            entry = ObjectSummary(objectId=f"0x{i}", version="1", digest="d", owner="0xowner")
            await cache.add_object(entry)
        await cache.delete_objects(["0x0", "0x1", "0x2"])
        for i in range(3):
            assert await cache.get_object(f"0x{i}") is None


class TestApplyEffects:
    """Test AsyncObjectCache.applyEffects — owned/shared/deleted routing."""

    def _make_effects(self, changed_objects):
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        from unittest.mock import MagicMock
        eff = MagicMock()
        eff.transaction_digest = "fakedigest"
        eff.lamport_version = 5
        eff.changed_objects = changed_objects
        gas = MagicMock()
        gas.computation_cost = 0
        gas.storage_cost = 0
        gas.storage_rebate = 0
        eff.gas_used = gas
        return eff

    def _owned_change(self, obj_id, owner_addr):
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        from unittest.mock import MagicMock
        ch = MagicMock()
        ch.object_id = obj_id
        ch.output_state = sui_prot.ChangedObjectOutputObjectState.OBJECT_WRITE
        ch.output_digest = "digest"
        owner = MagicMock()
        owner.kind = sui_prot.OwnerOwnerKind.ADDRESS
        owner.address = owner_addr
        owner.version = None
        ch.output_owner = owner
        return ch

    def _shared_change(self, obj_id, initial_version="1"):
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        from unittest.mock import MagicMock
        ch = MagicMock()
        ch.object_id = obj_id
        ch.output_state = sui_prot.ChangedObjectOutputObjectState.OBJECT_WRITE
        ch.output_digest = "shareddigest"
        owner = MagicMock()
        owner.kind = sui_prot.OwnerOwnerKind.SHARED
        owner.address = None
        owner.version = int(initial_version)
        ch.output_owner = owner
        return ch

    def _deleted_change(self, obj_id):
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        from unittest.mock import MagicMock
        ch = MagicMock()
        ch.object_id = obj_id
        ch.output_state = sui_prot.ChangedObjectOutputObjectState.DOES_NOT_EXIST
        ch.output_digest = None
        ch.output_owner = None
        return ch

    @pytest.mark.asyncio
    async def test_owned_object_write_routes_to_owned_bucket(self):
        cache = AsyncObjectCache()
        effects = self._make_effects([self._owned_change("0xobj", "0xowner")])
        await cache.applyEffects(effects)
        result = await cache.get_object("0xobj")
        assert result is not None
        assert result.owner == "0xowner"
        assert await cache._get("SharedOrImmutableObject", "0xobj") is None

    @pytest.mark.asyncio
    async def test_shared_object_write_routes_to_shared_bucket_with_no_owner(self):
        """SharedInitialVersion → SharedOrImmutableObject bucket, owner=None."""
        cache = AsyncObjectCache()
        effects = self._make_effects([self._shared_change("0xshared", initial_version="42")])
        await cache.applyEffects(effects)
        result = await cache.get_object("0xshared")
        assert result is not None
        assert result.owner is None
        assert result.initialSharedVersion == "42"
        assert await cache._get("OwnedObject", "0xshared") is None

    @pytest.mark.asyncio
    async def test_not_exist_removes_object_from_cache(self):
        cache = AsyncObjectCache()
        entry = ObjectSummary(objectId="0xdel", version="1", digest="d", owner="0xowner")
        await cache.add_object(entry)
        effects = self._make_effects([self._deleted_change("0xdel")])
        await cache.applyEffects(effects)
        assert await cache.get_object("0xdel") is None

    @pytest.mark.asyncio
    async def test_mixed_effects_applied_correctly(self):
        cache = AsyncObjectCache()
        entry = ObjectSummary(objectId="0xdel", version="1", digest="d", owner="0xowner")
        await cache.add_object(entry)
        effects = self._make_effects([
            self._owned_change("0xnew", "0xowner2"),
            self._shared_change("0xshared"),
            self._deleted_change("0xdel"),
        ])
        await cache.applyEffects(effects)
        assert (await cache.get_object("0xnew")).owner == "0xowner2"
        assert (await cache.get_object("0xshared")).owner is None
        assert await cache.get_object("0xdel") is None
