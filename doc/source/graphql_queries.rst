
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
