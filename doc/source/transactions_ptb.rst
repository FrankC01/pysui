================================
Programmable Transaction Blocks
================================

``pysui`` supports Programmable Transaction Blocks (PTBs) across GraphQL and
gRPC. Both share the same command set and identical calling conventions and
are **async only**.

For transaction builder construction, constructor options, and build methods,
see :doc:`transactions`.

Transaction Commands
--------------------

All commands listed below are available on both the GraphQL and gRPC
transaction builders.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.split_coin`
     - Create a new coin(s) with the defined amount(s), split from the provided coin.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.split_coin_equal`
     - Split one coin into equal parts and transfer all to transaction signer.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.merge_coins`
     - Merge one or more coins to a primary coin.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.transfer_objects`
     - Transfer one or more objects to a recipient.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.transfer_sui`
     - Transfer a Sui coin object to a recipient.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.public_transfer_object`
     - Public transfer of any object with KEY and STORE attributes.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.make_move_vector`
     - Convert a list of objects to a Sui Move vector of item_type.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.move_call`
     - Invoke a Move contract call.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.stake_coin`
     - Stake one or more coins to a specific validator.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.unstake_coin`
     - Unstake a Staked Sui Coin.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.publish`
     - Publish a Move package.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.publish_upgrade`
     - Authorize, publish, and commit an upgrade of a package.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.custom_upgrade`
     - Support for custom authorization and upgrade commitments.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.optional_object`
     - Wrap an object as a Move Option.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.coin_from_address_accumulator`
     - Withdraw Coin<T> from transaction source Sender or Sponsor account.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.withdrawal`
     - Produce a raw ``Withdrawal<T>`` PTB input from the Sender or Sponsor address accumulator for use as a ``move_call`` argument.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.create_balance`
     - Produce a ``Balance<T>`` PTB input from the Sender or Sponsor address accumulator for use as a ``move_call`` argument.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.fund_address_accumulator`
     - Send one or more coins to a recipient's address account balance (accumulator).

Executing Transactions
----------------------

+--------------------------+-----------------------------------------------------------------+
|  Implementation          | Class                                                           |
+==========================+=================================================================+
| GraphQL and gRPC async   | :py:class:`pysui.sui.sui_common.async_txn.AsyncSuiTransaction`  |
+--------------------------+-----------------------------------------------------------------+

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

    import pysui.sui.sui_common.sui_commands as cmd
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction


    async def graphql_example():
        """GraphQL async split and transfer."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)  # returns GqlProtocolClient

        txer: AsyncSuiTransaction = await client.transaction()
        scres = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
        await txer.transfer_objects(
            transfers=scres, recipient=client.config.active_address
        )
        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute(
            command=cmd.ExecuteTransaction(**txdict)
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


    async def grpc_example():
        """gRPC async split and transfer."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)  # returns GrpcProtocolClient

        txer: AsyncSuiTransaction = await client.transaction()
        scres = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
        await txer.transfer_objects(
            transfers=scres, recipient=client.config.active_address
        )
        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute(
            command=cmd.ExecuteTransaction(**txdict)
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
