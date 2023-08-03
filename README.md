<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

Python Client SDK for Sui blockchain

### pysui SDK Dependencies

- Rust (stable) for installation of Sui Binaries and building of the upcoming (0.33.0) `pysui-fastcrypto` wrapper
- Sui Binaries if using the Sui configuration (keystores, evironments) and publishing/upgradinge Sui packages
- Python version >= 3.10

### Release/Publish Strategy

See [Strategies](https://github.com/FrankC01/pysui/blob/main/OP_STRATEGIES.md)

## pysui SDK current (github)

**Release-0.32.0**

**BREAKING CHANGE**

The SuiTransaction execute method's `gas_budget` argument now strictly sets the gas budget for the transaction. Prior, an inspection
would be run and pysui used the greater of the two. Now, `gas_budget`'s default is an emptry string ("") and by leaving it that
way a dryRun will be run prior to execution to set the budget.


- Supports _SUI 1.7.x RPC API_
- Backwards compatable to _Sui 1.5.x RPC API_

## PyPi current: 0.32.0

**BREAKING CHANGE**

The SuiTransaction execute method's `gas_budget` argument now strictly sets the gas budget for the transaction. Prior, an inspection
would be run and pysui used the greater of the two. Now, `gas_budget`'s default is an emptry string ("") and by leaving it that
way a dryRun will be run prior to execution to set the budget.

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
