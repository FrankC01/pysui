Programmable Transactions
=========================

General
-------
In version 0.29.1 MystenLabs introduced Programmable Transactions (herein referred
to as SuiTransaction for the ``pysui`` flavor).

SuiTransactions consist of one or more commands and if any command fails, the entire transaciton is
rolled back.

A few powerful advantages of this capability include:

    * A more expresive batch transaction
    * Both `public`` **and** `public entry` functions can be called on a Sui Move contract
    * If one command produces a result (e.g. `split_coin`, that result may be used as an argument to one or more subsequent commands
    * And more...

The ``pysui`` Implementation
----------------------------

The ``pysui`` SuiTransaction's commands are similar to `Sui TS SDK <https://docs.sui.io/devnet/build/prog-trans-ts-sdk>`_ but do have
differences:

    * Encapsulates additional high level commands, such as `stake_coin`, `unstake_coin`, `split_coin_equal` and `publish_upgrade`
    * Transaction methods have a high degree of flexibility in providing arguments

Gettinig Started
################
SuiTransactions encapsulate a SuiClient, transaction signers and gas objects, inspection and execution methods as well as
the ability to add one or more commands.

Quick example
~~~~~~~~~~~~~
This requires providing at least an instantiated SuiClient. At the moment it only supports the synchronous client:

.. code-block:: Python

    from pysui.sui.sui_clients.sync_client import SuiClient
    from pysui.sui.sui_clients.transaction import SuiTransaction
    from pysui.sui.sui_config import SuiConfig

    def foo():
        """Demonstrates a simple SuiTransaction ."""

        # Get the Transaction/Transaction Builder
        # By default, this will assume that the 'active-address' is the sole signer of the transaction
        # However; support for MultiSig signers and Sponsoring transactions is supported
        txn = SuiTransaction(SuiClient(SuiConfig.default_config()))

        # Get a few objects to use as command arguments
        coin_to_split = ... # Retrieved somehow
        some_recipient = ... # Retrieve non-active-address somehow

        # Command that first splits a coin for some amount and uses
        # the results to pass to some recipient
        txn.transfer_objects(
            transfers=[txn.split_coin(coin=coin_to_split, amounts=[1000000])],
            recipient=some_recipient,
        )

        # Execute will use active-address to sign, pick a gas coin
        # that satisfies the budget. An inspection is done internally
        # and the budget will automatically adjust to the higher when compared
        tx_result = txb.execute(gas_budget="1000000")
        if tx_result.is_ok():
            print(tx_result.result_data.to_json(indent=2))
        else:
            print(tx_result.result_string)

Commands available
##################

Basic commands:
    * move_call
    * transfer_objects, transfer_sui
    * split_coin,split_coin_equal
    * make_move_vector
    * publish, publish_upgrade
    * stake_coin, unstake_coin

Inspection
##########

You can verify (inspect) a SuiTransaction as you are building out your transactions. See: :py:meth:`pysui.sui.sui_clients.transaction.SuiTransaction.inspect_all`

Execution
#########

You can execute the transaction directly:

#. :py:meth:`pysui.sui.sui_clients.transaction.SuiTransaction.execute`

Note that once you execute a transaction it is unusable.

Signing, Signers, etc.
######################

SuiTransactions have a property called `signature_block` that manages the potential signers of a transaction:
    * Sender - This can be an SuiAddress or a SigningMultiSig (wrapper over MultiSig address)
    * Sponsor - This can be an SuiAddress or a SigningMultiSig (wrapper over MultiSig address)
    * Additional Signers - A list of SuiAddress and/or SigningMultSig

Here is an example of a transaction that is sponsored:

Sponsored Transaction example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: Python

    from pysui.sui.sui_clients.sync_client import SuiClient
    from pysui.sui.sui_clients.transaction import SuiTransaction
    from pysui.sui.sui_config import SuiConfig

    def foo():
        """Demonstrates a simple sponsored SuiTransaction ."""

        # Get the Transaction/Transaction Builder
        # By default, this will assume that the 'active-address' is the sole signer of the transaction
        # But we want to sponsor the transaction from another address (who will pay for the transaction)
        txer = SuiTransaction(SuiClient(SuiConfig.default_config()))

        # Get a coin for splitting from the active-address and create the command
        coin_to_split = ... # Retrieved somehow
        txer.split_coin_equal(coin=main_coin, split_count=3)

        # But for execution we want the gas to come from a sponsoring address
        # and they sign as well
        some_sponsor = ... # Retrieve another address that will 'pay' for the transaction
        txer.signer_block.sponser = SuiAddress(some_sponsor)

        exec_result = txer.execute(gas_budget="1000000")
        if exec_result.is_ok():
            print(exec_result.result_data.to_json(indent=2))
        else:
            print(exec_result.result_string)
