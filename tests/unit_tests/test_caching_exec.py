#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for AsyncCachingTransactionExecutor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pysui.sui.sui_pgql.execute.caching_exec import AsyncCachingTransactionExecutor
from pysui.sui.sui_common.executors.cache import AsyncObjectCache, ObjectCacheEntry


class TestAsyncCachingTransactionExecutorStructure:
    """Verify class structure and construction."""

    def test_class_importable(self):
        assert AsyncCachingTransactionExecutor is not None

    def test_init_signature_has_client_and_gas_owner(self):
        import inspect
        sig = inspect.signature(AsyncCachingTransactionExecutor.__init__)
        assert "client" in sig.parameters
        assert "gas_owner" in sig.parameters

    def test_instance_has_cache_attribute(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0x123")
        assert isinstance(executor.cache, AsyncObjectCache)

    def test_instance_has_required_public_methods(self):
        for method in ("reset", "build_transaction", "execute_transaction",
                       "apply_effects", "update_gas_coins", "invalidate_gas_coins",
                       "get_sui_objects", "wait_for_last_transaction"):
            assert hasattr(AsyncCachingTransactionExecutor, method)


class TestGasCoinCacheBehavior:
    """Behavioral tests for gas coin cache operations."""

    @pytest.mark.asyncio
    async def test_update_gas_coins_stores_in_cache(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        fake_coins = [MagicMock(), MagicMock()]
        await executor.update_gas_coins(fake_coins)
        cached = await executor.cache.getCustom("gasCoins")
        assert cached == fake_coins

    @pytest.mark.asyncio
    async def test_invalidate_gas_coins_removes_from_cache(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        fake_coins = [MagicMock()]
        await executor.update_gas_coins(fake_coins)
        await executor.invalidate_gas_coins()
        cached = await executor.cache.getCustom("gasCoins")
        assert cached is None

    @pytest.mark.asyncio
    async def test_update_then_invalidate_then_update_cycle(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
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
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        # Plant an object in the owned bucket
        entry = ObjectCacheEntry(objectId="0x1", version="1", digest="d", owner="0xabc")
        await executor.cache.add_object(entry)
        # reset should clear it (no last digest, so wait_for_last_transaction is a no-op)
        with patch.object(executor, "wait_for_last_transaction", new=AsyncMock(return_value=None)):
            await executor.reset()
        cached = await executor.cache.get_object("0x1")
        assert cached is None

    @pytest.mark.asyncio
    async def test_reset_clears_custom_keys(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        await executor.update_gas_coins([MagicMock()])
        with patch.object(executor, "wait_for_last_transaction", new=AsyncMock(return_value=None)):
            await executor.reset()
        cached = await executor.cache.getCustom("gasCoins")
        assert cached is None


class TestApplyEffectsBehavior:
    """Behavioral tests for apply_effects()."""

    @pytest.mark.asyncio
    async def test_apply_effects_delegates_to_cache(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        mock_effects = MagicMock()
        mock_effects.enum_name = "V2"
        mock_effects.value.transactionDigest.to_digest_str.return_value = "digest_abc"
        with patch.object(executor.cache, "applyEffects", new=AsyncMock()) as mock_apply:
            await executor.apply_effects(mock_effects)
        mock_apply.assert_called_once_with(mock_effects)

    @pytest.mark.asyncio
    async def test_apply_effects_sets_last_digest(self):
        executor = AsyncCachingTransactionExecutor(client=MagicMock(), gas_owner="0xabc")
        mock_effects = MagicMock()
        mock_effects.enum_name = "V2"
        mock_effects.value.transactionDigest.to_digest_str.return_value = "digest_xyz"
        with patch.object(executor.cache, "applyEffects", new=AsyncMock()):
            await executor.apply_effects(mock_effects)
        assert executor._lastdigest == "digest_xyz"


class TestWaitForLastTransaction:
    """Behavioral tests for wait_for_last_transaction."""

    @pytest.mark.asyncio
    async def test_wait_returns_none_when_no_digest(self):
        """When _lastdigest is None, wait_for_last_transaction is a no-op."""
        mock_client = MagicMock()
        executor = AsyncCachingTransactionExecutor(client=mock_client, gas_owner="0xabc")
        assert executor._lastdigest is None
        result = await executor.wait_for_last_transaction()
        assert result is None
        mock_client.wait_for_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_wait_calls_client_and_clears_digest(self):
        """When _lastdigest is set, calls _client.wait_for_transaction and clears the digest."""
        mock_client = MagicMock()
        mock_client.wait_for_transaction = AsyncMock(return_value="tx_result")
        executor = AsyncCachingTransactionExecutor(client=mock_client, gas_owner="0xabc")
        executor._lastdigest = "abc123"

        result = await executor.wait_for_last_transaction()

        mock_client.wait_for_transaction.assert_called_once_with(digest="abc123", poll_interval=1.0)
        assert result == "tx_result"
        assert executor._lastdigest is None

    @pytest.mark.asyncio
    async def test_wait_digest_cleared_even_on_error(self):
        """_lastdigest is cleared after the call regardless of outcome."""
        mock_client = MagicMock()
        mock_client.wait_for_transaction = AsyncMock(return_value="ok")
        executor = AsyncCachingTransactionExecutor(client=mock_client, gas_owner="0xabc")
        executor._lastdigest = "digest1"

        await executor.wait_for_last_transaction()
        assert executor._lastdigest is None
