<img src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" width="150" height="200"/>

# pysui

Python Client SDK for Sui blockchain

**NOTICE: README FIRST**

**Release-0.15.0**

This is a _**beta**_ release. The degree of changes from 0.27.1 to 0.29.1 are such that we have not completed thorough testing. We wanted to get something out there for users who have moved to 0.29.x devnet or testinet.

We would appreciate any issues being reported in the [github issue log](https://github.com/FrankC01/pysui/issues)

Also, the amount of changes have eviscerated the pytest implementations and should not be trusted at this time.


Sui release 0.29.0 brings **_significant_** breaking changes. Please read the CHANGLOG first as many builders and data models have changed or even been removed. Refer to the [Changes](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md) log for recent additions, changes, constraints, fixes and removals...

- 100% coverage (builders, return types, etc.) for parity with _SUI 0.29.0 API_ on devnet (see Testnet below)
  - Multi-sig not yet supported.
  - Programmable Transactions not yet supported. We are working on a TransactionBuilder and should have this available soon.


**PyPi**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

There is a companion package called [pysui-gadgets](https://github.com/FrankC01/pysui_gadgets) with a few utilities and ge-gaws that
you may find interesting. It is a separate package also on on PyPi.

**Documentation**

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

## Ready to run

Requires:

- Linux or macos (x86_64 or M1)
- python 3.10 or greater
- pkg-config
- sui binaries to support `publish` function

### Setup environment

`python3 -m venv env`

If, instead, you want to work with repo latest source code then read [DEVELOP](https://github.com/FrankC01/pysui/blob/main/DEVELOP.md) from repo

### Activate

`source env/bin/activate`

### Install `pysui`

`pip install pysui`

## Samples

See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
