====
gRPC
====

``pysui`` supports the Sui gRPC service as a high-performance, async-only
transport protocol. The gRPC client is available on devnet, testnet, and
mainnet.

Running the Sample
------------------

``pgrpc_a_example.py`` is included in the project repository (not installed via
PyPI) and covers a variety of patterns — data queries, transaction building,
execution, and checkpoint subscriptions. It serves as a reference for exploring
available options and may be run optionally from an activated virtual
environment:

.. code-block:: shell

    python pgrpc_a_example.py

Client Setup
------------

Use :py:func:`pysui.sui.sui_common.factory.client_factory` to obtain a
gRPC client bound to the active configuration group. See
:doc:`PysuiConfiguration <pyconfig>` for configuration details.

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, client_factory

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)  # returns GrpcProtocolClient
        # All operations through client.execute(command=...)

    if __name__ == "__main__":
        asyncio.run(main())

Fetch Example
-------------

.. code-block:: python
   :linenos:

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, SuiRpcResult, client_factory

    async def get_object_example():
        """Fetch an object by ID."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)  # returns GrpcProtocolClient

        result: SuiRpcResult = await client.execute(
            command=cmd.GetObject(
                object_id="0x09f29cd8795c171136f0da589516bfdf4ca0f77084550830fe20611e06018dc7"
            )
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

        client.close()

    if __name__ == "__main__":
        asyncio.run(get_object_example())

Key Behaviours
--------------

- All gRPC service calls are **asynchronous** — there is no sync gRPC client.
- Every call returns a :py:class:`pysui.sui.sui_types.sui_txresult.SuiRpcResult`.
- Successful result data is returned as a typed ``dataclass`` instance.

Mysten Labs exposes the following gRPC services:
`gRPC on Sui <https://docs.sui.io/concepts/grpc-overview#grpc-on-sui>`_

.. note::

   Mysten Labs imposes rate limits on gRPC subscription endpoints (see
   :doc:`subscriptions`).

Pre-built Requests
------------------

See :doc:`grpc_requests` for the full list of pre-built
:py:mod:`pysui.sui.sui_grpc.pgrpc_requests` request classes.

Transaction Building
---------------------

Build and execute transactions using the unified transaction infrastructure:

.. code-block:: python
   :linenos:

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, client_factory

    async def transaction_example():
        """Build and execute a simple transaction."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        async with client_factory(cfg) as client:
            # Create transaction via client
            txn = await client.transaction()

            # Add transaction commands
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
            await txn.transfer_objects(
                transfers=[coin],
                recipient=cfg.active_address
            )

            # Build and sign
            build_result = await txn.build_and_sign()
            result = await client.execute(
                command=cmd.ExecuteTransaction(**build_result)
            )
            if result.is_ok():
                print(result.result_data)
            else:
                print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(transaction_example())

For serial and parallel executor reference, see :doc:`executors`.

Protocol-Level Access
----------------------

When you need direct access to gRPC requests without a ``SuiCommand`` wrapper,
use ``execute_grpc_request``:

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, client_factory
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    async def protocol_access_example():
        """Direct gRPC request for protocol-specific operation."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        async with client_factory(cfg) as client:
            result = await client.execute_grpc_request(
                request=rn.GetObject(
                    object_id="0x09f29cd8795c171136f0da589516bfdf4ca0f77084550830fe20611e06018dc7"
                )
            )
            if result.is_ok():
                print(result.result_data)
            else:
                print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(protocol_access_example())
