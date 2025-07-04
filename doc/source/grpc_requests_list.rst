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

+------------------------------------------------------------------------+
|                                  Name                                  |
+========================================================================+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetServiceInfo`           |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCheckpoint`            |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetEpoch`                 |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetObject`                |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPastObject`            |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjects`       |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetMultiplePastObjects`   |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetOwnedObjects`          |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetGas`                   |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetStaked`                |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetCoinInfo`              |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetBalance`               |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetBalances`              |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransaction`           |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetTransactions`          |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.ExecuteTransactions`      |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SimulateTransaction`      |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetPackage`               |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetModule`                |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetDataType`              |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.GetFunction`              |
+------------------------------------------------------------------------+
| :py:class:`pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoint`      |
+------------------------------------------------------------------------+
