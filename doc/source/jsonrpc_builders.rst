
Builders
========

Note: pysui Builders are deprecated. See the GraphQL alternative.

General
-------

With ``pysui`` 0.20.0, the SuiTransaction builder was introduced that offers a more powerful transaction compilation
capability. In 0.30.0 a number of `exec_builders` were removed making SuiTransaction the go to for complex transactions.

The Builder Package :py:mod:`pysui.sui.sui_builders` contains builders for
all of the SUI RPC Read API calls as well as a few transaction execution (complex) and subscription API.

A few  of the ``read builders`` are leveraged in the ``SuiClient(s)`` methods and only require
the expected parameters for the RPC call. All **tranaction** related interactions, however, are performed via
the SuiTransaction builder.

Module: base_builder - Sui Builders: Common types.
--------------------------------------------------

+-----------------------------------------------------------------------------+-------+
|                                     Name                                    | Notes |
+=============================================================================+=======+
| :py:class:`pysui.sui.sui_builders.base_builder.SuiRequestType`              |       |
+-----------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.base_builder.SuiTransactionBuilderMode`   |       |
+-----------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.base_builder.SuiBaseBuilder`              |       |
+-----------------------------------------------------------------------------+-------+

Module: exec_builders - Sui Builders: Complex transaction.
----------------------------------------------------------

+--------------------------------------------------------------------------+-------+
|                                   Name                                   | Notes |
+==========================================================================+=======+
| :py:class:`pysui.sui.sui_builders.exec_builders.ExecuteTransaction`      |       |
+--------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.DryRunTransaction`       |       |
+--------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.InspectTransaction`      |       |
+--------------------------------------------------------------------------+-------+


Module: get_builders - Sui Builders: Simple sui_getXXX calls.
-------------------------------------------------------------

+-------------------------------------------------------------------------------+-------+
|                                      Name                                     | Notes |
+===============================================================================+=======+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCoinMetaData`               |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetAllCoinBalances`            |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetAllCoins`                   |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCoinTypeBalance`            |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCoins`                      |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetLatestSuiSystemState`       |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTotalSupply`                |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetDynamicFieldObject`         |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetDynamicFields`              |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetObject`                     |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetMultipleObjects`            |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetObjectsOwnedByAddress`      |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetPastObject`                 |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetMultiplePastObjects`        |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetPackage`                    |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetModule`                     |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetFunction`                   |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetFunctionArgs`               |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetStructure`                  |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetRpcAPI`                     |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCommittee`                  |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.QueryEvents`                   |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.QueryTransactions`             |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetEvents`                     |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTotalTxCount`               |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTx`                         |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetDelegatedStakes`            |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetLatestCheckpointSequence`   |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpointByDigest`         |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpointBySequence`       |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpoints`                |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetReferenceGasPrice`          |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.NameServiceAddress`            |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.NameServiceNames`              |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetLoadedChildObjects`         |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetValidatorsApy`              |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetProtocolConfig`             |       |
+-------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetChainID`                    |       |
+-------------------------------------------------------------------------------+-------+
