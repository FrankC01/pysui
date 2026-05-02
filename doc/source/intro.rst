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
single unified call.

The **Unified Client Interface (UCI)** builds on three pillars:

1. **Protocol-Agnostic Command Execution**: Use ``await client.execute(command=...)``
   with any ``SuiCommand`` subclass. The same code runs identically on both
   GraphQL and gRPC transports. Switching protocols requires only a
   configuration change — no application code changes.
   See :doc:`sui_commands` for the full list of 41 available commands.

2. **Shared Transaction Infrastructure**: :doc:`Programmable Transaction Blocks (PTBs) <transactions>`
   with unified transaction builders and executor factories work across
   all protocols, providing consistent semantics for building, signing,
   and executing transactions. Executor instances are obtained via
   ``await client.serial_executor(**kwargs)`` or
   ``await client.parallel_executor(**kwargs)`` — direct instantiation
   of executor classes is not part of the UCI contract.

3. **Protocol-Level Access**: When you need capabilities beyond ``SuiCommand``:
   Use :doc:`GraphQL QueryNodes <graphql_queries>` via ``execute_query_node``
   for custom queries, or :doc:`gRPC Requests <grpc_requests>` via
   ``execute_grpc_request`` for direct gRPC interactions.

Together, these pillars fully encapsulate all protocol details: developers
write against commands, transaction builders, and executor factories — not
against transport-specific APIs. Direct protocol access remains available
when needed, but is never required for standard use.

Quick Start — Unified Client Interface
---------------------------------------

The simplest way to start is with a ``SuiCommand``:

.. code-block:: python
   :linenos:

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, client_factory, SuiRpcResult

    async def main():
        # Use SUI_GRPC_GROUP to target gRPC instead
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(cfg) as client:
            result = await client.execute(
                command=cmd.GetGas(owner=client.config.active_address)
            )
            if result.is_ok():
                print(result.result_data)
            else:
                print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(main())

Next Steps
----------

See :doc:`installation` to install pysui and configure your environment.
