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
`pip install -U --upgrade-strategy eager pysui` if upgrading.

### Without Rust on machine

1. Fetch the latest [pysui-fastcrypto](https://github.com/FrankC01/pysui-fastcrypto) binary from the release assets, unzip and `pip` install it
2. `pip install pysui`

## pysui SDK current (github)

**Release-0.99.0**

**BREAKING CHANGES**

- `profile_names(in_group=...)` no longer mutates the active group as a
side effect — callers relying on this behavior must call `make_active()` explicitly

- `use_account_for_gas` moved from the transaction constructor to build-time
parameters on build(), build_and_sign(), and transaction_data()

- `MoveFunctionGQL.parameters` changed from `list[dict]` to `list[OpenMoveTypeGQL]` — any code iterating raw dicts from function metadata must migrate to the new dataclass accessors
- `MoveFunctionGQL.returns` changed from `Optional[list]` to `list[OpenMoveTypeGQL]` — same migration required

- `GqlProtocolClient.transaction()` is now `async def` — all call sites must add `await`

- `SerialTransactionExecutor` renamed to `GqlSerialTransactionExecutor` — protocol prefix added
  to all executor class names for consistency; update imports accordingly

- `AsyncSuiGQLClient` renamed to `GqlProtocolClient`; `SuiGrpcClient` renamed to `GrpcProtocolClient` — update all imports and type annotations; old names no longer exist

## PyPi current

**Release-0.98.0 - Released 2026-04-13**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

### Client Instantiation Migration Guide

Release 0.98.0 introduces `client_factory` and `PysuiConfiguration` as the preferred way to create clients.
The legacy `SuiConfig`, `SuiClient` (JSON-RPC), and `SuiGQLClient` (synchronous GraphQL) are deprecated
and will be removed in a future release.

#### Before (deprecated)

**JSON-RPC synchronous client:**
```python
from pysui import SuiConfig
from pysui.sui.sui_clients.sync_client import SuiClient

config = SuiConfig.default_config()
client = SuiClient(config=config)
```

**JSON-RPC asynchronous client:**
```python
from pysui import SuiConfig
from pysui.sui.sui_clients.async_client import SuiClient

config = SuiConfig.default_config()
client = SuiClient(config=config)
```

**GraphQL synchronous client:**
```python
from pysui import PysuiConfiguration
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient

client = SuiGQLClient(pysui_config=PysuiConfiguration())
```

**GraphQL asynchronous client (direct instantiation):**
```python
from pysui import PysuiConfiguration
from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient

client = AsyncSuiGQLClient(pysui_config=PysuiConfiguration())
```

**gRPC asynchronous client (direct instantiation):**
```python
from pysui import PysuiConfiguration
from pysui.sui.sui_grpc.pgrpc_clients import SuiGrpcClient

client = SuiGrpcClient(pysui_config=PysuiConfiguration())
```

#### After (recommended)

Use `client_factory` with `PysuiConfiguration`. The active group's `group_protocol` setting
determines whether a `AsyncSuiGQLClient` (GraphQL) or `SuiGrpcClient` (gRPC) is returned.
Both implement the `PysuiClient` abstract interface.

**Default active group (protocol auto-detected from config):**
```python
from pysui import PysuiConfiguration, client_factory

config = PysuiConfiguration()
client = client_factory(config)   # Returns AsyncSuiGQLClient or SuiGrpcClient
```

**Non-standard group with explicit protocol:**
```python
from pysui import PysuiConfiguration, GroupProtocol, client_factory

config = PysuiConfiguration()
# group_name selects a named profile group; protocol must be specified explicitly
client = client_factory(config, group_name="my-custom-group", protocol=GroupProtocol.GRAPHQL)
```

**Async usage pattern:**
```python
import asyncio
from pysui import PysuiConfiguration, client_factory

async def main():
    config = PysuiConfiguration()
    client = client_factory(config)
    txn = client.transaction(sender=config.active_address)
    # ... build and execute transaction ...

asyncio.run(main())
```

Added support for Mysten `address balance`

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
