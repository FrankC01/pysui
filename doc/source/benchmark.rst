Benchmarks
==========

``pysui`` ships a benchmarking framework built around an instrumentation hook
system. Every concrete method and function in the pysui internals fires a
callback whenever a collector is active, so you can measure real pipeline costs
without modifying pysui source. The goal of this page is to show you how to
write your own benchmark using that framework.

Three ready-to-run reference scripts are also provided in ``benchmarks/``; they
are examples of the framework in use, not the primary subject of this page.

.. _benchmark-instrumentation:

Instrumentation Coverage
------------------------

.. note::

   **What is instrumented:**
   All concrete methods and functions (including ``__init__``) across:

   - ``pysui/sui/sui_common/`` — transaction building, gas resolution, executors, config
   - ``pysui/sui/sui_pgql/`` — GraphQL client, fragments, query dispatch, schema
   - ``pysui/sui/sui_grpc/`` — gRPC client and request handlers
   - ``pysui/sui/sui_crypto.py`` — signing, keypair, address derivation
   - ``pysui/sui/sui_utils.py`` — shared utility functions

   These total approximately **926 instrumentation hook points**.

   **What is NOT instrumented:**

   - ``pysui/sui/sui_common/instrumentation.py`` — the framework itself is excluded to avoid recursion
   - ``pysui/sui/sui_grpc/suimsgs/`` — generated protobuf stubs (do not edit)
   - Abstract base classes: ``client.py``, ``sui_command.py``, ``txn_arg_encoder.py`` — only concrete methods carry hooks

Writing a Custom Benchmark
---------------------------

The only pysui imports a custom benchmark needs are:

- :class:`~pysui.sui.sui_common.instrumentation.InstrumentationCollector` — subclass to receive timing callbacks
- :func:`~pysui.sui.sui_common.instrumentation.active_collector` — context manager that activates a collector for a block of code

Every instrumented pysui call inside an ``active_collector`` block automatically
invokes your collector's ``measure`` or ``sync_measure`` method. No changes to
pysui source are required.

**Step 1 — implement a collector:**

.. code-block:: python

    from contextlib import asynccontextmanager, contextmanager
    from time import perf_counter_ns
    from typing import AsyncIterator, Iterator
    from pysui.sui.sui_common.instrumentation import InstrumentationCollector

    class TimingCollector(InstrumentationCollector):
        def __init__(self) -> None:
            self.events: list[tuple[str, int]] = []

        @asynccontextmanager
        async def measure(self, label: str) -> AsyncIterator[None]:
            start = perf_counter_ns()
            yield
            self.events.append((label, perf_counter_ns() - start))

        @contextmanager
        def sync_measure(self, label: str) -> Iterator[None]:
            start = perf_counter_ns()
            yield
            self.events.append((label, perf_counter_ns() - start))

**Step 2 — wrap your code with** ``active_collector``:

.. code-block:: python

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.instrumentation import active_collector

    async def main() -> None:
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
            profile_name="devnet",
        )
        client = client_factory(cfg)
        collector = TimingCollector()

        try:
            txer = await client.transaction()
            async with active_collector(collector):
                # every instrumented pysui call inside this block fires the collector
                scres = await txer.split_coin(coin=txer.gas, amounts=[1_000])
                await txer.transfer_objects(transfers=[scres], recipient=cfg.active_address)
                await txer.build_and_sign()

            for label, elapsed_ns in collector.events:
                print(f"{label}: {elapsed_ns / 1_000_000:.2f} ms")
        finally:
            await client.close()

    if __name__ == "__main__":
        asyncio.run(main())

The collector receives one event per instrumented call that executes inside the
``active_collector`` block. Labels follow the pattern
``pysui.sui.<module>.<ClassName>.<method_name>``.

Prerequisites
-------------

Before running any benchmark:

#. A valid pysui configuration must exist at ``~/.pysui`` (or the path pointed to by
   ``PysuiConfiguration`` defaults) with a ``devnet`` profile configured for the
   protocol group you intend to use.
#. The active address must hold sufficient SUI gas when executing transactions
   on-chain.
#. Install dev dependencies from the repository root:

.. code-block:: console

    python -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

Reference Scripts
-----------------

The ``benchmarks/`` package contains three ready-to-run scripts that apply the
framework to a split-and-transfer PTB across both **GraphQL** and **gRPC**
protocol groups. Shared utilities (arg parsing, client setup, iteration loops,
chart generation) live in ``benchmarks/bench_common.py`` — that file is internal
to these scripts and is not part of the pysui public API.

All three accept the same CLI arguments:

.. code-block:: console

    python -m benchmarks.<script_name> [options]

    options:
      -h, --help               show this help message and exit
      -n N, --iterations N     Iterations per gas option per protocol (default: 10)
      -o DIR, --output-dir DIR Directory for PNG and JSON output files
                               (default: bench_results/)

Gas options exercised by the reference scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each reference script tests eight gas-resolution strategies. These are choices
made by the example scripts; a custom benchmark can use any subset or none.

.. list-table::
   :header-rows: 1
   :widths: 25 55

   * - Gas Option
     - Description
   * - ``default``
     - pysui selects gas coins and simulates for budget
   * - ``budget_only``
     - User-defined budget; pysui selects gas coins
   * - ``use_account``
     - Pay from account balance; pysui simulates for budget
   * - ``use_account_budget``
     - Pay from account balance with user-defined budget
   * - ``auto_gas``
     - pysui auto-detects gas source and simulates for budget
   * - ``auto_gas_budget``
     - pysui auto-detects gas source with user-defined budget
   * - ``gas_objects``
     - User-specified gas coins; pysui simulates for budget
   * - ``gas_objects_budget``
     - User-specified gas coins and user-defined budget

Options that supply a pre-computed budget skip the simulation step and are
consistently faster.

Build and Sign (split_transfer_ignore)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measures the cost of building and signing a PTB **without** submitting it on-chain.
The PTB splits 1000 MIST from the gas coin and transfers it to a recipient address.
No gas is consumed.

.. code-block:: console

    python -m benchmarks.split_transfer_ignore
    python -m benchmarks.split_transfer_ignore --iterations 20 --output-dir /tmp/bench

Output: ``bench_results/split_transfer_ignore.png`` and
``bench_results/split_transfer_ignore.json``.

Simulate (split_transfer_simulate)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measures the cost of **simulating** the same PTB in two modes:

*   ``SimulateTransaction`` — simulate with full transaction bytes and signatures.
*   ``SimulateTransactionKind`` — simulate with transaction-kind bytes only
    (no sender or gas resolution required).

No gas is consumed.

.. code-block:: console

    python -m benchmarks.split_transfer_simulate
    python -m benchmarks.split_transfer_simulate --iterations 20 --output-dir /tmp/bench

Output: ``bench_results/split_transfer_simulate.png`` and
``bench_results/split_transfer_simulate.json``.

Execute (split_transfer_execute)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measures the full end-to-end cost: build, sign, **and execute** the PTB on-chain.
Gas is consumed on every iteration. Gas coins and object versions are re-fetched
before each iteration to keep object references current after the previous
transaction commits. A one-second settling delay is applied between iterations.

.. warning::

   This benchmark spends real gas. Keep ``--iterations`` low (3–5) when first
   profiling and always run against **devnet**.

.. code-block:: console

    python -m benchmarks.split_transfer_execute --iterations 5
    python -m benchmarks.split_transfer_execute --iterations 5 --output-dir /tmp/bench

Output: ``bench_results/split_transfer_execute.png`` and
``bench_results/split_transfer_execute.json``.

Output Files
------------

Each benchmark writes two files to the output directory:

``<name>.png``
    A grouped bar chart. Each group on the X axis is a category (e.g. gas option);
    each bar within the group represents a protocol (GQL or GRPC). Bar height is
    the average time in milliseconds across all iterations.

``<name>.json``
    Raw timing data structured as
    ``{protocol: {category: {phase_label: [elapsed_ns, ...]}}}``.
    Use this file to compute custom statistics or build alternative visualisations.
