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
**pysui** SDK includes both synchronous (SuiClient) and asynchronous (SuiAsyncClient) flavors.
