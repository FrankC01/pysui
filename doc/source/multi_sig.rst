MultiSig
========

General
-------
**Sui** supports the creation of an address for which Transaction modifications require a MultiSig signing.

Version 0.16.0 of ``pysui`` added support for MultiSig. The remainder of this page walks through the fundementals.

MultiSig Implementation
-----------------------

A ``pysui`` MultiSig enables:

    * A level of security governance by having several people control individual signing keys
    * Generation of a unique address to which objects can be transfered to.
    * Signing transactions that modify/transfer objects owned by the MultiSig address.

Constructing a MultiSig
#######################
There are two ways to construct a MultiSig:

#. :py:meth:`pysui.sui.sui_crypto.MultiSig` - Constructor with required parameters.
#. :py:meth:`pysui.sui.sui_crypto.MultiSig.deserialize` - Deserialize a previously serialized MultiSig object.

In the first method it is important that:

    * The number of keys and the number of weights you provide are the same
    * The total of the weights is greater than or equal to the threshold

Once a MultiSig is constructed, you can use the SuiAddress of the MultiSig to send objects to as recipient, query information on
it (i.e. investigate object ownership), and/or participate in MoveCalls.

Example Construction Option 1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: Python

    from pysui import SuiConfig
    from pysui.sui.sui_crypto import MultiSig, SuiKeyPair

    def gen_ms(config: SuiConfig) -> MultiSig:
        """Create a new MultiSig object.

        In this scenario, the first two keys must be used together in signing to allow a
        modification of objects owned by the MultiSig address as their weights together only
        then reach the threshold amount.

        Imagine that the 3rd key is the master administrator and they alone can
        sign transactions as it's weight alone is equal to the threshold.
        """
        ms_keys:[config.keypair_for_address(...),config.keypair_for_address(...),config.keypair_for_address(...)]
        multi_sig = MultiSig(ms_keys, [1, 2, 3], 3)
        print(f"MultiSig address: {multi_sig.address}")
        return multi_sig

Example Construction Option 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: Python

    from pysui.sui.sui_crypto import MultiSig

    def gen_ms_from_base64(ser_str: str) -> MultiSig:
        """Create a MultiSig object by deserializing previous serialized MultiSig."""
        multi_sig: MultiSig = MultiSig.deserialize(ser_str)
        print(f"MultiSig address: {multi_sig.address}")
        return multi_sig

Signing Transactions using a MultiSig
#####################################
You need to sign transactions that change any object owned by the MultiSig address. This is where the
heightened security and governance aspect come into play.

A ``MultiSig`` is passed to transactions by first wrapping it in a
:py:class:`pysui.sui.sui_common.txb_signing.SigningMultiSig`, which pairs the
``MultiSig`` object with the specific public keys that will sign. That
``SigningMultiSig`` is then passed as the ``initial_sender`` to
``client.transaction()`` for standalone transactions, or as the ``sender``
argument when constructing an executor.

In the examples below the admin key (index 2, weight 3) does not participate —
the first two keys together reach the threshold.

Standalone Transaction
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    from pysui import PysuiConfiguration, SuiRpcResult, client_factory
    from pysui.sui.sui_common.txb_signing import SigningMultiSig
    from pysui.sui.sui_crypto import MultiSig
    import pysui.sui.sui_pgql.pgql_query as qn

    async def transfer_with_ms(
        msig: MultiSig,
        to_address: str,
        amount: int,
    ) -> SuiRpcResult:
        """Transfer some balance from a MultiSig address."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)

        # Wrap the MultiSig with the signing keys (first two keys, indices 0 and 1)
        signing_ms = SigningMultiSig(msig, msig.public_keys[0:2])

        # Build the transaction with the MultiSig as sender
        txer = await client.transaction(initial_sender=signing_ms)
        coin = await txer.split_coin(coin=txer.gas, amounts=[amount])
        await txer.transfer_objects(transfers=[coin], recipient=to_address)

        txdict = await txer.build_and_sign()
        result: SuiRpcResult = await client.execute_query_node(
            with_node=qn.ExecuteTransaction(**txdict)
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        return result

    if __name__ == "__main__":
        # msig constructed earlier — see Constructing a MultiSig above
        asyncio.run(transfer_with_ms(msig, "0xrecipient...", 1_000_000))

With an Executor
~~~~~~~~~~~~~~~~

When using a serial or parallel executor, pass the ``SigningMultiSig`` directly
as the ``sender`` when constructing the executor — it accepts either an address
string or a ``SigningMultiSig``:

.. code-block:: python

    import asyncio
    from pysui import PysuiConfiguration, client_factory, GqlSerialTransactionExecutor
    from pysui.sui.sui_common.txb_signing import SigningMultiSig
    from pysui.sui.sui_crypto import MultiSig

    async def executor_with_ms(msig: MultiSig) -> None:
        """Run a serial executor with MultiSig signing."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)

        signing_ms = SigningMultiSig(msig, msig.public_keys[0:2])
        executor = GqlSerialTransactionExecutor(client=client, sender=signing_ms)
        # Add transactions to the executor as normal ...

    if __name__ == "__main__":
        asyncio.run(executor_with_ms(msig))

Final Note: MultiSig and MultiSig Address Persistence
#####################################################
Unlike general Sui addresses and keys, MultiSig address and keys are not persisted by the Sui binaries
(i.e. ``client.yaml`` and ``sui.keystore``.

If is for this reason the ``pysui`` implementation provides the serialize/deserialization capabilities. It
is through these that the application/library developer can manage these based on their design and requirements.
