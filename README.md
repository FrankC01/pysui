# pysui

Python SUI client SDK for Sui - WIP and expect significant refactoring

- Repo Version: Unpublished **0.2.0**
- PyPi Version: **0.1.1**

Refer to the [Change](CHANGELOG.md) log for recent additions, changes, fixes and removals...

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
See DEVELOP.md

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
  {active-address,addresses,new-address,gas,object,objects,rpcapi,committee,faucet,merge-coin,split-coin,split-coin-equally,transfer-object,transfer-sui,pay,paysui,payallsui,package,publish,call,events,txns}
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
    split-coin          Split coin into one or more coins by amount
    split-coin-equally  Split coin into one or more coins equally
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