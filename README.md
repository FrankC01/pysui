<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

Python Client SDK for Sui blockchain

- Supports _SUI 1.15.x RPC API_
- Backwards compatable to _Sui 1.10.x RPC API_

## pysui SDK current (github)

**Release-0.40.0**

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

## PyPi current

**Release-0.40.0**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## pysui SDK Dependencies

- Rust (stable) for installation of Sui Binaries (optional) and building `pysui-fastcrypto` Rust wrapper (required)
- Python version >= 3.10


## Sui GraphQL RPC service lies ahead

MystenLabs announcement can be found [Here](https://github.com/mystenLabs/sui/issues/13700). This change transitions
from JSON RPC to GraphQL RPC.

We will be changing `pysui` to begin aligning with MystenLabs strategy. The timeline of changes will keep up with the Timeline as noted in their annoucement:

1. December 2023: We will introduce a GraphQL `SuiClient` (experimental) and begin implementing parallel 'read' methods as found in the current SuiClient.
2. January 2024: Continue with SuiClient parity changes and expose underlying GraphQL for users to craft their
own queries.
3. February 2024: Deprecate pysui Builders and existing SuiClients and enable SuiClient GraphQL 'streaming' support.
4. March 2024: Remove Builders and Obsolete SuiClients and bump pysui to version 1.0.0.


### Documentation

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
