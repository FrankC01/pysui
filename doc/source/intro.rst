=================
Introducing pysui
=================

**pysui** is a Python client SDK for the `Sui blockchain <https://sui.io>`_,
providing idiomatic access to Sui's GraphQL RPC and gRPC transports. A legacy
JSON-RPC client is included for compatibility but is planned for removal.

The Role of Sui Binaries
------------------------

``pysui`` requires the Sui CLI binaries for one specific operation:

- **Publishing and upgrading Move packages** — pysui invokes
  ``sui move build`` during publish and upgrade calls. If you do not need
  to publish Move code, Sui binaries are not required.

Transport Protocols
-------------------

pysui supports three transport protocols. For new code, choose between
**GraphQL** and **gRPC**; JSON-RPC is legacy.

+------------+---------------------+------------------+
| Protocol   | Status              | Planned Sunset   |
+============+=====================+==================+
| GraphQL    | Production          | None             |
+------------+---------------------+------------------+
| gRPC       | Production          | None             |
+------------+---------------------+------------------+
| JSON RPC   | Legacy              | 2026             |
+------------+---------------------+------------------+

For guidance on choosing between GraphQL and gRPC, see Mysten Labs'
`When to use gRPC or GraphQL <https://docs.sui.io/develop/accessing-data/data-serving#when-to-use-grpc-or-graphql-with-general-purpose-indexer>`_.

Client Design
-------------

pysui clients are intentionally thin. There are no fat ``get_coins``,
``get_object``, or similar convenience methods on the client itself.
All data access goes through typed request objects dispatched via a
single unified call:

- **Unified Client Interface (UCI)**: ``await client.execute(command=...)``
  — works identically on both GraphQL and gRPC transports.
  See :doc:`sui_commands` for the full command list.
- **GraphQL**: :doc:`QueryNodes <graphql_queries>` via
  ``execute_query_node`` — for custom queries with no ``SuiCommand`` equivalent.
- **gRPC**: :doc:`Requests <grpc_requests>` via
  ``execute_grpc_request`` — for direct gRPC request objects.
- **Transactions (PTBs)**: :doc:`transactions`

This keeps the client stable as the Sui protocol evolves: new query
capabilities are added as new ``SuiCommand`` subclasses without
changing the client API.

Next Steps
----------

See :doc:`getting_started` to install pysui and configure your environment.
