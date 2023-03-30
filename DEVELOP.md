# develop pysui

SUI Python Client SDK for Sui

This document is for contributors or the curious developer

## Ready to run
Requires:
 * Linux or macos (x86_64 or M1)
 * python 3.10 or greater
 * pkg-config
 * git
 * sui binaries to support `publish` function

### Clone this repo

`git clone git@github.com:FrankC01/pysui.git

### Setup virtual environment

`python3 -m venv env`

### Activate
`source env/bin/activate`

### Load core packages
`pip list`

  * If you get a warning about upgrading pip... do so

`pip install -r requirements.txt`

  * If you get an error with secp256k1 then:
    `pip install wheel` and try to install requirements again

### Load anciallary development packages

`pip install -r requirements-dev.txt` .

### Run sample wallet app for help
See [README](https://github.com/FrankC01/pysui/blob/main/README.md)
