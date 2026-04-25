#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Gas coin pool for parallel executor coins gas mode."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GasCoin:
    """A single Sui coin object used for gas payment."""

    object_id: str
    version: str
    digest: str
    balance: int


class GasCoinPool:
    """Bounded async queue of gas coins for parallel transaction execution.

    In coins gas mode, each in-flight transaction checks out one coin
    exclusively and returns it (at its new version) after effects are applied.
    checkout() blocks if the pool is empty, providing natural back-pressure.
    """

    def __init__(
        self,
        *,
        low_water_mark: int = 5,
        min_balance_per_coin: Optional[int] = None,
    ) -> None:
        self._queue: asyncio.Queue[GasCoin] = asyncio.Queue()
        self._low_water_mark = low_water_mark
        self._min_balance_per_coin = min_balance_per_coin

    async def checkout(self) -> GasCoin:
        """Remove and return a coin from the pool, blocking if empty."""
        coin = await self._queue.get()
        logger.debug("gas_pool: checked out %s (balance=%d)", coin.object_id, coin.balance)
        return coin

    async def checkin(self, coin: GasCoin, *, retire: bool = False) -> None:
        """Return a coin to the pool after use.

        If retire=True or the coin's balance is below min_balance_per_coin,
        the coin is not returned — the caller should add it to source_coins
        for the next refill cycle.
        """
        if retire:
            logger.debug("gas_pool: retiring %s (explicit)", coin.object_id)
            return
        if self._min_balance_per_coin is not None and coin.balance < self._min_balance_per_coin:
            logger.debug("gas_pool: retiring %s (balance %d below threshold)", coin.object_id, coin.balance)
            return
        await self._queue.put(coin)
        logger.debug("gas_pool: checked in %s", coin.object_id)

    async def replenish(self, coins: list[GasCoin]) -> None:
        """Add a batch of freshly-minted coins to the pool."""
        for coin in coins:
            await self._queue.put(coin)
        logger.debug("gas_pool: replenished with %d coins (total=%d)", len(coins), self._queue.qsize())

    def size(self) -> int:
        """Current number of available coins."""
        return self._queue.qsize()

    def is_low(self) -> bool:
        """True when available coins are at or below the low-water mark."""
        return self._queue.qsize() <= self._low_water_mark

    async def reset(self) -> None:
        """Drain the pool, discarding all coins."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
