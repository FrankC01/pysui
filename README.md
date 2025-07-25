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

`pip install pysui`

### Without Rust on machine

1. Fetch the latest [pysui-fastcrypto](https://github.com/FrankC01/pysui-fastcrypto) binary from the release assets, unzip and `pip` install it
2. `pip install pysui`

## pysui SDK current (github)

**Release-0.87.0**

- Supports _SUI 1.48.x JSON RPC API_, _SUI 1.50.x GRAPHQL_
- JSON RPC API backwards compatable to _Sui 1.41.x_

## PyPi current

**Release-0.86.0 - Released 2025-06-18**

- Supports _SUI 1.48.x JSON RPC API_, _SUI 1.50.x GRAPHQL_
- JSON RPC API backwards compatable to _Sui 1.41.x_

[BREAKING change](https://github.com/FrankC01/pysui/issues/313) The constructor of PysuiConfiguration no
longer creates the PysuiConfig.json file if does not exist. First time users must call class method `PysuiConfiguration.initialize_config`.
See [documentation](https://pysui.readthedocs.io/en/latest/pyconfig.html#first-time-instantiation).

- [Latest PyPi Version](https://pypi.org/project/pysui/)

### FULL Documentation

- [ReadTheDocs](https://pysui.readthedocs.io/en/latest/index.html)

### gRPC Support

- Refer to [pysui-grpc](https://github.com/FrankC01/pysui/blob/main/PYSUI_GRPC.md)

### GraphQL Support

- Refer to [pysui-graphql](https://github.com/FrankC01/pysui/blob/main/PYSUI_GRAPHQL.md)

### Changelog

See [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)

### Issues and enhancement requests

We would appreciate using the [github issue log](https://github.com/FrankC01/pysui/issues) to let us know!

### Release/Publish Strategy

See [Strategies](https://github.com/FrankC01/pysui/blob/main/OP_STRATEGIES.md)

### Discord

Discord server [click here](https://discord.gg/uCGYfY4Ph4):

### Local node support

Note: Only supported for JSON RPC clients, GraphQL not available for suibase at this time.

We leverage [suibase](https://github.com/ChainMovers/suibase) for our testing and SuiConfig includes an option for interacting directly with local nodes created by `suibase`

## Sample utilities

See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
