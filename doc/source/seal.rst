pysui SEAL
==========

SEAL (Sui Encryption and Access Layer) provides Identity-Based Encryption (IBE)
backed by on-chain key servers. This page walks through encrypt and decrypt using
:py:class:`pysui.zklogin_seal.seal_client.SealClient`.

For a detailed overview of the SEAL protocol, see the
`SEAL documentation <https://seal-docs.wal.app/>`_.

The complete runnable example is ``ucs_seal_example.py`` in the project root.

Prerequisites
-------------

* ``pysui[zklogin-seal]`` installed — see :doc:`zklogin_seal_install`.
* A deployed SEAL allowlist package (testnet constants are hardcoded in the example).
* Two configured pysui addresses: an owner (Bob / ``Primary``) and a member (Alice / ``Secondary``).

Setup: SealClient
-----------------

``SealClient`` wraps a pysui async client and a ``ZkSealConfig``. The following
imports cover the full SEAL workflow:

.. code-block:: python

    from pysui import (
        PysuiConfiguration,
        client_factory,
        AsyncClientBase,
        ExecuteTransaction,
    )
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
    from pysui.zklogin_seal.config import ZkSealConfig
    from pysui.zklogin_seal.seal_client import SealClient
    from pysui.zklogin_seal.types import SealDemType, SealEncryptedObject

Create the pysui client and ``SealClient``:

.. code-block:: python

    pysui_config = PysuiConfiguration()
    pysui_client: AsyncClientBase = client_factory(pysui_config)

    seal_config = ZkSealConfig()
    seal_client = SealClient(client=pysui_client, config=seal_config)

Refreshing Key Server URLs
--------------------------

Non-committee key server URLs are stored on-chain. Refresh before encrypting to
pick up any changes:

.. code-block:: python

    await seal_client.config.refresh_all_server_urls(client=seal_client.pysui_client)

This call is skipped automatically for committee (aggregator) servers whose URLs
are static.

Encrypting Data (Bob)
---------------------

``encrypt()`` fetches IBE public keys from the selected key servers and encrypts
data under a policy identity derived from the package ID and inner ID (typically
the allowlist object ID bytes):

.. code-block:: python

    inner_id = bytes.fromhex(ALLOWLIST_OBJECT_ID.removeprefix("0x"))

    encrypt_result = await seal_client.encrypt(
        package_id=DEMO_PACKAGE_ID,
        inner_id=inner_id,
        key_servers=[("mysten-testnet", "mysten-testnet-1", "mysten-testnet-2")],
        threshold=2,
        data=plaintext_bytes,
    )

    encrypted_obj, _dem_key = encrypt_result.result_data

The ``key_servers`` argument is a list of tuples. Each tuple names a server set
followed by the aliases of the servers to use from that set. ``threshold`` sets
how many shares are required to decrypt.

Key Server Modes
~~~~~~~~~~~~~~~~

Non-committee only (default):

.. code-block:: python

    key_servers=[("mysten-testnet", "mysten-testnet-1", "mysten-testnet-2")]

Mixed — one non-committee server plus one committee aggregator:

.. code-block:: python

    key_servers=[
        ("mysten-testnet", "mysten-testnet-1"),
        ("mysten-testnet-committee", "mysten-committee"),
    ]

The ``--committee`` flag in the example script switches between these two modes.

Decrypting Data (Alice)
-----------------------

Decryption requires three inputs:

#. The ``SealEncryptedObject`` produced by ``encrypt()``.
#. An unsigned ``seal_approve`` PTB — proof of policy eligibility for the key servers.
#. A ``SealCredentials`` bundle signed by Alice's keypair.

Generating Credentials
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    alice_creds = alice_seal_client.credentials()

Credentials are short-lived session tokens (default 30 minutes) tied to Alice's
active address and keypair.

Building the seal_approve PTB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The key server needs a PTB that calls the policy's ``seal_approve`` entry function.
This PTB is never executed on-chain — it is sent to the key server as proof of
eligibility. Use ``raw_kind()`` to serialise it:

.. code-block:: python

    alice_txn: AsyncSuiTransaction = await alice_seal_client.pysui_client.transaction()
    await alice_txn.move_call(
        target=f"{DEMO_PACKAGE_ID}::allowlist::seal_approve",
        arguments=[inner_id, ALLOWLIST_OBJECT_ID],
    )
    ptb_raw: bytes = (await alice_txn.raw_kind()).serialize()

Calling decrypt()
~~~~~~~~~~~~~~~~~

.. code-block:: python

    decrypt_result = await alice_seal_client.decrypt(
        encrypted_object=encrypted_obj,
        transaction_kind=ptb_raw,
        credentials=alice_creds,
    )

    plaintext: bytes = decrypt_result.result_data
    print(plaintext.decode())

``decrypt()`` contacts each key server embedded in the encrypted object, verifies
the returned key shares, and reassembles the plaintext.

Allowlist Management
--------------------

The examples below use the SEAL demo allowlist package deployed on **testnet** —
the package IDs are hardcoded in ``ucs_seal_example.py``. Allowlist management
is one access-control pattern; the SEAL protocol supports other policy types as well.

Creating an Allowlist (Bob)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    txn: AsyncSuiTransaction = await seal_client.pysui_client.transaction()
    await txn.move_call(
        target=f"{DEMO_PACKAGE_ID}::allowlist::create_allowlist_entry",
        arguments=[allowlist_name],
    )
    tx_dict: dict = await txn.build_and_sign()
    result = await seal_client.pysui_client.execute(command=ExecuteTransaction(**tx_dict))

Adding an Address (Bob)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    txn: AsyncSuiTransaction = await seal_client.pysui_client.transaction()
    await txn.move_call(
        target=f"{DEMO_PACKAGE_ID}::allowlist::add",
        arguments=[ALLOWLIST_OBJECT_ID, CAP_OBJECT_ID, address_to_add],
    )
    tx_dict: dict = await txn.build_and_sign()
    result = await seal_client.pysui_client.execute(command=ExecuteTransaction(**tx_dict))
