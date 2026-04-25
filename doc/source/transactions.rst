================================
Programmable Transaction Blocks
================================

``pysui`` supports Programmable Transaction Blocks (PTBs) across all three
transport protocols. GraphQL and gRPC share the same command set and identical
calling conventions; both are **async only** for new code. JSON-RPC
transactions are covered separately — see :doc:`jsonrpc_transactions`.

All transaction builder instances are obtained by calling
``client.transaction()`` on the active client.

Transaction Commands
--------------------

All commands listed below are available on both the GraphQL and gRPC
transaction builders. ``optional_object`` is not available on JSON-RPC.

+--------------------------+
|  Command                 |
+==========================+
| split_coin               |
+--------------------------+
| split_coin_equal         |
+--------------------------+
| merge_coin               |
+--------------------------+
| transfer_objects         |
+--------------------------+
| transfer_sui             |
+--------------------------+
| public_transfer_object   |
+--------------------------+
| make_move_vector         |
+--------------------------+
| move_call                |
+--------------------------+
| stake_coin               |
+--------------------------+
| unstake_coin             |
+--------------------------+
| publish                  |
+--------------------------+
| publish_upgrade          |
+--------------------------+
| custom_upgrade           |
+--------------------------+
| optional_object \*       |
+--------------------------+
| balance_from \*          |
+--------------------------+

\* GraphQL and gRPC only; not available on JSON-RPC.

Executing Transactions
----------------------

+--------------------------+---------------------------------------------------------------------+
|  Implementation          | Class                                                               |
+==========================+=====================================================================+
| GraphQL  asynchronous    | :py:class:`pysui.sui.sui_pgql.pgql_async_txn.AsyncSuiTransaction`   |
+--------------------------+---------------------------------------------------------------------+
| gRPC asynchronous        | :py:class:`pysui.sui.sui_grpc.pgrpc_async_txn.AsyncSuiTransaction`  |
+--------------------------+---------------------------------------------------------------------+

For JSON-RPC transaction classes see :doc:`jsonrpc_transactions`.

Executor classes (serial and parallel) that wrap the transaction lifecycle
are documented on :doc:`executors`.

Client Parity Example
---------------------

The example below builds and executes the same PTB — a coin split followed by
a transfer — against the GraphQL and gRPC transports using
:py:func:`pysui.sui.sui_common.factory.client_factory`.

Copy it to a local script and run with:

.. code-block:: shell

   python client_parity.py

.. code-block:: python
   :linenos:

    #    Copyright Frank V. Castellucci
    #    SPDX-License-Identifier: Apache-2.0

    """Client Transaction Parity — GraphQL and gRPC."""

    import asyncio

    from pysui import PysuiConfiguration, SuiRpcResult, client_factory

    import pysui.sui.sui_pgql.pgql_query as qn
    import pysui.sui.sui_pgql.pgql_async_txn as gql_async

    import pysui.sui.sui_grpc.pgrpc_requests as rn
    import pysui.sui.sui_grpc.pgrpc_async_txn as grpc_async


    async def graphql_example():
        """GraphQL async split and transfer."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)  # returns AsyncSuiGQLClient

        txer: gql_async.AsyncSuiTransaction = await client.transaction()
        scres = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
        await txer.transfer_objects(
            transfers=scres, recipient=client.config.active_address
        )
        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute_query_node(
            with_node=qn.ExecuteTransaction(**txdict)
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    async def grpc_example():
        """gRPC async split and transfer."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)  # returns SuiGrpcClient

        txer: grpc_async.AsyncSuiTransaction = await client.transaction()
        scres = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
        await txer.transfer_objects(
            transfers=scres, recipient=client.config.active_address
        )
        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute(
            request=rn.ExecuteTransaction(**txdict)
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    async def main():
        """Run both protocol examples."""
        await graphql_example()
        await grpc_example()


    if __name__ == "__main__":
        asyncio.run(main())


Argument Passing
----------------

GraphQL and gRPC accept **native Python types** as transaction command
arguments. Wrapping in pysui scalar objects (``ObjectID``, ``SuiU64``, etc.)
is not required.

``move_call`` on GraphQL and gRPC:

.. code-block:: python
   :linenos:

    txn.move_call(
        target="0x0cce...e9e::marketplace::buy_and_take",
        arguments=[
            "0xb468...9e",   # str — object ID
            "0xfd54...08",
            "0x97db...e5",
            coin_object_id,  # str
            coin_object_id,
            1350000000,      # int
        ],
        type_arguments=[
            "0x3dcf...cd::suifrens::SuiFren<...::capy::Capy>",
            "0x2::sui::SUI",
        ],
    )

JSON-RPC ``move_call`` requires pysui wrapper types for every argument — see
:ref:`jsonrpc-move-call` in :doc:`jsonrpc_transactions`.
