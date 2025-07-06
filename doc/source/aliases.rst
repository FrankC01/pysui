
=======
Aliases
=======

General
-------

MystenLabs added aliases support to Sui 1.16.0.  Aliases are associations of an
alias name to a Sui Address with the intent that you could use an alias name
in places where you would otherwise use an address.

Aliases are supported by both SuiConfig and PysuiConfiguration.

Runtime
-------

JSON RPC
++++++++

When instantiating a configuration either through
``SuiConfig.default_config()`` or ``SuiConfig.sui_base_config()`` then the
configuration location is searched for a ``sui.aliases`` file. If found, the
alias associations to addresses are loaded, otherwise aliases are generated for
each address and saved out to the file ``sui.aliases`` in the Mysten Sui
configuration folder.

As ``SuiConfig.user_config()`` is purley empemeral, generated aliases are
**not** persisted, however all of the methods added to SuiConfiguration
are supported.

New aliases
***********

Support for creating new aliases along with new address/keypair creation has been added for:
    * create_new_keypair_and_address
    * recover_keypair_and_address
    * add_keypair_from_keystring

If an alias name is not provided when calling these, one will be automatically
generated.

Use for lookup and substitutions
********************************

A number of associative lookups have been added to ``SuiConfiguration``:
    * addr4al - Given an alias name return the associated SuiAddress
    * kp4al - Given an alias name return the associated KeyPair
    * pk4al - Given an alias name return the associated PublicKey
    * al4addr - Given a SuiAddress type or address string, return the
      assoicated alias name
    * al4kp - Given a KeyPair type, return the assoicated alias name
    * al4pk - Given a PublicKey type, return the assoicated alias name

Renaming aliases
****************

To rename an alias, provide the existing name and a new name
to ``SuiConfiguration.rename_alias()``.

Example
^^^^^^^

.. code-block:: Python
    :linenos:

    # The underlying configuration and synchronous client
    from pysui import SuiConfig, SyncClient
    from pysui.sui.sui_builders.get_builders import GetAllCoins

    def alias_examples():
        """Examples to excercise alias capabilities."""
        # Load a default configuration (i.e. ~/.sui/sui_config/client.yaml)
        cfg = SuiConfig.default_config()
        # Or if testing with suibase
        # cfg = SuiConfig.sui_base_config()

        # See aliases generated or loaded
        for alias in cfg.aliases:
            print(f"Alias {alias}")
            print(f"Address {cfg.addr4al(alias)}")
            print(f"PublicKey {cfg.pk4al(alias)}\n")

        # Rename alias for the active_address
        new_name = "Primary"
        act_add_alias = cfg.al4addr(cfg.active_address)
        print(f"Existing alias for active address {cfg.active_address} is {act_add_alias}")
        cfg.rename_alias(old_alias=act_add_alias,new_alias=new_name)
        print(f"Address associated to new alias 'Primary' = {cfg.addr4al(new_name)}\n")

        # Instantiate client
        client = SyncClient(cfg)

        # Using alias for convenience
        result = client.execute(GetAllCoins(owner=cfg.addr4al(new_name)))
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)
