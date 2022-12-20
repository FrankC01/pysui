
Builders
========

General
-------

The Builder module :py:mod:`pysui.sui.sui_builders` contains a builder for
every SUI RPC API call.

Many of the ``builders`` are used in the common ``SuiClient(s)`` methods and only require
the expected parameters for the RPC call. However, all ``builders`` are exposed for the
developers use to construct as they see fit and calling the ``SuiClient(s)`` :py:meth:`pysui.sui.sui_rpc.SuiClient.execute`

Coverage
--------

+---------------------------------------------------------------+-------+
|                              Name                             | Notes |
+===============================================================+=======+
| :meth:`pysui.sui.sui_builders.SuiRequestType`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.SuiBaseBuilder`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetCoinTypeBalance`             |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetCoins`                       |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetCoinMetaData`                |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetSuiSystemState`              |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetTotalSupply`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetObjectsOwnedByAddress`       |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetObjectsOwnedByObject`        |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetObject`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetPastObject`                  |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetPackage`                     |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetModule`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetFunction`                    |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetFunctionArgs`                |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetStructure`                   |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetRpcAPI`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetCommittee`                   |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.TransactionEventQuery`          |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.MoveModuleEventQuery`           |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.MoveEventQuery`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.EventTypeQuery`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.SenderEventQuery`               |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.RecipientEventQuery`            |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.ObjectEventQuery`               |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.TimeRangeEventQuery`            |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetEvents`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetTotalTxCount`                |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetTx`                          |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetTxs`                         |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetTransactionsInRange`         |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.GetTxAuthSignatures`            |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.ExecuteTransaction`             |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.ExecuteSerializedTransaction`   |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.DryRunTransaction`              |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.TransferObject`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.TransferSui`                    |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.Pay`                            |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.PaySui`                         |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.PayAllSui`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.MergeCoin`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.SplitCoin`                      |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.SplitCoinEqually`               |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.BatchParameter`                 |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.TransferObjectParams`           |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.MoveCallRequestParams`          |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.BatchTransaction`               |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.Publish`                        |       |
+---------------------------------------------------------------+-------+
| :meth:`pysui.sui.sui_builders.MoveCall`                       |       |
+---------------------------------------------------------------+-------+


See :py:mod:`pysui.sui.sui_builders`