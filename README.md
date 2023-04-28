<img src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" width="150" height="200"/>

# pysui

Python Client SDK for Sui blockchain

**Release-0.18.0**

We are hardening and finalizing code in preperation of Sui going live on mainnet. We anticipate that this release is
a _production ready candidate_. We don't expect further `pysui` _**breaking**_ changes with the caveat that if MystenLabs makes a
breaking change we may not be able to address with existing code.

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

We would appreciate any issues being reported in the [github issue log](https://github.com/FrankC01/pysui/issues)

We also have a channel in the [sui-base](https://github.com/sui-base/sui-base) Discord server [click here](https://discord.com/invite/Erb6SwsVbH):

- 100% coverage (builders, return types, etc.) for parity with _SUI 0.33.0 API_ on devnet/testnet

**PyPi for 0.18.0**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

## Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

## Additions

There is a companion package called [pysui-gadgets](https://github.com/FrankC01/pysui_gadgets) with a few utilities and ge-gaws that you may find interesting. It is a separate package also on on PyPi.

We've started leveraging [sui-base](https://github.com/sui-base/sui-base) in our testing and we've modified SuiConfig initialization to include an option for interacting directly with local nodes created by `sui-base`

## Ready to run

Requires:

- Linux or macos (x86_64 or M1)
- python 3.10 or greater
- pkg-config
- libtool
- sui binaries to support `publish` and mutli-sig signing function

You will need `suibase` to interacting with local nodes, it is an indispensible addition to Sui developers tools!

### Setup environment

`python3 -m venv env`

If, instead, you want to work with repo latest source code then read [DEVELOP](https://github.com/FrankC01/pysui/blob/main/DEVELOP.md) from repo

### Activate

`source env/bin/activate`

or

`. env/bin/activate`

### Install `pysui`

`pip install --use-pep517 pysui`

## Samples

See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
