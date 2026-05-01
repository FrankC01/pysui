Migrating to the Unified Client Interface
==========================================

Introduction
------------

The **Unified Client Interface (UCI)** provides a protocol-agnostic programming model:
write once, run transparently on GraphQL or gRPC. This guide covers how to migrate
from the legacy protocol-specific APIs to the UCI and explains the key abstractions
that power transport-agnostic code.

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


Available SuiCommand Subclasses
-------------------------------

The following 41 SuiCommand subclasses are built-in and re-exported from the top-level
:mod:`pysui` module.  Every command listed here works on **both** GraphQL and gRPC
transports and returns the same canonical output type from either protocol.

**Transaction Execution (3):**
  - :class:`ExecuteTransaction`
  - :class:`SimulateTransaction`
  - :class:`SimulateTransactionKind`

**Transactions (3):**
  - :class:`GetTransaction`
  - :class:`GetTransactions`
  - :class:`GetTransactionKind`

**Coin Queries (8):**
  - :class:`GetCoinMetaData`
  - :class:`GetAddressCoinBalance`
  - :class:`GetAddressCoinBalances`
  - :class:`GetCoins`
  - :class:`GetGas`
  - :class:`GetStaked`
  - :class:`GetDelegatedStakes`
  - :class:`GetCoinSummary`

**Object Queries (9):**
  - :class:`GetObject`
  - :class:`GetPastObject`
  - :class:`GetMultipleObjects`
  - :class:`GetMultiplePastObjects`
  - :class:`GetObjectsOwnedByAddress`
  - :class:`GetDynamicFields`
  - :class:`GetObjectContent`
  - :class:`GetMultipleObjectContent`
  - :class:`GetObjectsForType`

**Epoch / System State Queries (4):**
  - :class:`GetEpoch`
  - :class:`GetBasicCurrentEpochInfo`
  - :class:`GetLatestSuiSystemState`
  - :class:`GetCurrentValidators`

**Checkpoint Queries (2):**
  - :class:`GetLatestCheckpoint`
  - :class:`GetCheckpointBySequence`

**Move Package & Type Queries (8):**
  - :class:`GetPackage`
  - :class:`GetPackageVersions`
  - :class:`GetModule`
  - :class:`GetMoveDataType`
  - :class:`GetStructure`
  - :class:`GetStructures`
  - :class:`GetFunction`
  - :class:`GetFunctions`

**Name Service (2):**
  - :class:`GetNameServiceAddress`
  - :class:`GetNameServiceNames`

**Network / Chain Info (2):**
  - :class:`GetChainIdentifier`
  - :class:`GetProtocolConfig`

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

Dual-Protocol Consistency Requirement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom commands should support both transports and return equivalent output from each.
Built-in commands that could not satisfy this requirement have been removed from the
SuiCommand layer; use the legacy :py:mod:`pysui.sui.sui_pgql.pgql_query` or
:py:mod:`pysui.sui.sui_grpc.pgrpc_requests` classes directly for those operations.

If you implement a custom command that is genuinely single-protocol, raise
:exc:`NotImplementedError` on the unsupported side — the client will catch it and return a
graceful ``SuiRpcResult(is_ok=False)`` rather than propagating an exception.  However,
prefer protocol-level access over a single-protocol SuiCommand when the operation is inherently
transport-specific and will never have a cross-protocol equivalent:

.. code-block:: python

    @dataclass
    class MyGqlOnlyCommand(SuiCommand):
        """Example: a hypothetical GQL-only custom command."""

        some_filter: dict

        def gql_node(self):
            return qn.SomeGqlQueryNode(filter=self.some_filter)

        def grpc_request(self):
            raise NotImplementedError("Not supported by gRPC")


Summary
-------

- **Prefer** :class:`SuiCommand` + :meth:`AsyncClientBase.execute(command=...)` for protocol-agnostic code.
- **Type annotations** as :class:`AsyncClientBase` to signal that your function works with any transport.
- **Check results** with :meth:`SuiRpcResult.is_ok()` before accessing ``result_data``.
- **Protocol-specific access** — :py:mod:`pysui.sui.sui_pgql.pgql_query` and :py:mod:`pysui.sui.sui_grpc.pgrpc_requests` are not deprecated; use them directly when a SuiCommand does not exist for your use case.
- **Custom commands** are supported by subclassing :class:`SuiCommand` and implementing :meth:`gql_node()` and :meth:`grpc_request()` — both protocols should return equivalent output.
