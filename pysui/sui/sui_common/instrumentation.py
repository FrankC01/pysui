#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui performance instrumentation — collector interface and ContextVar plumbing."""

from __future__ import annotations
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Optional, AsyncIterator, Iterator, Callable, Any

_collector_var: ContextVar = ContextVar("_pysui_collector", default=None)


class InstrumentationCollector:
    """Base collector — override measure() to record timings.

    Default implementation is a no-op; subclass and override measure()
    to capture elapsed time for each labeled code block.
    """

    @asynccontextmanager
    async def measure(self, label: str) -> AsyncIterator[None]:
        """No-op by default. Override to time the wrapped block."""
        yield

    @contextmanager
    def sync_measure(self, label: str) -> Iterator[None]:
        """No-op by default. Override to time the wrapped sync block."""
        yield

    def count(self, label: str) -> None:
        """No-op by default. Override to tally occurrences of a labeled event.

        Counts are deliberately separate from timings: an occurrence has no duration,
        and routing one through measure() would put zero-length entries into timing
        summaries.
        """


@asynccontextmanager
async def active_collector(
    collector: Optional[InstrumentationCollector],
) -> AsyncIterator[Optional[InstrumentationCollector]]:
    """Activate collector for the current async context and all callees.

    Usage::

        async with active_collector(DictCollector()) as col:
            await txn.build_and_sign()
        print(col.summary())

    Passing None is a no-op — it leaves whatever collector (or lack of one) is
    already active for the current context unchanged. This lets a caller that
    captured ``get_collector()`` at an earlier point (where no collector may
    have been active) re-activate it later without a separate branch.
    """
    if collector is None:
        yield None
        return
    token = _collector_var.set(collector)
    try:
        yield collector
    finally:
        _collector_var.reset(token)


def get_collector() -> Optional[InstrumentationCollector]:
    """Return the active collector for the current async context, or None."""
    return _collector_var.get()


@asynccontextmanager
async def measure(label: str) -> AsyncIterator[None]:
    """Hook point: time label if a collector is active; no-op otherwise."""
    col: Optional[InstrumentationCollector] = _collector_var.get()
    if col is not None:
        async with col.measure(label):
            yield
    else:
        yield


@contextmanager
def sync_measure(label: str) -> Iterator[None]:
    """Hook point: time label synchronously if a collector is active; no-op otherwise."""
    col: Optional[InstrumentationCollector] = _collector_var.get()
    if col is not None:
        with col.sync_measure(label):
            yield
    else:
        yield


def count(label: str) -> None:
    """Hook point: tally one occurrence of label if a collector is active; no-op otherwise."""
    col: Optional[InstrumentationCollector] = _collector_var.get()
    if col is not None:
        col.count(label)


def instrumented(label: str) -> Callable:
    """Decorator: wrap an async method with a measure(label) hook."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            col: Optional[InstrumentationCollector] = _collector_var.get()
            if col is not None:
                async with col.measure(label):
                    return await fn(*args, **kwargs)
            return await fn(*args, **kwargs)

        return wrapper

    return decorator


def sync_instrumented(label: str) -> Callable:
    """Decorator: wrap a sync method with a sync_measure(label) hook."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            col: Optional[InstrumentationCollector] = _collector_var.get()
            if col is not None:
                with col.sync_measure(label):
                    return fn(*args, **kwargs)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
