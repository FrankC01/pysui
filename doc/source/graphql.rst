
GraphQL
"""""""

MystenLab's announcement can be found `Here <https://github.com/mystenLabs/sui/issues/13700/>`_ . This change begins the
transitions from JSON RPC node interactions to GraphQL RPC node interactions.

``pysui`` has added support for interacting with the Sui GraphQL RPC node as well as porting Builders to what we
refer to as QueryNodes for, currently, read operations.

At the time of this writing, there are limitations to Sui GraphQL RPC. Before moving forward read `This <https://forums.sui.io/t/launching-the-beta-graphql-rpc-service/45104/12/>`_ to
know what is active in the beta.

====================
Subject to Change
====================

pysui's GraphQL implementation, class names, etc. subject to change. This implementation is not production ready and should be considered experiemental.


====================
Key Dependencies
====================

pysui uses `gql <https://pypi.org/project/gql/>`_ for GraphQL queries and eventually mutations and subscriptions. Includes DSL.

You can use the capabilities of this library to create your own query strings, DocumentNodes or QueryNodes.

====================
Running Samples
====================

If you have installed Sui binaries then change the environment to either testnet or mainnet. Note that Sui GraphQL mainnet has
less bugs than testnet.

.. code-block::

    . env/bin/activate # Or however you've setup a virtual environment
    python pgql_s_example.py # Synchronous
    python pgql_a_example.py # Asynchronous
    deactivate

====================
Simple dev example
====================

.. code-block:: python

    #
    """Development example."""

    from pysui.sui.sui_pgql.clients import SuiGQLClient
    import pysui.sui.sui_pgql.pgql_query as qn
    from pysui import SuiConfig,handle_result

    def main(client: SuiGQLClient):
        """Fetch 0x2::sui::SUI (default) for owner."""
        # GetCoins defaults to '0x2::sui::SUI' coin type so great for owners gas listing
        qres = client.execute_query_node(
            with_node=qn.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            )
        )
        # 1. QueryNode results are mapped to dataclasses/dataclasses-json
        print(qres.result_data.to_json(indent=2))

        # 2. Or get the data through handle_result
        # print(handle_result(qres).to_json(indent=2))

    

    if __name__ == "__main__":
        # Initialize synchronous client
        client_init = SuiGQLClient(config=SuiConfig.default_config(),write_schema=False)
        main(client_init)

------
Schema
------

To leverage the power of Sui GraphQL one would benefit to understand the schema implemented. To create a
copy of a Sui GraphQL RPC schema in use, you can instruct pysui to write a copy in the current directory:

.. code-block:: python

    from pysui.sui.sui_pgql.clients import SuiGQLClient
    from pysui import SuiConfig

    def main():
        """Dump Sui GraphQL Schema."""
        # Initialize synchronous client
        client_init = SuiGQLClient(config=SuiConfig.default_config(),write_schema=True)

        print(f"Schema dumped to: `devnet_schema-{client_init.schema_version}.graqhql`")

    if __name__ == "__main__":
        main()


=================
Executing Queries
=================

The SuiGQLClient encapsulates the ``gql`` Client and support multiple options to execute a query and
returning results

.. code-block:: python

    # Execute a query in a string
    def execute_query_string(
        self,
        *,
        string: str,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:

    # Execute a gql DocumentNode
    def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:

    # Execute a pysui QueryNode
    def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:

* ``execute_query_string`` convert a GraphQL query string to a gql `DocumentNode <https://gql.readthedocs.io/en/stable/usage/basic_usage.html#>`_ and execute, returning a dictionary result by default
* ``execute_document_node`` will execute a gql DocumentNode and return a dictionary result if no ``encode_fn`` function is defined
* ``execute_query_node`` will execute a ``pysui`` QueryNode and return a dictionary result if no ``encode_fn`` function is defined
* ``encode_fn`` is an explict callable for encoding a query result that takes a dictionary and returns Any. If specified along with a ``pysui`` QueryNode, it will override the encode_fn method

--------------
String queries
--------------

String queries are just that: A string describing the query. When submitted to
the ``SuiGQLClient.execute_query(with_string="query string")`` it will
convert the sting to a ``DocumentNode``, execute the query and either return the raw result or invoke the ``encode_fn`` if provided.

.. code-block:: python

    #
    """String query example."""

    from pysui.sui.sui_pgql.clients import SuiGQLClient
    from pysui import SuiConfig

    def main(client: SuiGQLClient):
        """Execute a static string query."""
        _QUERY = """
            query {
                chainIdentifier
                checkpointConnection (last: 1) {
                    nodes {
                        sequenceNumber
                        timestamp
                    }
                }
            }
        """
        qres = client.execute_query_string(string=_QUERY)
        print(qres)

    if __name__ == "__main__":
        # Initialize synchronous client
        client_init = SuiGQLClient(config=SuiConfig.default_config(),write_schema=False)
        main(client_init)

-----------------------
DocumentNode queries
-----------------------

``DocumentNode`` queries are those that use the ``gql`` intermediate step of convering a query string to a DocumentNode
using ``gql`` functions.

.. code-block:: python

    #
    """DocumentNode query example."""

    from gql import gql
    from pysui.sui.sui_pgql.clients import SuiGQLClient
    from pysui import SuiConfig

    def main(client: SuiGQLClient):
        """Execute a DocumentNode as result of `gql` compilation."""
        _QUERY = # Same query string as used above
        qres = client.execute_document_node(with_node=gql(_QUERY))
        print(qres)

    if __name__ == "__main__":
        # Initialize synchronous client
        client_init = SuiGQLClient(config=SuiConfig.default_config(),write_schema=False)
        main(client_init)

-----------------------
pysui QueryNode queries
-----------------------

pysui QueryNodes are those that subclass ``pysui.sui.sui_pgql.pgql_client.PGQL_QueryNode``. ``pysui`` provides a number of
predefined QueryNode queries that attempt to achieve parity with most pysui SDK Builders, however some may not be supported.

pysui QueryNodes (such as ``GetCoins`` above) take zero or more parameters depending on the query, and
some provide paging control for large results. All pysui can QueryNodes provide an ``NODE.encode_fn(dict)`` static method
to encode the dictionary result, from executing, to a encoding style of their own. This can be overriden as noted above.


pysui QueryNodes leverage gql's `DSL <https://gql.readthedocs.io/en/stable/advanced/dsl_module.html#>`_ to
construct queries, fragments and inline fragments. Once constructed, pysui QueryNodes can be submitted to
the client (SuiGQLClient or AsyncSuiGQLClient) ``execute_query`` method.

When passing a QueryNode to ``execute_query`` a few things happen prior to submitting:

#. The QueryNode's ``as_document_node`` is called to return a DocumentNode
#. The result is checked and if it is the ``PGQL_NoOp`` type, a ``NoopGQL`` object is returned, otherwise...
#. The DocumentNode is submitted for execution and ``gql`` returns a Python dict of the result
#. A check is then made to see if either ``encode_fn`` is provided or if the QueryNode provides an ``encode_fn`` the function is called to prepare the result and returns
#. Otherwise the Python dict is returned

================================
Creating PGQL_QueryNode queries
================================

-------
Notes:
-------

#. During the execute step, if a QueryNode has public property ``owner`` it is first checked if the value
    is an alias and will resolve it to the associated Sui address, otherwise the value is validated as a Sui address literal.
#. In the ``as_document_node`` call it does not have to be constructed using DSL as the example below in Step 2 shows. It is
    only required that the method returns a DocumentNode.

-------
Step 1:
-------

Note the required and optional methods from ``pysui.sui.sui_pgql.pgql_client.PGQL_QueryNode``:

.. code-block:: python

    class PGQL_QueryNode(ABC):
        """Base QueryNode class."""

        @abstractmethod
        def as_document_node(self, schema: DSLSchema) -> DocumentNode:
            """Returns a gql DocumentNode ready to execute.

            This must be implemented in subclasses.

            :param schema: The current Sui GraphQL schema
            :type schema: DSLSchema
            :return: A query processed into a gql DocumentNode
            :rtype: DocumentNode
            """

        @staticmethod
        def encode_fn() -> Union[Callable[[dict], Union[pgql_type.PGQL_Type, Any]], None]:
            """Return the serialization function in derived class or None.

            This is optional,

            :return: A function taking a dictionary as input and returning a PGQL_Type or Any, or None
            :rtype: Union[Callable[[dict], Union[pgql_type.PGQL_Type, Any]], None]
            """
            return None

-------
Step 2:
-------

Derive and implement your construct. This example is a predefined pysui QueryNode that uses the
``gql`` DSL with the schema. It also has defined an encoding type.

.. code-block:: python

    from typing import Optional, Callable, Union, Any
    from gql.dsl import DSLQuery, dsl_gql, DSLSchema
    from graphql import DocumentNode

    from pysui.sui.sui_pgql.pgql_clients import PGQL_QueryNode
    import pysui.sui.sui_pgql.pgql_types as pgql_type

    class GetCoinMetaData(PGQL_QueryNode):
        """GetCoinMetaData returns meta data for a specific `coin_type`."""

        def __init__(self, *, coin_type: Optional[str] = "0x2::sui::SUI") -> None:
            """QueryNode initializer.

            :param coin_type: The specific coin type string, defaults to "0x2::sui::SUI"
            :type coin_type: str, optional
            """
            self.coin_type = coin_type

        def as_document_node(self, schema: DSLSchema) -> DocumentNode:
            """Build the DocumentNode."""
            qres = schema.Query.coinMetadata(coinType=self.coin_type).select(
                schema.CoinMetadata.decimals,
                schema.CoinMetadata.name,
                schema.CoinMetadata.symbol,
                schema.CoinMetadata.description,
                schema.CoinMetadata.iconUrl,
                schema.CoinMetadata.supply,
                object_data=schema.CoinMetadata.asMoveObject.select(
                    schema.MoveObject.asObject.select(meta_object_id=schema.Object.location)
                ),
            )
            return dsl_gql(DSLQuery(qres))

        @staticmethod
        def encode_fn() -> Callable[[dict], pgql_type.SuiCoinMetadataGQL]:
            """Return the encoding function to create a SuiCoinMetadataGQL dataclass."""
            return pgql_type.SuiCoinMetadataGQL.from_query
