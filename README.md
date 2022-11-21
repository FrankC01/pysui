# pysui

Python SUI client SDK for Sui - WIP and expect significant refactoring

- Repo Version: Unpublished **0.1.0**
- PyPi Version: **0.0.11**

Refer to the [Change](CHANGELOG.md) log for recent additions, changes, fixes and removals...

## Known issues or missing capability
* Doesn't support `sui_batchTransaction` RPC API yet
* Doesn't use mnemonics yet (see [Issue](https://github.com/FrankC01/pysui/issues/9))

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
### Example 1 - Query Gas
Here is a sample script demonstrating the fundementals for effective pysui usage:
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

## Sample Wallet
Implementation demonstrating most SUI RPC API calls like the SUI CLI (i.e. `sui client ...`).

**NOTE**: Sample wallet uses synchronous SuiClient. I leave it up to the ambitious to
write similar for asynchronous SuiAsynchClient

### Run sample wallet app for help
- pysui 0.0.6 or 0.0.7: `python -m samples.wallet`
- pysui >= 0.0.7: `wallet`

#### Output
```bash
usage: wallet.py [options] command [--command_options]

options:
  -h, --help            show this help message and exit
  -v, --version         Show pysui SDK version

commands:
  {active-address,addresses,new-address,gas,object,objects,rpcapi,committee,faucet,merge-coin,split-coin,transfer-object,transfer-sui,pay,paysui,payallsui,package,publish,call,events,txns}
    active-address      Shows active address
    addresses           Shows all addresses
    new-address         Generate new address and keypair
    gas                 Shows gas objects and total mist
    object              Show object by id
    objects             Show all objects
    rpcapi              Show Sui RPC API information
    committee           Show committee info for epoch
    faucet              Get additional gas from SUI faucet
    merge-coin          Merge two coins together
    split-coin          Split coin into one or more coins
    transfer-object     Transfer an object from one address to another
    transfer-sui        Transfer SUI 'mist(s)' to a Sui address
    pay                 Send coin of any type to recipient(s)
    paysui              Send SUI coins to a list of addresses.
    payallsui           Send all SUI coin(s) to recipient(s)
    package             Show normalized package information
    publish             Publish a SUI package
    call                Call a move contract function
    events              Show events for types
    txns                Show transaction information
```

### Run sample wallet app for events query help
`wallet events -h`

### Output
```bash
usage: events subcommand [--subcommand_options]

options:
  -h, --help            show this help message and exit

subcommand:
  {all,module,struct,object,recipient,sender,time,transaction}
    all                 Return all events
    module              Return events emitted in a specified Move module
    struct              Return events with the given move structure name
    object              Return events associated with the given object
    recipient           Return events associated with the given recipient
    sender              Return events associated with the given sender
    time                Return events emitted in [start_time, end_time) interval
    transaction         Return events emitted by the given transaction
```

### Run sample wallet app for transaction query help
`wallet txns -h`
`wallet txns txnsq -h`

### Output
```bash
usage: txns subcommand [--subcommand_options]

options:
  -h, --help         show this help message and exit

subcommand:
  {count,txn,txnsq}
    count            Return total transaction count from server
    txn              Return transaction information
    txnsq            Show events for types

wallet txns txnsq -h

usage: txns subcommand [--subcommand_options]

options:
  -h, --help            show this help message and exit

subcommand:
  {all,movefunc,input,mutated,from,to}
    all                 Return all events
    movefunc            Return transaction events for move function.
    input               Return transaction events for the input object.
    mutated             Return transaction events for the mutate object.
    from                Return transaction events from sender address.
    to                  Return transaction events from recipient address.
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