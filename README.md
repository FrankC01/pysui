# pysui

Experimental (pre-alpha) python client side toolkit for Sui - WIP and expect significant refactoring

## Run sample
### Setup environment
`python3 -m venv pysuienv`

### Activate
`source pysuienv/bin/activate`

### Load packages
`pip install -r requirements.txt`

### Run sample wallet app for help
`python -m samples.wallet`

#### Output
```bash
usage: wallet.py [-h] {active-address,addresses,gas,new-address,object,objects,rpcapi} ...

options:
  -h, --help            show this help message and exit

commands:
  {active-address,addresses,gas,new-address,object,objects,rpcapi}
    active-address      Shows active address
    addresses           Shows all addresses
    gas                 Shows gas objects
    new-address         Generate new address and keypair
    object              Show object by id
    objects             Show all objects
    rpcapi              Display Sui RPC API information
```