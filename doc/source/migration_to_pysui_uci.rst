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
:class:`GqlProtocolClient` and :class:`GrpcProtocolClient` inherit from it. Type your client
parameter as :class:`AsyncClientBase` and your code becomes transport-agnostic — the active
protocol is determined by :class:`PysuiConfiguration` at runtime.

:func:`client_factory` returns :class:`AsyncClientBase`. Update your type annotations accordingly:

.. code-block:: python

    # Old — protocol-specific type
    from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient
    client: GqlProtocolClient = client_factory(config)  # binds you to GraphQL

    # New — UCI type
    from pysui import AsyncClientBase, client_factory
    client: AsyncClientBase = client_factory(config)    # works with any transport

:class:`AsyncClientBase` supports the async context manager protocol for automatic resource
cleanup:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory, AsyncClientBase, GetCoins

    async def main():
        config = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(config) as client:
            result = await client.execute(command=GetCoins(owner=config.active_address))
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
    from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient
    import pysui.sui.sui_pgql.pgql_query as qn

    gql_client: GqlProtocolClient = client_factory(PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP))
    result = await gql_client.execute_query_node(with_node=qn.GetCoins(owner=addr))

    # gRPC version:
    from pysui.sui.sui_grpc.pgrpc_clients import GrpcProtocolClient
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    grpc_client: GrpcProtocolClient = client_factory(PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP))
    result = await grpc_client.execute_grpc_request(request=rn.GetCoins(owner=addr))

**New approach** — unified interface:

.. code-block:: python

    from pysui import AsyncClientBase, client_factory, GetCoins

    # Works with any protocol; client type is determined at runtime
    config = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    client: AsyncClientBase = client_factory(config)
    result = await client.execute(command=GetCoins(owner=addr))

Protocol-Agnostic Pattern
-------------------------

Type your client parameter as :class:`AsyncClientBase` instead of a concrete protocol client. This allows your functions to work transparently with both GraphQL and gRPC transports.

.. code-block:: python

    from pysui import AsyncClientBase, GetCoins

    async def get_owner_coins(client: AsyncClientBase, owner: str) -> list:
        """Fetch all coins owned by an address — all pages.

        Works with both GraphQL and gRPC clients.
        """
        result = await client.execute_for_all(command=GetCoins(owner=owner))
        if result.is_ok():
            return result.result_data.objects
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
    from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient
    client: GqlProtocolClient = client_factory(config)  # ❌ Misleading

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
    from pysui import GetCoins
    result = await client.execute(command=GetCoins(owner=addr))

GetGas (gRPC → Unified)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Old (gRPC)
    import pysui.sui.sui_grpc.pgrpc_requests as rn
    result = await client.execute_grpc_request(request=rn.GetGas(owner=addr))

    # New (Protocol-agnostic)
    from pysui import GetGas
    result = await client.execute(command=GetGas(owner=addr))

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
    from pysui import SimulateTransactionKind
    result = await client.execute(
        command=SimulateTransactionKind(
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
    from pysui import ExecuteTransaction
    bdict = await txer.build_and_sign()
    result = await client.execute(command=ExecuteTransaction(**bdict))

Paginated Commands (→ execute_for_all)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Commands that return paginated results previously required either a manual cursor
loop using ``PagingCursor`` objects, or a transport-specific helper such as
``async_get_all_owned_objects()`` from ``pgql_utils`` / ``pgrpc_utils``.
Both of those approaches are deprecated in 0.99.0.

.. code-block:: python

    # Old (GQL-specific helper — deprecated)
    from pysui.sui.sui_pgql.pgql_utils import async_get_all_owned_objects
    objects = await async_get_all_owned_objects(owner, client)

    # Old (manual PagingCursor loop — deprecated)
    result = await client.execute_query_node(with_node=qn.GetCoins(owner=addr))
    while result.result_data.next_cursor.hasNextPage:
        result = await client.execute_query_node(
            with_node=qn.GetCoins(owner=addr, next_page=result.result_data.next_cursor)
        )

    # New (Protocol-agnostic — all pages in one call)
    from pysui import GetObjectsOwnedByAddress
    result = await client.execute_for_all(command=GetObjectsOwnedByAddress(owner=addr))
    if result.is_ok():
        for obj in result.result_data.objects:
            print(obj.to_json(indent=2))

See :ref:`pageable-commands` in the SuiCommand Reference for the full list of
pageable commands and all three usage patterns.


Available SuiCommand Subclasses
-------------------------------

The following 45 SuiCommand subclasses are built-in and re-exported from the top-level
:mod:`pysui` module.  Every command listed here works on **both** GraphQL and gRPC
transports and returns the same canonical output type from either protocol.

Commands marked *(pageable)* may return partial results from a single
:meth:`execute` call; use :meth:`execute_for_all` to accumulate all pages.
See :ref:`pageable-commands` for the full table and usage examples.

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
  - :class:`GetAddressCoinBalances` *(pageable)*
  - :class:`GetCoins` *(pageable)*
  - :class:`GetGas` *(pageable)*
  - :class:`GetStaked` *(pageable)*
  - :class:`GetDelegatedStakes` *(pageable)*
  - :class:`GetCoinSummary`

**Object Queries (11):**
  - :class:`GetObject`
  - :class:`GetPastObject`
  - :class:`GetMultipleObjects`
  - :class:`GetMultiplePastObjects`
  - :class:`GetObjectsOwnedByAddress` *(pageable)*
  - :class:`GetDynamicFields` *(pageable)*
  - :class:`GetObjectContent`
  - :class:`GetMultipleObjectContent`
  - :class:`GetObjectsForType` *(pageable)*
  - :class:`GetObjectSummary`
  - :class:`GetMultipleObjectSummary`

**Epoch / System State Queries (4):**
  - :class:`GetEpoch`
  - :class:`GetBasicCurrentEpochInfo`
  - :class:`GetLatestSuiSystemState`
  - :class:`GetCurrentValidators` *(pageable, GQL only)*

**Checkpoint Queries (2):**
  - :class:`GetLatestCheckpoint`
  - :class:`GetCheckpointBySequence`

**Move Package & Type Queries (8):**
  - :class:`GetPackage` *(pageable, GQL only)*
  - :class:`GetPackageVersions` *(pageable)*
  - :class:`GetModule`
  - :class:`GetMoveDataType`
  - :class:`GetStructure`
  - :class:`GetStructures` *(pageable, GQL only)*
  - :class:`GetFunction`
  - :class:`GetFunctions` *(pageable, GQL only)*

**Name Service (2):**
  - :class:`GetNameServiceAddress`
  - :class:`GetNameServiceNames`

**Network / Chain Info (2):**
  - :class:`GetChainIdentifier`
  - :class:`GetProtocolConfig`

**Signature Verification (2):**
  - :class:`VerifyTransactionSignature`
  - :class:`VerifyPersonalMessageSignature`

All are importable directly from the top-level ``pysui`` package:

.. code-block:: python

    from pysui import GetCoins, GetGas, ExecuteTransaction  # etc.


Custom SuiCommand Subclasses (Advanced)
----------------------------------------

You can create custom :class:`SuiCommand` subclasses for operations not yet supported by pysui.

Implementing a Custom Command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Subclass :class:`SuiCommand`, declare the ``ClassVar`` fields, and implement the
protocol-specific methods:

.. code-block:: python

    from dataclasses import dataclass
    from typing import ClassVar
    from pysui.sui.sui_common.sui_command import SuiCommand
    import pysui.sui.sui_pgql.pgql_query as qn
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    @dataclass(kw_only=True)
    class MyGetObject(SuiCommand):
        gql_class: ClassVar[type] = qn.GetObject
        grpc_class: ClassVar[type] = rn.GetObject
        object_id: str

        def gql_node(self):
            return self.gql_class(object_id=self.object_id)

        def grpc_request(self):
            return self.grpc_class(object_id=self.object_id)

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

    @dataclass(kw_only=True)
    class MyGqlOnlyCommand(SuiCommand):
        gql_class: ClassVar[type] = qn.SomeGqlQueryNode
        grpc_class: ClassVar[type] = None
        some_filter: dict

        def gql_node(self):
            return self.gql_class(filter=self.some_filter)

        def grpc_request(self):
            raise NotImplementedError("Not supported by gRPC")


Summary
-------

- **Prefer** :class:`SuiCommand` + :meth:`AsyncClientBase.execute(command=...)` for protocol-agnostic code.
- **Type annotations** as :class:`AsyncClientBase` to signal that your function works with any transport.
- **Check results** with :meth:`SuiRpcResult.is_ok()` before accessing ``result_data``.
- **Protocol-specific access** — :py:mod:`pysui.sui.sui_pgql.pgql_query` and :py:mod:`pysui.sui.sui_grpc.pgrpc_requests` are not deprecated; use them directly when a SuiCommand does not exist for your use case.
- **Custom commands** are supported by subclassing :class:`SuiCommand` and implementing :meth:`gql_node()` and :meth:`grpc_request()` — both protocols should return equivalent output.
