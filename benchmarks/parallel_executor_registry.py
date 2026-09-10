#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Benchmark: ParallelExecutor object-registry seeding (backlog #60).

Runs a batch of concurrent transactions that all split from and transfer a
slice of the SAME on-chain coin object, so every transaction in the batch
depends on that object's latest version being resolved correctly across its
concurrent siblings — the exact scenario backlog #60's read-side fix targets.
Reports, per batch, how many network round-trips were made (via the existing
gql._execute / grpc._dispatch_grpc_request instrumentation chokepoints),
total elapsed time, and OCS seeding outcomes: registry hits, misses, and
tombstoned entries skipped.

There is no before/after comparison run. Pre-#60 behaviour was broken rather
than merely slower, so a baseline measures nothing. Read the run forward
instead: from the second transaction onward hits should equal the number of
shared objects, while a run reporting only misses means object ids are not
reaching conflict_ids and nothing is being seeded at all.

Usage::
    python -m benchmarks.parallel_executor_registry
    python -m benchmarks.parallel_executor_registry --tx-count 8 --iterations 1
"""

from __future__ import annotations
import argparse
import asyncio
import json
import os
from time import perf_counter_ns

from pysui import AsyncClientBase
from pysui.sui.sui_common.executors import ExecutorOptions, GasMode
from pysui.sui.sui_common.instrumentation import active_collector

from benchmarks.bench_common import (
    TimingCollector,
    fetch_gas_coins,
    get_recipient,
    setup_clients,
    SPLIT_AMOUNT,
)

_NETWORK_LABEL: dict[str, str] = {
    "gql": "gql._execute",
    "grpc": "grpc._dispatch_grpc_request",
}

# Trivially satisfied by the sender's existing address-balance accumulator —
# this only governs when on_balance_low would fire, not how much gas is
# available.
_ADDR_BALANCE_THRESHOLD = 1

# The candidate coin must individually hold at least this much (5 SUI) so
# the shared source coin doesn't run dry mid-batch.
_MIN_COIN_BALANCE = 5_000_000_000


def _select_source_coin(owned_coins: list, protocol: str):
    """Return the first coin in owned_coins whose individual `balance` meets
    _MIN_COIN_BALANCE (as returned by fetch_gas_coins(), in whatever order
    GetGas returned them).
    """
    for coin in owned_coins:
        if (coin.balance or 0) >= _MIN_COIN_BALANCE:
            return coin
    raise ValueError(
        f"{protocol}: need at least 1 SUI coin with balance >= "
        f"{_MIN_COIN_BALANCE} MIST at the active address; found none "
        f"(of {len(owned_coins)} total)"
    )


def build_bench_parser() -> argparse.ArgumentParser:
    """Return the CLI parser for this benchmark.

    Distinct from bench_common.build_arg_parser(): ParallelExecutor's own
    GasMode (COINS/ADDRESS_BALANCE) and batch shape don't fit the shared
    per-gas-option build_and_sign loop that helper is built around.
    """
    parser = argparse.ArgumentParser(
        description=(
            "ParallelExecutor object-registry seeding benchmark (backlog #60) — "
            "network calls made when concurrent transactions share one coin object"
        )
    )
    parser.add_argument(
        "--tx-count", type=int, default=8,
        help="Number of concurrent transactions per batch (default: 8)",
    )
    parser.add_argument(
        "--iterations", "-n", type=int, default=1,
        help=(
            "Number of batches to run (default: 1 — each batch executes real "
            "transactions on-chain, so keep this low unless gas budget allows more)"
        ),
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="bench_results",
        help="Directory for JSON output (default: bench_results/)",
    )
    return parser


async def run_batch(
    *,
    client: AsyncClientBase,
    protocol: str,
    tx_count: int,
    recipient: str,
) -> dict[str, int]:
    """Run one batch of tx_count concurrent transactions sharing one source coin.

    Gas comes from the sender's address-balance accumulator (GasMode.
    ADDRESS_BALANCE) rather than a dedicated coin pool, sidestepping a
    separate gas-pool coin-version-refresh question uncovered while
    debugging this benchmark (see backlog #60 handoff notes). One coin is
    reserved as the shared source: every transaction in the batch splits
    from and transfers a slice of it. Returns network_calls, elapsed_ns and
    the three OCS seed counters.
    """
    owned_coins = await fetch_gas_coins(client)
    source_coin = _select_source_coin(owned_coins, protocol)

    options = ExecutorOptions(
        sender=client.config.active_address,
        gas_mode=GasMode.ADDRESS_BALANCE,
        initial_coins=[],
        min_threshold_balance=_ADDR_BALANCE_THRESHOLD,
        max_concurrent=tx_count,
    )
    collector = TimingCollector()
    # The executor MUST be constructed inside the active_collector scope.
    # _initialize() ends with asyncio.create_task(self._build_worker()), and
    # create_task snapshots the current context — a worker started outside this
    # block carries _collector_var=None for its whole life, silently no-op'ing
    # every count()/measure() in the build and execute paths, including the
    # _execute_item tasks it spawns. That is what produced the misleading
    # "0 hits / 0 misses / 0 tombstoned / 0 network calls" readings.
    async with active_collector(collector):
        executor = await client.parallel_executor(options=options)
        # Timed after construction so elapsed_ns stays comparable with earlier
        # runs; network_calls now also includes _initialize's balance query.
        start = perf_counter_ns()
        txns = []
        for _ in range(tx_count):
            txn = await executor.new_transaction()
            split = await txn.split_coin(coin=source_coin.object_id, amounts=[SPLIT_AMOUNT])
            await txn.transfer_objects(transfers=[split], recipient=recipient)
            txns.append(txn)

        futures = executor.submit(txns)
        results = await asyncio.gather(*futures)
    elapsed_ns = perf_counter_ns() - start

    # Printed before result checking so a failing batch still reports seeding
    # behaviour — a failure is exactly when these numbers matter most.
    print(
        f"  OCS {collector.counts.get('executor.ocs.seed_hit', 0)} hits"
        f" / {collector.counts.get('executor.ocs.seed_miss', 0)} misses"
        f" / {collector.counts.get('executor.ocs.seed_tombstone', 0)} tombstoned"
    )

    await executor.close()

    for result in results:
        if isinstance(result, tuple):
            err, exc = result
            raise RuntimeError(f"{protocol}: transaction failed: {err.name} — {exc}")

    network_label = _NETWORK_LABEL[protocol]
    network_calls = sum(1 for label, _ in collector.events if label == network_label)
    return {
        "network_calls": network_calls,
        "elapsed_ns": elapsed_ns,
        "seed_hits": collector.counts.get("executor.ocs.seed_hit", 0),
        "seed_misses": collector.counts.get("executor.ocs.seed_miss", 0),
        "seed_tombstones": collector.counts.get("executor.ocs.seed_tombstone", 0),
    }


async def main() -> None:
    """Run the ParallelExecutor object-registry seeding benchmark against gRPC."""
    args = build_bench_parser().parse_args()

    clients: dict[str, AsyncClientBase] = {}
    try:
        clients = await setup_clients()
        protocol = "grpc"
        client = clients[protocol]
        recipient = get_recipient(client.config)

        print(f"\n{protocol}: {args.tx_count} concurrent txns x{args.iterations}")
        batch_results = []
        for i in range(args.iterations):
            batch = await run_batch(
                client=client,
                protocol=protocol,
                tx_count=args.tx_count,
                recipient=recipient,
            )
            print(
                f"  batch {i + 1}: {batch['network_calls']} network calls, "
                f"{batch['elapsed_ns'] / 1_000_000:.1f} ms"
            )
            batch_results.append(batch)
        raw_results: dict[str, list[dict[str, int]]] = {protocol: batch_results}

        os.makedirs(args.output_dir, exist_ok=True)
        json_path = os.path.join(args.output_dir, "parallel_executor_registry.json")
        with open(json_path, "w") as f:
            json.dump(raw_results, f, indent=2)
        print(f"\nSaved: {json_path}")
    finally:
        for client in clients.values():
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
