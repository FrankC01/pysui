# pysui examples and utilities

Samples and utilities included in both the `pysui` repo as well as when installing through PyPi

## Utilities

- keys-to-0210 Converts keystores prior to SUI 0.21.0 to keystore structure introduced in 0.21.0

## keys-to-0210 - Sui 0.20.0 and below keystore to 0.21.0 keystore convert

SUI 0.21.0 introduces a change to keystore (file) keystring persist. We are providing
this utility to transition existing keys to the new format for those
who want to keep any addresses created prior. For reference, see [sui change](https://github.com/MystenLabs/sui/pull/6989).

This utility SHOULD BE RUN BEFORE USING ANY OF `pysui` Sui Clients. If you've deleted your previous keystore and created
new keys with SUI 0.21.0 binaries, you can ignore running this utility

### Usage

Utilitiy operation:

1. Backs up the keystore file as defined by options below
2. Each ed25519, secp256k1 and/or secp256r1 key will be disassembled as per the SUI keystring definition
3. The converted keys will be written back to the source, overwritting original
4. If any error occurs, you can go to the path and `rm sui.keystore` and then `mv sui.keystore.bak sui.keystore`
5. If errors continue after trying again, please open an issue

NOTE: If invoking from pip installed `pysui` use `keys-to-0210` at the command line, else if running in cloned repo use `python samples/keys_to_2021.py`

```bash
fastfrank@~/frankc01/pysui $ keys-to-0210 -h
usage: keys-to-0210 [options] command [--command_options]

Convert ed25519, secp256k1 and secp256r1 keys to new 0.21.0 keystore format. A backup (.bak) of file is created

options:
  -h, --help            show this help message and exit
  -d, --default         Convert default SUI keystore keystrings
  -p USEPATH, --path-to-keystore USEPATH
                        Convert keystrings from keystore in path
```

`-d` Option will look for keys in keystore file to convert in `~/.sui/sui_config/sui.keystore`

`-p` Option allows you to specify path to keystore to convert keys in (example below)

### Example using `-p path_to_file` option

```bash
fastfrank@~/frankc01/pysui $ keys-to-0210 -p ~/sui_0201/sui_config/sui.keystore

Backing up existing keystore to '/Users/fastfrank/sui_0201/sui_config/sui.keystore.bak'
Created backup: '/Users/fastfrank/sui_0201/sui_config/sui.keystore.bak'

Converting keys in keystore: '/Users/fastfrank/sui_0201/sui_config/sui.keystore'
Old keystrings [
  "AKcurSAcUDafzezOTYPd+7wdBRbL1nCwa95ebl/Wc1wyEYI+ozwxNs1IuNZDiU1GL2B8Sqfsg7FgUT55m3If148=",
  "APZBPYYFPAF1bQLN6sAI362UcFJNkAfxyjbNc1m1njwDiOsV/paaGyppmwXVMGeH7vmG+2/BGd2iwp9yUHFIJ9s=",
  "AGbpmvhjNXKGLMkvMHnw03HwSerM3hAyEQ+OVzmGH43qqAt5XDjCGshLh/axD7MLHBcGkpTWdNWRJBPE7dNaCLY=",
  "AQOHn7v/wZzH9XNJAhl6jfSpaXDbtzPCCBzNGrtybVAtoc+Y9kNwaPpzYTY/0zVJvPMS60ou6qrVDLTzizC550Gc"
]
Converting AKcurSAcUDafzezOTYPd+7wdBRbL1nCwa95ebl/Wc1wyEYI+ozwxNs1IuNZDiU1GL2B8Sqfsg7FgUT55m3If148=
    keytype signature 0 len 65 -> ed25519

Converting APZBPYYFPAF1bQLN6sAI362UcFJNkAfxyjbNc1m1njwDiOsV/paaGyppmwXVMGeH7vmG+2/BGd2iwp9yUHFIJ9s=
    keytype signature 0 len 65 -> ed25519

Converting AGbpmvhjNXKGLMkvMHnw03HwSerM3hAyEQ+OVzmGH43qqAt5XDjCGshLh/axD7MLHBcGkpTWdNWRJBPE7dNaCLY=
    keytype signature 0 len 65 -> ed25519

Converting AQOHn7v/wZzH9XNJAhl6jfSpaXDbtzPCCBzNGrtybVAtoc+Y9kNwaPpzYTY/0zVJvPMS60ou6qrVDLTzizC550Gc
    keytype signature 1 len 66 -> secp256k1

Writing new keystrings [
  "ABGCPqM8MTbNSLjWQ4lNRi9gfEqn7IOxYFE+eZtyH9eP",
  "AIjrFf6WmhsqaZsF1TBnh+75hvtvwRndosKfclBxSCfb",
  "AKgLeVw4whrIS4f2sQ+zCxwXBpKU1nTVkSQTxO3TWgi2",
  "Ac+Y9kNwaPpzYTY/0zVJvPMS60ou6qrVDLTzizC550Gc"
]

Operation completed!
```

## Examples:

- async-gas collects and prints all gas for all addresses found in configuration
- async-sub Listens on generally broad events for Move events and Transaction events
- Sample [Wallet](#wallet) providing equivalent functionality as `sui client ...`

**Note:** If running from cloned repo, examples are started with `python -m ....`

- `python -m sample.wallet`
- `python -m sample.async_gas`
- `python -m sample.async_sub`

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
