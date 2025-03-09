<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

[![Downloads](https://static.pepy.tech/badge/pysui/month)](https://pepy.tech/project/pysui)

Python Client SDK for Sui blockchain

## pysui SDK Dependencies

- Rust (stable) for installation of Sui Binaries (optional) and building `pysui-fastcrypto` Rust wrapper (required)
- Python version >= 3.10

## pysui SDK current (github)

**Release-0.81.0**

- Supports _SUI 1.44.x JSON RPC API_, _SUI 1.43.x GRAPHQL_
- JSON RPC API backwards compatable to _Sui 1.36.x_

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

## PyPi current

**Release-0.80.0 - Released 2025-03-08**

- Supports _SUI 1.44.x JSON RPC API_, _SUI 1.43.x GRAPHQL_
- JSON RPC API backwards compatable to _Sui 1.36.x_

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## Sui GraphQL RPC beta

MystenLabs announcement can be found [Here](https://github.com/mystenLabs/sui/issues/13700). This change transitions
from JSON RPC to GraphQL RPC.

Note: MystenLabs/Sui GraphQL RPC is available on devnet, testnet and mainnet. Note that devnet beta is usable but
we recommend using testnet or mainnet beta for stability. We are tracking a few failures we are monitoring [Isssues](https://github.com/FrankC01/pysui/issues?q=is%3Aissue+is%3Aopen++Sui+GraphQL+RPC).

### Sui GraphQL IDEs

  [Mainnet](https://sui-mainnet.mystenlabs.com/graphql)

  [Testnet](https://sui-testnet.mystenlabs.com/graphql)

  [Devnet](https://sui-devnet.mystenlabs.com/graphql)

### pysui GraphQL support

**Note**: Functionality of pysui GraphQl should be considered beta, use in production at your own risk.

With pysui 0.50.0 we released beta `pysui`'s beta alignment with MystenLabs strategy. The timeline of changes will keep up with the Timeline as noted in the Sui GraphQL annoucement. We are not yet stable however we have Clients and TransactionBuilder running against Sui GraphQL.

We continue to monitor and support changes from MystenLabs as they occur.

#### Examples

  - **_pgql_s_example_** - Synchronous examples for all supported QueryNode queries and mutations
  - **_pgql_a_example_** - Asynchronous examples for all supported QueryNode queries and mutations
  - **_pgql_s_ptb_** - Example of new pysui Transaction Builder leveraging Sui GraphQL

You can read pysui documentation on graphql beta [here](https://pysui.readthedocs.io/en/latest/graphql.html)

#### Known Issues
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

### Local node support

Note: Only supported for JSON RPC clients, GraphQL not available for suibase at this time.

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
