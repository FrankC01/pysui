#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Transaction execution queues."""

import asyncio
from typing import Callable, TypeVar, List

T = TypeVar("T")


class SerialQueue:
    def __init__(self):
        self._queue: List[Callable[[], None]] = []

    async def run_task(self, task: Callable[[], asyncio.Future[T]]) -> T:
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        self._queue.append(
            lambda: asyncio.ensure_future(task()).add_done_callback(
                lambda f: self._process_queue(f, future)
            )
        )

        if len(self._queue) == 1:
            self._queue[0]()

        return await future

    def _process_queue(self, future: asyncio.Future, main_future: asyncio.Future):
        try:
            result = future.result()
            main_future.set_result(result)
        except Exception as e:
            main_future.set_exception(e)
        finally:
            self._queue.pop(0)
            if self._queue:
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
    from functools import partial

    async def doit(arg):
        print(arg)

    async def test():
        ser = ParallelQueue(5)
        future = ser.run_task(partial(doit, "Foo"))
        future2 = ser.run_task(partial(doit, "Bar"))
        await asyncio.gather(future, future2)

    try:
        asyncio.run(test())
    except ValueError as ve:
        print(ve)
