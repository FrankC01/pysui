<img src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" width="150" height="200"/>

# pysui

Python Client SDK for Sui blockchain

**Release-0.26.0**

- Runs with Sui binaries installed: `SuiConfig.default_config()`
- Runs without Sui binaries installed: `SuiConfig.user_config(...)`
- Runs localnode with [suibase](#local-node-support) `SuiConfig.sui_base_config()`
- Syncrhnoous and Asynchronous clients (provider) and transaction builders
- 100% parity with _SUI 1.5.0 RPC API_ on devnet
- 100% parity with _SUI 1.3.0 RPC API_ on testnet
- 100% parity with _SUI 1.3.0 RPC API_ on mainnet

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

We would appreciate any issues being reported in the [github issue log](https://github.com/FrankC01/pysui/issues)

**Discord**

Discord server [click here](https://discord.gg/uCGYfY4Ph4):

**PyPi for 0.25.0**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

## Additions

There is a companion package called [pysui-gadgets](https://github.com/FrankC01/pysui_gadgets) with a few utilities and ge-gaws that you may find interesting. It is a separate package also on on PyPi.

# Local node support

We've started leveraging [suibase](https://github.com/ChainMovers/suibase) in our testing and we've modified SuiConfig initialization to include an option for interacting directly with local nodes created by `suibase`

## Ready to run

Requires:

- Linux or macos (x86_64 or M1)
- python 3.10 or greater
- pkg-config
- libtool
- sui binaries to support `publish` Sui move packages

You will need `suibase` for interacting with local nodes, it is an indispensible addition to Sui developers tools!

### Setup environment

`python3 -m venv env`

If, instead, you want to work with repo latest source code then read [DEVELOP](https://github.com/FrankC01/pysui/blob/main/DEVELOP.md) from repo

### Activate

`source env/bin/activate`

or

`. env/bin/activate`

### Install `pysui`

`pip install pysui`

## Samples

See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
