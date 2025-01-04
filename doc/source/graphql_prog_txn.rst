
GraphQL Programmable Transactions
"""""""""""""""""""""""""""""""""

Like the **pysui** legacy Programmable Transaction Builder (PTB), we have introduced a *new* PTB that
leverages GraphQL RPC instead of JSON RPC. There are also other enhencements added to this new capabiity.

As with the previous page, the GraphQL PTB should be considered *not ready for production*.

The sections that follow will demonstrate using both the legacy and new PTB.

====================
PTB Initialization
====================

A few minor differences, noted in code comments, to initialize the PTB can be seen in the examples below.

Legacy
-------

.. code-block:: python
    :linenos:

    from pysui import SuiConfig, SyncClient
    from pysui.sui.sui_txn import SyncTransaction

    client = SyncClient(SuiConfig.default_config())
    txn = SyncTransaction(client=client)

New
---

.. code-block:: python
    :linenos:

    from pysui import PysuiConfiguration, SyncGqlClient
    from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction

    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP )
    client = SyncGqlClient(pysui_config=cfg)
    txn = SuiTransaction(client=client)

===============
Notable Changes
===============

Besides using our GraphQL QueryNodes behind the scene in the new PTB, we have also eliminated
the need to *wrap* transaction command arguments. Now you can use native Python types for command parameters
and **move_call** arguments.

Legacy
------

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

New
---

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

General conversions in new argument processor
---------------------------------------------
When a transaction command is created it's arguments are validated and transformed based on
the types that are defined by either commands (i.e. split_coins) or the `move_call` programs function
arguments.

Scalars
+++++++

+-----------------------------+----------------------------------+---------------------------+
|     Sui Argument            |       Accepts                    |      Example              |
+=============================+==================================+===========================+
| bool                        | bool                             | True                      |
+-----------------------------+----------------------------------+---------------------------+
| vector<u8>                  | str                              | 'foo'                     |
+-----------------------------+----------------------------------+---------------------------+
| String                      | str                              | 'foo'                     |
+-----------------------------+----------------------------------+---------------------------+
| u8 through u256             | int                              | sum([1,2,9999343134343])  |
+-----------------------------+----------------------------------+---------------------------+
| vector<u8> - vector<256>    | bytes                            | bytes.fromhex("BEEF")     |
+-----------------------------+----------------------------------+---------------------------+
| address, ID                 | str                              | '0x....' (valid Sui addr) |
+-----------------------------+----------------------------------+---------------------------+

Scalar Option
+++++++++++++

If the Sui program function takes Option for a scalar or vector of scalars, internally the
transaction builder will 'wrap' the inputs.

+-----------------------------+----------------------------------+---------------------------+
|     Sui Argument            |       Accepts                    |      Example              |
+=============================+==================================+===========================+
| Option<scalar>              | see Scalars above                | see above or None         |
+-----------------------------+----------------------------------+---------------------------+
| vector<Option<scalar>>      | list[see Scalars above]          | ['foo',None,'bar']        |
+-----------------------------+----------------------------------+---------------------------+

Objects
+++++++

Object vectors use `make_move_vec`
Option objects use `optional_object`

+-----------------------------+----------------------------------+---------------------------+
|     Sui Argument            |       Accepts                    |      Example              |
+=============================+==================================+===========================+
| Obj, &Obj, &mut Obj         | str                              | '0x....' (valid obj ID)   |
+-----------------------------+----------------------------------+---------------------------+
| Obj, &Obj, &mut Obj         | pgql_type.ObjectReadGQL          | GraphQL result            |
+-----------------------------+----------------------------------+---------------------------+

Object Option
+++++++++++++

If the Sui program function takes Option for an object or vector of objects, the transaction builder provides
the `optional_object` method.

For example, this contrived move function:

.. code-block::
    :linenos:

    public fun check_object_option<T>(oparg:Option<T>,_ctx:&mut TxContext) ...

For setting up arguments in pysui use the `optional_object` method on the transaction:

.. code-block:: python
    :linenos:

    txer = SuiTransaction(client=client)

    fooey = txer.move_call(
        target=f"{_PACKAGE}::{target_module}::{target_function}",
        arguments=[
            txer.optional_object(
                optional_object="0x....",
                type_arguments=["0x2::coin::Coin<0x2::sui::SUI>"],
            ),
        ],
        type_arguments=["0x2::coin::Coin<0x2::sui::SUI>"],
    )


===================
DryRun Transaction
===================

Before executing a transaction for debugging and general insight into how the transaction may perform, you
can execute a DryRun:

DryRun Lite
-----------
A lite weight dryrun just uses the TransactionKind (transaction before all gas is reconcilled). The query node to
use in this case is ``DryRunTransactionKind``. If no options are provided, Sui will provide defaults. See the
DryRunTransactionKind documentation.

.. code-block:: python
    :linenos:

    def dry_run_kind(txn:SuiTransaction):
        """Uses defaults for DryRunTransactionKind."""
        raw_kind = txer.raw_kind()
        raw_kind_ser = base64.b64encode(raw_kind.serialize().decode())

        # Print the TransactionType BCS (pre-serialized) structure
        # print(raw_kind.to_json(indent=2))
        # print(raw_kind_ser)

        # Execute the dry run for kind
        result = txer.client.execute_query_node(
            with_node=qn.DryRunTransactionKind(tx_bytestr=raw_kind_ser)
        )

        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

DryRun Full
-----------
The full dryrun is basiscally a fully built transaction without signatures, but
is dryrun for inspection

.. code-block:: python
    :linenos:

    def dry_run(txn:SuiTransaction):
        """Uses fully built TransactionData for DryRunTransaction"""
        raw_kind = txer.raw_kind()
        # Print the TransactionData BCS (pre-serialized) structure
        # print(raw_kind.to_json(indent=2))

        # Execute the dry run
        result =
            txn.client.execute_query_node(
                with_node=qn.DryRunTransaction(tx_bytestr=txn.build())
            )

        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

===================
Execute Transaction
===================

When it comes time to execute a transaction, both the bytecode of the transaction and signatures are
required:

.. code-block:: python
    :linenos:

    def transaction_execute(txn: SuiTransaction):
        """Uses fully built and serialized TransactionData for ExecuteTransaction."""
        raw_kind = txn.raw_kind()
        # Print the TransactionData BCS (pre-serialized) structure
        # print(raw_kind.to_json(indent=2))

        # Build and sign to get the base64 transaction bytes and list of signatures
        tx_dict = txer.build_and_sign()
        # Execute the transaction
        result = txer.client.execute_query_node(
            with_node=qn.ExecuteTransaction(**tx_dict)

        if result.is_ok():
            # Unlike JSON RPC, the GraphRPC transaction execution just returns
            # Status and the transaction digest. You can then take the transaction digest
            # and then execute the GetTx for details.
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)
