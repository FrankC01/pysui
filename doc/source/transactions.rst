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


Export Formats
~~~~~~~~~~~~~~

``export_json`` accepts a ``format`` argument that controls which fields are
included in the output.

Standard
^^^^^^^^

The default format.  Emits only the core Sui V2 PTB fields compatible with
Mysten TS-SDK import/export:

- ``version`` — always ``2``
- ``sender`` — transaction sender address
- ``expiration`` — epoch expiry or ``null``
- ``gasData`` — budget, price, and payment objects
- ``inputs`` — transaction inputs (resolved pure and object arguments)
- ``commands`` — PTB commands

pysui extensions are omitted.  Use this format when handing the JSON to
other tools or SDKs that follow the Sui V2 standard.

Extended
^^^^^^^^

Includes everything in *Standard* plus pysui-specific additions to the Sui V2
schema:

- ``env`` — network environment block:

  - ``name`` — active profile name from ``PysuiConfiguration``
  - ``url`` — node RPC URL
  - ``protocol`` — transport protocol (``"GraphQL"`` or ``"gRPC"``)

- ``UnresolvedObject`` — extended with three optional type-hint fields:

  - ``isOptional`` — ``true`` if the object parameter is ``Option<T>`` in the
    Move signature
  - ``isReceiving`` — ``true`` if the object is consumed as ``Receiving<T>``
  - ``typeStr`` — Move type string of the parameter (e.g.
    ``"0x2::coin::Coin<0x2::sui::SUI>"``)

- ``UnresolvedPure`` — extended with an optional ``valueType`` field carrying
  the Move type annotation for the raw value (e.g. ``"u64"``,
  ``"vector<vector<u8>>"``)

- ``$Intent.FundsWithdrawal`` — pysui-defined intent command for
  address-balance coin withdrawal; not yet in the Mysten TS-SDK schema

Use this format when round-tripping through pysui or storing transactions for
later reconstruction on the correct network.  The ``env`` block is used by
``from_json`` to automatically resolve the correct ``PysuiConfiguration``
group and client (see `Network Environment Resolution`_).  The
``UnresolvedObject`` and ``UnresolvedPure`` extensions preserve type context
across tools without requiring a live node lookup.

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


Network Environment Resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an imported JSON document contains an ``env`` block (*extended* format
only), ``from_json`` inspects the ``url`` field and attempts to locate a
matching group and profile in the caller's ``PysuiConfiguration``.  The
optional ``env.protocol`` field (``"GraphQL"`` or ``"gRPC"``) narrows the
search to groups tagged with the matching transport protocol.

Three outcomes are possible:

**Already active** — the matched group and profile are already the active
ones in the caller's ``PysuiConfiguration``.  The passed-in ``client`` is
used as-is and ``info["profile_switched"]`` is ``False``.

**Profile switch required** — the URL is found but belongs to a different
group or profile.  pysui constructs a new ``PysuiConfiguration`` instance
(from the same persist file) with the matched group and profile set as active,
then instantiates a new client via ``client_factory()``.  The new client is
returned in ``info["client"]`` and ``info["profile_switched"]`` is ``True``.
The caller's original ``PysuiConfiguration`` and client are **not** mutated.

.. note::

   When a profile switch occurs, the caller receives at least two
   ``PysuiConfiguration`` instances backed by the same persist file.  Both
   are valid and independent; the caller is responsible for managing their
   lifecycles.

**Failure** — a ``ValueError`` is raised in any of these cases:

- The ``env.protocol`` value is present but is not ``"GraphQL"`` or
  ``"gRPC"`` — raised immediately before any group walk.
- The ``env.url`` does not match any profile URL in the caller's
  ``PysuiConfiguration`` (after applying any protocol narrowing).
- The ``env.url`` matches a group whose protocol tag is not ``GraphQL`` or
  ``gRPC"`` (i.e. a user-defined group without a recognised transport).

The ``info`` Dictionary
~~~~~~~~~~~~~~~~~~~~~~~

The returned ``info`` dict captures metadata from the original JSON: gas and
expiry settings, and — when an ``env`` block is present — the results of
network environment resolution.  Gas and expiry values are **not**
automatically applied to the reconstructed transaction; pass them explicitly
to a build method when needed:

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
   * - ``env_url``
     - Node URL from the ``env`` block in the JSON, or ``None`` if absent
       (standard format or no ``env`` key present).
   * - ``profile_switched``
     - ``True`` if ``from_json`` resolved the ``env`` URL to a different
       group or profile than the caller's active one and constructed a new
       client.  ``False`` otherwise.
   * - ``group_name``
     - Name of the ``PysuiConfiguration`` group the ``env`` URL resolved to,
       or ``None`` if no profile switch occurred.
   * - ``profile_name``
     - Name of the profile within that group, or ``None`` if no profile
       switch occurred.
   * - ``client``
     - The ``AsyncClientBase`` to use with the reconstructed transaction.
       When ``profile_switched`` is ``False`` this is the same object as the
       ``client`` argument passed to ``from_json``; when ``True`` it is a
       newly instantiated client bound to the resolved group and profile.

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
