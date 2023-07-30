# develop pysui

SUI Python Client SDK for Sui

This document is for contributors or the curious developer

## Ready to run

Requires:

- Linux or macos (x86_64 or M1)
- Rust (stable) which also includes rustup and cargo
- python 3.10 or greater
- Rust (stable) which also includes rustup and cargo
- pkg-config
- libtool
- git
- sui binaries to support `publish` function

### Clone the pysui repo

`git clone git@github.com:FrankC01/pysui.git

### Setup virtual environment

`python3 -m venv env`

### Activate

`source env/bin/activate`

### Load core packages

`pip list`

- If you get a warning about upgrading pip... do so

`pip install -r requirements.txt`

### Load anciallary development packages

`pip install -r requirements-dev.txt` .

At this point you can decide to run samples, etc. or build and install
pysui into your own development environment. For the latter, first build the pysui
distribution:

`bin/package-build.sh`

You can then `pip install <LOCAL-PATH-TO-PYSUI-REPO>` to your own virtual environment
assuming you've set one up for own app/library development.

### Run sample wallet app for help

See [README](https://github.com/FrankC01/pysui/blob/main/README.md)
