ZkSealConfig
============

:py:class:`pysui.zklogin_seal.config.ZkSealConfig` is the configuration manager for
both zkLogin providers and SEAL key servers. By default the configuration is persisted
to ``~/.pysui/ZkSealConfig.json`` however developers can store and manage from a
different location. The configuration is shared across both features.

.. note::

   The active ``ZkSealConfig`` group must align with the active ``PysuiConfiguration``
   profile. For example, if your ``PysuiConfiguration`` is set to the ``testnet``
   profile, ``ZkSealConfig`` should also have ``testnet`` as its active group.
   Using mismatched groups will result in connecting to the wrong network.

Default Behaviour
-----------------

On first instantiation, ``ZkSealConfig`` writes a default configuration file to
``~/.pysui/ZkSealConfig.json`` containing built-in groups for devnet, testnet, and
mainnet. Testnet ships with two pre-configured SEAL key server sets:

* ``mysten-testnet`` — two non-committee key servers (independent IBE shares)
* ``mysten-testnet-committee`` — one committee aggregator

.. code-block:: python

    from pysui.zklogin_seal.config import ZkSealConfig

    cfg = ZkSealConfig()
    print(cfg.active_group.group_name)  # testnet

The active group defaults to ``testnet``.

.. note::

   SEAL is not supported on devnet — ``SealClient`` raises an error on instantiation
   when the active group is ``devnet``.

   Mainnet ships with no pre-configured SEAL key servers. Add the appropriate key
   server sets before using SEAL on mainnet. See `Adding a Key Server Set`_ below.

Listing Key Server Sets
-----------------------

.. code-block:: python

    sets = cfg.list_sets(group_name="testnet")
    print(sets)  # ['mysten-testnet', 'mysten-testnet-committee']

Adding a Key Server Set
-----------------------

.. code-block:: python

    cfg.add_key_server_set(
        group_name="testnet",
        set_name="my-custom-set",
        is_committee=False,
    )

Adding a Key Server to a Set
-----------------------------

.. code-block:: python

    cfg.add_server(
        group_name="testnet",
        set_name="my-custom-set",
        alias="my-server-1",
        object_id="0x<on-chain-object-id>",
        url="https://my-key-server.example.com",
    )

To resolve the URL automatically from the key server's on-chain dynamic fields:

.. code-block:: python

    await cfg.add_verified_server(
        group_name="testnet",
        set_name="my-custom-set",
        alias="my-server-1",
        object_id="0x<on-chain-object-id>",
        client=pysui_client,
    )

Refreshing Server URLs
----------------------

Non-committee key server URLs can change. Call ``refresh_all_server_urls()``
before encrypting to fetch current URLs from the chain:

.. code-block:: python

    await cfg.refresh_all_server_urls(client=pysui_client)

Committee (aggregator) server URLs are static and are skipped during refresh.

Persisting Changes
------------------

Most mutating methods accept a ``persist=True`` keyword to save immediately:

.. code-block:: python

    cfg.add_key_server_set(
        group_name="testnet",
        set_name="my-set",
        is_committee=False,
        persist=True,
    )

Or save explicitly at any point:

.. code-block:: python

    cfg.save()

Changing the Active Group
-------------------------

Pass ``group_name`` to the constructor to activate a different group for the session:

.. code-block:: python

    cfg = ZkSealConfig(group_name="mainnet")

To make the change permanent (persisted to disk), call ``make_active()`` with
``persist=True``:

.. code-block:: python

    cfg = ZkSealConfig()
    cfg.make_active(group_name="mainnet", persist=True)

zkLogin Provider Configuration
-------------------------------

Each network group ships with pre-configured zkLogin providers (``google``,
``facebook``, ``twitch``) and their proof-generation service URLs. To update
a prover URL — for example, to point to a self-hosted prover:

.. code-block:: python

    cfg.update_provider_url(
        group_name="testnet",
        name="google",
        prover_url="https://my-prover.example.com/v1",
        persist=True,
    )

To add a custom provider:

.. code-block:: python

    cfg.add_provider(
        group_name="testnet",
        name="my-provider",
        iss="https://my-provider.example.com",
        prover_url="https://my-prover.example.com/v1",
        persist=True,
    )
