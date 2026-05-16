
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

Commands whose result set may span multiple pages expose a ``next_page_token``
field.  Use :meth:`~pysui.sui.sui_common.client.AsyncClientBase.execute_for_all`
to accumulate all pages automatically, or iterate manually by passing the returned
token back into a fresh command.  See :ref:`pageable-commands` for the full list
and usage examples.

.. note::

   **Protocol consistency contract.** A SuiCommand is only valid if both protocol
   paths work *and* return equivalent output.  Commands that are single-protocol
   only, or whose two protocol outputs diverged significantly, have been removed from
   the SuiCommand layer.  Use the legacy
   :py:mod:`pysui.sui.sui_pgql.pgql_query` or
   :py:mod:`pysui.sui.sui_grpc.pgrpc_requests` classes directly to access those features.

.. seealso::

   :doc:`migration_to_pysui_uci` — migrating existing code to the UCI.

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

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectSummary`
     - Fetch a thin summary (object ID, version, digest, owner) for a single object

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetMultipleObjectSummary`
     - Fetch thin summaries (object ID, version, digest, owner) for a list of objects


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
     - Fetch all structs in a Move module

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunction`
     - Fetch a specific Move function by name

   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunctions`
     - Fetch all functions in a Move module


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


Signature Verification
-----------------------

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Command
     - Description
   * - :py:class:`~pysui.sui.sui_common.sui_commands.VerifyTransactionSignature`
     - Verify a transaction signature against a signer address

   * - :py:class:`~pysui.sui.sui_common.sui_commands.VerifyPersonalMessageSignature`
     - Verify a personal message signature against a signer address


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

.. _pageable-commands:

Pageable Commands
-----------------

The following SuiCommands require paging to retrieve all results where the
protocol column is ``True``.  A ``—`` means that protocol returns all results
in a single call.

.. list-table::
   :widths: 52 12 12
   :header-rows: 1

   * - Command
     - GQL
     - gRPC
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetAddressCoinBalances`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCoins`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetGas`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStaked`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetDelegatedStakes`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectsOwnedByAddress`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetDynamicFields`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetObjectsForType`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPackageVersions`
     - True
     - True
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetPackage`
     - True
     - —
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetStructures`
     - True
     - —
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetFunctions`
     - True
     - —
   * - :py:class:`~pysui.sui.sui_common.sui_commands.GetCurrentValidators`
     - True
     - —

Three usage patterns are available, illustrated here with
:py:class:`~pysui.sui.sui_common.sui_commands.GetGas`.  All patterns work
identically on both transports — no protocol-specific code is required.

**Form 1 — single page.**  :meth:`execute` returns one page.
``result_data.next_page_token`` is set when more pages remain.

.. code-block:: python

   async def do_gas(client: AsyncClientBase):
       result = await client.execute(
           command=cmd.GetGas(owner=client.config.active_address)
       )
       if result.is_ok():
           print(f"Coins this page: {len(result.result_data.objects)}")
           if result.result_data.next_page_token:
               print("  (more pages available)")

**Form 2 — manual iteration.**  Pass the returned ``next_page_token`` back into
a fresh command each loop; stop when the token is ``None``.

.. code-block:: python

   async def do_all_gas(client: AsyncClientBase):
       owner = client.config.active_address
       all_coins, next_page_token = [], None
       while True:
           result = await client.execute(
               command=cmd.GetGas(owner=owner, next_page_token=next_page_token)
           )
           if not result.is_ok():
               break
           all_coins.extend(result.result_data.objects)
           next_page_token = result.result_data.next_page_token
           if not next_page_token:
               break
       print(f"Total coins: {len(all_coins)}")

**Form 3 — automatic accumulation.**
:meth:`~pysui.sui.sui_common.client.AsyncClientBase.execute_for_all` accumulates
every page internally and returns a single result containing the complete list.

.. code-block:: python

   async def do_all_gas_alt(client: AsyncClientBase):
       result = await client.execute_for_all(
           command=cmd.GetGas(owner=client.config.active_address)
       )
       if result.is_ok():
           print(f"Total coins: {len(result.result_data.objects)}")
           print(f"Total mists: {sum(int(x.balance) for x in result.result_data.objects)}")

----

Extending SuiCommand
--------------------

User-defined commands follow the same pattern as built-ins: subclass
:py:class:`~pysui.sui.sui_common.sui_command.SuiCommand`, declare the
``ClassVar`` fields, and implement ``gql_node()`` and ``grpc_request()``.
Raise ``NotImplementedError`` from the unsupported side to return a graceful
``SuiRpcResult`` error rather than an exception.

Non-pageable command
~~~~~~~~~~~~~~~~~~~~

For commands that return a complete result in a single call:

.. code-block:: python

   from dataclasses import dataclass
   from typing import ClassVar
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

Pageable command
~~~~~~~~~~~~~~~~

For commands whose result set may span multiple pages, declare the four
paging ``ClassVar`` fields and expose ``next_page_token``.
:meth:`~pysui.sui.sui_common.client.AsyncClientBase.execute_for_all`
reads these fields to drive automatic page accumulation.

.. code-block:: python

   from dataclasses import dataclass
   from typing import ClassVar, Optional
   from pysui.sui.sui_common.sui_command import SuiCommand
   import pysui.sui.sui_pgql.pgql_query as pgql_query
   import pysui.sui.sui_grpc.pgrpc_requests as rn

   @dataclass(kw_only=True)
   class MyPageableCommand(SuiCommand):
       gql_class: ClassVar[type] = pgql_query.SomeListQueryNode
       grpc_class: ClassVar[type] = rn.SomeListRequest
       is_pageable_gql: ClassVar[bool] = True
       paginated_field_path_gql: ClassVar[tuple[str, ...]] = ("items",)
       is_pageable_grpc: ClassVar[bool] = True
       paginated_field_path_grpc: ClassVar[tuple[str, ...]] = ("items",)
       my_param: str
       next_page_token: Optional[bytes] = None

       def gql_node(self):
           return self.gql_class(param=self.my_param, next_page_token=self.next_page_token)

       def grpc_request(self):
           return self.grpc_class(param=self.my_param, page_token=self.next_page_token)
