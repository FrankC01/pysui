#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for SerialQueue and ParallelQueue."""

import pytest
import asyncio
from pysui.sui.sui_common.executors import SerialQueue, ParallelQueue


class TestSerialQueue:
    """Test SerialQueue for serial task execution."""

    @pytest.mark.asyncio
    async def test_serial_queue_creation(self):
        """SerialQueue is created successfully."""
        queue = SerialQueue()
        assert queue is not None

    @pytest.mark.asyncio
    async def test_serial_queue_runs_task(self):
        """run_task executes the coroutine and returns result."""
        queue = SerialQueue()

        async def sample_task():
            return "result"

        result = await queue.run_task(sample_task)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_serial_queue_executes_serially(self):
        """No two tasks overlap: every end_N must precede start_{N+1}."""
        queue = SerialQueue()
        execution_order = []

        async def task(task_id: int, delay: float = 0.01):
            execution_order.append(f"start_{task_id}")
            await asyncio.sleep(delay)
            execution_order.append(f"end_{task_id}")
            return task_id

        tasks = [
            asyncio.create_task(queue.run_task(lambda i=i: task(i)))
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)
        assert sorted(results) == [0, 1, 2]

        # At most one task may be running at any moment in the event log.
        running: set = set()
        for event in execution_order:
            if event.startswith("start_"):
                assert not running, (
                    f"{event} began while {running} still running — queue is not serial"
                )
                running.add(event)
            elif event.startswith("end_"):
                running.discard(f"start_{event.split('_', 1)[1]}")

    @pytest.mark.asyncio
    async def test_serial_queue_with_lambda(self):
        """run_task works with lambda expressions."""
        queue = SerialQueue()

        result = await queue.run_task(lambda: "lambda_result")
        assert result == "lambda_result"

    @pytest.mark.asyncio
    async def test_serial_queue_with_exception(self):
        """Exceptions in tasks are properly raised."""
        queue = SerialQueue()

        async def failing_task():
            raise ValueError("task error")

        with pytest.raises(ValueError, match="task error"):
            await queue.run_task(failing_task)

    @pytest.mark.asyncio
    async def test_serial_queue_releases_lock_after_exception(self):
        """Lock is released after a failing task so subsequent tasks can run."""
        queue = SerialQueue()

        async def failing_task():
            raise RuntimeError("boom")

        async def succeeding_task():
            return "ok"

        with pytest.raises(RuntimeError):
            await queue.run_task(failing_task)

        result = await queue.run_task(succeeding_task)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_serial_queue_rejects_coroutine_object(self):
        """run_task raises TypeError when a coroutine object is passed instead of a callable."""
        queue = SerialQueue()

        async def sample():
            return 42

        coro = sample()
        with pytest.raises(TypeError, match="callable"):
            await queue.run_task(coro)
        coro.close()

    @pytest.mark.asyncio
    async def test_serial_queue_task_with_args(self):
        """run_task passes arguments to the coroutine."""
        queue = SerialQueue()

        async def task_with_args(a, b, c=3):
            return a + b + c

        # Using lambda to pass arguments
        result = await queue.run_task(lambda: task_with_args(1, 2, c=4))
        assert result == 7


class TestParallelQueue:
    """Test ParallelQueue for parallel task execution."""

    @pytest.mark.asyncio
    async def test_parallel_queue_creation(self):
        """ParallelQueue is created successfully."""
        queue = ParallelQueue(max_tasks=2)
        assert queue is not None

    @pytest.mark.asyncio
    async def test_parallel_queue_runs_task(self):
        """run_task executes the coroutine and returns result."""
        queue = ParallelQueue(max_tasks=2)

        async def sample_task():
            return "result"

        result = await queue.run_task(sample_task)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_parallel_queue_executes_in_parallel(self):
        """Tasks are executed in parallel."""
        queue = ParallelQueue(max_tasks=2)
        task_count = 0
        max_concurrent = 0

        async def task(task_id: int):
            nonlocal task_count, max_concurrent
            task_count += 1
            max_concurrent = max(max_concurrent, task_count)
            await asyncio.sleep(0.01)
            task_count -= 1
            return task_id

        # Launch multiple tasks
        tasks = [
            asyncio.create_task(queue.run_task(lambda i=i: task(i)))
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)

        # All tasks should complete
        assert len(results) == 3
        assert results == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_parallel_queue_with_exception(self):
        """Exceptions in tasks are properly raised."""
        queue = ParallelQueue(max_tasks=2)

        async def failing_task():
            raise ValueError("parallel task error")

        with pytest.raises(ValueError, match="parallel task error"):
            await queue.run_task(failing_task)

    @pytest.mark.asyncio
    async def test_parallel_queue_rejects_coroutine_object(self):
        """run_task raises TypeError when a coroutine object is passed instead of a callable."""
        queue = ParallelQueue(max_tasks=2)

        async def sample():
            return 42

        coro = sample()
        with pytest.raises(TypeError, match="callable"):
            await queue.run_task(coro)
        coro.close()
