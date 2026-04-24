#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Base caching executor ABC for protocol-agnostic transaction caching."""

from abc import ABC, abstractmethod
from typing import Optional

from pysui.sui.sui_common.executors.cache import AsyncObjectCache
from pysui.sui.sui_common.types import TransactionEffects


class _BaseCachingExecutor(ABC):
    """Protocol-agnostic base for caching transaction executors."""

    def __init__(self, gas_owner: Optional[str] = None) -> None:
        self._gas_owner = gas_owner
        self.cache: AsyncObjectCache = AsyncObjectCache()

    @abstractmethod
    async def build_transaction(self, tx, signer_block, default_gas_budget: int = 50_000_000) -> str:
        """Build a transaction and return it as a base64 string."""

    async def apply_effects(self, effects: TransactionEffects) -> None:
        await self.cache.applyEffects(effects)

    async def reset(self) -> None:
        await self.cache.reset()

    async def update_gas_coins(self, coins: list[str]) -> None:
        await self.cache.setCustom("gasCoins", coins)

    async def invalidate_gas_coins(self) -> None:
        await self.cache.setCustom("gasCoins", None)
