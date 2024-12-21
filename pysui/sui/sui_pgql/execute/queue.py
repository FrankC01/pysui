#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Transaction execution queues."""

import asyncio
import logging
from functools import partial
import inspect
from typing import Any, Callable, TypeVar, List

T = TypeVar("T")
logger = logging.getLogger("queue")
logger.setLevel(logging.DEBUG)


async def _non_async(task: Callable[[Any], None]) -> Any:
    """."""
    return task()


class SerialQueue:
    def __init__(self):
        self._queue: List[Callable[[Any], None]] = []

    async def run_task(self, task: Callable[[Any], asyncio.Future[T]]) -> T:
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        task = task if inspect.isawaitable(task) else partial(_non_async, task)

        logger.debug(f"run_task queing {task}")
        self._queue.append(
            lambda: asyncio.ensure_future(task()).add_done_callback(
                lambda f: self._process_queue(f, future)
            )
        )

        if len(self._queue) == 1:
            logger.debug(f"run_task running {self._queue[0]}")
            self._queue[0]()

        logger.debug(f"run_task returning {future}")
        return await future

    def _process_queue(self, future: asyncio.Future, main_future: asyncio.Future):
        logger.debug(f"_process_queue result {future}")
        try:
            result = future.result()
            main_future.set_result(result)
        except Exception as e:
            main_future.set_exception(e)
        finally:
            self._queue.pop(0)
            if self._queue:
                logger.debug(f"_process_queue running {self._queue[0]}")
                self._queue[0]()


class ParallelQueue:
    def __init__(self, max_tasks: int):
        self._queue: List[Callable[[], None]] = []
        self.active_tasks = 0
        self.max_tasks = max_tasks

    async def run_task(self, task: Callable[[], asyncio.Future[T]]) -> T:
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        if self.active_tasks < self.max_tasks:
            self.active_tasks += 1

            try:
                result = await task()
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                if self._queue:
                    next_task = self._queue.pop(0)
                    loop.create_task(next_task())
                else:
                    self.active_tasks -= 1
        else:
            self._queue.append(lambda: self.run_task(task))
            return await future


if __name__ == "__main__":

    def doit(arg) -> Any:
        print(arg)
        return arg

    async def test():
        ser = SerialQueue()
        future = ser.run_task(partial(doit, "Foo"))
        future2 = ser.run_task(partial(doit, "Bar"))
        await asyncio.gather(future, future2)

    try:
        asyncio.run(test())
    except ValueError as ve:
        print(ve)
