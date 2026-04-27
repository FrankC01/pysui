
:orphan:

====================
GraphQL Query Nodes
====================

General
-------

With ``pysui's GraphQL`` implementation a number of pre-built and ready to use
 QueryNodes were delivered as part of the pysui package.

The pre-built module :py:mod:`pysui.sui.sui_pgql.pgql_query` contains
QueryNodes for a number of query and execution classes requiring only simple
parameters.


.. note::

   These QueryNodes are **EC-5 escape hatches** for cases where no
   :py:class:`~pysui.sui.sui_common.sui_command.SuiCommand` equivalent exists.
   For standard queries prefer ``await client.execute(command=...)`` with a
   :doc:`SuiCommand <sui_commands>` subclass — it works identically on both
   GraphQL and gRPC transports.

QueryNode Classes
-----------------

+-------------------------------------------------------------------------+
|                                  Name                                   |
+=========================================================================+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCoinMetaData`               |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetAddressCoinBalance`         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetAllCoinBalances`            |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetAddressCoinBalances`        |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCoinSummary`                |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCoins`                      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetGas`                        |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetLatestSuiSystemState`       |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetObject`                     |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetObjectsForType`             |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetObjectContent`              |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleObjectContent`      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetObjectsOwnedByAddress`      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleGasObjects`         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleObjects`            |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetPastObject`                 |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleVersionedObjects`   |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetDynamicFields`              |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetEvents`                     |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetTx`                         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleTx`                 |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetFilteredTx`                 |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetTxKind`                     |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetDelegatedStakes`            |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetBasicCurrentEpochInfo`      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetEpoch`                      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetLatestCheckpointSequence`   |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCheckpointBySequence`       |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCheckpoints`                |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetProtocolConfig`             |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetReferenceGasPrice`          |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetNameServiceAddress`         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetNameServiceNames`           |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCurrentValidators`          |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetValidatorExchangeRates`     |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetStructure`                  |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMoveDataType`               |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetStructures`                 |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetFunction`                   |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetFunctions`                  |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetModule`                     |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetPackage`                    |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetPackageVersions`            |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.DryRunTransactionKind`         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.DryRunTransaction`             |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.SimulateTransactionKind`       |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.SimulateTransaction`           |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.ExecuteTransaction`            |
+-------------------------------------------------------------------------+