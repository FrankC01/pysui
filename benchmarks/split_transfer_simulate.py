#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Benchmark: SimulateTransaction vs SimulateTransactionKind — GQL and gRPC.

Measures pre-execution (as_document_node for GQL / __init__ for gRPC) and
decode (encode_fn for GQL / 0 for gRPC) time for each protocol+variant.

Usage::
    python -m benchmarks.split_transfer_simulate
    python -m benchmarks.split_transfer_simulate --iterations 10 --output-dir /tmp/bench
"""

from __future__ import annotations
import asyncio
import json
import os

import pysui.sui.sui_common.sui_commands as cmd

from benchmarks.bench_common import (
    build_arg_parser,
    setup_clients,
    fetch_gas_coins,
    GasOption,
    run_protocol_bench,
    save_simulate_chart,
    AsyncClientBase,
    AsyncSuiTransaction,
    BUDGET,
    SPLIT_AMOUNT,
    RECIPIENT,
)

# Instrumentation label emitted per variant for each metric
_OVERALL_LABEL: dict[str, str] = {
    "gql-SimulateTransaction":      "gql.execute",
    "gql-SimulateTransactionKind":  "gql.execute",
    "grpc-SimulateTransaction":     "grpc.execute",
    "grpc-SimulateTransactionKind": "grpc.execute",
}
_PRE_EXEC_LABEL: dict[str, str] = {
    "gql-SimulateTransaction":      "gql.SimulateTransactionSC.as_document_node",
    "gql-SimulateTransactionKind":  "gql.SimulateTransactionKindSC.as_document_node",
    "grpc-SimulateTransaction":     "grpc.SimulateTransaction.init",
    "grpc-SimulateTransactionKind": "grpc.SimulateTransactionKind.init",
}
_NETWORK_LABEL: dict[str, str] = {
    "gql-SimulateTransaction":      "gql._execute",
    "gql-SimulateTransactionKind":  "gql._execute",
    "grpc-SimulateTransaction":     "grpc._dispatch_grpc_request",
    "grpc-SimulateTransactionKind": "grpc._dispatch_grpc_request",
}
_DECODE_LABEL: dict[str, str | None] = {
    "gql-SimulateTransaction":      "gql.SimulateTransactionKindSC.encode_fn.<locals>._encode",
    "gql-SimulateTransactionKind":  "gql.SimulateTransactionKindSC.encode_fn.<locals>._encode",
    "grpc-SimulateTransaction":     None,
    "grpc-SimulateTransactionKind": None,
}


async def _bench_simulate_txn(
    client: AsyncClientBase, txer: AsyncSuiTransaction, gas_kwargs: dict
) -> None:
    """SimulateTransaction: PTB → transaction_data → simulate."""
    scres = await txer.split_coin(coin=txer.gas, amounts=[SPLIT_AMOUNT])
    await txer.transfer_objects(transfers=[scres], recipient=RECIPIENT)
    tx_data = await txer.transaction_data(**gas_kwargs)
    await client.execute(command=cmd.SimulateTransaction(tx_bytestr=tx_data.serialize()))


async def _bench_simulate_kind(
    client: AsyncClientBase, txer: AsyncSuiTransaction, gas_kwargs: dict
) -> None:
    """SimulateTransactionKind: PTB → raw_kind → simulate (no gas resolution)."""
    scres = await txer.split_coin(coin=txer.gas, amounts=[SPLIT_AMOUNT])
    await txer.transfer_objects(transfers=[scres], recipient=RECIPIENT)
    await client.execute(
        command=cmd.SimulateTransactionKind(
            tx_kind=txer.raw_kind(),
            tx_meta={"sender": client.config.active_address},
        )
    )


async def main() -> None:
    """."""
    args = build_arg_parser(
        "Simulate benchmark — pre-exec and decode timing for GQL and gRPC variants"
    ).parse_args()

    clients = {}
    try:
        print("Setting up clients...")
        clients = await setup_clients()
        gql_client = clients["gql"]
        grpc_client = clients["grpc"]

        # Fetch one gas coin for the faux gas option used by SimulateTransaction
        gas_coins = await fetch_gas_coins(gql_client)
        faux_gas = GasOption("faux", {"use_gas_objects": [gas_coins[0]], "gas_budget": BUDGET})
        no_gas = GasOption("faux", {})

        RUNS = [
            ("gql-SimulateTransaction",      gql_client,  _bench_simulate_txn,  faux_gas),
            ("gql-SimulateTransactionKind",  gql_client,  _bench_simulate_kind, no_gas),
            ("grpc-SimulateTransaction",     grpc_client, _bench_simulate_txn,  faux_gas),
            ("grpc-SimulateTransactionKind", grpc_client, _bench_simulate_kind, no_gas),
        ]

        raw_results: dict = {}
        for variant_key, client, bench_fn, gas_opt in RUNS:
            print(f"\nVariant: {variant_key} x{args.iterations}")
            raw_results[variant_key] = await run_protocol_bench(
                client, [gas_opt], args.iterations, bench_fn=bench_fn
            )

        os.makedirs(args.output_dir, exist_ok=True)
        json_path = os.path.join(args.output_dir, "split_transfer_simulate.json")
        with open(json_path, "w") as f:
            json.dump(raw_results, f, indent=2)
        print(f"Saved: {json_path}")

        def _avg_ms(vals: list[int]) -> float:
            return sum(vals) / len(vals) / 1_000_000 if vals else 0.0

        # Compute per-variant averages for the four chart metrics
        variant_avgs: dict[str, dict[str, float]] = {}
        for variant_key, proto_results in raw_results.items():
            faux_data = proto_results.get("faux", {})
            dec_label = _DECODE_LABEL[variant_key]
            variant_avgs[variant_key] = {
                "overall":  _avg_ms(faux_data.get(_OVERALL_LABEL[variant_key], [])),
                "pre-exec": _avg_ms(faux_data.get(_PRE_EXEC_LABEL[variant_key], [])),
                "network":  _avg_ms(faux_data.get(_NETWORK_LABEL[variant_key], [])),
                "decode":   _avg_ms(faux_data.get(dec_label, []) if dec_label else []),
            }

        save_simulate_chart(
            variant_avgs,
            args.output_dir,
            "split_transfer_simulate",
            f"Simulate Variants ({args.iterations} iterations)",
            bar_labels=["overall", "pre-exec", "network", "decode"],
        )
    finally:
        for client in clients.values():
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
