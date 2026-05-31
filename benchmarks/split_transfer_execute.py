#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Benchmark: build_and_sign() — execute transaction after build+sign.

Usage::
    python -m benchmarks.split_transfer_execute
    python -m benchmarks.split_transfer_execute --iterations 5 --output-dir /tmp/bench

WARNING: Mode C submits real transactions — gas is consumed each iteration.
         Use a low --iterations count and run on devnet only.
"""

from __future__ import annotations
import asyncio

from benchmarks.bench_common import (
    build_arg_parser,
    setup_clients,
    fetch_gas_coins,
    make_gas_options,
    run_protocol_bench,
    save_chart,
    AsyncClientBase,
    AsyncSuiTransaction,
    SPLIT_AMOUNT,
    RECIPIENT,
)


GAS_OPTION_LABELS: dict[str, str] = {
    "default":            "pysui selects gas coins and simulates for budget",
    "budget_only":        "User defined budget, pysui selects gas coins",
    "use_account":        "Pay from account balance, pysui simulates for budget",
    "use_account_budget": "Pay from account balance, user defined budget",
    "auto_gas":           "pysui auto-detects gas source, simulates for budget",
    "auto_gas_budget":    "pysui auto-detects gas source, user defined budget",
    "gas_objects":        "User specified gas coins, pysui simulates for budget",
    "gas_objects_budget": "User specified gas coins and budget",
}


async def _bench_fn(client: AsyncClientBase, txer: AsyncSuiTransaction, gas_kwargs: dict) -> None:
    scres = await txer.split_coin(coin=txer.gas, amounts=[SPLIT_AMOUNT])
    await txer.transfer_objects(transfers=[scres], recipient=RECIPIENT)
    # TODO: replace build_and_sign with transaction_data + ExecuteTransaction once SuiCommand API confirmed
    await txer.build_and_sign(**gas_kwargs)


async def main() -> None:
    """."""
    args = build_arg_parser(
        "build_and_sign benchmark — execute transaction after build+sign (real gas consumed)"
    ).parse_args()

    clients = {}
    try:
        print("Setting up clients...")
        clients = await setup_clients()

        all_results: dict = {}
        for proto, client in clients.items():
            print(f"\nProtocol: {proto.upper()}")
            gas_coins = await fetch_gas_coins(client)
            gas_options = make_gas_options(gas_coins)
            all_results[proto] = await run_protocol_bench(
                client, gas_options, args.iterations, bench_fn=_bench_fn
            )

        save_chart(
            all_results,
            args.output_dir,
            "split_transfer_execute",
            f"Split and Transfer ({args.iterations}) - execute",
            GAS_OPTION_LABELS,
        )
    finally:
        for client in clients.values():
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
