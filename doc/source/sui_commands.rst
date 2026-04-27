
======================
SuiCommand Reference
======================

The **Unified Client Interface (UCI)** is a single ``await client.execute(command=...)``
dispatch that works identically across GraphQL and gRPC transports.
:py:class:`SuiCommand <pysui.sui.sui_common.sui_command.SuiCommand>` is the
protocol-neutral command object passed to that call — a typed data carrier that
the client resolves to the appropriate underlying query or request.

.. code-block:: python

   import asyncio
   import pysui.sui.sui_common.sui_commands as cmd
   from pysui import PysuiConfiguration, client_factory, handle_result

   async def main():
       cfg = PysuiConfiguration()
       async with client_factory(cfg) as client:
           result = await client.execute(
               command=cmd.GetGas(owner=client.config.active_address)
           )
           handle_result(result)

   asyncio.run(main())

All commands are exported from ``pysui`` directly and also from
:py:mod:`pysui.sui.sui_common.sui_commands`.

Protocol support is noted per command.  Commands marked **gRPC only** or
**GQL only** return a ``SuiRpcResult(is_ok=False)`` when called against the
unsupported transport — they never raise an exception.

Commands that paginate on GraphQL but return a flat result on gRPC
(``GetCurrentValidators``, ``GetStructures``, ``GetFunctions``) auto-paginate
internally on the GQL transport — the caller always receives the full result.

.. seealso::

   :doc:`migration_sui_command` — migrating existing code to the UCI.

----

Transaction Execution
---------------------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.ExecuteTransaction`
     - Execute a signed transaction on-chain
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.SimulateTransaction`
     - Simulate a serialized transaction (BCS bytes or base64)
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.SimulateTransactionKind`
     - Simulate a ``TransactionKind`` without committing
     - Both

Coin / Balance
--------------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCoinMetaData`
     - Fetch metadata for a specific coin type
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetAddressCoinBalance`
     - Fetch the total balance of a coin type owned by an address
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetAddressCoinBalances`
     - Fetch all coin-type balances for an address (paginated)
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCoins`
     - Fetch all coin objects of a specific type owned by an address
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetGas`
     - Fetch all SUI gas coin objects owned by an address
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStaked`
     - Fetch all staked SUI coin objects owned by an address
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetDelegatedStakes`
     - Fetch all delegated-stake (``StakedSui``) objects owned by an address
     - Both

Objects
-------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObject`
     - Fetch the current state of a single object
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPastObject`
     - Fetch a specific version of an object
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultipleObjects`
     - Fetch the current state of multiple objects by ID list
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultiplePastObjects`
     - Fetch specific versions of multiple objects
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectsOwnedByAddress`
     - Fetch all objects owned by an address (paginated)
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetDynamicFields`
     - Fetch dynamic fields of an object (paginated)
     - Both

Epoch / System State
--------------------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetEpoch`
     - Fetch epoch information by ID, or the current epoch
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetLatestSuiSystemState`
     - Fetch the latest Sui system state
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetBasicCurrentEpochInfo`
     - Fetch minimal epoch fields needed for gas and expiry building
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCurrentValidators`
     - Fetch the active validator set (auto-paginated on GQL)
     - Both

Checkpoints
-----------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetLatestCheckpoint`
     - Fetch the latest checkpoint
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCheckpointBySequence`
     - Fetch a checkpoint by sequence number
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCheckpointByDigest`
     - Fetch a checkpoint by digest
     - gRPC only

Transactions
------------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetTx`
     - Fetch a single transaction by digest
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetTxKind`
     - Fetch the transaction kind for a given digest
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultipleTx`
     - Fetch multiple transactions by digest list
     - gRPC only
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFilteredTx`
     - Fetch transactions matching a ``TransactionBlockFilter`` (paginated)
     - GQL only
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetEvents`
     - Fetch events matching a filter (paginated)
     - GQL only

Move / Packages
---------------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPackage`
     - Fetch a Move package by ID
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPackageVersions`
     - Fetch all versions of a Move package sharing the same original ID
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetModule`
     - Fetch a Move module's structure and function definitions
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMoveDataType`
     - Fetch a Move struct or enum by name
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStructure`
     - Fetch a specific Move struct by name
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStructures`
     - Fetch all structs in a Move module (auto-paginated on GQL)
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunction`
     - Fetch a specific Move function by name
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunctions`
     - Fetch all functions in a Move module (auto-paginated on GQL)
     - Both

Name Service
------------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetNameServiceAddress`
     - Resolve a SuiNS name to an address
     - Both
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetNameServiceNames`
     - Resolve an address to its SuiNS name(s)
     - Both

gRPC-only
---------

.. list-table::
   :widths: 35 50 15
   :header-rows: 1

   * - Command
     - Description
     - Protocols
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetServiceInfo`
     - Query general gRPC service information
     - gRPC only
   * - :py:class:`~pysui.sui.sui_common.sui_commands.SubscribeCheckpoint`
     - Subscribe to a live checkpoint feed (streaming)
     - gRPC only
   * - :py:class:`~pysui.sui.sui_common.sui_commands.VerifySignature`
     - Verify a cryptographic signature against a message
     - gRPC only

----

Extending SuiCommand
--------------------

User-defined commands follow the same pattern as built-ins: subclass
:py:class:`~pysui.sui.sui_common.sui_command.SuiCommand`, declare
``gql_class`` and ``grpc_class`` as ``ClassVar``, and implement
``gql_node()`` and ``grpc_request()``.  Raise ``NotImplementedError``
from the unsupported side to return a graceful ``SuiRpcResult`` error
rather than an exception.

.. code-block:: python

   from dataclasses import dataclass
   from typing import ClassVar, Optional
   from pysui.sui.sui_common.sui_command import SuiCommand
   import pysui.sui.sui_pgql.pgql_query as pgql_query
   import pysui.sui.sui_grpc.pgrpc_requests as rn

   @dataclass(kw_only=True)
   class MyCommand(SuiCommand):
       gql_class: ClassVar[type] = pgql_query.SomeQueryNode
       grpc_class: ClassVar[type] = rn.SomeRequest
       my_param: str

       def gql_node(self):
           return self.gql_class(param=self.my_param)

       def grpc_request(self):
           return self.grpc_class(param=self.my_param)
