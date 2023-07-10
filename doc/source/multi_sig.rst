MutliSig
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

With version '0.21.1' of ``pysui`` signing with MultiSig no longer relies on Sui binaries keytool

In the following scenarios it is assumed that the admin does not participate in the signing. This example uses
the first two keys that are in the MultiSig but in a real world scenario it is likely the
public keys to sign with are provided through some other mechanism.

.. code-block:: Python

    from pysui import SyncClient, SuiAddress, ObjectID, handle_result
    from pysui.sui.sui_txn import SyncTransaction, SigningMultiSig
    from pysui.sui.sui_crypto import MultiSig, SuiPublicKey

    def transfer_with_ms(
        client: SyncClient,
        to_addy: SuiAddress,
        msig: MultiSig,
        from_coin:ObjectID,
        amount: int
        ) -> SuiRpcResult:
        """Transfer some balance from MultiSig address to some other address."""

        # Initialize a transaction build
        txer = SyncTransaction(
             client, initial_sender=SigningMultiSig(msig, msig.public_keys[0:2])
        )

        # Split some coinage and transfer
        coin = txer.split_coin(coin=from_coin, amounts=[amount])
        txer.transfer_objects(transfers=[coin], recipient=to_addy)

        result = handle_result(txer.execute())
        print(result.to_json(indent=2))

Final Note: MultiSig and MultiSig Address Persistence
#####################################################
Unlike general Sui addresses and keys, MultiSig address and keys are not persisted by the Sui binaries
(i.e. ``client.yaml`` and ``sui.keystore``.

If is for this reason the ``pysui`` implementation provides the serialize/deserialization capabilities. It
is through these that the application/library developer can manage these based on their design and requirements.
