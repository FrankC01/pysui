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
     - Serializes the transaction to a base64-encoded byte string without
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
   * - ``auto_gas``
     - ``False``
     - Automatically select the gas path based on sender balance at build
       time. When set to ``True``, queries the sender's address balance and
       routes to the address balance gas path if balance is positive,
       otherwise falls back to standard coin gas selection.

.. note::

   On the standard coin path (``use_account_for_gas=False``),
   ``gas_budget`` and ``use_gas_objects`` are independent overrides and
   may be combined freely.


Transaction JSON Interchange
----------------------------

``AsyncSuiTransaction`` supports serializing an in-progress transaction to a
JSON string and reconstructing it on another client or at a later time via two
methods:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.export_json`
     - Serializes the current transaction state to a V2 JSON interchange
       string. See `Fidelity Guarantees`_ for known caveats on the exported
       gas data.
   * - :py:meth:`~pysui.sui.sui_common.async_txn.AsyncSuiTransaction.from_json`
     - Class method. Reconstructs an ``AsyncSuiTransaction`` from a V2 JSON
       interchange string. Returns a ``(txn, info)`` tuple.


Reconstructing a Transaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   txer, info = await AsyncSuiTransaction.from_json(
       json_str=jstr,
       client=client,
   )

Sender and sponsor overrides can be supplied to replace the values found in
the JSON. Each accepts a string address or a ``SigningMultiSig`` instance:

.. code-block:: python

   txer, info = await AsyncSuiTransaction.from_json(
       json_str=jstr,
       client=client,
       sender=client.config.active_address,
   )


The ``info`` Dictionary
~~~~~~~~~~~~~~~~~~~~~~~

The returned ``info`` dict captures the gas and expiry metadata from the
original JSON. These values are **not** automatically applied to the
reconstructed transaction; pass them explicitly to a build method when needed:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Key
     - Description
   * - ``sender``
     - Sender address from the JSON.
   * - ``sponsor``
     - Sponsor address from the JSON, or ``None``.
   * - ``gas_budget``
     - Integer gas budget from the JSON, or ``None`` if not set.
   * - ``use_gas_objects``
     - List of gas payment object dicts from the JSON, or ``None``.
   * - ``txn_expires_after``
     - Expiration epoch from the JSON, or ``None``.

Example — reconstructing and building with the original gas settings:

.. code-block:: python

   txer, info = await AsyncSuiTransaction.from_json(json_str=jstr, client=client)
   result = await txer.build_and_sign(
       gas_budget=info["gas_budget"],
       use_gas_objects=info["use_gas_objects"],
       txn_expires_after=info["txn_expires_after"],
   )


Fidelity Guarantees
~~~~~~~~~~~~~~~~~~~

The JSON interchange preserves the transaction's **inputs** and **commands**
exactly. The following known differences exist between the original JSON and
the re-exported JSON from a reconstructed (unbuilt) transaction:

- **gasData** — reflects the unbuilt state after reconstruction. ``budget``
  will be ``null`` and ``owner`` will be set to the active sender until the
  transaction is built. Use the ``info`` dict to restore the original gas
  settings.
- **Address normalisation** — short-form hex addresses (e.g.
  ``0x123::foo::Bar``) are normalised to their full 32-byte form (e.g.
  ``0x0000000000000000000000000000000000000000000000000000000000000123::foo::Bar``)
  during reconstruction. This is semantically equivalent on-chain.
- **Pure inputs are resolved** — Pure inputs (scalars, strings, optional
  values, vectors, etc.) are BCS-encoded into their ``bytes`` form at the
  point of command construction, not at build time. The JSON interchange
  captures and restores these encoded bytes directly. The original Python
  values are not recoverable from the interchange format.
- **Unresolved object inputs** — Unresolved object inputs (``UnresolvedObject``)
  carry only the object ID, not ``version`` or ``digest``. This is intentional:
  version and digest are chain state that can change between export and
  execution. Including them in the JSON would allow consumers to build
  transactions with stale object references, which fail at execution. When
  building from a JSON-sourced transaction, pysui always calls ``GetObject`` to
  fetch the current on-chain state. Only ``mutable`` and ``initialSharedVersion``
  are safe to carry on unresolved inputs because they are transaction-level
  intent and an immutable property respectively, not live chain state.
