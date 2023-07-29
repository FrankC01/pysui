Introducing pysui
=================

**pysui** is the Python Sui RPC API Client SDK.

The role of Sui Binaries
------------------------
**pysui** roughly relies on Sui Binaries for one core reason

-
    | If publishing or publishing upgrades, these functions rely on the
    | presence of the binaries during the publish call as it invokes: ``sui move build``


-
    | When not running with ``user configuration``, creating a Client relies on the presence of the ``client.yaml`` the Sui binaries created.
    | For example, if SuiConfig is created with :meth:`pysui.sui.sui_config.SuiConfig.default_config` it looks for:
    | ``.sui/sui_config/client.yaml``

The Clients
-----------

All **pysui** SDK usage commonly starts with the creation of one or more SuiClients. Their job is handling
the interactions between itself and the SUI blockchain via the SUI RPC API.

**pysui** SDK includes synchronous and asynchronous clients for interacting with SUI RPC API and an
asynchronous client for subscriptions.

The first two client types have the same methods (parity) so it is a matter of choice, or necessity, on which to use. It
is pretty much standard that the client is allocated at the very begining of your application. Here
are examples of doing just that as well as allocating a subscription client:

.. code-block:: Python
   :linenos:

    # The underlying configuration class
    from pysui import SuiConfig

    # For synchronous RPC API interactions
    from pysui import SyncClient

    # For asynchronous RPC API interactions
    from pysui import AsyncClient

    # For asynchronous subscriptions interactions
    from pysui import Subscribe

    # Synchronous client
    client = SyncClient(SuiConfig.default_config())

    # Asynchronous client
    client = AsyncClient(SuiConfig.default_config())

    # Asynchronous subscriber
    client = Subscribe(SuiConfig.default_config())

The raw workhorse for submitting transactions is :py:meth:`pysui.sui.sui_clients.sync_client.SuiClient.execute` which takes a
**Builder** object. Builders describe the RPC call, any parameters and how to format sucessful results.

While some of the SuiClient convenience methods (e.g. :meth:`pysui.sui.sui_clients.sync_client.SuiClient.get_object`) take care of
creating a Builder for the caller, and then executing, all **Builders** are available to setup outside of the SuiClient.

Running With `suibase`
----------------------

We have aligned with `The sui-base utility <https://suibase.io/>`_ which provides
superior localnet configurability and repeatability. It is the framework for our ``pysui`` unit/integration testing and we've
made usage easier to leverage in developing with ``pysui``.

In the code block above, you will notice the use of `SuiConfig.default_config()` which is driven by the standard `client.yaml`.

Whereas with `suibase` it loads a persistant, and configurable, Sui configuration along with 5 addresses of each keytype
and providing a copius amount of Sui coin per address.

First ensure proper setup of `sui-base`:

.. code-block:: bash
   :linenos:

    # From ~/
    git clone git@github.com:sui-base/suibase.git

    # Install sui-base scripts
    cd suibase
    ./install

    # Generate and start a local node
    # This will clone the Sui source and buid the sui binary and sui-faucet
    localnet start

    # Ensure that active symlink is set to localnet
    localnet set-active


Having compleded that, the change you will notices is loading the right configuration into your SuiClient so all operations
interact with the sui-base localnet node. All operations are the same whether you are interacting with `devnet`,
`testnet`, `mainnet` or the **sui-base** `localnode`. So once you set the client correctly all code should behave as normal:

.. code-block:: Python
   :linenos:

    # The underlying configuration class
    from pysui import SuiConfig

    # For synchronous RPC API interactions
    from pysui import SyncClient

    # For asynchronous RPC API interactions
    from pysui import AsyncClient

    # For asynchronous subscriptions interactions
    from pysui import Subscribe

    # Synchronous client
    client = SyncClient(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running

    # Asynchronous client
    client = AsyncClient(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running

    # Asynchronous subscriber
    client = Subscribe(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running


Remember to shutdown `suibase` when done:

.. code-block:: bash
   :linenos:

    # When you are done you should stop the localnode
    localnet stop


Running With user configuration
-------------------------------

A new option for loading a configuration was added in `pysui` 0.25.0: :py:meth:`pysui.sui.sui_config.SuiConfig.user_config`

With this option, you set the rpc_url, keystrings and optional web socket url. For example:

.. code-block:: Python
   :linenos:

    # The underlying configuration class
    from pysui import SuiConfig, SyncClient

    # Option-1: Setup configuration with one or more known keystrings and optional web services.
    cfg = SuiConfig.user_config(
        # Required
        rpc_url="https://fullnode.devnet.sui.io:443",
        # Optional. First entry becomes the 'active-address'
        # Must be a valid Sui base64 keystring (i.e. 'key_type_flag | private_key_seed' )
        prv_keys=["AOM6UAQrFe7r9nNDGRlWwj1o7m1cGK6mDZ3efRJJmvcG"],
        # Optional, only needed for subscribing
        ws_url="wss://fullnode.devnet.sui.io:443",
    )

    # Option-2: Alternate setup configuration without keystrings or web sercices
    cfg = SuiConfig.user_config(rpc_url="https://fullnode.devnet.sui.io:443")

    # One address (and keypair), at least, should be created
    # First becomes the 'active-address'
    _mnen, _address = cfg.create_new_keypair_and_address(SignatureScheme.ED25519)

    # Synchronous client
    client = SyncClient(cfg)

Caveats
#######

With user configuraiton, as it does not assume the installation of Sui binaries, the following are
considerations:

1. You can not publish or upgrade Sui move contracts, attempting to do so will thow a **ValueError** exception
2. Any new address/keypair creations **will not** be persisted as `user_config` is emphemeral
