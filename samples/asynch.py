#    Copyright 2022 Frank V. Castellucci
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


"""pysui Asynchronous client."""

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

print(sys.path)

from pysui.sui import SUI_COIN_DENOMINATOR
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_rpc import SuiAsynchClient
from pysui.sui.sui_types import ObjectInfo, SuiAddress, SuiGasDescriptor, SuiGas


def object_stats(objs: list[ObjectInfo]) -> None:
    """object_stats Print stats about objects for address.

    :param objs: List of object descriptors
    :type objs: list[ObjectInfo]
    """
    obj_types = {}
    for desc in objs:
        if desc.type_ not in obj_types:
            obj_types[desc.type_] = 0
        obj_types[desc.type_] = obj_types[desc.type_] + 1
    print(f"owned types and counts:\n{json.dumps(obj_types,indent=2)}")


def print_gas(gasses: list[SuiGas]) -> None:
    """Print gas objects."""
    total = 0
    for gas_result in gasses:
        total += gas_result.balance
        print(f"{gas_result.identifier} has {gas_result.balance:12} -> {gas_result.balance/SUI_COIN_DENOMINATOR:12}")
    print(f"Total gas {total:12} -> {total/SUI_COIN_DENOMINATOR:12}")
    print()


async def get_all_gas(client: SuiAsynchClient) -> dict[SuiAddress, list[SuiGas]]:
    """Spin 'em all."""
    config: SuiConfig = client.config
    # Build up gas descriptor fetch for each address
    addys = [SuiAddress(x) for x in config.addresses]
    addy_list = [client.get_address_object_descriptors(SuiGasDescriptor, x) for x in addys]
    gresult = await asyncio.gather(*addy_list, return_exceptions=True)
    # Get gas object for each descriptor for each address
    obj_get_list = []
    for gres in gresult:
        obj_get_list.append(client.get_objects_for([x.identifier for x in gres.result_data]))
    gresult = await asyncio.gather(*obj_get_list, return_exceptions=True)
    return_map = {}
    for index, gres in enumerate(gresult):
        return_map[addys[index]] = gres.result_data
    return return_map


async def main(client: SuiAsynchClient):
    """main Asynchronous entry point."""
    config: SuiConfig = client.config
    owned_objects = asyncio.create_task(client.get_address_object_descriptors())
    gasses = asyncio.create_task(get_all_gas(client))
    print(f"Getting owned objects for :{config.active_address}")
    result = await owned_objects
    object_stats(result.result_data)
    result = await gasses

    for key, value in result.items():
        print(f"\nGas objects for :{key.identifier}")
        print_gas(value)

    # print(result.keys())
    print("Exiting async pysui")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Comment out for local running
    configuration = SuiConfig.default()

    # Uncomment for local running. Assumes `sui genesis --working-dir sui_local/` in user home
    # Also must `sui start --network.config ~/sui_local/network.yaml`
    # configuration = SuiConfig.from_config_file("~/sui_local/client.yaml")

    arpc = SuiAsynchClient(configuration)
    loop.run_until_complete(main(arpc))
