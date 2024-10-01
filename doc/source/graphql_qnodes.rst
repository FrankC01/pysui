
QueryNodes
==========

General
-------

With ``pysui GraphQL`` implementation a number of pre-built and ready to use QueryNodes were delivered as part
of the pysui package.

The pre-built QueryNode module :py:mod:`pysui.sui.sui_pgql.pgql_query` contains QueryNodes for
a number of query and execution classes requiring only simple parameters. Many of the QueryNodes include
pagination options.


QueryNode Classes
-----------------

+-------------------------------------------------------------------------+
|                                  Name                                   |
+=========================================================================+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCoinMetaData`               |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetAllCoinBalances`            |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCoins`                      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetLatestSuiSystemState`       |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetObject`                     |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetObjectsOwnedByAddress`      |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleGasObjects`         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultipleObjects`            |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetPastObject`                 |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetMultiplePastObjects`        |
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
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetLatestCheckpointSequence`   |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCheckpointByDigest`         |
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
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetValidatorsApy`              |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetCurrentValidators`          |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.GetStructure`                  |
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
| :py:class:`pysui.sui.sui_pgql.pgql_query.DryRunTransactionKind`         |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.DryRunTransaction`             |
+-------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_pgql.pgql_query.ExecuteTransaction`            |
+-------------------------------------------------------------------------+