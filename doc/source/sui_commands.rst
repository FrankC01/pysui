
======================
SuiCommand Reference
======================

:py:class:`SuiCommand <pysui.sui.sui_common.sui_command.SuiCommand>` provides
protocol-neutral command objects for the most common blockchain operations. Write
code once and run it transparently on GraphQL or gRPC — switching transports requires
only a configuration change.

.. code-block:: python

   import asyncio
   import pysui.sui.sui_common.sui_commands as cmd
   from pysui import PysuiConfiguration, client_factory

   async def main():
       cfg = PysuiConfiguration()
       async with client_factory(cfg) as client:
           result = await client.execute(
               command=cmd.GetGas(owner=client.config.active_address)
           )
           if result.is_ok():
               print(result.result_data)
           else:
               print(result.result_string)

   asyncio.run(main())

All commands are exported from ``pysui`` directly and also from
:py:mod:`pysui.sui.sui_common.sui_commands`.

Commands that paginate on GraphQL but return a flat result on gRPC
(``GetStructures``, ``GetFunctions``) auto-paginate
internally on the GQL transport — the caller always receives the full result.

.. note::

   **Protocol consistency contract.** A SuiCommand is only valid if both protocol
   paths work *and* return equivalent output.  Commands that are single-protocol
   only, or whose two protocol outputs diverged significantly, have been removed from
   the SuiCommand layer.  Use the legacy
   :py:mod:`pysui.sui.sui_pgql.pgql_query` or
   :py:mod:`pysui.sui.sui_grpc.pgrpc_requests` classes directly to access those features.

.. seealso::

   :doc:`migration_sui_command` — migrating existing code to the UCI.

----

Transaction Execution
---------------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.ExecuteTransaction`
     - Execute a signed transaction on-chain

   * - :py:class:`~pysui.sui.sui_common.sui_commands.SimulateTransaction`
     - Simulate a serialized transaction (BCS bytes or base64)

   * - :py:class:`~pysui.sui.sui_common.sui_commands.SimulateTransactionKind`
     - Simulate a ``TransactionKind`` without committing


Transactions
------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetTransaction` :sup:`1,2,3`
     - Fetch a single executed transaction by digest; ``None`` if not found or pruned
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetTransactions` :sup:`1,2,3`
     - Fetch multiple transactions by digest list; result list matches input length with ``None`` in unresolved slots
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetTransactionKind` :sup:`1,2,3`
     - Fetch only the ``TransactionKind`` discriminator for a transaction


Coin / Balance
--------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCoinMetaData`
     - Fetch metadata for a specific coin type

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetAddressCoinBalance`
     - Fetch the total balance of a coin type owned by an address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetAddressCoinBalances`
     - Fetch all coin-type balances for an address (paginated)

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCoins`
     - Fetch all coin objects of a specific type owned by an address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetGas`
     - Fetch all SUI gas coin objects owned by an address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStaked`
     - Fetch all staked SUI coin objects owned by an address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetDelegatedStakes`
     - Fetch all delegated-stake (``StakedSui``) objects owned by an address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCoinSummary`
     - Fetch an aggregated coin-type summary (count, total balance) for an address


Objects
-------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObject`
     - Fetch the current state of a single object

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPastObject`
     - Fetch a specific version of an object

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultipleObjects`
     - Fetch the current state of multiple objects by ID list

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultiplePastObjects`
     - Fetch specific versions of multiple objects

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectsOwnedByAddress`
     - Fetch all objects owned by an address (paginated)

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetDynamicFields`
     - Fetch dynamic fields of an object (paginated)

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectContent`
     - Fetch BCS-encoded object content by ID

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultipleObjectContent`
     - Fetch BCS-encoded content for multiple objects by ID list

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectsForType`
     - Fetch all objects of a specific Move type owned by an address


Epoch / System State
--------------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetEpoch`
     - Fetch epoch information by ID, or the current epoch

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetBasicCurrentEpochInfo`
     - Fetch minimal epoch fields needed for gas and expiry building

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetLatestSuiSystemState`
     - Fetch the full ``SuiSystemStateInnerV2`` BCS object — epoch, protocol version, validator set, storage fund, stake subsidy, and system parameters

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCurrentValidators`
     - Fetch the list of active validators from the current system state (returns ``list[Validator]``)


Checkpoints
-----------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetLatestCheckpoint`
     - Fetch the latest checkpoint

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCheckpointBySequence`
     - Fetch a checkpoint by sequence number


Move / Packages
---------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPackage`
     - Fetch a Move package by ID

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPackageVersions`
     - Fetch all versions of a Move package sharing the same original ID

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetModule`
     - Fetch a Move module's structure and function definitions

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMoveDataType`
     - Fetch a Move struct or enum by name

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStructure`
     - Fetch a specific Move struct by name

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStructures`
     - Fetch all structs in a Move module (auto-paginated on GQL)

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunction`
     - Fetch a specific Move function by name

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunctions`
     - Fetch all functions in a Move module (auto-paginated on GQL)


Name Service
-------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetNameServiceAddress`
     - Resolve a SuiNS name to an address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetNameServiceNames`
     - Resolve an address to its SuiNS name(s)


Network / Chain Info
--------------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetChainIdentifier`
     - Fetch the chain identifier for the current network

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetProtocolConfig`
     - Fetch the current node's protocol configuration and feature flags


----

GQL Caveats
-----------

Some commands return partial data when executed via the GraphQL transport because
the GQL schema does not expose every field that the gRPC protocol provides.
Superscript numbers in the command tables above refer to the caveats below.

1. ``MoveCall.type_arguments`` — not populated via GQL; always an empty list on that transport.
2. ``ChangeEpochTransaction.system_packages`` — not populated via GQL; always an empty list.
3. ``EndOfEpochTransactionKind.execution_time_observations`` — not populated via GQL; always an empty list.

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
