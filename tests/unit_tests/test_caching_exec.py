#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for GqlCachingTransactionExecutor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_pgql.execute.caching_exec import GqlCachingTransactionExecutor
from pysui.sui.sui_common.executors.cache import AsyncObjectCache, ObjectCacheEntry


class TestGqlCachingTransactionExecutorStructure:
    """Verify class structure and construction."""

    def test_class_importable(self):
        assert GqlCachingTransactionExecutor is not None

    def test_init_signature_has_client_and_gas_owner(self):
        import inspect
        sig = inspect.signature(GqlCachingTransactionExecutor.__init__)
        assert "client" in sig.parameters
        assert "gas_owner" in sig.parameters

    def test_instance_has_cache_attribute(self):
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0x123")
        assert isinstance(executor.cache, AsyncObjectCache)

    def test_instance_has_required_public_methods(self):
        for method in ("reset", "build_transaction", "execute_transaction",
                       "apply_effects", "update_gas_coins", "invalidate_gas_coins",
                       "get_sui_objects"):
            assert hasattr(GqlCachingTransactionExecutor, method)


class TestGasCoinCacheBehavior:
    """Behavioral tests for gas coin cache operations."""

    @pytest.mark.asyncio
    async def test_update_gas_coins_stores_in_cache(self):
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        fake_coins = [MagicMock(), MagicMock()]
        await executor.update_gas_coins(fake_coins)
        cached = await executor.cache.getCustom("gasCoins")
        assert cached == fake_coins

    @pytest.mark.asyncio
    async def test_invalidate_gas_coins_removes_from_cache(self):
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        fake_coins = [MagicMock()]
        await executor.update_gas_coins(fake_coins)
        await executor.invalidate_gas_coins()
        cached = await executor.cache.getCustom("gasCoins")
        assert cached is None

    @pytest.mark.asyncio
    async def test_update_then_invalidate_then_update_cycle(self):
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        coins_a = [MagicMock()]
        coins_b = [MagicMock(), MagicMock()]
        await executor.update_gas_coins(coins_a)
        await executor.invalidate_gas_coins()
        await executor.update_gas_coins(coins_b)
        cached = await executor.cache.getCustom("gasCoins")
        assert cached == coins_b


class TestResetBehavior:
    """Behavioral tests for reset()."""

    @pytest.mark.asyncio
    async def test_reset_clears_owned_objects(self):
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        # Plant an object in the owned bucket
        entry = ObjectCacheEntry(objectId="0x1", version="1", digest="d", owner="0xabc")
        await executor.cache.add_object(entry)
        await executor.reset()
        cached = await executor.cache.get_object("0x1")
        assert cached is None

    @pytest.mark.asyncio
    async def test_reset_clears_custom_keys(self):
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        await executor.update_gas_coins([MagicMock()])
        await executor.reset()
        cached = await executor.cache.getCustom("gasCoins")
        assert cached is None


class TestApplyEffectsBehavior:
    """Behavioral tests for apply_effects()."""

    @pytest.mark.asyncio
    async def test_apply_effects_delegates_to_cache(self):
        from pysui.sui.sui_common.types import TransactionEffects, ExecutionStatus, GasCostSummary
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        effects = TransactionEffects(
            transaction_digest="digest_abc",
            status=ExecutionStatus(success=True),
            gas_used=GasCostSummary(
                computation_cost=1000,
                storage_cost=500,
                storage_rebate=200,
            ),
            lamport_version=1,
            changed_objects=[],
        )
        with patch.object(executor.cache, "applyEffects", new=AsyncMock()) as mock_apply:
            await executor.apply_effects(effects)
        mock_apply.assert_called_once_with(effects)

    @pytest.mark.asyncio
    async def test_apply_effects_sets_last_digest(self):
        from pysui.sui.sui_common.types import TransactionEffects, ExecutionStatus, GasCostSummary
        executor = GqlCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        effects = TransactionEffects(
            transaction_digest="digest_xyz",
            status=ExecutionStatus(success=True),
            gas_used=GasCostSummary(
                computation_cost=1000,
                storage_cost=500,
                storage_rebate=200,
            ),
            lamport_version=1,
            changed_objects=[],
        )
        with patch.object(executor.cache, "applyEffects", new=AsyncMock()):
            await executor.apply_effects(effects)
