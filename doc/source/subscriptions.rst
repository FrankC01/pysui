=============
Subscriptions
=============

gRPC Checkpoint Subscription
-----------------------------

The gRPC transport supports native server-side streaming via
:py:class:`pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoint`. The
client receives checkpoint events as an async iterator.

.. note::

    Mysten Labs servers impose rate limits on subscription endpoints.

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, SuiGrpcClient, client_factory
    import pysui.sui.sui_common.sui_commands as cmd

    async def stream_checkpoints():
        """Stream checkpoint events via gRPC subscription."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)  # returns SuiGrpcClient

        result = await client.execute(command=cmd.SubscribeCheckpoint())

        count = 0
        async for checkpoint in result.result_data:
            print(checkpoint.to_json(indent=2))
            count += 1
            if count >= 3:
                break

    if __name__ == "__main__":
        asyncio.run(stream_checkpoints())

See ``pgrpc_a_example.py`` in the project root for a runnable version.

GraphQL Checkpoint Polling
--------------------------

The GraphQL transport does not support native subscriptions. Use
:py:class:`pysui.sui.sui_pgql.pgql_query.GetCheckpoints` to poll for the
latest checkpoint batch.

.. note::

    ``GetCheckpoints`` (paginated batch) has no ``SuiCommand`` equivalent —
    this is an **EC-5 escape hatch**.  Use ``execute_query_node`` directly.

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, AsyncSuiGQLClient, client_factory
    import pysui.sui.sui_pgql.pgql_query as qn

    async def poll_checkpoints():
        """Fetch the current checkpoint batch via GraphQL (EC-5)."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)  # returns AsyncSuiGQLClient

        result = await client.execute_query_node(with_node=qn.GetCheckpoints())
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(poll_checkpoints())

See ``pgql_a_example.py`` in the project root for a runnable version.

JSON-RPC
--------

Mysten has deprecated subscriptions for JSON-RPC.
