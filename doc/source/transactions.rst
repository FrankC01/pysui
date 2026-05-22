============
Transactions
============

``pysui`` uses a single async transaction builder,
:py:class:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction`, across both
GraphQL and gRPC. PTB commands available on the builder are documented on
:doc:`transactions_ptb`.


Obtaining a Builder
-------------------

Transaction builders are obtained through the active client:

.. code-block:: python

   txer: AsyncSuiTransaction = await client.transaction()

All keyword arguments are optional. The user-facing parameters are:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Default
     - Description
   * - ``client``
     - *(required)*
     - The active async protocol client (``GqlProtocolClient`` or
       ``GrpcProtocolClient``). Supplied automatically when obtained via
       ``client.transaction()``.
   * - ``initial_sender``
     - ``None``
     - Override the transaction sender. Accepts a string address or a
       ``SigningMultiSig`` instance for multi-sig transactions. Defaults to
       the active address in the client configuration.
   * - ``initial_sponsor``
     - ``None``
     - Designate a sponsor to pay gas on behalf of the sender. Accepts the
       same types as ``initial_sender``.
   * - ``compress_inputs``
     - ``True``
     - Collapses duplicate inputs into a single reference, reducing
       transaction size. Appropriate for almost all use cases.


Build Methods
-------------

All three methods share the same gas and expiry arguments (see
`Gas and Expiry Arguments`_ below).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.transaction_data`
     - Returns the raw ``bcs.TransactionData`` BCS object. Use this when
       you want to inspect the constructed transaction
       (e.g. ``.to_json(indent=2)``) or to serialise and sign it
       externally.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.build`
     - Serialises the transaction to a base64-encoded byte string without
       signing. Use when you need the raw bytes for external signing or
       custom serialisation.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.build_and_sign`
     - Finalises the transaction, simulates gas (unless ``gas_budget`` is
       provided), signs, and returns a ``dict`` containing ``tx_bytestr``
       (base64-encoded) and ``sig_array``. The dict unpacks directly into
       :py:class:`~pysui.sui.sui_common.sui_commands.ExecuteTransaction`.


Gas and Expiry Arguments
------------------------

All three build methods accept:

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Parameter
     - Default
     - Description
   * - ``gas_budget``
     - ``None``
     - Explicit gas budget in MIST. When provided, the simulation
       round-trip is skipped and this value is used directly as the
       transaction fee cap.
   * - ``use_gas_objects``
     - ``None``
     - List of coin object IDs or ``Object`` instances to use for gas
       payment. When provided, pysui's automatic gas-coin selection is
       bypassed.
   * - ``txn_expires_after``
     - ``None``
     - Controls the single ``TransactionExpiration`` field, but the
       variant used depends on the gas path. On the standard coin path
       this becomes ``Epoch(N)`` — the transaction will not execute
       after epoch N. When ``use_account_for_gas=True`` this becomes
       a ``ValidDuring([N, N+1])`` window required by the coin
       reservation; if omitted, the current epoch is used as N.
   * - ``use_account_for_gas``
     - ``False``
     - Draw gas from the sender's address balance (accumulator) rather
       than coin objects. When set, ``use_gas_objects`` is ignored.

.. note::

   On the standard coin path (``use_account_for_gas=False``),
   ``gas_budget`` and ``use_gas_objects`` are independent overrides and
   may be combined freely.
