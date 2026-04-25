#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Per-object FIFO conflict tracker for parallel executor serialization."""

import asyncio
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ConflictReservation:
    """Holds an active conflict claim; release via async context manager or release()."""

    def __init__(self, tracker: "ConflictTracker", claimed: list[tuple[str, asyncio.Event]]) -> None:
        self._tracker = tracker
        self._claimed = claimed

    async def release(self) -> None:
        """Release the claimed conflict reservations."""
        await self._tracker._release(self._claimed)

    async def __aenter__(self) -> "ConflictReservation":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.release()


class ConflictTracker:
    """Tracks in-flight object IDs and serializes transactions that share owned objects.

    Transactions are queued FIFO per object ID. IDs are always claimed in sorted
    order to prevent deadlock when a transaction needs multiple objects.
    """

    def __init__(self) -> None:
        self._waiters: dict[str, deque[asyncio.Event]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def acquire(self, conflict_ids: set[str]) -> ConflictReservation:
        """Block until all object IDs are free, then mark them in-use.

        Sorted acquisition order prevents deadlock when transactions
        claim overlapping sets of object IDs.
        """
        claimed: list[tuple[str, asyncio.Event]] = []
        async with self._lock:
            for oid in sorted(conflict_ids):
                ev = asyncio.Event()
                q = self._waiters[oid]
                if not q:
                    ev.set()
                q.append(ev)
                claimed.append((oid, ev))

        for oid, ev in claimed:
            await ev.wait()
            logger.debug("conflict_tracker: acquired %s", oid)

        return ConflictReservation(self, claimed)

    async def _release(self, claimed: list[tuple[str, asyncio.Event]]) -> None:
        async with self._lock:
            for oid, ev in claimed:
                q = self._waiters[oid]
                if q and q[0] is ev:
                    q.popleft()
                    if q:
                        q[0].set()
                        logger.debug("conflict_tracker: released %s, waking next waiter", oid)
                    else:
                        del self._waiters[oid]
                        logger.debug("conflict_tracker: released %s, queue empty", oid)
                else:
                    try:
                        q.remove(ev)
                    except ValueError:
                        pass

    def in_flight_ids(self) -> set[str]:
        """Return the set of object IDs currently claimed by at least one transaction."""
        return set(self._waiters.keys())
