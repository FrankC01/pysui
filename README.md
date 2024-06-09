<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

[![Downloads](https://static.pepy.tech/badge/pysui/month)](https://pepy.tech/project/pysui)

Python Client SDK for Sui blockchain

## pysui SDK Dependencies

- Rust (stable) for installation of Sui Binaries (optional) and building `pysui-fastcrypto` Rust wrapper (required)
- Python version >= 3.10

**Note**: If moving from 0.51.0 or earlier it is recommended to start a new virtual environment and installing from PyPi!

## pysui SDK current (github)

**Release-0.63.0**

- Supports _SUI 1.27.x RPC API_
- Backwards compatable to _Sui 1.20.x RPC API_

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

## PyPi current

**Release-0.62.1 - Released 2024-06-08**

- Supports _SUI 1.27.x RPC API_
- Backwards compatable to _Sui 1.20.x RPC API_

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## Sui GraphQL RPC beta

MystenLabs announcement can be found [Here](https://github.com/mystenLabs/sui/issues/13700). This change transitions
from JSON RPC to GraphQL RPC.

Note: MystenLabs/Sui GraphQL RPC is available on devnet, testnet and mainnet. Note that devnet beta is still quite fragile and
we recommend using testnet beta. We are tracking a few failures we are monitoring [Isssues](https://github.com/FrankC01/pysui/issues?q=is%3Aissue+is%3Aopen++Sui+GraphQL+RPC).

### Sui GraphQL IDEs

  [Mainnet](https://sui-mainnet.mystenlabs.com/graphql)

  [Testnet](https://sui-testnet.mystenlabs.com/graphql)

  [Devnet](https://sui-devnet.mystenlabs.com/graphql/stable)

### pysui GraphQL support

**Note**: Functionality of pysui GraphQl should be considered beta, use in production is at your own risk.

With pysui 0.50.0 we released beta `pysui`'s beta alignment with MystenLabs strategy. The timeline of changes will keep up with the Timeline as noted in the Sui GraphQL annoucement. We are not yet stable and have Client and TransactionBuilder running against Sui GraphQL.

We continue to monitor and support changes from MystenLabs as they occur.

#### Examples

  - [Synchronous Client](https://github.com/FrankC01/pysui/blob/v0.59.0/pgql_s_example.py) - Examples for all supported QueryNode queries and mutations
  - [Asynchronous Client](https://github.com/FrankC01/pysui/blob/v0.59.0/pgql_a_example.py) - Examples for all supported QueryNode queries and mutations
  - [Synchronous TransactionBuilder](https://github.com/FrankC01/pysui/blob/v0.59.0/pgql_s_ptb.py) - Example of new pysui Transaction Builder leveraging Sui GraphQL

You can read pysui documentation on graphql beta [here](https://pysui.readthedocs.io/en/latest/graphql.html)

#### Known Issues
- Sui GraphQL fails fetching ProtocolConfiguration versions greater than 39
- No subscription support at this time


### FULL Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

### Changelog

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

### Issues and enhancement requests

We would appreciate using the [github issue log](https://github.com/FrankC01/pysui/issues) to let us know!

### Release/Publish Strategy

See [Strategies](https://github.com/FrankC01/pysui/blob/main/OP_STRATEGIES.md)

### Discord

Discord server [click here](https://discord.gg/uCGYfY4Ph4):

### Additions

There is a companion package called [pysui-gadgets](https://github.com/FrankC01/pysui_gadgets) with a few utilities and ge-gaws that you may find interesting. It is a separate package also on on PyPi.

### Local node support

We leverage [suibase](https://github.com/ChainMovers/suibase) for our testing and SuiConfig includes an option for interacting directly with local nodes created by `suibase`

## Ready to run

Requires:

- Linux or macos (x86_64 or Mx)
- Rust (stable) which also includes rustup and cargo
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
