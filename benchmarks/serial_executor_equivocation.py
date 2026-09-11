#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Benchmark: SerialExecutor equivocation retry (backlog #105).

Simulates a realistic collision: one SerialExecutor pays out `tx-count`
recipients as individual sequential transactions, each splitting a slice off
a single shared "bank" coin -- the canonical Serial use case (one transaction
at a time, in order). Concurrently, one raw, non-executor transaction (built
and submitted directly via client.transaction() + client.execute(), no
executor involved) also splits from that same bank coin, representing an
external actor outside the payout job's control.

SerialQueueProcessor owns one long-lived, isolated cache with no shared
registry (unlike ParallelExecutor) -- so the only way it learns its cached
bank-coin version is stale is the way it happens in production: a build,
transport, or on-chain attempt fails, and the equivocation-retry path added
in backlog #105 restores the unresolved input, evicts the stale cache entry,
and rebuilds against fresh state.

Reports, per run: network round-trips, total elapsed time, the four
executor.serial.* equivocation counters (build, transport, on-chain, and
conflict-extraction-failure), and how many of the payout batch's
transactions ultimately resolved OK vs failed outright. A final failure from
retry exhaustion under real contention is not necessarily a bug -- see
backlog #105 handoff for why the racer isn't itself retried.

Usage::
    python -m benchmarks.serial_executor_equivocation
    python -m benchmarks.serial_executor_equivocation --tx-count 8 --iterations 1
"""

from __future__ import annotations
import argparse
import asyncio
import json
import logging
import os
from time import perf_counter_ns

from pysui import AsyncClientBase
from pysui.sui.sui_common.executors import ExecutorOptions, GasMode
from pysui.sui.sui_common.instrumentation import active_collector
import pysui.sui.sui_common.sui_commands as cmd

from benchmarks.bench_common import (
    TimingCollector,
    fetch_gas_coins,
    get_recipient,
    setup_clients,
    SPLIT_AMOUNT,
)

logger = logging.getLogger(__name__)

_NETWORK_LABEL: dict[str, str] = {
    "gql": "gql._execute",
    "grpc": "grpc._dispatch_grpc_request",
}

# Trivially satisfied by the sender's existing address-balance accumulator --
# this only governs when on_balance_low would fire, not how much gas is
# available.
_ADDR_BALANCE_THRESHOLD = 1

# The bank coin must individually hold at least this much (5 SUI) so it
# survives the whole payout batch plus the racer's own split.
_MIN_COIN_BALANCE = 5_000_000_000

# Generous relative to tx-count: two independent actors racing the same
# coin can force several consecutive losses before the batch's cached
# version catches up, and retry exhaustion should reflect a genuinely
# under-provisioned budget, not this script's own default.
_MAX_RETRIES_PER_TX_COUNT = 2


def _select_bank_coin(owned_coins: list, protocol: str):
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

    Distinct from bench_common.build_arg_parser(): SerialExecutor's payout
    batch plus a concurrent raw racer transaction don't fit the shared
    per-gas-option build_and_sign loop that helper is built around.
    """
    parser = argparse.ArgumentParser(
        description=(
            "SerialExecutor equivocation-retry benchmark (backlog #105) -- "
            "a payout batch racing one external raw transaction over the same coin"
        )
    )
    parser.add_argument(
        "--tx-count", type=int, default=8,
        help="Number of sequential payout transactions per run (default: 8)",
    )
    parser.add_argument(
        "--iterations", "-n", type=int, default=1,
        help=(
            "Number of runs (default: 1 -- each run executes real "
            "transactions on-chain, so keep this low unless gas budget allows more)"
        ),
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="bench_results",
        help="Directory for JSON output (default: bench_results/)",
    )
    return parser


async def _fire_racer(
    *,
    client: AsyncClientBase,
    bank_coin_id: str,
    recipient: str,
) -> bool:
    """Submit one raw, non-executor transaction splitting from the bank coin.

    Represents an actor outside the payout job's control -- no executor,
    no retry of its own. Returns True on success, False on failure (either
    outcome is a valid benchmark result: this transaction losing the race
    is exactly what exercises the payout batch's equivocation-retry path).
    """
    try:
        racer_txn = await client.transaction()
        split = await racer_txn.split_coin(coin=bank_coin_id, amounts=[SPLIT_AMOUNT])
        await racer_txn.transfer_objects(transfers=[split], recipient=recipient)
        build_dict = await racer_txn.build_and_sign(use_account_for_gas=True)
        result = await client.execute(command=cmd.ExecuteTransaction(**build_dict))
        return result.is_ok()
    except Exception as exc:
        logger.warning("racer transaction failed: %s", exc)
        return False


async def run_batch(
    *,
    client: AsyncClientBase,
    protocol: str,
    tx_count: int,
    recipient: str,
) -> dict[str, int]:
    """Run one payout batch of tx_count sequential transactions against a
    shared bank coin, racing one concurrent raw transaction over the same coin.

    Gas comes from the sender's address-balance accumulator (GasMode.
    ADDRESS_BALANCE) for both the payout batch and the racer, so gas payment
    itself is never the thing racing -- only the bank coin is shared.
    Returns network_calls, elapsed_ns, the four executor.serial.* equivocation
    counters, and ok_count/failed_count for the payout batch.
    """
    owned_coins = await fetch_gas_coins(client)
    bank_coin = _select_bank_coin(owned_coins, protocol)

    options = ExecutorOptions(
        sender=client.config.active_address,
        gas_mode=GasMode.ADDRESS_BALANCE,
        initial_coins=[],
        min_threshold_balance=_ADDR_BALANCE_THRESHOLD,
        max_retries=max(1, tx_count * _MAX_RETRIES_PER_TX_COUNT),
    )
    collector = TimingCollector()
    # The executor MUST be constructed inside the active_collector scope --
    # see benchmarks/parallel_executor_registry.py for why (context capture
    # at asyncio.create_task time applies identically to SerialExecutor's
    # _processor_loop background task).
    async with active_collector(collector):
        executor = await client.serial_executor(options=options)
        start = perf_counter_ns()
        txns = []
        for _ in range(tx_count):
            txn = await executor.new_transaction()
            split = await txn.split_coin(coin=bank_coin.object_id, amounts=[SPLIT_AMOUNT])
            await txn.transfer_objects(transfers=[split], recipient=recipient)
            txns.append(txn)

        futures = executor.submit(txns)
        racer_task = asyncio.create_task(
            _fire_racer(client=client, bank_coin_id=bank_coin.object_id, recipient=recipient)
        )
        results = await asyncio.gather(*futures)
        racer_ok = await racer_task
    elapsed_ns = perf_counter_ns() - start

    ok_count = sum(1 for r in results if not isinstance(r, tuple))
    failed_count = len(results) - ok_count

    # Printed before the hard-failure check so a batch with genuine failures
    # still reports what the equivocation machinery actually did.
    print(
        f"  racer {'OK' if racer_ok else 'failed'}, payout {ok_count} ok / {failed_count} failed"
        f" -- equivocation retries: build {collector.counts.get('executor.serial.equivocation_retry_build', 0)}"
        f", transport {collector.counts.get('executor.serial.equivocation_retry_transport', 0)}"
        f", on-chain {collector.counts.get('executor.serial.equivocation_retry', 0)}"
    )

    await executor.close()

    network_label = _NETWORK_LABEL[protocol]
    network_calls = sum(1 for label, _ in collector.events if label == network_label)
    return {
        "network_calls": network_calls,
        "elapsed_ns": elapsed_ns,
        "ok_count": ok_count,
        "failed_count": failed_count,
        "racer_ok": int(racer_ok),
        "equivocation_retry_build": collector.counts.get("executor.serial.equivocation_retry_build", 0),
        "equivocation_retry_transport": collector.counts.get("executor.serial.equivocation_retry_transport", 0),
        "equivocation_retry_onchain": collector.counts.get("executor.serial.equivocation_retry", 0),
        "conflict_extraction_failed": collector.counts.get("executor.serial.conflict_extraction_failed", 0),
    }


async def main() -> None:
    """Run the SerialExecutor equivocation-retry benchmark against gRPC."""
    args = build_bench_parser().parse_args()

    clients: dict[str, AsyncClientBase] = {}
    try:
        clients = await setup_clients()
        protocol = "grpc"
        client = clients[protocol]
        recipient = get_recipient(client.config)

        print(f"\n{protocol}: {args.tx_count} sequential payout txns x{args.iterations}, racing 1 external txn")
        batch_results = []
        for i in range(args.iterations):
            batch = await run_batch(
                client=client,
                protocol=protocol,
                tx_count=args.tx_count,
                recipient=recipient,
            )
            print(
                f"  run {i + 1}: {batch['network_calls']} network calls, "
                f"{batch['elapsed_ns'] / 1_000_000:.1f} ms"
            )
            batch_results.append(batch)
        raw_results: dict[str, list[dict[str, int]]] = {protocol: batch_results}

        os.makedirs(args.output_dir, exist_ok=True)
        json_path = os.path.join(args.output_dir, "serial_executor_equivocation.json")
        with open(json_path, "w") as f:
            json.dump(raw_results, f, indent=2)
        print(f"\nSaved: {json_path}")
    finally:
        for client in clients.values():
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
