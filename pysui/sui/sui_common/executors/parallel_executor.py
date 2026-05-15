#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Public parallel executor shell — protocol-agnostic."""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING

from pysui.sui.sui_common.executors.base_parallel_executor import _BaseParallelExecutor
from pysui.sui.sui_common.executors.exec_types import ExecutorOptions
from pysui.sui.sui_common.executors._queue_types import _SENTINEL

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction


class ParallelExecutor(_BaseParallelExecutor):
    """Parallel transaction executor.

    Obtain via ``await client.parallel_executor(options=ExecutorOptions(...))``.
    Do not instantiate directly.
    """

    def submit(self, txn: AsyncSuiTransaction | list[AsyncSuiTransaction]) -> asyncio.Future | list[asyncio.Future]:
        """Submit one or more transactions for parallel execution.

        :param txn: A single AsyncSuiTransaction or a list of them.
        :return: Single Future or list of Futures.
        """
        if isinstance(txn, list):
            return [self._submit_one(t) for t in txn]
        return self._submit_one(txn)

    async def close(self) -> None:
        """Signal shutdown and wait for all in-flight work to complete."""
        if not self._dead and not self._closing:
            self._closing = True
            self._dead = True
            self._build_queue.put_nowait(_SENTINEL)
        if self._build_task is not None:
            try:
                await self._build_task
            except asyncio.CancelledError:
                pass
        if self._in_flight:
            await asyncio.gather(*list(self._in_flight), return_exceptions=True)

    async def new_transaction(self, **kwargs):
        """Create a new DEFERRED transaction for submission to this executor."""
        return await self._new_transaction(**kwargs)

    async def add_funds(self, coins: list) -> None:
        """Add coins to the executor's gas state (on_balance_low response handler)."""
        await self._add_funds(coins)
