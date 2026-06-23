<p align="center">
  <img width="150" height="200" src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" alt='PySui'>
</p>

# pysui

[![Downloads](https://static.pepy.tech/badge/pysui/month)](https://pepy.tech/project/pysui)

Python Client SDK for Sui blockchain

## A cup of coffee

- The team could use a cup or carafe. Sui address `0xc45e5ea887e037ddc6a482afa412773b4291c8fdc338f647fb0fcea324975d8e`

## pysui SDK install

### With Rust on machine

`pip install pysui` if first time or
`pip install -U pysui` if upgrading.

For zkLogin and SEAL features, install with the optional extra features

`pip install pysui[zklogin-seal]` if first time or
`pip install -U pysui[zklogin-seal]` if upgrading

### Without Rust on machine

1. Fetch the latest [pysui-fastcrypto](https://github.com/FrankC01/pysui-fastcrypto) wheel from the release assets, unzip and `pip` install it
2. `pip install pysui`

For zkLogin and SEAL features

1. Fetch the pysui-fastcrypto wheel as noted above
2. Fetch the latest [pysui-crypto](https://github.com/Suitters/pysui-crypto) wheel from the release assets and `pip` install it
3. `pip install pysui[zklogin-seal]`

## pysui SDK current (github)

**Release-1.2.0**

Future releases are in branches named `release_X.Y.Z`

## PyPi current

**Release-1.1.0 - Released 2026-06-23**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

This release brings _zkLogin and Mysten SEAL capabilities_ (optional install).
In addition, _json export and import of transaction (PTB) compatible with Mystens TS-SDK_.

### FULL Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

### Changelog

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

### Issues and enhancement requests

We would appreciate using the [github issue log](https://github.com/FrankC01/pysui/issues) to let us know!

### Release/Publish Strategy

See [Strategies](https://github.com/FrankC01/pysui/blob/main/OP_STRATEGIES.md)

### Discord

Discord server invitation is [Found here](https://discord.gg/uCGYfY4Ph4):

## Sample utilities

**Note**: Sample utilities are implemented using pysui UCI

See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
