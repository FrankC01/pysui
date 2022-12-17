
<img src="https://github.com/FrankC01/pysui/blob/main/images//pysui_logo_color.png" width="150" height="200" align="center"/>
<br clear="center"/>

# pysui

Python Client SDK for Sui blockchain

**BROKEN:** With SUI 0.19.0 the transaction signing has changed. This breaks `pysui` for executing transactions. All `Get`
types work fine however.  Hope to rectify this ASAP.

- 80% coverage (builders, return types, etc.) of **new** SUI 0.19.0 API (will address pre `pysui` "Lena" milestone)
- 90% coverage (builders, return types, etc.) of **new** SUI 0.18.0 API (lacking subscriptions, targeted for `pysui` "Lena" milestone)
- 100% coverage SUI 0.17.0

- PyPi Version: [latest](https://pypi.org/project/pysui/)

Refer to the [Changes](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md) log for recent additions, changes, fixes and removals...

`pysui` is documented:
* `latest [Here](https://pysui.readthedocs.io/en/latest/index.html)

## Ready to run
Requires:
 * Linux or macos (x86_64 or M1)
 * python 3.10 or greater
 * pkg-config
 * sui binaries to support `publish` function

### Setup environment
`python3 -m venv env`

If, instead, you want to work with repo latest source code then read [DEVELOP](https://github.com/FrankC01/pysui/blob/main/DEVELOP.md) from repo

### Activate
`source env/bin/activate`

### Install `pysui`
`pip install pysui`

## Samples
See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
