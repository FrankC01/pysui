# pysui

Experimental (pre-alpha) python client side toolkit for Sui - WIP and expect significant refactoring

## Ready to run
Requires:
 * Linux or macos (x86_64 or M1)
 * python 3.10 or greater
 * pkg-config

## Run with devnet
By default, `pysui` will use the `client.yaml` configuration found in `.sui/sui_config/`. See [below](#run-local) for running
with different configuration (e.g. Local)

### Setup environment
`python3 -m venv pysuienv`

### Activate
`source pysuienv/bin/activate`

### Load packages
`pip list`

  * If you get a warning about upgrading pip... do so

`pip install -r requirements.txt` .

  * If you get an error with secp256k1 then:
    `pip install wheel` and try to install requirements again

### Run sample wallet app for help
`python -m samples.wallet`

#### Output
```bash
usage: wallet.py [options] command [--command_options]

options:
  -h, --help            show this help message and exit

commands:
  {active-address,addresses,new-address,gas,object,objects,rpcapi,merge-coin,split-coin,transfer-object,transfer-sui,pay,paysui,payallsui,package-object,package,publish,call,events,committee}
    active-address      Shows active address
    addresses           Shows all addresses
    new-address         Generate new address and keypair
    gas                 Shows gas objects and total mist
    object              Show object by id
    objects             Show all objects
    rpcapi              Show Sui RPC API information
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
    events              Show events for types
    committee           Show committee info for epoch
```
### Run sample wallet app for more help
`python -m samples.wallet events -h`

### Output
```bash
usage: events subcommand [--subcommand_options]

options:
  -h, --help            show this help message and exit

subcommand:
  {module,struct,object,recipient,sender,time,transaction}
    module              Return events emitted in a specified Move module
    struct              Return events with the given move event struct name
    object              Return events associated with the given object
    recipient           Return events associated with the given recipient
    sender              Return events associated with the given sender
    time                Return events emitted in [start_time, end_time) interval
    transaction         Return events emitted by the given transaction
```

## Run Local
To run locally, especially useful when devnet is down, below are the steps to follow:

### Setup local (example from home directory)
1. `mkdir sui_local` from your home directory
2. `sui genesis --working-dir sui_local/`
3. `sui start --network.config sui_local/network.yaml`
4. Open another terminal
5. `sui-node --config-path sui_local/fullnode.yaml`
6. If you haven't already, setup your `pysui` environment as shown [above](#setup-environment)
7. Prefix `pysui` commands with `--cfg ~/sui_local/client.yaml`

Example:
```bash
python -m samples.wallet --cfg ~/sui_local/client.yaml gas
```