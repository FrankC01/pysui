<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

Python Client SDK for Sui blockchain

## pysui SDK Dependencies

- Rust for installation of Sui Binaries and building the `pysui-fastcrypto` package
- Sui Binaries if using the Sui configuration (keystores, evironments) and publishing/upgradinge Sui packages
- Python, at a minimum, version 3.10

## pysui SDK current

**Release-0.31.0**

- Supports _SUI 1.6.x/1.7.x RPC API_ on devnet
- Supports _SUI 1.6.x/1.7.x RPC API_ on testnet
- Supports _SUI 1.5.x/1.6.x RPC API_ on mainnet

**Deprecation Strategy**

Functions, classes and methods marked 'Deprecated' will be removed 2-3 releases after initial marking. Refer to
the CHANGELOG.md.

**Changelog**

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

We would appreciate any issues being reported in the [github issue log](https://github.com/FrankC01/pysui/issues)

**Discord**

Discord server [click here](https://discord.gg/uCGYfY4Ph4):

**PyPi for 0.31.0**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

## Additions

There is a companion package called [pysui-gadgets](https://github.com/FrankC01/pysui_gadgets) with a few utilities and ge-gaws that you may find interesting. It is a separate package also on on PyPi.

# Local node support

We've started leveraging [suibase](https://github.com/ChainMovers/suibase) in our testing and we've modified SuiConfig initialization to include an option for interacting directly with local nodes created by `suibase`

## Ready to run

Requires:

- Linux or macos (x86_64 or Mx)
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
