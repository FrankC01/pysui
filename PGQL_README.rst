""""""""""""""""""""""""""""""""""""""""""""
pgql a.k.a pysui-gql (pysui GraphQL client)
""""""""""""""""""""""""""""""""""""""""""""

.. contents:: Overview
    :depth: 3

====================
Introduction
====================

**ALPHA ALPHA ALPHA** - Use tenderly, it's fragile!

A graphql stub to test against Sui RPC 2.0 graphql (currently beta is 1.5)

====================
Key Dependencies
====================

pysui-gql uses `gql <https://pypi.org/project/gql/>`_ for GraphQL queries, mutations, etc. Includes DSL


--------------------------
Running Samples
--------------------------

.. code-block::

    . env/bin/activate
    python pgql_s_example.py # Synchronous
    python pgql_a_example.py # Asynchronous
    deactivate

====================
Simple dev example
====================

.. code-block:: python

    #
    """Development example."""

    from pysui.sui.sui_pgql.clients import SuiGQLClient, SUI_GRAPHQL_MAINNET
    import pysui.sui.sui_pgql.pgql_query as qn

    def main(client: SuiGQLClient):
        """Fetch 0x2::sui::SUI (default) for owner."""
        # GetCoins defaults to '0x2::sui::SUI' coin type so great for owners gas listing
        qres = client.execute_query(
            with_query_node=qn.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            )
        )
        # Results are mapped to dataclasses/dataclasses-json
        print(qres.to_json(indent=2))

    if __name__ == "__main__":
        client_init = SuiGQLClient(gql_rpc_url=SUI_GRAPHQL_MAINNET)
        main(client_init)

========================================
Anatomy of client.execute_query
========================================

The SuiGQLClient support multiple options to execute a query

.. code-block:: python

    def execute_query(
        self,
        *,
        with_string: Optional[str] = None,
        with_document_node: Optional[DocumentNode] = None,
        with_query_node: Optional[PGQL_QueryNode] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> Any:


* ``with_string`` convert a GraphQL query string to a gql `DocumentNode <https://gql.readthedocs.io/en/stable/usage/basic_usage.html#>`_ and execute, returning a dictionary result by default
* ``with_document_node`` will execute a gql DocumentNode and return a dictionary result by default
* ``with_query_node`` will execute a ``pysui`` QueryNode and return a dictionary result if no ser_fn function is defined
* ``encode_fn`` is an explict callable for encoding a query result that takes a dictionary and returns Any. If specified along with a ``pysui`` QueryNode, it will override the encode_fn method

===============
pysui QueryNode
===============

pysui QueryNodes are predefined GraphQL queries that attempt to achieve parity with most pysui SDK Builders. However some may not be supported.

pysui QueryNodes can take zero or more parameters depending on the query, and some provide paging control for large results. All pysui QueryNodes
provide an ``encode_fn`` to encode the dictionary result from gql to a dataclass/dataclass-json class. This can be overriden as
noted above.

pysui QueryNodes leverage gql's `DSL <https://gql.readthedocs.io/en/stable/advanced/dsl_module.html#>`_ to
construct queries, fragments and inline fragments. Once constructed, pysui QueryNodes can be submitted to the client ``execute_query``
method.
