=================
Introducing pysui
=================

**pysui** is the Python Sui RPC, GraphQL and gRPC API Client SDK.

The role of Sui Binaries
------------------------
**pysui** roughly relies on Sui Binaries for one core reason

-
    | If publishing or publishing upgrades, these functions rely on the
    | presence of the binaries during the publish call as
    | it invokes: ``sui move build``


The Clients
-----------

All **pysui** SDK usage starts with the creation of one kind of SuiClient.
The client's job is handling the interactions between itself and the
SUI blockchain via a particular SUI protocol (JSON RPC, GraphQL or gRPC).

What type of client you use depends on a number of factors:

- Production readiness
- Flexibility
- Performance
- Longevity
- Asynch or sync models (A/S)
- Subscriptions (Subs?)
- etc.

The following table is what client types and protocols are current available:

+--------------------+------------+----------------+-------------+-------+
|  API Support | A/S?| Prod Ready | Planned Sunset | Performance | Subs? |
+==============+=====+============+================+=============+=======+
|  gRPC        | A   | No (alpha) | No             | Fastest     | Yes   |
+--------------------+------------+----------------+-------------+-------+
|  JSON RPC    | A/S | Yes        | Yes (2026)     | Fast        | No    |
+--------------------+------------+----------------+-------------+-------+
|  GraphQL     | A/S | No (alpha) | No             | Not so Fast | Yes   |
+--------------------+------------+----------------+-------------+-------+


For gRPC and GraphQL here is `Additional considerations`_ .

.. _Additional considerations: https://docs.sui.io/guides/developer/getting-started/data-serving

When both asynchronous and synchronous client are available it is a matter
of choice, or necessity, on which to use. It is typical that a client is
instantiated at the very begining of your application.

JSON RPC **pysui** client Setup
+++++++++++++++++++++++++++++++

.. code-block:: Python
   :linenos:

    # The underlying configuration classes
    from pysui import SuiConfig

    # For synchronous and asynchronous JSON RPC API interactions
    from pysui import SyncClient, AsyncClient

    # JSON RPC Synchronous client setup
    client = SyncClient(SuiConfig.default_config())

    # JSON RPC Asynchronous client
    client = AsyncClient(SuiConfig.default_config())

SuiConfig is a thin wrapper around Mystens configuraiton when you've
installed Sui binaries.

GraphQL **pysui** client Setup
++++++++++++++++++++++++++++++

.. code-block:: Python
   :linenos:

    # The underlying configuration classes
    from pysui import PysuiConfiguration

    # For synchronous and asynchronous GraphQL API interactions
    from pysui import SyncGqlClient, AsyncGqlClient

    # GraphQL Synchronous client setup
    client = SyncGqlClient(pysui_config=...)

    # GraphQL Asynchronous client
    client = AsyncGqlClient(pysui_config=PysuiConfiguration(...))

See the :doc:`PysuiConfiguration <pyconfig>` page for detailed information.

gRPC **pysui** client Setup
+++++++++++++++++++++++++++

.. code-block:: Python
   :linenos:

    # The underlying configuration classes
    from pysui import PysuiConfiguration

    # For asynchronous (only option) gRPC API interactions
    from pysui import SuiGrpcClient

    # gRPC Asynchronous client
    client = SuiGrpcClient(pysui_config=PysuiConfiguration(...))

See the :doc:`PysuiConfiguration <pyconfig>` page for detailed information.

Blockchain Queries
------------------

Each client type (JSON RPC, GraphQL and gRPC) facilitates fetching data
and executing transactions through various mechanisms.

- JSON RPC: **pysui** encapsualtes support in class objects called Builders
- GraphQL: **pysui** encapsulates support in class objects called QueryNodes
- gRPC: **pysui** encapsualtes support in class objects call Requests

There is general parity of capabilities across clients although in some cases
they may be unique.

+-----------+--------------------------------------+
|  Protocol | Classes                              |
+===========+======================================+
| JSON RPC  | :doc:`Builders <builders>`           |
+-----------+--------------------------------------+
| GraphQL   | :doc:`Query Nodes <graphql_qnodes>`  |
+-----------+--------------------------------------+
| gRPC      | :doc:`Requests <grpc_requests_list>` |
+-----------+--------------------------------------+

JSON RPC fetch object
+++++++++++++++++++++

.. code-block:: Python
   :linenos:

    # Fundemental classes
    from pysui import SuiConfig, SyncClient, ObjectID

    # The JSON RPC builders
    import pysui.sui.sui_builders.get_builders as bn

    def get_object_example():
        """Fetch an object by ID."""

        # Setup synchronous client using defaults in Mysten's client.yaml
        client = SyncClient(SuiConfig.default_config())

        # Setup the get object builder
        builder = bn.GetObject(
            object_id=ObjectID(
                "0x09f29cd8795c171136f0da589516bfdf4ca0f77084550830fe20611e06018dc7"
            )
        )

        # Execute and reviewe the results
        result = client.execute(builder=builder)
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

GraphQL fetch object
+++++++++++++++++++++

.. code-block:: Python
   :linenos:

    # Fundemental classes
    from pysui import PysuiConfiguration, SyncGqlClient

    # The GraphQL query nodes
    import pysui.sui.sui_pgql.pgql_query as qn

    def get_object_example():
        """Fetch an object by ID."""

        # SUI_GQL_RPC_GROUP is a named group in the configuration.
        # Default configuration is located in the `~/.pysui` folder.

        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        )
        client = SyncGqlClient(pysui_config=cfg)

        query_node = qn.GetObject(
            object_id="0x09f29cd8795c171136f0da589516bfdf4ca0f77084550830fe20611e06018dc7"
        )
        result = client.execute_query_node(with_node=query_node)
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)


gRPC fetch object
+++++++++++++++++

.. code-block:: Python
   :linenos:

    # gRPC client is asynchronous only
    import asyncio

    # Fundemental classes
    from pysui import PysuiConfiguration, SuiGrpcClient

    # The gRPC request nodes
    import pysui.sui.sui_grpc.pgrpc_requests as rn

    async def get_object_example():
        """Fetch an object by ID."""

        # SUI_GRPC_GROUP is a named group in the configuration.
        # Default configuration is located in the `~/.pysui` folder.

        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        )
        client = SuiGrpcClient(pysui_config=cfg)

        request = rn.GetObject(
            object_id="0x09f29cd8795c171136f0da589516bfdf4ca0f77084550830fe20611e06018dc7"
        )
        result = await grpc_client.execute(request=request)
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

    if __name__ == "__main__":
        try:
            asyncio.run(main(cfg))
        except ValueError as ve:
            print(ve)

Running With `suibase` (JSON RPC ONLY)
--------------------------------------

We have aligned with `The sui-base utility <https://suibase.io/>`_ which provides
superior localnet configurability and repeatability. It is the framework for
our ``pysui`` unit/integration testing and we've made usage easier to leverage
in developing with ``pysui``.

In the code block above, you will notice the use of
`SuiConfig.default_config()` which is driven by the standard `client.yaml`.

Whereas with `suibase` it loads a persistant, and configurable,
Sui configuration along with 5 addresses of each keytype and providing
a copius amount of Sui coin per address.

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


Having compleded that, the change you will notices is loading the right
configuration into your SuiClient so all operations interact with
the sui-base localnet node. All operations are the same whether you are
interacting with `devnet`, `testnet`, `mainnet` or the
**sui-base** `localnode`. So once you set the client correctly
all code should behave as normal:

.. code-block:: Python
   :linenos:

    # The underlying configuration class
    from pysui import SuiConfig

    # For synchronous RPC API interactions
    from pysui import SyncClient

    # For asynchronous RPC API interactions
    from pysui import AsyncClient

    # Synchronous client
    client = SyncClient(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running

    # Asynchronous client
    client = AsyncClient(SuiConfig.sui_base_config()) # Assumes sui-base localnet is running


Remember to shutdown `suibase` when done:

.. code-block:: bash
   :linenos:

    # When you are done you should stop the localnode
    localnet stop


Running With user configuration  (JSON RPC ONLY)
------------------------------------------------

This is specific to the JSON RPC clients and SuiConfig only.

A new option for loading a configuration was added
in `pysui` 0.25.0: :py:meth:`pysui.sui.sui_config.SuiConfig.user_config`

With this option, you set the rpc_url, keystrings. For example:

.. code-block:: Python
   :linenos:

    # The underlying configuration class
    from pysui import SuiConfig, SyncClient

    # Option-1: Setup configuration with one or more known keystrings and optional web services.
    cfg = SuiConfig.user_config(
        # Required
        rpc_url="https://fullnode.devnet.sui.io:443",

        # Optional. First entry becomes the 'active-address'
        # List elemente must be a valid Sui base64 keystring (i.e. 'key_type_flag | private_key_seed' )
        # List can contain a dict for importing Wallet keys for example:
        # prv_keys=['AO.....',{'wallet_key': '0x.....', 'key_scheme': SignatureScheme.ED25519}]
        #   where
        #   wallet_key value is 66 char hex string
        #   key_scheme can be ED25519, SECP256K1 or SECP256R1
        prv_keys=["AOM6UAQrFe7r9nNDGRlWwj1o7m1cGK6mDZ3efRJJmvcG"],

    )

    # Option-2: Alternate setup configuration without keystrings
    cfg = SuiConfig.user_config(rpc_url="https://fullnode.devnet.sui.io:443")

    # One address (and keypair), at least, should be created
    # First becomes the 'active-address'
    _mnen, _address = cfg.create_new_keypair_and_address(SignatureScheme.ED25519)

    # Synchronous client
    client = SyncClient(cfg)

Caveats
+++++++

With user configuraiton, as it does not assume the installation of Sui
binaries, the following are considerations:

1. You can not publish or upgrade Sui move contracts, attempting
to do so will thow a **ValueError** exception
1. Any new address/keypair creations **will not** be persisted
as `user_config` is emphemeral
