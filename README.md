<img src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" width="150" height="200"/>

# pysui

Python Client SDK for Sui blockchain

**NOTICE: README FIRST**
SUI 0.21.0 introduces a change to keystore (file) keystring persist.

If you still have keystores from pre 0.21.0, run the utility [keys-to-0210](https://github.com/FrankC01/pysui/blob/main/samples/README.md)

This utility SHOULD BE RUN BEFORE USING `pysui` SDK or samples

If you have already regenerated keys with the SUI 0.21.0 binary install you can ignore the utility usage.

**Release-0.9.0**

- Breaking changes
- 99.9% coverage (builders, return types, etc.) of **new** SUI 0.20.1 API (no support for secp256r1 yet)

**PyPi**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

There is a companion package called [pysui-gadgets](https://github.com/FrankC01/pysui_gadgets) with a few utilities and ge-gaws that
you may find interesting. It is a separate package also on on PyPi.

**Documentation**

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

Refer to the [Changes](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md) log for recent additions, changes, fixes and removals...

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
