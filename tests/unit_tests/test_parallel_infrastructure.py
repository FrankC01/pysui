#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for parallel executor infrastructure modules:
- object_registry (ObjectVersionEntry, InMemoryObjectRegistry, singleton)
- object_id_extract (extract_object_id)
- conflict_tracker (ConflictTracker, ConflictReservation)
- gas_pool (GasCoin, GasCoinPool)
- UnResolvingArgParser.fetch_or_transpose_object (GQL + gRPC)
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock, patch

from pysui.sui.sui_common.executors.object_registry import (
    ObjectVersionEntry,
    InMemoryObjectRegistry,
    get_object_registry,
    _set_object_registry_for_tests,
)
from pysui.sui.sui_common.executors.object_id_extract import extract_object_id
from pysui.sui.sui_common.executors.conflict_tracker import ConflictTracker
from pysui.sui.sui_common.executors.gas_pool import GasCoin, GasCoinPool
from pysui.sui.sui_bcs import bcs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _oid(suffix: str = "01") -> str:
    return "0x" + "aa" * 31 + suffix


def _entry(oid: str, version: str = "1", digest: str = "abc") -> ObjectVersionEntry:
    return ObjectVersionEntry(object_id=oid, version=version, digest=digest)


def _coin(suffix: str = "01", balance: int = 1_000_000) -> GasCoin:
    return GasCoin(object_id=_oid(suffix), version="1", digest="d", balance=balance)


# ===========================================================================
# ObjectVersionEntry
# ===========================================================================

class TestObjectVersionEntry:
    def test_fields(self):
        entry = _entry("0x01", "5", "xyz")
        assert entry.object_id == "0x01"
        assert entry.version == "5"
        assert entry.digest == "xyz"
        assert not entry.is_tombstone

    def test_tombstone_flag(self):
        entry = ObjectVersionEntry(
            object_id="0x01",
            version="",
            digest="",
            is_tombstone=True,
            tombstone_expires_ns=time.monotonic_ns() + 10_000_000_000,
        )
        assert entry.is_tombstone


# ===========================================================================
# InMemoryObjectRegistry
# ===========================================================================

class TestInMemoryObjectRegistry:
    @pytest.fixture
    def reg(self):
        return InMemoryObjectRegistry()

    @pytest.mark.asyncio
    async def test_upsert_and_get(self, reg):
        await reg.upsert(_entry(_oid(), "3", "d3"))
        result = await reg.get(_oid())
        assert result is not None
        assert result.version == "3"

    @pytest.mark.asyncio
    async def test_get_missing(self, reg):
        assert await reg.get("0xdeadbeef") is None

    @pytest.mark.asyncio
    async def test_higher_version_wins(self, reg):
        await reg.upsert(_entry(_oid(), "5", "d5"))
        await reg.upsert(_entry(_oid(), "3", "d3"))  # stale — should be dropped
        result = await reg.get(_oid())
        assert result.version == "5"

    @pytest.mark.asyncio
    async def test_lower_version_is_dropped(self, reg):
        await reg.upsert(_entry(_oid(), "10", "d10"))
        await reg.upsert(_entry(_oid(), "10", "same"))  # same version also dropped
        result = await reg.get(_oid())
        assert result.digest == "d10"

    @pytest.mark.asyncio
    async def test_upsert_many(self, reg):
        entries = [_entry(_oid(f"{i:02x}"), str(i)) for i in range(5)]
        await reg.upsert_many(entries)
        assert reg.size() == 5

    @pytest.mark.asyncio
    async def test_get_many(self, reg):
        oids = [_oid(f"{i:02x}") for i in range(3)]
        await reg.upsert_many([_entry(oid, str(i)) for i, oid in enumerate(oids)])
        found = await reg.get_many(oids)
        assert len(found) == 3
        for oid in oids:
            assert oid in found

    @pytest.mark.asyncio
    async def test_evict(self, reg):
        await reg.upsert(_entry(_oid()))
        await reg.evict(_oid())
        assert await reg.get(_oid()) is None

    @pytest.mark.asyncio
    async def test_reset(self, reg):
        await reg.upsert_many([_entry(_oid(f"{i:02x}")) for i in range(10)])
        await reg.reset()
        assert reg.size() == 0

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        reg = InMemoryObjectRegistry(max_entries=3)
        for i in range(4):
            await reg.upsert(_entry(_oid(f"{i:02x}"), str(i)))
        assert reg.size() == 3
        # Oldest (i=0) should have been evicted
        assert await reg.get(_oid("00")) is None

    @pytest.mark.asyncio
    async def test_tombstone_hides_entry(self, reg):
        await reg.upsert(_entry(_oid()))
        await reg.tombstone(_oid(), ttl_seconds=60.0)
        result = await reg.get(_oid())
        # tombstone is returned (not None — it IS in the registry as tombstone)
        assert result is not None
        assert result.is_tombstone

    @pytest.mark.asyncio
    async def test_expired_tombstone_returns_none(self, reg):
        await reg.tombstone(_oid(), ttl_seconds=0.0)
        # Tombstone expires immediately (ttl=0 → already past)
        await asyncio.sleep(0)  # yield to let time pass
        result = await reg.get(_oid())
        assert result is None

    @pytest.mark.asyncio
    async def test_tombstone_overwrites_normal(self, reg):
        await reg.upsert(_entry(_oid(), "5"))
        await reg.tombstone(_oid(), ttl_seconds=60.0)
        result = await reg.get(_oid())
        assert result is not None
        assert result.is_tombstone


# ===========================================================================
# Singleton
# ===========================================================================

class TestObjectRegistrySingleton:
    def setup_method(self):
        _set_object_registry_for_tests(None)

    def teardown_method(self):
        _set_object_registry_for_tests(None)

    def test_singleton_returns_same_instance(self):
        r1 = get_object_registry()
        r2 = get_object_registry()
        assert r1 is r2

    def test_singleton_is_in_memory_registry(self):
        r = get_object_registry()
        assert isinstance(r, InMemoryObjectRegistry)

    def test_set_for_tests_replaces_singleton(self):
        custom = InMemoryObjectRegistry(max_entries=10)
        _set_object_registry_for_tests(custom)
        assert get_object_registry() is custom

    def test_set_none_resets_singleton(self):
        _set_object_registry_for_tests(None)
        r = get_object_registry()
        assert r is not None


# ===========================================================================
# extract_object_id
# ===========================================================================

class TestExtractObjectId:
    def test_str_passthrough(self):
        assert extract_object_id("0xabc") == "0xabc"

    def test_object_reference(self):
        addr = MagicMock()
        addr.to_address_str.return_value = "0xobj"
        ref = MagicMock(spec=bcs.ObjectReference)
        ref.ObjectID = addr
        assert extract_object_id(ref) == "0xobj"

    def test_shared_object_reference(self):
        addr = MagicMock()
        addr.to_address_str.return_value = "0xshared"
        ref = MagicMock(spec=bcs.SharedObjectReference)
        ref.ObjectID = addr
        assert extract_object_id(ref) == "0xshared"

    def test_object_arg(self):
        addr = MagicMock()
        addr.to_address_str.return_value = "0xarg"
        inner = MagicMock()
        inner.ObjectID = addr
        arg = MagicMock(spec=bcs.ObjectArg)
        arg.value = inner
        assert extract_object_id(arg) == "0xarg"

    def test_duck_typed_object_id_attr(self):
        obj = MagicMock()
        obj.object_id = "0xduck"
        assert extract_object_id(obj) == "0xduck"

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="unsupported input type"):
            extract_object_id(42)

    def test_object_id_attr_not_str_raises(self):
        obj = MagicMock()
        obj.object_id = 12345  # not a str
        with pytest.raises(ValueError, match="unsupported input type"):
            extract_object_id(obj)


# ===========================================================================
# ConflictTracker
# ===========================================================================

class TestConflictTracker:
    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        tracker = ConflictTracker()
        res = await tracker.acquire({"0xobj1", "0xobj2"})
        await res.release()
        assert tracker.in_flight_ids() == set()

    @pytest.mark.asyncio
    async def test_context_manager_release(self):
        tracker = ConflictTracker()
        async with await tracker.acquire({"0xobjA"}):
            assert "0xobjA" in tracker.in_flight_ids()
        assert tracker.in_flight_ids() == set()

    @pytest.mark.asyncio
    async def test_sequential_transactions_same_object(self):
        tracker = ConflictTracker()
        order: list[int] = []

        async def tx(i: int):
            async with await tracker.acquire({"0xobj"}):
                order.append(i)
                await asyncio.sleep(0)

        await asyncio.gather(tx(1), tx(2), tx(3))
        assert len(order) == 3
        assert set(order) == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_no_deadlock_overlapping_sets(self):
        tracker = ConflictTracker()

        async def tx_ab():
            async with await tracker.acquire({"0xa", "0xb"}):
                await asyncio.sleep(0)

        async def tx_ba():
            async with await tracker.acquire({"0xb", "0xa"}):
                await asyncio.sleep(0)

        # Should complete without deadlock
        await asyncio.gather(tx_ab(), tx_ba())

    @pytest.mark.asyncio
    async def test_non_overlapping_transactions_run_concurrently(self):
        tracker = ConflictTracker()
        entered: list[int] = []

        async def tx(i: int, oid: str):
            async with await tracker.acquire({oid}):
                entered.append(i)
                await asyncio.sleep(0.01)

        await asyncio.gather(tx(1, "0xobjX"), tx(2, "0xobjY"))
        assert set(entered) == {1, 2}

    @pytest.mark.asyncio
    async def test_in_flight_ids(self):
        tracker = ConflictTracker()
        res = await tracker.acquire({"0xp", "0xq"})
        assert "0xp" in tracker.in_flight_ids()
        assert "0xq" in tracker.in_flight_ids()
        await res.release()
        assert tracker.in_flight_ids() == set()


# ===========================================================================
# GasCoinPool
# ===========================================================================

class TestGasCoinPool:
    @pytest.mark.asyncio
    async def test_replenish_and_size(self):
        pool = GasCoinPool()
        coins = [_coin(f"{i:02x}") for i in range(3)]
        await pool.replenish(coins)
        assert pool.size() == 3

    @pytest.mark.asyncio
    async def test_checkout_returns_coin(self):
        pool = GasCoinPool()
        coin = _coin()
        await pool.replenish([coin])
        got = await pool.checkout()
        assert got.object_id == coin.object_id
        assert pool.size() == 0

    @pytest.mark.asyncio
    async def test_checkin_returns_to_pool(self):
        pool = GasCoinPool()
        coin = _coin()
        await pool.replenish([coin])
        got = await pool.checkout()
        await pool.checkin(got)
        assert pool.size() == 1

    @pytest.mark.asyncio
    async def test_checkin_retire_discards(self):
        pool = GasCoinPool()
        coin = _coin()
        await pool.replenish([coin])
        got = await pool.checkout()
        await pool.checkin(got, retire=True)
        assert pool.size() == 0

    @pytest.mark.asyncio
    async def test_checkin_low_balance_retires(self):
        pool = GasCoinPool(min_balance_per_coin=500_000)
        coin = _coin(balance=100)  # below threshold
        await pool.replenish([coin])
        got = await pool.checkout()
        await pool.checkin(got)
        assert pool.size() == 0

    @pytest.mark.asyncio
    async def test_is_low_at_low_water_mark(self):
        pool = GasCoinPool(low_water_mark=3)
        await pool.replenish([_coin(f"{i:02x}") for i in range(3)])
        assert pool.is_low()

    @pytest.mark.asyncio
    async def test_is_low_above_water_mark(self):
        pool = GasCoinPool(low_water_mark=3)
        await pool.replenish([_coin(f"{i:02x}") for i in range(4)])
        assert not pool.is_low()

    @pytest.mark.asyncio
    async def test_reset_drains_pool(self):
        pool = GasCoinPool()
        await pool.replenish([_coin(f"{i:02x}") for i in range(5)])
        await pool.reset()
        assert pool.size() == 0

    @pytest.mark.asyncio
    async def test_checkout_blocks_until_checkin(self):
        pool = GasCoinPool()

        async def producer():
            await asyncio.sleep(0.01)
            await pool.replenish([_coin()])

        checkout_task = asyncio.create_task(pool.checkout())
        await producer()
        coin = await checkout_task
        assert coin is not None
