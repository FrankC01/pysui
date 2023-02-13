
Builders
========

General
-------

The Builder Package :py:mod:`pysui.sui.sui_builders` contains builders for
every SUI RPC API call.

Many of the ``builders`` are used in the common ``SuiClient(s)`` methods and only require
the expected parameters for the RPC call. However, all ``builders`` are exposed for the
developers use to construct as they see fit and calling the ``SuiClient(s)`` :py:meth:`pysui.sui.sui_clients.sync_client.SuiClient.execute`

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

+---------------------------------------------------------------------------------+-------+
|                                       Name                                      | Notes |
+=================================================================================+=======+
| :py:class:`pysui.sui.sui_builders.exec_builders.ExecuteTransaction`             |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.ExecuteSerializedTransaction`   |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.DryRunTransaction`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.InspectTransaction`             |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.TransferObject`                 |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.TransferSui`                    |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.Pay`                            |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.PaySui`                         |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.PayAllSui`                      |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.MergeCoin`                      |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.SplitCoin`                      |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.SplitCoinEqually`               |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.BatchParameter`                 |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.TransferObjectParams`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.MoveCallRequestParams`          |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.BatchTransaction`               |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.Publish`                        |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.MoveCall`                       |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.RequestAddDelegation`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.RequestSwitchDelegation`        |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.exec_builders.RequestWithdrawDelegation`      |       |
+---------------------------------------------------------------------------------+-------+

.. _subscription-filters:

Module: subscription_builders - Sui Builders: For subscriptions and filters.
----------------------------------------------------------------------------

+---------------------------------------------------------------------------------+-------+
|                                       Name                                      | Notes |
+=================================================================================+=======+
| :py:class:`pysui.sui.sui_builders.subscription_builders.SenderFilter`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.PackageFilter`          |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.ModuleFilter`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.MoveEventTypeFilter`    |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.MoveEventFieldFilter`   |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.EventTypeFilter`        |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.ObjectFilter`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.AndFilter`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.OrFilter`               |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.AllFilter`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.AnyFilter`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.SubscribeEvent`         |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.subscription_builders.SubscribeTransaction`   |       |
+---------------------------------------------------------------------------------+-------+

Module: get_builders - Sui Builders: Simple sui_getXXX calls.
-------------------------------------------------------------

+---------------------------------------------------------------------------------+-------+
|                                       Name                                      | Notes |
+=================================================================================+=======+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCoinMetaData`                 |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetAllCoinBalances`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetAllCoins`                     |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCoinTypeBalance`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCoins`                        |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetSuiSystemState`               |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTotalSupply`                  |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetObjectsOwnedByAddress`        |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetObjectsOwnedByObject`         |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetDynamicFieldObject`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetDynamicFields`                |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetObject`                       |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetPastObject`                   |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetPackage`                      |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetModule`                       |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetFunction`                     |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetFunctionArgs`                 |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetStructure`                    |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetRpcAPI`                       |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCommittee`                    |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.TransactionEventQuery`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.MoveModuleEventQuery`            |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.MoveEventQuery`                  |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.EventTypeQuery`                  |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.SenderEventQuery`                |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.RecipientEventQuery`             |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.ObjectEventQuery`                |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.TimeRangeEventQuery`             |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetEvents`                       |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTotalTxCount`                 |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTx`                           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTxs`                          |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTransactionsInRange`          |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetTxAuthSignatures`             |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetDelegatedStakes`              |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetValidators`                   |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpointContents`           |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpointContentsByDigest`   |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpointSummary`            |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetCheckpointSummaryByDigest`    |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetLatestCheckpointSequence`     |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.GetReferenceGasPrice`            |       |
+---------------------------------------------------------------------------------+-------+
| :py:class:`pysui.sui.sui_builders.get_builders.SignRandomnessObject`            |       |
+---------------------------------------------------------------------------------+-------+
