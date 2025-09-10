====================
GraphQL
====================

MystenLab's announcement can be found `Here <https://github.com/mystenLabs/sui/issues/13700/>`_ . This change begins the
transitions from JSON RPC node interactions to GraphQL RPC node interactions.

``pysui`` has added support for interacting with the Sui GraphQL RPC node as
well as porting Builders to what are refered to as QueryNodes.

At the time of this writing, there are limitations to Sui GraphQL RPC. Before moving forward read `This <https://forums.sui.io/t/launching-the-beta-graphql-rpc-service/45104/12/>`_ to
know what is active in the beta.

Subject to Change
------------------

pysui's GraphQL implementation, class names, etc. subject to change. This
implementation is not production ready and should be considered BETA.

Key Dependencies
----------------

pysui uses `gql <https://pypi.org/project/gql/>`_ for GraphQL queries, mutations and eventually  subscriptions. Includes DSL.

You can use the capabilities of this library to create your own query strings,
GraphQLRequest or QueryNodes.

Running Samples
---------------

If you have installed Sui binaries you can change the environment Profile
to either testnet or mainnet. Note that Sui GraphQL mainnet has less bugs
than testnet.

.. code-block::

    . env/bin/activate # Or however you've setup a virtual environment
    python pgql_s_example.py # Synchronous
    python pgql_a_example.py # Asynchronous
    deactivate         # Or however you've virtual environment is closed

------
Schema
------

To leverage the power of Sui GraphQL one would benefit to understand the
schema implemented. To create a copy of a Sui GraphQL RPC schema in use,
you can instruct pysui to write a copy in the current directory:

.. code-block:: python
    :linenos:

    from pysui import PysuiConfiguration, SyncGqlClient

    def main():
        """Dump Sui GraphQL Schema."""
        # Initialize synchronous client
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP )
        client_init = SyncGqlClient(pysui_config=cfg,write_schema=True)
        print(f"Schema dumped to: {client_init.base_schema_version}.graqhql`")

    if __name__ == "__main__":
        main()

HTTP Client Headers
-------------------

You can set global HTTP client headers at the creation of the SuiGQLClient
and you can override/extend them with each query execution. If used at query
execution it is merged/update with the global.

If not provided at construction, it defaults to ``{"headers":None}``

.. code-block:: python
    :emphasize-lines: 8,15

    from pysui import PysuiConfiguration, SyncGqlClient
    import pysui.sui.sui_pgql.pgql_query as qn

    def main():
        """Set global headers to include in the RPC calls."""
        # Initialize synchronous client with default headers
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP )
        client_init = SyncGqlClient(pysui_config=cfg,default_header={"headers": {"from": "youremail@acme.org"}})
        print(client.client_headers)
        # Use different 'from' in headers for this one call
        qres = client.execute_query_node(
            with_node=qn.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            ),
            with_headers={"headers":{"from": "otheremail@coyote.org"
        )

    if __name__ == "__main__":
        main()
