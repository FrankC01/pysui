# develop pysui

SUI Python Client SDK for Sui

This document is for contributors or the curious developer

## Ready to run
Requires:
 * Linux or macos (x86_64 or M1)
 * python 3.10 or greater
 * pkg-config
 * git
 * sui binaries to support `publish` function

### Clone this repo

`git clone git@github.com:FrankC01/pysui.git

### Setup virtual environment

`python3 -m venv env`

### Activate
`source env/bin/activate`

### Load core packages
`pip list`

  * If you get a warning about upgrading pip... do so

`pip install -r requirements.txt`

  * If you get an error with secp256k1 then:
    `pip install wheel` and try to install requirements again

### Load anciallary development packages

`pip install -r requirements-dev.txt` .

### Run sample wallet app for help
See [README](https://github.com/FrankC01/pysui/blob/main/README.md)

## SDK Examples

### Example 1 - Synchronous Query Gas
Sample script (example1.py) demonstrating the fundementals for synchronous pysui usage.
Copy following to `example1.py`
```python
"""Simple SDK example - Get gas for active address."""

from pysui.sui.sui_rpc import SuiClient, RpcResult
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_types import SuiGas, SuiGasDescriptor

# Well knowns
GAS_TYPE_SIG: str = "0x2::coin::Coin<0x2::sui::SUI>"

# Helper funcs

def print_gas_objects(client: SuiClient, indata: list[SuiGasDescriptor]) -> None:
    """Get each object and print it's balance.

    :param client: Instance of SuiClient
    :type client: SuiClient
    :param indata: List of gas descriptors
    :type indata: list[SuiGasDescriptor]
    """
    # Assume the indata list came from a function that returns a list of SuiGasDescriptors
    for item in indata:
        # print(item)
        obj_result: RpcResult = client.get_object(item.identifier)
        if obj_result.is_ok():
            # Result data is SuiGas type object
            gas_object: SuiGas = obj_result.result_data
            print(f"Gas object: {gas_object.identifier} has {gas_object.balance:12} mists")


# Main body

def main():
    """Entry point for execution."""
    # Load configuration from SUI configuration.
    cfg: SuiConfig = SuiConfig.default()
    # Load the synchronous RPC provider with this configuration
    client: SuiClient = SuiClient(cfg)
    print(f"Getting gas for address: {cfg.active_address} from endpoint {cfg.rpc_url}")

    # Execute the command to get all object descriptors of type Gas
    result: RpcResult = client.get_address_object_descriptors(SuiGasDescriptor)

    # Check the results:
    if result.is_ok():
        print_gas_objects(client, result.result_data)
    else:
        print(f"Failed execution with {result.result_string}")

if __name__ == "__main__":
    main()
```

Then run the script:
`python -m example1` or `python example1.py`

With the resulting (your gas mileage may vary) output:
```bash
Gas object: 0x4a1c27adc0163435766e0ae707214f05c2e3453a has     10000000 mists
Gas object: 0x7a904a97278d1318037a139769b4e7d0ed9f0dcf has     10000000 mists
Gas object: 0x7d2607545ab848c80b5ed81cafa0b4bd55d372fd has     10000000 mists
Gas object: 0x84abdb287cc9a5ed7d8beb8eb5aecc93e4b02320 has     10000000 mists
Gas object: 0xb8dd24512bd7b4637a1a82dfa28135aa13ff03bf has     10000000 mists
Gas object: 0xd186730be1236a5ee1a9768cf1c1273f3e705a4c has     10000000 mists
Gas object: 0xe99582bbc9a077f220f29a5dfe270eae86d3db6f has     10000000 mists
Gas object: 0xef1b53443f14248d9c4271c176bfcff00dd8ebde has     10000000 mists
Gas object: 0xfc7729a83a1e13973cb0bbbd1a92f70ed772e14f has     10000000 mists
```

### Example 2 - Asynchronous Query Gas
Sample script demonstrating the fundementals for asynchronous pysui usage. This
is included in `samples/async_gas.py`:
```python
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


def print_gas(gasses: list[SuiGas]) -> int:
    """print_gas Prints gas balances for each gas object `gasses`.

    :param gasses: A list of SuiGas type objects
    :type gasses: list[SuiGas]
    :return: Total gas summed from all SuiGas in gasses
    :rtype: int
    """
    total = 0
    for gas_result in gasses:
        total += gas_result.balance
        print(f"{gas_result.identifier} has {gas_result.balance:12} -> {gas_result.balance/SUI_COIN_DENOMINATOR:12}")
    print(f"Total gas {total:12} -> {total/SUI_COIN_DENOMINATOR:12}")
    print()
    return total


async def get_all_gas(client: SuiAsynchClient) -> dict[SuiAddress, list[SuiGas]]:
    """get_all_gas Gets all SuiGas for each address in configuration.

    :param client: Asynchronous Sui Client
    :type client: SuiAsynchClient
    :return: Dictionary of all gas objects for each address
    :rtype: dict[SuiAddress, list[SuiGas]]
    """
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


async def main_run(client: SuiAsynchClient):
    """main Asynchronous entry point."""
    config: SuiConfig = client.config
    owned_objects = asyncio.create_task(client.get_address_object_descriptors())
    gasses = asyncio.create_task(get_all_gas(client))
    print(f"Getting owned objects for :{config.active_address}")
    result = await owned_objects
    object_stats(result.result_data)
    result = await gasses
    grand_total: int = 0
    for key, value in result.items():
        print(f"\nGas objects for :{key.identifier}")
        grand_total += print_gas(value)
        print()
    print(f"Grand Total gas {grand_total:12} -> {grand_total/SUI_COIN_DENOMINATOR:12}\n")

    # print(result.keys())
    print("Exiting async pysui")


def main():
    """Setup asynch loop and run."""
    arpc = SuiAsynchClient(SuiConfig.default())
    asyncio.get_event_loop().run_until_complete(main_run(arpc))


if __name__ == "__main__":
    main()
```
Then run the script:
`python -m samples.asynch_gas` or `python samples/asynch_gas.py`

With the resulting (your gas mileage may vary) output:
```bash
Getting owned objects for :0x656194d2a3b39eb3795d91d9b068c08aa0ef1169
owned types and counts:
{
  "0x2::coin::Coin<0x2::sui::SUI>": 10,
  "0x4bc57a9dfe1f0b90b3927c11d1aa05be46d17f10::dancer::Tracker": 1
}

Gas objects for :0x656194d2a3b39eb3795d91d9b068c08aa0ef1169
0x092bfe4fec8b8571b94bd1b86fb52c81527f94e4 has      9998070 ->   0.00999807
0x14db9112c8eca023a9d5e03ba7098824ef303899 has     10000000 ->         0.01
0x319d29c7ec5bba038b4871342749f078355f90cb has     10000000 ->         0.01
0x5dc5330324638135cfecdf9e260163054f3592f7 has     10000000 ->         0.01
0x7271947d31b23b4f101b8e8adf4b0c3fed93be76 has     10000000 ->         0.01
0x804d1917912d4cddb64839ec0463410149528e0e has     10000000 ->         0.01
0xb2a08c5794f564fb938e2d4c6d2e0b6d3a8c5a85 has     10000000 ->         0.01
0xdd1154cf4c30d47aa67b12342067988c86198c38 has     10000000 ->         0.01
0xea3aac0b6e4e568399cab61e774dbe899c0e479a has     10000000 ->         0.01
0xfb696ccf370dd86846c017552c667685eee67efd has     10000000 ->         0.01
Total gas     99998070 ->   0.09999807


Gas objects for :0xcb76b1a89ef1212f1fa166dcd3171d4c6a96032f
0x0268199adaaab0c74c568291031ce957aeadfc53 has      9999886 ->  0.009999886
0x202fac27d5d84fc15d4809fc0276435d2e8ce13c has     10000000 ->         0.01
0xa6c4006e9cbd99617ea3820a968802983f8df2c3 has     10000000 ->         0.01
0xe6f5fdc1c5ef9b1d9df511505a754a7f0e0727fc has     10000000 ->         0.01
0xffae089bec039431ed52d713536045c458dd9ae4 has     10000000 ->         0.01
Total gas     49999886 ->  0.049999886


Gas objects for :0xdac92f51e82a4e6b857eb8ccb25aa422bbebdf21
0x3d8ef8625138c845d77a0239252eb0b028597425 has      9999886 ->  0.009999886
0x3e79b0f62bb29490cfdda79e275434d0b7bd47d8 has     10000000 ->         0.01
0x6b6ad685d430a196ece3b58c88250c839467b5a3 has     10000000 ->         0.01
0xbdf78cf64f7ef9eae53dcbaf2f2ba9a295697eef has     10000000 ->         0.01
0xc3e4cc9d9bea8fbf7107fcc82014ea351df514cd has     10000000 ->         0.01
Total gas     49999886 ->  0.049999886

Exiting async pysui
```