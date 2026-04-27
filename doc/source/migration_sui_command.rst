Migrating to the Unified Client Interface
==========================================

Introduction
------------

Prior to pysui 0.99.0, writing code against the SDK required importing and using protocol-specific
client classes and query or request classes — :class:`AsyncSuiGQLClient` together with
:mod:`pysui.sui.sui_pgql.pgql_query` for GraphQL, or :class:`SuiGrpcClient` together with
:mod:`pysui.sui.sui_grpc.pgrpc_requests` for gRPC. The same blockchain operation required two
different APIs depending on which transport was active.

pysui 0.99.0 introduces the **Unified Client Interface (UCI)** — a protocol-agnostic programming
model built on two abstractions:

- :class:`AsyncClientBase` — the unified client type; use it instead of a protocol-specific client class
- :class:`SuiCommand` — protocol-agnostic command objects covering the core blockchain interaction
  patterns: querying data, building transactions, and executing them

The UCI reduces the number of protocol-specific classes you need to understand. More importantly,
new capabilities in querying, transaction building, and execution will be introduced at the UCI
level — making them available across all transports automatically, without requiring separate
protocol-specific implementations.

This guide covers the UCI changes and helps you migrate from the legacy protocol-specific APIs.

AsyncClientBase
---------------

:class:`AsyncClientBase` is the abstract base class for all async pysui clients. Both
:class:`AsyncSuiGQLClient` and :class:`SuiGrpcClient` inherit from it. Type your client
parameter as :class:`AsyncClientBase` and your code becomes transport-agnostic — the active
protocol is determined by :class:`PysuiConfiguration` at runtime.

:func:`client_factory` returns :class:`AsyncClientBase`. Update your type annotations accordingly:

.. code-block:: python

    # Old — protocol-specific type
    from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
    client: AsyncSuiGQLClient = client_factory(config)  # binds you to GraphQL

    # New — UCI type
    from pysui import AsyncClientBase, client_factory
    client: AsyncClientBase = client_factory(config)    # works with any transport

:class:`AsyncClientBase` supports the async context manager protocol for automatic resource
cleanup:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory, AsyncClientBase
    import pysui.sui.sui_common.sui_commands as cmd

    async def main():
        config = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(config) as client:
            result = await client.execute(command=cmd.GetCoins(owner=config.active_address))
            if result.is_ok():
                print(result.result_data)

The :meth:`execute(command=...)` method is the single UCI dispatch point — it accepts a
:class:`SuiCommand` object and routes it to the appropriate protocol internally. The
:class:`SuiCommand` abstractions are covered in the sections below.

Quick Start
-----------

**Old approach** — different APIs per protocol:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
    import pysui.sui.sui_pgql.pgql_query as qn

    gql_client: AsyncSuiGQLClient = client_factory(PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP))
    result = await gql_client.execute_query_node(with_node=qn.GetCoins(owner=addr))

    # gRPC version:
    from pysui.sui.sui_grpc.pgrpc_clients import SuiGrpcClient
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    grpc_client: SuiGrpcClient = client_factory(PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP))
    result = await grpc_client.execute_grpc_request(request=rn.GetCoins(owner=addr))

**New approach** — unified interface:

.. code-block:: python

    from pysui import AsyncClientBase, client_factory
    import pysui.sui.sui_common.sui_commands as cmd

    # Works with any protocol; client type is determined at runtime
    config = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    client: AsyncClientBase = client_factory(config)
    result = await client.execute(command=cmd.GetCoins(owner=addr))

Protocol-Agnostic Pattern
-------------------------

Type your client parameter as :class:`AsyncClientBase` instead of a concrete protocol client. This allows your functions to work transparently with both GraphQL and gRPC transports.

.. code-block:: python

    from pysui import AsyncClientBase
    import pysui.sui.sui_common.sui_commands as cmd

    async def get_owner_coins(client: AsyncClientBase, owner: str) -> list:
        """Fetch all coins owned by an address.

        Works with both GraphQL and gRPC clients.
        """
        result = await client.execute(command=cmd.GetCoins(owner=owner))
        if result.is_ok():
            return result.result_data
        else:
            raise ValueError(result.result_string)

    # Call with either transport
    from pysui import PysuiConfiguration, client_factory
    config = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    client = client_factory(config)  # Returns AsyncClientBase
    coins = await get_owner_coins(client, "0x1234...")

.. note::
    :class:`AsyncClientBase` is the contract. The actual implementation is determined by the active Sui client configuration (set in ``~/.sui/sui_config/``). Call :func:`client_factory()` to instantiate the configured client without needing to know which protocol it is.

Factory Return Type
~~~~~~~~~~~~~~~~~~~

The :func:`client_factory()` function now returns :class:`AsyncClientBase`. Update type annotations:

.. code-block:: python

    # Old
    from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
    client: AsyncSuiGQLClient = client_factory(config)  # ❌ Misleading

    # New
    from pysui import AsyncClientBase, client_factory
    client: AsyncClientBase = client_factory(config)  # ✓ Accurate


Migration Table
---------------

Below are the most common patterns and their updated equivalents:

GetCoins (GraphQL → Unified)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Old (GraphQL)
    import pysui.sui.sui_pgql.pgql_query as qn
    result = await client.execute_query_node(with_node=qn.GetCoins(owner=addr))

    # New (Protocol-agnostic)
    import pysui.sui.sui_common.sui_commands as cmd
    result = await client.execute(command=cmd.GetCoins(owner=addr))

GetGas (gRPC → Unified)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Old (gRPC)
    import pysui.sui.sui_grpc.pgrpc_requests as rn
    result = await client.execute_grpc_request(request=rn.GetGas(owner=addr))

    # New (Protocol-agnostic)
    import pysui.sui.sui_common.sui_commands as cmd
    result = await client.execute(command=cmd.GetGas(owner=addr))

SimulateTransactionKind (gRPC → Unified)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Old (gRPC)
    import pysui.sui.sui_grpc.pgrpc_requests as rn
    result = await client.execute_grpc_request(
        request=rn.SimulateTransactionKind(
            transaction=kind_bytes,
            sender="0x1234...",
            gas_selection=True,
        )
    )

    # New (Protocol-agnostic)
    import pysui.sui.sui_common.sui_commands as cmd
    result = await client.execute(
        command=cmd.SimulateTransactionKind(
            tx_kind=kind_bytes,
            tx_meta={"sender": "0x1234..."},
            gas_selection=True,
        )
    )

ExecuteTransaction
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Old (gRPC)
    import pysui.sui.sui_grpc.pgrpc_requests as rn
    bdict = await txer.build_and_sign()
    result = await client.execute_grpc_request(request=rn.ExecuteTransaction(**bdict))

    # New (Protocol-agnostic)
    import pysui.sui.sui_common.sui_commands as cmd
    bdict = await txer.build_and_sign()
    result = await client.execute(command=cmd.ExecuteTransaction(**bdict))


Graceful Unsupported Commands (Error Class 3)
----------------------------------------------

Some commands are not supported by one or both protocols. Rather than raising an exception, the client returns a :class:`SuiRpcResult` with success flag ``False`` and a descriptive message.

Example: GetEvents
~~~~~~~~~~~~~~~~~~~

GetEvents is supported by GraphQL but not by gRPC:

.. code-block:: python

    import pysui.sui.sui_common.sui_commands as cmd

    # On a gRPC client
    result = await grpc_client.execute(command=cmd.GetEvents(event_filter={}))

    if not result.is_ok():
        print(result.result_string)
        # Output: "Command not supported by gRPC"

Example: GetServiceInfo
~~~~~~~~~~~~~~~~~~~~~~~~

GetServiceInfo is supported by gRPC but not by GraphQL:

.. code-block:: python

    import pysui.sui.sui_common.sui_commands as cmd

    # On a GraphQL client
    result = await gql_client.execute(command=cmd.GetServiceInfo())

    if not result.is_ok():
        print(result.result_string)
        # Output: "Command not supported by GraphQL"

.. tip::
    Always check :meth:`SuiRpcResult.is_ok()` when using protocol-agnostic code. If you need to support only one protocol for a given feature, document it and consider dropping down to the concrete client (see :ref:`escape-hatch`).


.. _escape-hatch:

Escape Hatch: Protocol-Specific APIs (Error Class 5)
-----------------------------------------------------

When a :class:`SuiCommand` does not exist for your use case or you need protocol-specific features, drop down to the concrete client's protocol-specific methods. These are not deprecated.

GraphQL Escape Hatch
~~~~~~~~~~~~~~~~~~~~

Use :meth:`AsyncSuiGQLClient.execute_query_node()` with :mod:`pysui.sui.sui_pgql.pgql_query` objects:

.. code-block:: python

    from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
    import pysui.sui.sui_pgql.pgql_query as qn

    async def gql_only(client: AsyncSuiGQLClient):
        """Use GraphQL-only query features."""
        result = await client.execute_query_node(
            with_node=qn.GetMultipleTx(digests=tx_digests)
        )
        return result.result_data

gRPC Escape Hatch
~~~~~~~~~~~~~~~~~

Use :meth:`SuiGrpcClient.execute_grpc_request()` with :mod:`pysui.sui.sui_grpc.pgrpc_requests` objects:

.. code-block:: python

    from pysui.sui.sui_grpc.pgrpc_clients import SuiGrpcClient
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    async def grpc_only(client: SuiGrpcClient):
        """Use gRPC-specific features."""
        result = await client.execute_grpc_request(
            request=rn.SubscribeCheckpoint(field_mask=["sequenceNumber", "digest"])
        )
        return result.result_data

.. note::
    Escape hatch methods are not deprecated and are the proper way to access protocol-specific advanced features. If you find yourself in the escape hatch frequently, consider whether your use case truly requires one protocol or whether a SuiCommand should be added to pysui.


Available SuiCommand Subclasses
-------------------------------

The following SuiCommand subclasses are built-in and re-exported from the top-level :mod:`pysui` module:

**Transaction Execution:**
  - :class:`ExecuteTransaction`
  - :class:`SimulateTransaction`
  - :class:`SimulateTransactionKind`

**Coin Queries:**
  - :class:`GetCoinMetaData`
  - :class:`GetAddressCoinBalance`
  - :class:`GetAddressCoinBalances`
  - :class:`GetCoins`
  - :class:`GetGas`
  - :class:`GetStaked`
  - :class:`GetDelegatedStakes`
  - :class:`GetCoinSummary`

**Object Queries:**
  - :class:`GetObject`
  - :class:`GetPastObject`
  - :class:`GetMultipleObjects`
  - :class:`GetMultiplePastObjects`
  - :class:`GetObjectsOwnedByAddress`
  - :class:`GetDynamicFields`
  - :class:`GetObjectContent`
  - :class:`GetMultipleObjectContent`
  - :class:`GetObjectsForType`

**Epoch & Validator Queries:**
  - :class:`GetEpoch`
  - :class:`GetLatestSuiSystemState`
  - :class:`GetBasicCurrentEpochInfo`
  - :class:`GetCurrentValidators`

**Checkpoint Queries:**
  - :class:`GetLatestCheckpoint`
  - :class:`GetCheckpointBySequence`
  - :class:`GetCheckpointByDigest`

**Transaction Queries:**
  - :class:`GetTx`
  - :class:`GetTxKind`
  - :class:`GetMultipleTransactions`
  - :class:`GetFilteredTx`
  - :class:`GetEvents`

**Move Package & Type Queries:**
  - :class:`GetPackage`
  - :class:`GetPackageVersions`
  - :class:`GetModule`
  - :class:`GetMoveDataType`
  - :class:`GetStructure`
  - :class:`GetStructures`
  - :class:`GetFunction`
  - :class:`GetFunctions`

**Name Service & System Queries:**
  - :class:`GetNameServiceAddress`
  - :class:`GetNameServiceNames`
  - :class:`GetServiceInfo`
  - :class:`GetProtocolConfig`

**Subscriptions & Verification:**
  - :class:`SubscribeCheckpoint`
  - :class:`VerifySignature`

All are importable as:

.. code-block:: python

    import pysui.sui.sui_common.sui_commands as cmd

    # cmd.ExecuteTransaction, cmd.GetCoins, etc.


Custom SuiCommand Subclasses (Advanced)
----------------------------------------

You can create custom :class:`SuiCommand` subclasses for operations not yet supported by pysui.

Implementing a Custom Command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Subclass :class:`SuiCommand` and implement the protocol-specific methods:

.. code-block:: python

    from dataclasses import dataclass
    from pysui import SuiCommand
    import pysui.sui.sui_pgql.pgql_query as qn
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    @dataclass
    class MyGetObject(SuiCommand):
        """A custom command that wraps GetObject on both protocols."""

        object_id: str

        def gql_node(self):
            """Return the GraphQL query node."""
            return qn.GetObject(object_id=self.object_id)

        def grpc_request(self):
            """Return the gRPC request."""
            return rn.GetObject(object_id=self.object_id)

Using a Custom Command
~~~~~~~~~~~~~~~~~~~~~~

Once defined, use it exactly like built-in commands:

.. code-block:: python

    from pysui import AsyncClientBase

    async def use_custom(client: AsyncClientBase):
        result = await client.execute(command=MyGetObject(object_id="0x6"))
        if result.is_ok():
            return result.result_data

Single-Protocol Custom Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a command is only supported by one protocol, raise :exc:`NotImplementedError` on the unsupported side:

.. code-block:: python

    @dataclass
    class GqlOnlyCommand(SuiCommand):
        """Only supported by GraphQL."""

        event_filter: dict

        def gql_node(self):
            return qn.GetEvents(event_filter=self.event_filter)

        def grpc_request(self):
            raise NotImplementedError("Not supported by gRPC")

The client will catch this and return a graceful error (Error Class 3) rather than raising an exception to the caller.


Summary
-------

- **Prefer** :class:`SuiCommand` + :meth:`AsyncClientBase.execute(command=...)` for protocol-agnostic code.
- **Type annotations** as :class:`AsyncClientBase` to signal that your function works with any protocol.
- **Check results** with :meth:`SuiRpcResult.is_ok()` — unsupported commands return gracefully.
- **Drop to escape hatch** when you need protocol-specific features — use :meth:`execute_query_node()` for GraphQL or gRPC-specific APIs directly.
- **Custom commands** are supported by subclassing :class:`SuiCommand` and implementing :meth:`gql_node()` and :meth:`grpc_request()`.
