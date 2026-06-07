#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Reference DictCollector for pysui InstrumentationCollector.

Usage::

    import asyncio
    from benchmarks.dict_collector import DictCollector
    from pysui.sui.sui_common.instrumentation import active_collector

    async def main():
        collector = DictCollector()
        async with active_collector(collector):
            txn = await client.transaction()
            await txn.split_coin(...)
            await txn.build_and_sign()
        print(collector.heat_map())

    asyncio.run(main())
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from time import perf_counter_ns
from typing import AsyncIterator

from pysui.sui.sui_common.instrumentation import InstrumentationCollector


class DictCollector(InstrumentationCollector):
    """Accumulates (label, elapsed_ns) events; supports summary and heat-map output."""

    def __init__(self) -> None:
        self.events: list[tuple[str, int]] = []

    @asynccontextmanager
    async def measure(self, label: str) -> AsyncIterator[None]:
        start = perf_counter_ns()
        yield
        self.events.append((label, perf_counter_ns() - start))

    def summary(self) -> dict[str, int]:
        """Return total elapsed_ns per label (summed across repeated calls)."""
        result: dict[str, int] = {}
        for label, elapsed in self.events:
            result[label] = result.get(label, 0) + elapsed
        return result

    def heat_map(self, root: str = "ptb.build_and_sign") -> str:
        """Percentage breakdown of all labels relative to root label elapsed time."""
        totals = self.summary()
        root_ns = totals.get(root, 0)
        if not root_ns:
            return f"No measurement found for '{root}'"
        lines = [f"{root}: {root_ns / 1_000_000:.2f}ms  100.0%"]
        for label, elapsed in sorted(totals.items()):
            if label != root:
                pct = elapsed / root_ns * 100
                lines.append(f"  {label}: {elapsed / 1_000_000:.2f}ms  {pct:.1f}%")
        return "\n".join(lines)
