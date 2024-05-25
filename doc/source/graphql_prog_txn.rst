
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

    from pysui import SyncClient, SuiConfig
    from pysui.sui.sui_txn import SyncTransaction

    client = SyncClient(SuiConfig.default_config())
    txn = SyncTransaction(client=client)

New
---

.. code-block:: python
    :linenos:

    from pysui import SuiConfig
    from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
    from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction

    client = SuiGQLClient(config=SuiConfig.default_config()) # Keyword argument
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
------

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
