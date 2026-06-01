#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Transaction execution queues."""

import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented

T = TypeVar("T")
logger = logging.getLogger(__name__)
# Note: do not call logger.setLevel here — the host application controls log levels.


class SerialQueue:
    """Queue for serial (sequential) task execution."""

    @sync_instrumented("pysui.sui.sui_common.executors.queue.SerialQueue.__init__")
    def __init__(self):
        self._lock = asyncio.Lock()

    @instrumented("pysui.sui.sui_common.executors.queue.SerialQueue.run_task")
    async def run_task(self, task: Callable[[], T]) -> T:
        """Run a task serially under the queue lock.

        :param task: A zero-arg callable that returns a coroutine or value.
            Pass a lambda or functools.partial — do NOT pass a coroutine object.
        :type task: Callable[[], T]
        :return: The result of the task
        :raises TypeError: If a coroutine object is passed instead of a callable
        """
        if asyncio.iscoroutine(task):
            raise TypeError(
                "SerialQueue.run_task expects a zero-arg callable, not a coroutine. "
                "Pass a lambda (e.g. lambda: my_coro()) instead of my_coro()."
            )
        async with self._lock:
            logger.debug("Running task %s", task)
            try:
                result = task()
                if asyncio.iscoroutine(result):
                    result = await result
                logger.debug("Task %s completed", task)
                return result
            except Exception as e:
                logger.debug("Task %s failed: %s", task, e)
                raise


class ParallelQueue:
    """Queue for parallel task execution with max concurrency."""

    @sync_instrumented("pysui.sui.sui_common.executors.queue.ParallelQueue.__init__")
    def __init__(self, max_tasks: int = 4):
        """Initialize parallel queue.

        :param max_tasks: Maximum concurrent tasks, defaults to 4
        """
        self._semaphore = asyncio.Semaphore(max_tasks)

    @instrumented("pysui.sui.sui_common.executors.queue.ParallelQueue.run_task")
    async def run_task(self, task: Callable[[], T]) -> T:
        """Run a task with concurrency control.

        :param task: A zero-arg callable that returns a coroutine or value
        :type task: Callable[[], T]
        :return: The result of the task
        :raises TypeError: If a coroutine object is passed instead of a callable
        """
        if asyncio.iscoroutine(task):
            raise TypeError(
                "ParallelQueue.run_task expects a zero-arg callable, not a coroutine."
            )
        async with self._semaphore:
            logger.debug("Running task %s", task)
            try:
                result = task()
                if asyncio.iscoroutine(result):
                    result = await result
                logger.debug("Task %s completed", task)
                return result
            except Exception as e:
                logger.debug("Task %s failed: %s", task, e)
                raise


if __name__ == "__main__":

    @instrumented("pysui.sui.sui_common.executors.queue.test")
    async def test():
        ser = SerialQueue()

        @instrumented("pysui.sui.sui_common.executors.queue.sample_task")
        async def sample_task(n):
            await asyncio.sleep(0.01)
            return n * 2

        results = await asyncio.gather(
            ser.run_task(lambda: sample_task(1)),
            ser.run_task(lambda: sample_task(2)),
            ser.run_task(lambda: sample_task(3)),
        )
        print(f"Results: {results}")

    try:
        asyncio.run(test())
    except ValueError as ve:
        print(ve)
