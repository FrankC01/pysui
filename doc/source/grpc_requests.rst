:orphan:

=============
gRPC Requests
=============

General
-------

With ``pysui's gRPC`` implementation a number of pre-built and ready to use
requests are delivered as part of the pysui package.

The pre-built module :py:mod:`pysui.sui.sui_grpc.pgrpc_requests` contains
requests for a number of query and execution classes requiring only simple
parameters.

.. note::

   These request objects are **EC-5 escape hatches** for cases where no
   :py:class:`~pysui.sui.sui_common.sui_command.SuiCommand` equivalent exists.
   For standard queries prefer ``await client.execute(command=...)`` with a
   :doc:`SuiCommand <sui_commands>` subclass — it works identically on both
   GraphQL and gRPC transports.  Use ``execute_grpc_request(request=...)``
   only when you need a request type not covered by a built-in SuiCommand.

Request Classes
---------------

+-------------------------------------------------------------------------------+
|                                     Name                                      |
+===============================================================================+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetServiceInfo`                  |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetChainIdentifierSC`            |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpoint`                   |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetLatestCheckpoint`             |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpointBySequence`         |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpointByDigest`           |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetEpoch`                        |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetLatestSuiSystemState`         |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetLatestSuiSystemStateSC`       |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCurrentValidators`            |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCurrentValidatorsSC`          |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetBasicCurrentEpochInfo`        |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetProtocolConfig`               |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObject`                       |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ObjectContentBCS`                |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObjectContent`                |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPastObject`                   |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObjectSC`                     |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPastObjectSC`                 |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjects`              |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests._GetMultipleObjectsResolvedSC`   |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDynamicFields`                |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ObjectsContentBCS`               |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjectContent`        |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultiplePastObjects`          |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObjectsOwnedByAddress`        |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCoins`                        |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetGas`                          |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStaked`                       |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDelegatedStakes`              |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCoinMetaData`                 |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetAddressCoinBalance`           |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetBalance`                      |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetAddressCoinBalances`          |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetAllCoinBalances`              |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransaction`                  |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTx`                           |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransactions`                 |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleTx`                   |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTxKind`                       |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransactionSC`                |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransactionsSC`               |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransactionKindSC`            |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ExecuteTransaction`              |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SimulateTransaction`             |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SimulateTransactionKind`         |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SimulateTransactionLKind`        |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPackageVersions`              |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPackage`                      |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMoveDataType`                 |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDataType`                     |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStructure`                    |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.MoveStructuresGRPC`              |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.MoveFunctionsGRPC`               |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStructures`                   |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetFunction`                     |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetFunctions`                    |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetModule`                       |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoint`             |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.VerifySignature`                 |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetNameServiceAddress`           |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.NameLookup`                      |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetNameServiceNames`             |
+-------------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ReverseNameLookup`               |
+-------------------------------------------------------------------------------+