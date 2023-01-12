<img src="https://raw.githubusercontent.com/FrankC01/pysui/main/images//pysui_logo_color.png" width="150" height="200"/>

# pysui

Python Client SDK for Sui blockchain

**NOTICE: README FIRST**
SUI 0.21.0 introduces a change to keystore (file) keystring persist. We will be providing
a utility in the next release coming this week to transition existing keys to the new format for those
who want to keep them. See [sui change](https://github.com/MystenLabs/sui/pull/6989).
This utility SHOULD BE RUN BEFORE USING ANY OF `pysui` Sui Clients.

If you will be regenerating keys with the new binary install you can ignore the utility usage.

Stay tuned....

**SizaLena Milestone-0.7.0**

- Breaking changes
- 99.9% coverage (builders, return types, etc.) of **new** SUI 0.20.0 API (no support for secp256r1 yet)
- Subscriptions

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
