# pysui examples and utilities

Samples and utilities included in both the `pysui` repo as well as when installing through PyPi


## Examples:

- async-gas collects and prints all gas for all addresses found in configuration
- Sample [WalletG](#walletG) providing equivalent functionality as `sui client ...`

**Note:** If running from cloned repo, examples are started with `python -m ....`

- `python -m samples.walletg`
- `python -m samples.async_gasg`

**Note:** If running from PyPi install, examples can be started directly

- `wallet`
- `async-gas`

### Async Gas

Example demonstrating using the `pysui` asynchronus client. See [DEVELOP](../DEVELOP.md)

### WalletG

Implementation demonstrating most commands like the SUI CLI (i.e. `sui client ...`) using Sui GraphQL RPC.

#### WalletG Commands
```shell
usage: walletg.py [options] command [--command_options]

options:
  -h, --help            show this help message and exit
  -v, --version         Show pysui SDK version

commands:
  {aliases,active-address,addresses,new-address,gas,object,objects,merge-coin,split-coin,split-coin-equally,transfer-object,transfer-sui,pay,gql-query,tx-dryrun-data,tx-dryrun-kind,execute-signed-tx,package,publish,call,txns}
    aliases             Sui Address alias management
    active-address      Shows active address
    addresses           Shows all addresses
    new-address         Generate new address and keypair
    gas                 Shows gas objects and total mist. If owwner or alias not provided, defaults to active-address.
    object              Show object by id
    objects             Show all objects. If owwner or alias not provided, defaults to active-address.
    merge-coin          Merge two coins together. If owwner or alias not provided, defaults to active-address.
    split-coin          Split coin into one or more coins by amount. If owwner or alias not provided, defaults to active-address.
    split-coin-equally  Split coin into one or more coins equally. If owwner or alias not provided, defaults to active-address.
    transfer-object     Transfer an object from one address to another. If owwner or alias not provided, defaults to active-address.
    transfer-sui        Transfer SUI 'mist(s)' to a Sui address. If owwner or alias not provided, defaults to active-address.
    pay                 Send coin of any type to recipient(s). If owwner or alias not provided, defaults to active-address.
    gql-query           Execute a GraphQL query.
    tx-dryrun-data      Dry run a transaction block (TransactionData).
    tx-dryrun-kind      Dry run a transaction block kind (TransactionKind).
    execute-signed-tx   Dry run a transaction block (TransactionData).
    package             Show normalized package information
    publish             Publish a SUI package. If owwner or alias not provided, defaults to active-address.
    call                Call a move contract function. If owwner or alias not provided, defaults to active-address.
    txns                Show transaction information
```

### Run sample wallet app for events query help (wallet only)

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

### Run sample wallet app for transaction query help (wallet and walletg)

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

## Run Local (wallet only)

We've changed the abbility to operate with a local running node to rely on [sui-base](https://github.com/ChainMovers/suibase).

After you've cloned and installed `suibase` you can add the `--local` flag as shown below

Note that this is different if you are swiitching between `envs` using the standard sui configuration.

### Running with `sui-base`

1. Change to your home folder `cd ~/`
2. `git clone git@github.com:ChainMovers/suibase.git`
3. `cd suibase`
4. `./install`
5. `localnet start` <= This will download sui source code and start a local node (devnet level)
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

```bash
walletg gas
```

Or (if running pysui from repo clone):

```bash
python samples/wallet.py gas
```

```bash
python samples/walletg.py gas
```
