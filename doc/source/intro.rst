Introducing pysui
=================

**pysui** is a SUI RPC API Client SDK for Python.

The role of Sui Binaries
------------------------
**pysui** roughly relies on Sui Binaries for two core reasons

-
    | If using the Publish builder, it relies on the presence of the binaries during the publish
    | call as it invokes: ``sui move build``


-
    | When creating a Client it relies on the presence of the ``client.yaml`` the Sui binaries created.
    | For example, if SuiConfig is created with :meth:`pysui.sui.sui_config.SuiConfig.default_config` it looks for:
    | ``.sui/sui_config/client.yaml``


The Client
----------

All **pysui** SDK usage commonly starts with the creation of one or more SuiClients. Their job is handling
the interactions between itself and the SUI blockchain via the SUI RPC API.

**pysui** SDK includes synchronous and asynchronous clients for interacting with SUI RPC API and an
asynchronous client for subscriptions.

The first two client types have the same methods (parity) so it is a matter of choice, or necessity, on which to use. It
is pretty much standard that the client is allocated at the very begining of your application. Here
are examples of doing just that as well as allocating a subscription client:

.. code-block:: Python
   :linenos:

    # For synchronous RPC API interactions
    from pysui.sui.sui_clients.sync_client import SuiClient as sync_client

    # For asynchronous RPC API interactions
    from pysui.sui.sui_clients.async_client import SuiClient as async_client

    # For asynchronous subscriptions interactions
    from pysui.sui.sui_clients.subscribe import SuiClient as async_subscriber

    # Synchronous client
    client = sync_client(SuiConfig.default_config()) # Assumes devnet or testnet

    # Asynchronous client
    client = async_client(SuiConfig.default_config()) # Assumes devnet or testnet

    # Asynchronous subscriber
    client = async_subscriber(SuiConfig.default_config()) # Assumes devnet or testnet

The raw workhorse for submitting transactions is :py:meth:`pysui.sui.sui_clients.sync_client.SuiClient.execute` which takes a
**Builder** object. Builders describe the RPC call, any parameters and how to format sucessful results.

While many of the SuiClient convenience methods (i.e. :meth:`pysui.sui.sui_clients.sync_client.SuiClient.get_object`) take care of
creating a Builder for the caller, and then executing, all **Builders** are available to setup outside of the SuiClient.

Running Locally
---------------

Starting in version 0.16.1 of ``pysui``, we have aligned with `The sui-base utility <https://suibase.io/>`_ which provides
superior localnet configurability and repeatability. It is the framework for our ``pysui`` unit/integration testing and we've
made usage easier to leverage in developing with ``pysui``.

In the code block above, you will notice the use of `SuiConfig.default_config()` which is assuming connection with devnet or
testnet.

Whereas with `suibase` it loads a present, configurable, Sui configuration along with 5 addresses of each keytype
and each address providing a copius amount of Sui coin.

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

    # See below to having pysui leverage the running instance and binaries
    # When you are done you should stop the localnode
    localnet stop


Having compleded that, the change you will notices is loading the right configuration into your SuiClient so all operations
interact with the sui-base localnet node. All operations are the same whether you are interacting with `devnet`,
`testnet` or the **sui-base** `localnode`. So once you set the client correctly all code should behave as normal:

.. code-block:: Python
   :linenos:

    # For synchronous RPC API interactions
    from pysui.sui.sui_clients.sync_client import SuiClient as sync_client

    # For asynchronous RPC API interactions
    from pysui.sui.sui_clients.async_client import SuiClient as async_client

    # For asynchronous subscriptions interactions
    from pysui.sui.sui_clients.subscribe import SuiClient as async_subscriber

    # Synchronous client
    client = sync_client(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running

    # Asynchronous client
    client = async_client(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running

    # Asynchronous subscriber
    client = async_subscriber(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running
