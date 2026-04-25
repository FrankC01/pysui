==========================
JSON-RPC Transactions
==========================

.. note::

   JSON-RPC is the original pysui transport and is considered legacy.
   New code should target :doc:`graphql` or :doc:`grpc`.

``pysui`` supports Programmable Transaction Blocks (PTBs) over JSON-RPC with
both synchronous and asynchronous clients.

Executing Transactions
----------------------

+--------------------------+---------------------------------------------------------------------+
|  Implementation          | Class                                                               |
+==========================+=====================================================================+
| JSON RPC synchronous     | :py:class:`pysui.sui.sui_txn.sync_transaction.SuiTransaction`       |
+--------------------------+---------------------------------------------------------------------+
| JSON RPC asynchronous    | :py:class:`pysui.sui.sui_txn.async_transaction.SuiTransactionAsync` |
+--------------------------+---------------------------------------------------------------------+

Usage Examples
--------------

.. code-block:: python
   :linenos:

    #    Copyright Frank V. Castellucci
    #    SPDX-License-Identifier: Apache-2.0

    """JSON-RPC Transaction Examples."""

    import asyncio
    from pysui import SuiConfig, SyncClient, AsyncClient, SuiRpcResult
    import pysui.sui.sui_txn as jsonrpc


    def json_rpc_example():
        """Synchronous JSON-RPC split and transfer."""
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
        """Asynchronous JSON-RPC split and transfer."""
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


    if __name__ == "__main__":
        json_rpc_example()
        asyncio.run(json_rpc_example_async())


.. _jsonrpc-move-call:

Argument Conversions
--------------------

JSON-RPC requires pysui wrapper types for every ``move_call`` argument.
GraphQL and gRPC accept native Python types — see :doc:`transactions`.

``move_call`` on JSON-RPC:

.. code-block:: python
   :linenos:

    txn.move_call(
        target="0x0cce...e9e::marketplace::buy_and_take",
        arguments=[
            ObjectID("0xb468...9e"),
            ObjectID("0xfd54...08"),
            ObjectID("0x97db...e5"),
            SuiAddress(coin_object_id),
            ObjectID(coin_object_id),
            SuiU64(1350000000),
        ],
        type_arguments=[
            "0x3dcf...cd::suifrens::SuiFren<...::capy::Capy>",
            "0x2::sui::SUI",
        ],
    )

The full set of supported argument types and their conversions:

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
