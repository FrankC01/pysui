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

**Release-0.92.0**

DryRunTransactionKind `tx_meta` argument requires 'sender' This is due to a constraint in Sui GraphQL.

**ANNOUNCE** This release will be the last one for JSON RPC issues. Strongly advised
to move to pysui gRPC or GraphQL.


## PyPi current

**Release-0.91.0 - Released 2025-10-02**

**BREAKING CHANGES**

Transition to GraphQL BETA support. This will require changing the GraphQL URLs in `PysuiConfig.json`.
See [pysui-graphql](https://github.com/FrankC01/pysui/blob/main/PYSUI_GRAPHQL.md)

- [Latest PyPi Version](https://pypi.org/project/pysui/)

Includes support for gRPC BETA: queries, programmable transactions, subscriptions and transaction execution.

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

Discord server invitation is [Found here](https://discord.gg/uCGYfY4Ph4):

### Local node support

Note: Only supported for JSON RPC clients, GraphQL not available for suibase at this time.

We leverage [suibase](https://github.com/ChainMovers/suibase) for our testing and SuiConfig includes an option for interacting directly with local nodes created by `suibase`

## Sample utilities

**Note**: Sample utiities are implemented using GraphQL

See [samples](https://github.com/FrankC01/pysui/blob/main/samples/README.md)
