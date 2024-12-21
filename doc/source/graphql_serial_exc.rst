
GraohQL SerialTransactionExecutor
=================================

General
-------

The SerialTransactionExecutor is implemented along with GraphQL support. It highly efficient when creating transactions
signed by the same address and where the objects owned by the address executing transactions are unlikely to be
changed by transactions not executed through this executor.

The executor is backed by an object cache that is initially populated by resolving the first transactions objects. said objects
are updated (diged, version) by the transaction results. Subsequent transactions objects are then resolved by the cache as is
the gas object used to pay for the transaction.

Note that all available gas objects will be smashed to one gas object during transaction build processing.

Here is a simple example:

.. code-block:: python
    :linenos:

    async def test_splits():
        """."""
        client = AsyncGqlClient(
            write_schema=False,
            pysui_config=PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP
            ),
        )
        ser_txne = SerialTransactionExecutor(
            client=client, signer=client.config.active_address, default_gas_budget=5000000
        )
        # Tx 1
        ser_txn_1: CachingTransaction = await ser_txne.new_transaction()
        scoin = await ser_txn_1.split_coin(coin=ser_txn_1.gas, amounts=[1000000000])
        await ser_txn_1.transfer_objects(
            transfers=[scoin], recipient=client.config.active_address
        )

        # Tx 2
        ser_txn_2: CachingTransaction = await ser_txne.new_transaction()
        scoin = await ser_txn_2.split_coin(coin=ser_txn_2.gas, amounts=[1000000000])
        await ser_txn_2.transfer_objects(
            transfers=[scoin], recipient=client.config.active_address
        )
        gx = await ser_txne.execute_transactions([ser_txn_1, ser_txn_2])
        for gres in gx:
            print(gres.to_json(indent=2))

In this example the two transaction times are, respectivley:

.. code-block:: shell
    :linenos:

    serial_exec DEBUG tx execution 3.573889970779419
    serial_exec DEBUG tx execution 0.1877460479736328
