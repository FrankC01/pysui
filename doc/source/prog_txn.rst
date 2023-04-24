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

Command Inputs and Arguments
############################

Command Inputs
~~~~~~~~~~~~~~

``pysui`` encapsulate the inputs to commands from their lower level treatment and detail. For the most part, all of the input
variations on what 'type' of Pythoon or ``pysui`` the command will accept can be seen for each Command
method in :py:class:`pysui.sui.sui_clients.transaction.SuiTransaction` reference.

Move Call Arguments
~~~~~~~~~~~~~~~~~~~

However; the `arguments` to a Move Call command require special treatment to aid in disambiguating whether it is an object
reference or just a pure value. Here is a snippet of a move call where arguments are wrapped in ``pysui`` types. Below the
example is a coercion table describing the effect of resolving in `move_call` arguments.

.. code-block:: Python

    txer.move_call(
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


+----------------------------------------------------------+----------------------------+
|     Types                                                |       Converts to          |
+==========================================================+============================+
| bool, str, int, bytes, SuiBoolean, SuiString, SuiInteger | Passed by value            |
+----------------------------------------------------------+----------------------------+
| SuiU8, SuiU16, SuiU32, SuiU64, SuiU128, SuiU256          | Passed by value  [#f1]_    |
+----------------------------------------------------------+----------------------------+
| SuiAddress, OptionalU64                                  | Passed by value            |
+----------------------------------------------------------+----------------------------+
| ObjectID, SuiCoinObject, ObjectRead                      | Passed by reference [#f2]_ |
+----------------------------------------------------------+----------------------------+
| Result of previous command [#f3]_                        | Command Result index       |
+----------------------------------------------------------+----------------------------+

.. rubric:: Footnotes

.. [#f1] Explicit unsigned integer bit size types
.. [#f2] Will determine if Shared object or not before transaction execution
.. [#f3] Result may be a list, so understanding which commands return a single or multiple is important
