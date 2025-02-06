#    Copyright Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-


"""pysui Asynchronous client example.

Shows:
* Loading an asynchronous client (see `main`)
* Fetching all address owned object descriptors from Sui blockchain
* Fetching all address owned gas objects for each address from Sui blockchain
"""

import asyncio
import os
import pathlib
import sys
import json

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

_async_gas_version = "1.0.1"
from samples.cmd_argsg import build_async_gas_parser


from pysui import PysuiConfiguration, AsyncGqlClient, __version__
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type


async def _get_all_gas_objects(
    client: AsyncGqlClient, address_id: str
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Retreive all Gas Objects."""
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
    result = await client.execute_query_node(with_node=qn.GetCoins(owner=address_id))
    while True:
        if result.is_ok():
            coin_list.extend(result.result_data.data)
            if result.result_data.next_cursor.hasNextPage:
                result = await client.execute_query_node(
                    with_node=qn.GetCoins(
                        owner=address_id, next_page=result.result_data.next_cursor
                    )
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")
    return coin_list


def print_gas(gasses: list[pgql_type.SuiCoinObjectGQL]) -> int:
    """print_gas Prints gas balances for each gas object `gasses`.

    :param gasses: A list of SuiGas type objects
    :type gasses: list[SuiGas]
    :return: Total gas summed from all SuiGas in gasses
    :rtype: int
    """
    total: int = 0
    try:
        for gas_result in gasses:
            total += int(gas_result.balance)
            print(
                f"{gas_result.coin_object_id} has {int(gas_result.balance):12} -> {int(gas_result.balance)/SUI_COIN_DENOMINATOR:.8f}"
            )
        print(f"Total gas {total:12} -> {total/SUI_COIN_DENOMINATOR:.8f}")
        print()
    except TypeError:
        total = 0

    return total


async def get_all_gas(
    client: AsyncGqlClient,
) -> dict[str, list[pgql_type.SuiCoinObjectGQL]]:
    """get_all_gas Gets all SuiGas for each address in configuration.

    :param client: Asynchronous Sui Client
    :type client: AsyncSuiGQLClient
    :return: Dictionary of all gas objects for each address
    :rtype: dict[str, list[SuiGas]]
    """
    addys = [x for x in client.config.model.active_group.address_list]

    addy_list = [_get_all_gas_objects(client, x) for x in addys]
    gresult = await asyncio.gather(*addy_list, return_exceptions=True)
    return_map = {}
    for index, gres in enumerate(gresult):
        return_map[addys[index]] = gres
    return return_map


async def main_run(client: AsyncGqlClient):
    """Main Asynchronous entry point."""
    gasses = asyncio.create_task(get_all_gas(client))
    result = await gasses
    grand_total: int = 0
    for key, value in result.items():
        print(f"\nGas objects for: {key}")
        grand_total += print_gas(value)
        print()
    print(
        f"Grand Total gas {grand_total:12} -> {grand_total/SUI_COIN_DENOMINATOR:.8f}\n"
    )
    print("Exiting async pysui")
    await client.close()


def sdk_version():
    """Dispay version(s)."""
    print(f"async_gas_version: {_async_gas_version} SDK version: {__version__}")


def _group_pull(cli_arg: list, config: PysuiConfiguration) -> list:
    """Check for group and set accordingly."""

    if cli_arg.count("--group"):
        ndx = cli_arg.index("--group")
        nvl: str = cli_arg[ndx + 1]
        config.make_active(group_name=nvl)

    return cli_arg


def main():
    """Setup asynch loop and run."""
    # Handle a different client.yaml than default
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    arg_line = _group_pull(sys.argv[1:].copy(), cfg)
    parsed = build_async_gas_parser(arg_line, cfg)

    cfg.make_active(
        group_name=parsed.group_name, profile_name=parsed.profile_name, persist=False
    )
    if parsed.version:
        sdk_version()
        return
    arpc = AsyncGqlClient(pysui_config=cfg)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_run(arpc))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
