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
    client = sync_client(SuiConfig.default_config())  # or
    client = sync_client(SuiConfig.sui_base_config(...))

    # Asynchronous client
    client = async_client(SuiConfig.default_config())  # or
    client = async_client(SuiConfig.sui_base_config(...))

    # Asynchronous subscriber
    client = async_subscriber(SuiConfig.default_config())  # or
    client = async_subscriber(SuiConfig.sui_base_config(...))

The raw workhorse for submitting transactions is :py:meth:`pysui.sui.sui_clients.sync_client.SuiClient.execute` which takes a
**Builder** object. Builders describe the RPC call, any parameters and how to format sucessful results.

While many of the SuiClient convenience methods (i.e. :meth:`pysui.sui.sui_clients.sync_client..get_object`) take care of
creating a Builder for the caller, and then executing, all **Builders** are available to setup outside of the SuiClient.
