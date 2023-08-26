<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

Python Client SDK for Sui blockchain

### pysui SDK Dependencies

- Rust (stable) for installation of Sui Binaries (optional) and building `pysui-fastcrypto` Rust wrapper (required)
- Python version >= 3.10

### Release/Publish Strategy

See [Strategies](https://github.com/FrankC01/pysui/blob/main/OP_STRATEGIES.md)

## pysui SDK current (github)

**Release-0.34.0**

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

- Supports _SUI 1.9.x RPC API_
- Backwards compatable to _Sui 1.6.x RPC API_


## PyPi current

**Release-0.34.0 includes BREAKING CHANGE**

With this release, the `bip-utils` library has been removed in favor of [pysui-fastcrypto](https://github.com/FrankC01/pysui-fastcrypto). This is a Python wrapper around the MystenLabs [fastcrypto](https://github.com/MystenLabs/fastcrypto) Rust crate used in Sui itself.

Because of this change, pysui now requires Rust and Cargo to be installed!
See [Rust Install](https://www.rust-lang.org/tools/install). This will allow the Rust crate and wrapper to be
built specifically for your platform.

- [Latest PyPi Version](https://pypi.org/project/pysui/)

### Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

### Changelog

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

### Issues and enhancement requests

We would appreciate using the [github issue log](https://github.com/FrankC01/pysui/issues) to let us know!

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
