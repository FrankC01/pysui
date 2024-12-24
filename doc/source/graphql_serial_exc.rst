
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

Here is a simple sunny day example:

.. code-block:: python
    :linenos:

    import logging

    logger = logging.getLogger()
    logging.basicConfig(
        filename="ser_txn.log",
        filemode="w",
        encoding="utf-8",
        format="%(asctime)s %(module)s %(levelname)s %(message)s",
        level=logging.INFO,
    )

    from pysui import PysuiConfiguration, AsyncGqlClient
    from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction
    from pysui.sui.sui_pgql.execute.serial_exec import (
        SerialTransactionExecutor,
        ser_txn_exc_logger,
    )


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
        # Set logging level
        ser_txn_exc_logger.setLevel(logging.DEBUG)
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

    serial_exec DEBUG tx execution 0.9674050807952881
    serial_exec DEBUG tx execution 0.1889028549194336

Note that the first transaction smashes and primes the gas object as well as resolving unresolved objects

Exceptions
----------

Use caution when evaluating the result of the execution. If the result is not an instance of ExecutionResultGQL then
it is some error returned from either building, signing or executing the transaction. So, if the result is a
tuple (vs. an instance of ExecutionResultGQL) then it contains:

`(ExecutorError,Exception)`


.. code-block:: python
    :linenos:

    from pysui.sui.sui_pgql.pgql_types import ExecutionResultGQL

    async def test_splits():
        """."""
        # All code omitted
        gx = await ser_txne.execute_transactions([ser_txn_1, ser_txn_2])

        for gres in gx:
            if not isinstance(gres,tuple):
                print(gres.to_json(indent=2))
            else:
                error_enum, exception = gres
                print(f"Type error: {error_enum.name} exception: {exception}")
