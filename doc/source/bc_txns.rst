=======================
Blockchain Transactions
=======================

``pysui`` supports Programmable Transaction Blocks (PTB), ``transaction`` for
short, for the three client flavors (JSON RPC, GraphQL and gRPC).

All transactions have parity for the fundamental commands. **Note** that the
gRPC transaction _only_ supports `async` command methods

Transaction Commands
--------------------

+--------------------------+---------------+
|  Command                 | Available     |
+==========================+===============+
| split_coin               | all           |
+--------------------------+---------------+
| split_coin_equal         | all           |
+--------------------------+---------------+
| merge_coin               | all           |
+--------------------------+---------------+
| transfer_objects         | all           |
+--------------------------+---------------+
| transfer_sui             | all           |
+--------------------------+---------------+
| public_transfer_object   | all           |
+--------------------------+---------------+
| make_move_vector         | all           |
+--------------------------+---------------+
| move_call                | all           |
+--------------------------+---------------+
| stake_coin               | all           |
+--------------------------+---------------+
| unstake_coin             | all           |
+--------------------------+---------------+
| publish                  | all           |
+--------------------------+---------------+
| publish_upgrade          | all           |
+--------------------------+---------------+
| custom_upgrade           | all           |
+--------------------------+---------------+
| optional_object          | GraphQL/gRPC  |
+--------------------------+---------------+

Executing Transactions
----------------------

The various PTB implementations:

+--------------------------+---------------------------------------------------------------------+
|  Command                 | Link                                                                |
+==========================+=====================================================================+
| JSON RPC synchronous     | :py:class:`pysui.sui.sui_txn.sync_transaction.SuiTransaction`       |
+--------------------------+---------------------------------------------------------------------+
| JSON RPC asynchronous    | :py:class:`pysui.sui.sui_txn.async_transaction.SuiTransactionAsync` |
+--------------------------+---------------------------------------------------------------------+
| GraphQL  synchronous     | :py:class:`pysui.sui.sui_pgql.pgql_sync_txn.SuiTransaction`         |
+--------------------------+---------------------------------------------------------------------+
| GraphQL  asynchronous    | :py:class:`pysui.sui.sui_pgql.pgql_async_txn.AsyncSuiTransaction`   |
+--------------------------+---------------------------------------------------------------------+
| gRPC asynchronous        | :py:class:`pysui.sui.sui_grpc.pgrpc_async_txn.AsyncSuiTransaction`  |
+--------------------------+---------------------------------------------------------------------+

See `JSON RPC Nuances`_ for additional considerations when using said client.

The example below shows variations of building and executing a Transaction
for each of the client flavors with a common `split_coin` and
`transfer_objects` command set.

Copy the example to a local script (e.g. ``client parity.py``) then
execute via:

.. code-block:: shell
   :linenos:

   python client_parity.py -s  # for JSON RPC and GraphQL synchronous clients
   python client_parity.py -a  # for gRPC and GraphQL asynchronous clients
   python client_parity.py -b  # for both synchronous and asynchronous clients


.. code-block:: python
   :linenos:

    #    Copyright Frank V. Castellucci
    #    SPDX-License-Identifier: Apache-2.0

    # -*- coding: utf-8 -*-

    """Client Transaction Parity."""

    import asyncio
    import sys


    # For Clients, Configurations and Results
    from pysui import (
        # For All
        SuiRpcResult,
        # For JSON RPC
        SuiConfig,
        SyncClient,
        AsyncClient,
        # For GraphQL and gRPC
        PysuiConfiguration,
        SyncGqlClient,
        AsyncGqlClient,
        SuiGrpcClient,
    )

    # For JSON RPC
    import pysui.sui.sui_txn as jsonrpc

    # For GraphQL
    import pysui.sui.sui_pgql.pgql_query as qn
    import pysui.sui.sui_pgql.pgql_sync_txn as gql_sync
    import pysui.sui.sui_pgql.pgql_async_txn as gql_async

    # For gRPC
    import pysui.sui.sui_grpc.pgrpc_requests as rn
    import pysui.sui.sui_grpc.pgrpc_async_txn as grpc_async


    def json_rpc_example():
        """Simple JSON RPC split and transfer."""
        client = SyncClient(SuiConfig.default_config())
        txer: jsonrpc.SyncTransaction = client.transaction()
        split = txer.split_coin(coin=txer.gas, amounts=[1_000_000_000])
        txer.transfer_objects(
            transfers=[split],
            recipient=client.config.active_address,
        )
        result: SuiRpcResult = txer.execute()
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    async def json_rpc_example_async():
        """Simple async JSON RPC split and transfer."""
        client = AsyncClient(SuiConfig.default_config())
        txer: jsonrpc.AsyncTransaction = client.transaction()
        split = await txer.split_coin(coin=txer.gas, amounts=[1_000_000_000])
        await txer.transfer_objects(
            transfers=[split],
            recipient=client.config.active_address,
        )
        result: SuiRpcResult = await txer.execute()
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    def graphql_example():
        """Simple GraphQL split and transfer."""
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        )
        client = SyncGqlClient(pysui_config=cfg)

        txer: gql_sync.SuiTransaction = client.transaction()
        scres = txer.split_coin(coin=txer.gas, amounts=[1000000])
        txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
        txdict = txer.build_and_sign()
        result: SuiRpcResult = client.execute_query_node(
            with_node=qn.ExecuteTransaction(**txdict)
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    async def graphql_example_async():
        """Simple async GraphQL split and transfer."""
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        )
        client = AsyncGqlClient(pysui_config=cfg)

        txer: gql_async.AsyncSuiTransaction = client.transaction()
        scres = await txer.split_coin(coin=txer.gas, amounts=[1000000])
        await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute_query_node(
            with_node=qn.ExecuteTransaction(**txdict)
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    async def grpc_example_async():
        """Simple async gRPC split and transfer."""
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        )
        client: SuiGrpcClient = SuiGrpcClient(pysui_config=cfg)
        txer: grpc_async.AsyncSuiTransaction = client.transaction()
        scres = await txer.split_coin(coin=txer.gas, amounts=[1000000])
        await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute(request=rn.ExecuteTransaction(**txdict))
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    def sync_main():
        """Uncomment which to run."""

        json_rpc_example()
        graphql_example()


    async def async_main():
        """Uncomment which async protocol to run."""
        await json_rpc_example_async()
        await graphql_example_async()
        await grpc_example_async()


    def main():
        """Main entry point."""
        args = sys.argv[1:]
        try:
            if args[0][1] == "s":
                sync_main()
            elif args[0][1] == "a":
                asyncio.run(async_main())
            elif args[0][1] == "b":
                sync_main()
                asyncio.run(async_main())
        except Exception as e:
            print(e)


    if __name__ == "__main__":
        main()


JSON RPC Nuances
----------------

GraphQL and gRPC PTBs eliminate the need to **wrap** transaction command
arguments. You can use native Python types for command parameters and
**move_call** arguments.

JSON RPC
++++++++

.. code-block:: python
    :linenos:

    txn.move_call(
        target="0x0cce956e2b82b3844178b502e3a705dead7d2f766bfbe35626a0bbed06a42e9e::marketplace::buy_and_take",
        arguments=[
            ObjectID("0xb468f361f620ac05de721e487e0bdc9291c073a7d4aa7595862aeeba1d99d79e"),
            ObjectID("0xfd542ebc0f6743962077861cfa5ca9f1f19de8de63c3b09a6d9d0053d0104908"),
            ObjectID("0x97db1bba294cb30ce116cb94117714c64107eabf9a4843b155e90e0ae862ade5"),
            SuiAddress(coin_object_id),
            ObjectID(coin_object_id),
            SuiU64(1350000000),
        ],
        type_arguments=[
            "0x3dcfc5338d8358450b145629c985a9d6cb20f9c0ab6667e328e152cdfd8022cd::suifrens::SuiFren<0x3dcfc5338d8358450b145629c985a9d6cb20f9c0ab6667e328e152cdfd8022cd::capy::Capy>",
            "0x2::sui::SUI",
        ],
    )

GrqphQL and gRPC
++++++++++++++++

.. code-block:: python
    :linenos:

    txn.move_call(
        target="0x0cce956e2b82b3844178b502e3a705dead7d2f766bfbe35626a0bbed06a42e9e::marketplace::buy_and_take",
        arguments=[
            "0xb468f361f620ac05de721e487e0bdc9291c073a7d4aa7595862aeeba1d99d79e",
            "0xfd542ebc0f6743962077861cfa5ca9f1f19de8de63c3b09a6d9d0053d0104908",
            "0x97db1bba294cb30ce116cb94117714c64107eabf9a4843b155e90e0ae862ade5",
            coin_object_id,
            coin_object_id,
            1350000000,
        ],
        type_arguments=[
            "0x3dcfc5338d8358450b145629c985a9d6cb20f9c0ab6667e328e152cdfd8022cd::suifrens::SuiFren<0x3dcfc5338d8358450b145629c985a9d6cb20f9c0ab6667e328e152cdfd8022cd::capy::Capy>",
            "0x2::sui::SUI",
        ],
    )

JSON RPC Argument Conversions
+++++++++++++++++++++++++++++

+----------------------------------------------------------+-----------------------------+
|     Types                                                |       Converts to           |
+==========================================================+=============================+
| str, SuiString                                           | Passed as vector<u8>        |
+----------------------------------------------------------+-----------------------------+
| int, SuiInteger                                          | Passed as minimal bit value |
+----------------------------------------------------------+-----------------------------+
| bool, bytes, SuiBoolean                                  | Passed as raw value         |
+----------------------------------------------------------+-----------------------------+
| SuiU8, SuiU16, SuiU32, SuiU64, SuiU128, SuiU256          | Passed as value  [#f1]_     |
+----------------------------------------------------------+-----------------------------+
| list, SuiArray [#f2]_                                    | Members passed as values    |
+----------------------------------------------------------+-----------------------------+
| OptionalU8, OptionalU16, OptionalU32,                    |                             |
| OptionalU64, OptionalU128, OptionalU256                  | Passed as Optional<uX>      |
+----------------------------------------------------------+-----------------------------+
| SuiAddress                                               | Passed as move address      |
+----------------------------------------------------------+-----------------------------+
| ObjectID, SuiCoinObject, ObjectRead                      | Passed as reference [#f3]_  |
+----------------------------------------------------------+-----------------------------+
| Result of previous command [#f4]_                        | Command Result index        |
+----------------------------------------------------------+-----------------------------+

.. rubric:: Footnotes

.. [#f1] Explicit unsigned integer bit size types
.. [#f2] Members must be scalars, SuiAddresses or results of previous commands. For Object vectors use :py:meth:`pysui.sui.sui_clients.transaction.SuiTransaction.make_move_vector`
.. [#f3] Will determine if Shared object or not before transaction execution
.. [#f4] Result may be a list, so understanding which commands return a zero, 1 or multiple(list) is important
