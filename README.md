# pysui

Python SUI client SDK for Sui - WIP and expect significant refactoring

Refer to the [Change](CHANGELOG.md) log for recent additions, changes, fixes and removals...

## Known issues or missing capability
* Doesn't support `sui_batchTransaction` RPC API yet
* Doesn't use mnemonics yet (see [Issue](https://github.com/FrankC01/pysui/issues/9))
* Partial coverage for `sui_getTransaction...` RPC API
* Doesn't support `sui_getEvents` RPC API (added in SUI 0.15.0) yet

## Ready to run
Requires:
 * Linux or macos (x86_64 or M1)
 * python 3.10 or greater
 * pkg-config

## Run with devnet
By default, `pysui` will use the `client.yaml` configuration found in `.sui/sui_config/`. See [below](#run-local) for running
with different configuration (e.g. Local)

### Setup environment
`python3 -m venv env`

If, instead, you want to work with repo source code then read DEVELOP.md from repo

### Activate
`source env/bin/activate`

### Install `pysui`
`pip install pysui`

## Using the SDK
Here is a sample script demonstrating the fundementals for effective pysui usage:
```python
"""Simple SDK example - Get gas for active address."""

from pysui.sui.sui_rpc import SuiClient, RpcResult
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_types import SuiGasType, SuiGasDescriptor

# Well knowns
GAS_TYPE_SIG: str = "0x2::coin::Coin<0x2::sui::SUI>"

# Helper funcs


# Main body


def main():
    """Get gas objects."""
    # Load configuration from SUI configuration.
    cfg: SuiConfig = SuiConfig.default()
    # Load the synchronous RPC provider with this configuration
    client: SuiClient = SuiClient(cfg)
    print(f"Getting gas for address: {cfg.active_address} from endpoint {cfg.rpc_url}")

    # Execute the command to get all object descriptors of type Gas
    result: RpcResult = client.get_address_object_descriptors(SuiGasDescriptor)
    # Alternate: Get all descriptors (gas and data). Comment line above and uncomment line below
    # result: RpcResult = client.get_address_object_descriptors()

    # Check the results:
    if result.is_ok():
        # The call returns 1 or more object descriptors. We want those of specific type
        for item in result.result_data:
            # For each check if a gas type object and, if so, get the details
            # on the object
            if item.type_ == GAS_TYPE_SIG:
                print(item)
                obj_result: RpcResult = client.get_object(item.identifier)
                # builder = GetObject(ObjectID(item["objectId"]))
                # obj_res: RpcResult = client.execute(builder)
                if obj_result.is_ok():
                    # Use the helper function to convert the json results
                    # to a sui_type SuiGasType object
                    gas_object: SuiGasType = obj_result.result_data
                    print(f"Gas object: {gas_object.identifier} has {gas_object.balance} mists")
            else:
                print(item)

    else:
        print(f"Failed execution with {result.result_string}")


if __name__ == "__main__":
    main()
```

Then run the script:
`python -m example1` or `python example1.py`

With the resulting (your gas mileage may vary) output:
```bash
Getting gas for address: 0x78696a213bb7ce38e5dc5017ac07c44e85e24703 from endpoint https://fullnode.devnet.sui.io:443
Gas object: 0x0c6b9bd8b91324c00707e3e901c0bb6a57fcd4cf has 9998893 mists
Gas object: 0x38c52e5f2b736478f1818dbcc16f25d195c0225b has 9999961 mists
Gas object: 0x3a89ed7f63ce9827bdb690a8d64cffc55bf93617 has 10000000 mists
Gas object: 0x58c6dfeb6f275b3ce14c5ab84ba72fff01b1e5ed has 10000000 mists
Gas object: 0x5994c55b1d37bda820d7b723a41e4b2e6ab3f221 has 10000000 mists
Gas object: 0x9a2cd933061591768c3d24ef07ab4bd360e360e3 has 10000000 mists
Gas object: 0xa8328e1cad9e1f62cedf7561d397790748ce930c has 10000000 mists
Gas object: 0xa949c55f881de11c7b4fae8b52f1e9598da63c33 has 10000000 mists
Gas object: 0xab53291370ab42a4e19c4cfffc2c7795fcd72470 has 10000000 mists
Gas object: 0xae8294ee7b328c30cfd40692a121707f5c69cd7a has 10000000 mists
Gas object: 0xb4ece7d23bbb0d2ad2524e319036ff03f4cff331 has 10000000 mists
Gas object: 0xc837ffd69a2c8fdc8c735ac2019c6e4f97c7003e has 10000000 mists
Gas object: 0xdbb9e15527519601540ab00fc3108e579bb06cd0 has 10000000 mists
Gas object: 0xf167805d6098e4c5e1393e5a578aeb13b53e1c6a has 10000000 mists
Gas object: 0xfe1bf20b9c1e806b9ace359c37c72f1a2bd31984 has 10000000 mists
```

## Sample Wallet
Implementation demonstrating most SUI RPC API calls like the SUI CLI (i.e. `sui client ...`).

### Run sample wallet app for help
- pysui 0.0.6 or 0.0.7: `python -m samples.wallet`
- pysui >= 0.0.7: `wallet`

#### Output
```bash
usage: wallet [options] command [--command_options]

options:
  -h, --help            show this help message and exit

commands:
  {active-address,addresses,new-address,gas,object,objects,rpcapi,committee,merge-coin,split-coin,transfer-object,transfer-sui,pay,paysui,payallsui,package-object,package,publish,call,txns}
    active-address      Shows active address
    addresses           Shows all addresses
    new-address         Generate new address and keypair
    gas                 Shows gas objects and total mist
    object              Show object by id
    objects             Show all objects
    rpcapi              Show Sui RPC API information
    committee           Show committee info for epoch
    merge-coin          Merge two coins together
    split-coin          Split coin into one or more coins
    transfer-object     Transfer an object from one address to another
    transfer-sui        Transfer SUI 'mist(s)' to a Sui address
    pay                 Send coin of any type to recipient(s)
    paysui              Send SUI coins to a list of addresses.
    payallsui           Send all SUI coin(s) to recipient(s)
    package-object      Show raw package object with Move disassembly
    package             Show normalized package information
    publish             Publish a SUI package
    call                Call a move contract function
    txns                Show transaction information
```

### Run sample wallet app for transaction query help
`wallet txns -h`

### Output
```bash
usage: txns subcommand [--subcommand_options]

options:
  -h, --help   show this help message and exit

subcommand:
  {count,txn}
    count      Return total transaction count from server
    txn        Return transaction information
```

## Run Local
To run locally, especially useful when devnet is down, below are the steps to follow:

### Setup local (example from home directory)
1. `mkdir sui_local` from your home directory
2. `sui genesis --working-dir sui_local/`
3. `sui start --network.config sui_local/network.yaml`
4. Open another terminal
5. If you haven't already, setup your `pysui` environment as shown [above](#setup-environment)
6. Prefix `pysui` commands with `--local ~/sui_local/client.yaml`

Example:
```bash
wallet --local ~/sui_local/client.yaml gas
```