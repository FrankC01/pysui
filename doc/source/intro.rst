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

**pysui** SDK includes both synchronous :py:class:`~pysui.sui.sui_rpc.SuiClient` and asynchronous :py:class:`~pysui.sui.sui_rpc.SuiAsynchClient` flavors.

Both client types have the same methods (parity) so it is a matter of choice, or necessity, on which to use. It
is pretty much standard that the client is allocated at the very begining of your application. Here
are examples of doing just that:

.. code-block:: Python
   :linenos:

    # Synchronous client
    client = SuiClient(SuiConfig.default())  # or
    client = SuiClient(SuiConfig.from_config_file(...))

    # Asynchronous client
    client = SuiAsyncClient(SuiConfig.default())  # or
    client = SuiAsyncClient(SuiConfig.from_config_file(...))

The raw workhorse for submitting transactions is :py:meth:`pysui.sui.sui_rpc.SuiClient.execute` which takes a
**Builder** object. Builders describe the RPC call, any parameters and how to format sucessful results.

While many of the SuiClient convenience methods (i.e. :meth:`pysui.sui.sui_rpc.SuiClient.get_object`) take care of
creating a Builder for the caller, and then executing, all **Builders** are available to setup outside of the SuiClient.

The Builders
------------

See :py:mod:`pysui.sui.sui_builders`