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
