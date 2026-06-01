#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Benchmark: build_and_sign() — discard result (pure build+sign timing).

Usage::
    python -m benchmarks.split_transfer_ignore
    python -m benchmarks.split_transfer_ignore --iterations 50 --output-dir /tmp/bench
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
    get_recipient,
    AsyncClientBase,
    AsyncSuiTransaction,
    SPLIT_AMOUNT,
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


async def main() -> None:
    """."""
    args = build_arg_parser(
        "build_and_sign benchmark — discard result (pure build+sign timing)"
    ).parse_args()

    clients = {}
    try:
        print("Setting up clients...")
        clients = await setup_clients()
        recipient = get_recipient(next(iter(clients.values())).config)

        async def _bench_fn(client: AsyncClientBase, txer: AsyncSuiTransaction, gas_kwargs: dict) -> None:
            scres = await txer.split_coin(coin=txer.gas, amounts=[SPLIT_AMOUNT])
            await txer.transfer_objects(transfers=[scres], recipient=recipient)
            await txer.build_and_sign(**gas_kwargs)

        all_results: dict = {}
        for proto, client in clients.items():
            print(f"\nProtocol: {proto.upper()}")
            gas_coins = await fetch_gas_coins(client)
            gas_options = make_gas_options(gas_coins)
            all_results[proto] = await run_protocol_bench(client, gas_options, args.iterations, bench_fn=_bench_fn)

        save_chart(
            all_results,
            args.output_dir,
            "split_transfer_ignore",
            f"Split and Transfer ({args.iterations}) - discard result",
            GAS_OPTION_LABELS,
        )
    finally:
        for client in clients.values():
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
