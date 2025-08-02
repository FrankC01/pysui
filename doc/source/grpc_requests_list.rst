=============
gRPC Requests
=============

General
-------

With ``pysui's gRPC`` implementation a number of pre-built and ready to use
requests are delivered as part of the pysui package.

The pre-builts module :py:mod:`pysui.sui.sui_grpc.pgrpc_requests` contains
requests for a number of query and execution classes requiring only simple
parameters.


Request Classes
---------------

+--------------------------------------------------------------------------+
|                                   Name                                   |
+==========================================================================+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetServiceInfo`             |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpoint`              |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetLatestCheckpoint`        |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpointBySequence`    |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpointByDigest`      |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetEpoch`                   |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetLatestSuiSystemState`    |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetValidatorsApy`           |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCurrentValidators`       |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObject`                  |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ObjectContentBCS`           |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObjectContent`           |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPastObject`              |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjects`         |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDynamicFields`           |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ObjectsContentBCS`          |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjectContent`   |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultiplePastObjects`     |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObjectsOwnedByAddress`   |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCoins`                   |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetGas`                     |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStaked`                  |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDelegatedStakes`         |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCoinMetaData`            |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetBalance`                 |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetAllCoinBalances`         |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransaction`             |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTx`                      |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransactions`            |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleTx`              |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTxKind`                  |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ExecuteTransaction`         |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SimulateTransaction`        |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SimulateTransactionLKind`   |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPackageVersions`         |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPackage`                 |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDataType`                |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStructure`               |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.MoveStructuresGRPC`         |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.MoveFunctionsGRPC`          |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStructures`              |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetFunction`                |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetFunctions`               |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetModule`                  |
+--------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoint`        |
+--------------------------------------------------------------------------+
