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
    | When creating a Client it relies on the presence of the ``client.yaml`` the binaries created.
    | For example, if SuiConfig is created with :meth:`pysui.sui.sui_config.SuiConfig.default` it looks for:
    | ``.sui/sui_config/client.yaml``


| *Why roughly?*
| If you won't be using ``pysui publish`` and you won't be using the ``sui ...`` command line
| then an alternative would be to generate your own ``client.yaml``
| and point to that with :meth:`pysui.sui.sui_config.SuiConfig.from_config_file`

The Client
----------
| All **pysui** SDK usage starts with the creation of a HTTPS client. It's job is handling all
| the interactions between itself and the SUI blockchain via the SUI RPC API.

**pysui** SDK includes synchronous and asynchronous clients for interacting with SUI RPC API and an
asynchronous client for subscriptions.

The first two client types have the same methods (parity) so it is a matter of choice, or necessity, on which to use. It
is pretty much standard that the client is allocated at the very begining of your application. Here
are examples of doing just that as well as allocating a subscription client:

.. code-block:: Python
   :linenos:

    from pysui.sui.sui_clients.sync_client import SuiClient as sync_client
    from pysui.sui.sui_clients.async_client import SuiClient as async_client
    from pysui.sui.sui_clients.subscribe import SuiClient as async_subscriber

    # Synchronous client
    client = sync_client(SuiConfig.default())  # or
    client = sync_client(SuiConfig.from_config_file(...))

    # Asynchronous client
    client = async_client(SuiConfig.default())  # or
    client = async_client(SuiConfig.from_config_file(...))

    # Asynchronous subscriber
    client = async_subscriber(SuiConfig.default())  # or
    client = async_subscriber(SuiConfig.from_config_file(...))

The raw workhorse for submitting transactions is :py:meth:`pysui.sui.sui_clients.sync_client.SuiClient.execute` which takes a
**Builder** object. Builders describe the RPC call, any parameters and how to format sucessful results.

While many of the SuiClient convenience methods (i.e. :meth:`pysui.sui.sui_clients.sync_client..get_object`) take care of
creating a Builder for the caller, and then executing, all **Builders** are available to setup outside of the SuiClient.
