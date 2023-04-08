Programmable Transactions
=========================

General
-------
In version 0.29.1 MystenLabs introduced Programmable Transactions (herein referred
to as Transaction or SuiTransaction for the ``pysui`` flavor).

Transactions consist of one or more commands and if any command fails, the entire transaciton is
rolled back.

A few powerful advantages of this capability include:

    * A more expresive batch transaction
    * Both `public`` **and** `public entry` functions can be called on a Sui Move contract
    * If one command produces a result (e.g. `split_coin`, that result may be used as an argument to one or more subsequent commands
    * And more...

The ``pysui`` Implementation
----------------------------

A ``pysui`` SuiTransaciton commands are similar to `Sui TS SDK <https://docs.sui.io/devnet/build/prog-trans-ts-sdk>`_ but do have
differences:

    * Encapsulates additional high level commands, such as `stake_coin`, `unstake_coin` and `publish_upgrade`
    * Transaction methods have a high degree of flexibility in providing arguments

Gettinig Started
################
SuiTransactions encapsulate a SuiClient, gas objects, inspection and execution methods as well as the ability to add
one or more commands.

Quick example
~~~~~~~~~~~~~
This requires providing at least an instantiated SuiClient. At the moment it only supports the synchronous client:

.. code-block:: Python

    from pysui.sui.sui_clients.sync_client import SuiClient
    from pysui.sui.sui_clients.transaction import SuiTransaction

    def foo():
        """Demonstrate ."""

        # Get the Transaction/Transaction Builder
        txn = SuiTransaction(SuiClient(SuiConfig.default()))

        # Get a few objects to use as command arguments
        coin_to_split = ... # Retrieved somehow
        some_recipient = ... # Retrieve non-active-address somehow

        # Command that first splits a coin for some amount and uses
        # the results to pass to some recipient
        txn.transfer_objects(
            transfers=[txn.split_coin(coin=coin_to_split, amount=10000)],
            recipient=some_recipient,
        )

        # Execute will use active-address to sign, pick a gas coin
        # that satisfies the budget. An inspection is done internally
        # and the budget will automatically adjust to the higher when compared
        tx_result = txb.execute(signer=None, gas=None, gas_budget=1000)
        if tx_result.is_ok():
            print(tx_result.result_data.to_json(indent=2))
        else:
            print(tx_result.result_string)

Commands available
~~~~~~~~~~~~~~~~~~

Basic commands:
    * transfer_objects, transfer_sui
    * split_coin, split_coin_equally
    * make_move_vector
    * publish

Extended commands (provided as convenience):
    * stake_coin, unstake_coin

Coming soon:
    * publish_upgrade
