<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

Python Client SDK for Sui blockchain


## pysui SDK Dependencies

- Rust (stable) for installation of Sui Binaries (optional) and building `pysui-fastcrypto` Rust wrapper (required)
- Python version >= 3.10

**Note**: If moving from 0.51.0 or earlier it is recommended to start a new virtual environment and installing from PyPi!

## pysui SDK current (github)

**Release-0.56.0**

- Supports _SUI 1.22.x RPC API_
- Backwards compatable to _Sui 1.18.x RPC API_

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

## PyPi current

**Release-0.55.0 - Released 2024-03-22**

- Supports _SUI 1.22.x RPC API_
- Backwards compatable to _Sui 1.18.x RPC API_

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## Sui GraphQL RPC beta

MystenLabs announcement can be found [Here](https://github.com/mystenLabs/sui/issues/13700). This change transitions
from JSON RPC to GraphQL RPC.

With pysui 0.50.0 we released `pysui`'s initial alignment with MystenLabs strategy. The timeline of changes will keep up with the Timeline as noted in the Sui GraphQL annoucement.

Note: The MystenLabs/Sui GraphQL RPC is currently only available on testnet

pysui 0.52.0 contains initial support for our February 2024 target:

1. **_December 2023_**: Synchronous and asynchronous GraphQL clients (experimental) with intial 'read' queries parallel to current pysui read _Builders_. Also expose underlying GraphQL for users to craft their own queries.
2. **_January 2024_**: Continue with GraphQL and Builder parity changes. Mysten to roll out live data to devnet, testnet and mainnet. Note, only testnet was available in Jan '24.
3. **February 2024**: Begin deprecatating pysui Builders and existing SuiClients and enable SuiClient GraphQL 'streaming' support. Note, only testnet and mainnet are currently available in Feb '24, in addition:

  - DryRun and Execute are available
  - streaming is not yet supported
  - Examples for all supported queries and mutations are in `pgql_s_example`` (Synchronous) and `pgql_a_example` (Asynchronous)
  - Demo of new pysui Transaction Builder leveraging Sui GraphQL in `pgql_s_ptb`
4. Sometime in 2024: Remove Builders, obsolete SuiClients and SuiTransaction, and bump pysui to version 1.0.0.

You can read pysui documentation on graphql beta [here](https://pysui.readthedocs.io/en/latest/graphql.html)

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
