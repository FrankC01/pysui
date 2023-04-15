# pysui examples and utilities

Samples and utilities included in both the `pysui` repo as well as when installing through PyPi

## Examples:

- async-gas collects and prints all gas for all addresses found in configuration
- async-sub Listens on generally broad events for Move events (Transaction events removed by Sui 0.27.0)
- Sample [Wallet](#wallet) providing equivalent functionality as `sui client ...`

**Note:** If running from cloned repo, examples are started with `python -m ....`

- `python -m samples.wallet`
- `python -m samples.async_gas`
- `python -m samples.async_sub`

**Note:** If running from PyPi install, examples can be started directly

- `wallet`
- `async-gas`
- `async-sub`

### Async Gas

Example demonstrating using the `pysui` SuiAsynchClient. See [DEVELOP](../DEVELOP.md)

### Wallet

Implementation demonstrating most SUI RPC API calls like the SUI CLI (i.e. `sui client ...`).

## Run with devnet or local

By default, `pysui` will use the `client.yaml` configuration found in `.sui/sui_config/`. See [below](#run-local) for running
with different configuration (e.g. Local)

**NOTE**: Sample wallet uses synchronous SuiClient. I leave it up to the ambitious to
write similar for asynchronous SuiAsynchClient

### Run sample wallet app for help

Depending on how you installed pysui:

- `python -m samples.wallet` (from cloned repo)
- `python samples/wallet.py` (from cloned repo)
- `wallet` (from PyPi install)

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

We've changed the abbility to operate with a local running node to rely on [sui-base](https://github.com/sui-base/sui-base).

After you've cloned and installed `sui-base` you can add the `--local` flag as shown below

Note that this is different if you are swiitching between `envs` using the standard sui configuration.

### Running with `sui-base`

1. Change to your home folder `cd ~/`
2. `git clone git@github.com:sui-base/sui-base.git`
3. `cd sui-base`
4. `./install`
5. `localnet start` <= This will download sui source code and start a local node
6. Finally, add the `--local` switch to the command line `pysui` wallet or other samples

Example:

```bash
wallet --local gas
```

Or (if running pysui from repo clone):

```bash
python samples/wallet.py --local gas
```

### Running with standard sui configuration

If your standard configuration has `envs` that include `localnet`

1. `sui client switch --env localnet

Example:

```bash
wallet gas
```

Or (if running pysui from repo clone):

```bash
python samples/wallet.py gas
```
