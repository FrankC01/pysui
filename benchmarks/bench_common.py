#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Common utilities for pysui build_and_sign benchmark scripts."""

from __future__ import annotations
import argparse
import json
import os
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from time import perf_counter_ns
from typing import AsyncIterator, Iterator, Callable, Awaitable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from pysui import PysuiConfiguration, client_factory, AsyncClientBase
from pysui.sui.sui_common.instrumentation import InstrumentationCollector, active_collector
from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
import pysui.sui.sui_common.sui_commands as cmd


BUDGET = 4_000_000
SPLIT_AMOUNT = 1_000
RECIPIENT = "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28"

class TimingCollector(InstrumentationCollector):
    """Accumulates (label, elapsed_ns) events; resets between iterations."""

    def __init__(self) -> None:
        self.events: list[tuple[str, int]] = []

    @asynccontextmanager
    async def measure(self, label: str) -> AsyncIterator[None]:
        start = perf_counter_ns()
        yield
        self.events.append((label, perf_counter_ns() - start))

    def summary(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for label, elapsed in self.events:
            result[label] = result.get(label, 0) + elapsed
        return result

    @contextmanager
    def sync_measure(self, label: str) -> Iterator[None]:
        start = perf_counter_ns()
        yield
        self.events.append((label, perf_counter_ns() - start))

    def reset(self) -> None:
        self.events.clear()


@dataclass
class GasOption:
    label: str
    kwargs: dict = field(default_factory=dict)


def build_arg_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--iterations", "-n", type=int, default=10,
        help="Iterations per gas option per protocol (default: 10)",
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="bench_results",
        help="Directory for PNG and JSON output files (default: bench_results/)",
    )
    return parser


async def setup_clients() -> dict[str, AsyncClientBase]:
    """Create GQL and gRPC devnet clients."""
    return {
        "gql": client_factory(PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
            profile_name="devnet",
        )),
        "grpc": client_factory(PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
            profile_name="devnet",
        )),
    }


async def fetch_gas_coins(client: AsyncClientBase) -> list:
    """Fetch available gas coin objects for the active address."""
    result = await client.execute(
        command=cmd.GetGas(owner=client.config.active_address)
    )
    if result.is_ok():
        return result.result_data.objects
    raise ValueError(f"Failed to fetch gas coins: {result.result_string}")


def make_gas_options(gas_coins: list) -> list[GasOption]:
    """Return up to 8 gas option combinations.

    use_gas_objects rows are included only when coins are available.
    """
    gas_coin = gas_coins[0] if gas_coins else None
    options = [
        GasOption("default"),
        GasOption("budget_only", {"gas_budget": BUDGET}),
        GasOption("use_account", {"use_account_for_gas": True}),
        GasOption("use_account_budget", {"use_account_for_gas": True, "gas_budget": BUDGET}),
        GasOption("auto_gas", {"auto_gas": True}),
        GasOption("auto_gas_budget", {"auto_gas": True, "gas_budget": BUDGET}),
    ]
    if gas_coin is not None:
        options.extend([
            GasOption("gas_objects", {"use_gas_objects": [gas_coin]}),
            GasOption("gas_objects_budget", {"use_gas_objects": [gas_coin], "gas_budget": BUDGET}),
        ])
    return options


async def run_protocol_bench(
    client: AsyncClientBase,
    gas_options: list[GasOption],
    iterations: int,
    bench_fn: Callable[[AsyncClientBase, AsyncSuiTransaction, dict], Awaitable[None]],
) -> dict[str, dict[str, list[int]]]:
    """Run N iterations for each gas option.

    bench_fn: coroutine called once per iteration with (client, txer, gas_kwargs);
    responsible for the full operation — PTB setup plus build_and_sign, simulate, or execute.
    Returns {option_label: {phase_label: [elapsed_ns, ...]}}
    """
    results: dict[str, dict[str, list[int]]] = {}
    collector = TimingCollector()

    for gas_opt in gas_options:
        print(f"    {gas_opt.label} x{iterations}")
        opt_results: dict[str, list[int]] = {}

        for _ in range(iterations):
            collector.reset()
            txer: AsyncSuiTransaction = await client.transaction()
            async with active_collector(collector):
                await bench_fn(client, txer, gas_opt.kwargs)
            for label, elapsed in collector.summary().items():
                opt_results.setdefault(label, []).append(elapsed)

        results[gas_opt.label] = opt_results

    return results


def save_chart(
    all_results: dict[str, dict[str, dict[str, list[int]]]],
    output_dir: str,
    basename: str,
    title: str,
    key_map: dict[str, str],
    *,
    metric_root: str = "ptb.build_and_sign",
    x_axis_label: str = "Gas Option",
    y_axis_label: str = "Average ms",
) -> None:
    """Generate a grouped bar chart (one bar per protocol per category) and save PNG + JSON.

    all_results: {protocol: {category: {phase_label: [elapsed_ns, ...]}}}
    key_map: {category: description} shown in the key table below the chart.
    Outputs <output_dir>/<basename>.png and <output_dir>/<basename>.json.
    """
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, f"{basename}.png")
    json_path = os.path.join(output_dir, f"{basename}.json")

    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved: {json_path}")

    protocols = list(all_results.keys())

    gas_labels: list[str] = []
    for proto_data in all_results.values():
        for gas_label in proto_data:
            if gas_label not in gas_labels:
                gas_labels.append(gas_label)

    avgs: dict[str, list[float]] = {}
    for proto, proto_data in all_results.items():
        proto_avgs = []
        for gas_label in gas_labels:
            vals = proto_data.get(gas_label, {}).get(metric_root, [])
            proto_avgs.append(sum(vals) / len(vals) / 1_000_000 if vals else 0.0)
        avgs[proto] = proto_avgs

    x = np.arange(len(gas_labels))
    n_proto = len(protocols)
    width = 0.7 / n_proto
    colors = ["steelblue", "coral", "mediumseagreen", "gold"]

    fig, (ax, ax_key) = plt.subplots(
        2, 1,
        figsize=(max(8, len(gas_labels) * 1.4), 7),
        gridspec_kw={"height_ratios": [4, 1]},
    )
    for i, proto in enumerate(protocols):
        offset = (i - (n_proto - 1) / 2) * width
        bars = ax.bar(x + offset, avgs[proto], width, label=proto.upper(), color=colors[i % len(colors)])
        ax.bar_label(bars, fmt="%.0f", padding=2, fontsize=7)

    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(gas_labels, rotation=45, ha="right", fontsize=9)
    ax.legend()

    ax_key.axis("off")
    table_data = [[k, key_map.get(k, "")] for k in gas_labels if k in key_map]
    tbl = ax_key.table(
        cellText=table_data,
        colLabels=["Gas Option", "Description"],
        cellLoc="left",
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.auto_set_column_width([0, 1])

    plt.tight_layout()
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {png_path}")
    plt.close()


def save_simulate_chart(
    variant_avgs: dict[str, dict[str, float]],
    output_dir: str,
    basename: str,
    title: str,
    bar_labels: list[str],
    *,
    bar_colors: list[str] | None = None,
    x_axis_label: str = "Simulate Variant",
    y_axis_label: str = "Average ms",
) -> None:
    """Generate a grouped bar chart comparing simulate variants.

    variant_avgs: {variant_key: {metric_name: avg_ms}}
    bar_labels: ordered list of metric names to plot as bar groups per variant.
    Outputs <output_dir>/<basename>.png.
    """
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, f"{basename}.png")

    variants = list(variant_avgs.keys())
    n_bars = len(bar_labels)
    colors = bar_colors or ["steelblue", "coral", "mediumseagreen", "gold"]

    x = np.arange(len(variants))
    width = 0.7 / n_bars

    fig, ax = plt.subplots(figsize=(max(8, len(variants) * 2.5), 6))

    for i, bar_name in enumerate(bar_labels):
        vals = [variant_avgs[v].get(bar_name, 0.0) for v in variants]
        offset = (i - (n_bars - 1) / 2) * width
        bars = ax.bar(x + offset, vals, width, label=bar_name, color=colors[i % len(colors)])
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=7)

    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(variants, rotation=30, ha="right", fontsize=9)
    ax.legend()

    plt.tight_layout()
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {png_path}")
    plt.close()
