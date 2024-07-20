GraphQL PysuiConfiguration
""""""""""""""""""""""""""

PysuiConfiguration is the replacement for the legacy SuiConfig and this new class should be
used when creating a new GraphQL clients. This new configuration scheme is also leveraged
by the GraphQL SuiTransaction.


General
=======
Up until now, pysui relied on the presence of ``~/.sui`` and it's constituent configuration elements including
``client.yaml``, ``sui.keystore``, and ``sui.aliases`` which were all encapsulated by SuiConfig. While SuiConfig
supported some maniplations (i.e. adding new keys, alias management, etc.) it fell short of a more robust management
strategy. In addition, the code itself did not gracefully age with the advent of Sui GraphQL RPC. Until Mysten
eliminates JSON RPC, SuiConfig may continue to be used with the JSON RPC clients.

PysuiConfiguration persists its own configuratoin (default to ``~/.pysui``) and offers more flexibility when it
comes to configuration management. Amongst other things:

#. It does not presume it's configuration is persisted to a fixed location (configurable)
#. It supports programmatic switching between it's primary components (see Anatomy below)
#. It has a smaller code base that, when legacy JSON RPC support is removed, has a smaller memory footprint
#. And more...

Anatomy of PysuiConfiguration
=============================
The primary data model for PysuiConfiguration is a series of related ``dataclasses`` objects:

* The root data model is ``PysuiConfigModel`` which is a member of PysuiConfiguration.
    It manages one or more...

    * ``ProfileGroup``, or group for short, encapsulates unique environment configurations.
        Example configuration may include "sui_json_config" (reserved), "sui_gql_config" (reserved)
        or "user" (reserved). New groups may be created by the developer. Its construct includes,
        all of which are configurable:

        * One or more ``Profile``, or profile, a named object containing individual urls for communicatinhg to Sui with.
        * Associated keys, aliases and addresses
        * Identifies an active profile
        * Identifies an active address

PysuiConfiguration
==================

PysuiConfiguration is the primary object to interact with when managing or using the underlying groups and
profiles. However; it is import to understand the initial setup before using it as part of the GraphQL Clients
and the arguments you can pass to the constructor rely on that understanding.

First time instantiation
------------------------
The first time PysuiConfiguration is used it will look for the ``PysuiConfig.json`` file in the
default configuration folder ``~/.pysui`` unless that folder path is overriden with
the argument ``from_cfg_path``. If the configuration file is found it is loaded, otherwise it initializes
a new configuration file with initial groups and their contents.

If Sui binaries installed
~~~~~~~~~~~~~~~~~~~~~~~~~
Three groups will be created and initially populated:

    **sui_json_config** - This group and it's profiles will be populated from the contents of ``~/.sui/sui_config`` from the
    files ``client.yaml``, ``sui.keystore`` and ``sui.aliases``.

    **sui_gql_config** - This group and will create four profiles, each one with a ``url`` pointing to Mysten's free
    GraphQL nodes. It will also copy the keys, aliases and addresses from the ``sui_json_config`` group.

    **user** - Even though you may create your own groups this group is initially created as a convenience and begins
    empty.

The location of the ``sui`` binary will be captured, if present, enabling Move project compiling.

If Sui binaries not installed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**sui_gql_config** and **user** will be created however; **sui_gql_config** will be populated with a new
active address and keypair (ed25519), an alias of 'Primary', and will make 'testnet' profile active.

The location of the ``sui`` binary will be captured, if present, enabling Move project compiling.

Changing PysuiConfig Active
===========================
Defaults of what is considered 'active' is whatever was last persisted but can be
changed at runtime.

At PysuiConfig Construction
----------------------------

* from_cfg_path (str) - Controls where PysuiConfiguration reads/writes ``PysuiConfig.json``
* group_name (str) - Sets the ``active_group`` for the session, for example:

.. code-block:: python
    :linenos:

    # Set group to builtin Sui's GraphQL RPC group
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP )

    # Set group to builtin 'user' group
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_USER_GROUP)

    # Set group to other user defined group
    cfg = PysuiConfiguration(group_name="Primary Group")

* profile_name (str) - Sets which profile is active of the current ``active_group``. It is the equivalent of ``sui client switch --env``:

.. code-block:: python
    :linenos:

    # Set group to builtin Sui's GraphQL RPC group
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP, profile_name="mainnet" )

* address or alias (str) - Sets which Sui address is active using either and explicit address or an alias. It is the equivalent of ``sui client switch --address``:

.. code-block:: python
    :linenos:

    # Set group to builtin Sui's GraphQL RPC group
    cfg = PysuiConfiguration(alias="Primary")

* persist (bool) - Controls whether to persist any changes made above to ``PysuiConfig.json``. If not set to True the changes are in memory only.

After Construction
------------------
Changing what is active after PysuiConfiguration has been constructed is done through the ``PysuiConfig.make_active(...)`` method.
It takes the same arguments as the constructor with the exception of the ``from_cfg_path``.

**NOTE** If changing the active group and or profile after you've constructed a client will require creating a new
client. Changing the active address will not require recreating a client.

.. code-block:: python
    :linenos:

    # Set group to builtin Sui's GraphQL RPC group
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP, profile_name="mainnet" )
    client = SyncGqlClient(pysui_config=cfg)

    # Changing active profile
    client.config.make_active(profile_name="testnet")
    client = SyncGqlClient(pysui_config=cfg)

Rebuilding from ``client.yaml``
===============================
Depending on use of the Sui command line ``sui client ...`` it may be desierable to reconstruct the PysuiConfiguration
``sui_json_config`` group again or for the first time.

**WARNING** This is a destructive call that will delete the existing ``sui_json_config`` group if it exists as well as
the ``sui_gql_config`` if you so choose.

The following shows the method defaults

.. code-block:: python

    cfg.rebuild_from_sui_client(rebuild_gql: bool = False,persist: bool = True)
