#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui async gas sample.

Shows fetching all SUI gas objects for the active address via GRAPHQL or GRPC protocol.
"""

import asyncio
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

_async_gas_version = "2.0.0"

from samples.cmd_argsg import build_async_gas_parser, pre_config_pull
from pysui import PysuiClient, client_factory, __version__
from pysui.sui.sui_common.config.confgroup import GroupProtocol
from pysui.sui.sui_common.sui_commands import GetGas
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR


async def _get_gas_gql(client: PysuiClient, address: str) -> list:
    """Fetch all SUI gas objects for address via GQL (auto-paged by dispatcher)."""
    result = await client.execute(command=GetGas(owner=address))
    if result.is_ok():
        return result.result_data.objects
    return []


async def _get_gas_grpc(client: PysuiClient, address: str) -> list:
    """Fetch all SUI gas objects for address via gRPC (manual cursor loop)."""
    objects: list = []
    page_token: bytes | None = None
    while True:
        result = await client.execute(command=GetGas(owner=address, grpc_page_token=page_token))
        if not result.is_ok():
            break
        resp = result.result_data
        objects.extend(resp.objects)
        if not resp.next_page_token:
            break
        page_token = resp.next_page_token
    return objects


def print_gas(gasses: list) -> int:
    """Print gas balances and return total mist."""
    total: int = 0
    for obj in gasses:
        total += obj.balance
        print(
            f"{obj.object_id} has {obj.balance:12} -> {obj.balance / SUI_COIN_DENOMINATOR:.8f}"
        )
    print(f"Total gas {total:12} -> {total / SUI_COIN_DENOMINATOR:.8f}")
    print()
    return total


async def get_all_gas(client: PysuiClient) -> dict:
    """Get all SUI gas for each address in the active group."""
    protocol = client.config.active_group.group_protocol
    fetch = _get_gas_gql if protocol == GroupProtocol.GRAPHQL else _get_gas_grpc
    addys = client.config.active_group.address_list
    results = await asyncio.gather(*[fetch(client, a) for a in addys], return_exceptions=True)
    return dict(zip(addys, results))


async def main_run(client: PysuiClient) -> None:
    """Main async entry point."""
    gas_map = await get_all_gas(client)
    grand_total: int = 0
    for address, objects in gas_map.items():
        print(f"\nGas objects for: {address}")
        if isinstance(objects, Exception):
            print(f"  Error: {objects}")
            continue
        grand_total += print_gas(objects)
        print()
    print(f"Grand Total gas {grand_total:12} -> {grand_total / SUI_COIN_DENOMINATOR:.8f}\n")
    print("Exiting async pysui")
    await client.close()


def sdk_version() -> None:
    """Display version(s)."""
    print(f"async_gas_version: {_async_gas_version} SDK version: {__version__}")


def main() -> None:
    """Setup async loop and run."""
    cfg, arg_line = pre_config_pull(sys.argv[1:].copy())
    parsed = build_async_gas_parser(arg_line, cfg)
    cfg.make_active(
        group_name=parsed.group_name, profile_name=parsed.profile_name, persist=False
    )
    if parsed.version:
        sdk_version()
        return
    if cfg.active_group.group_protocol == GroupProtocol.OTHER:
        print(
            f"Error: active group '{cfg.active_group.group_name}' has unsupported protocol. "
            "Use a GRAPHQL or GRPC group."
        )
        sys.exit(1)
    arpc = client_factory(cfg)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_run(arpc))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
