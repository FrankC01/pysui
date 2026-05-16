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

**Release-0.99.1**

## PyPi current

**Release-0.99.0 - Released 2026-05-16**

- [Latest PyPi Version](https://pypi.org/project/pysui/)

> **⚠️ Deprecation Notice:** Release 1.0.0 will **remove** the legacy JSON-RPC client
> and synchronous GraphQL client. If your code uses either, migrate before upgrading.
> See the [Migration Guide](https://pysui.readthedocs.io/en/latest/migration_to_pysui_uci.html)
> on ReadTheDocs.

This is a significant release that redesigns pysui around the **Unified Client Interface (UCI)**.
It introduces breaking changes — see [CHANGELOG](https://github.com/FrankC01/pysui/blob/main/CHANGELOG.md)
for the full list.

### Unified Client Interface (UCI)

The **UCI** provides a protocol-agnostic programming model: write application code once and run it
transparently on either GraphQL or gRPC. The active transport is determined by configuration at
runtime — no code changes required to switch.

The UCI is built on four pillars:

1. **Thin Client Design** — pysui clients carry no convenience methods such as `get_coins` or
   `get_object`. All data access goes through typed request objects dispatched via
   `await client.execute(command=...)`, keeping the client surface small and transport-neutral.

2. **Protocol-Agnostic Command Execution** — Use `await client.execute(command=...)` with any
   `SuiCommand` subclass. The same code runs identically on both GraphQL and gRPC. Switching
   protocols requires only a configuration change.

3. **Shared Transaction Infrastructure** — PTBs with unified transaction builders and executor
   factories work across all protocols. Obtain a transaction builder via
   `await client.transaction(**kwargs)`, and executors via `await client.serial_executor(options=...)`
   or `await client.parallel_executor(options=...)`.

4. **Protocol-Level Access** — When you need capabilities beyond `SuiCommand`: use GraphQL
   QueryNodes via `execute_query_node` for custom queries, or gRPC Requests via
   `execute_grpc_request` for direct gRPC access.

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
