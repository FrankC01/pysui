
GraphQL
"""""""

MystenLab's announcement can be found `Here <https://github.com/mystenLabs/sui/issues/13700/>`_ . This change begins the
transitions from JSON RPC node interactions to GraphQL RPC node interactions.

``pysui`` has added support for interacting with the Sui GraphQL RPC node as well as porting most Builders to what we
refer to as QueryNodes.

As of this writing, there are limitations to Sui GraphQL RPC. Before moving forward, read `This <https://forums.sui.io/t/launching-the-beta-graphql-rpc-service/45104/12/>`_ to
know what is active in the beta.

====================
Key Dependencies
====================

pysui uses `gql <https://pypi.org/project/gql/>`_ for GraphQL queries and eventually mutations and subscriptions. Includes DSL.

You can use the capabilities of this library to create your own query strings, DocumentNodes or QueryNodes.

====================
Running Samples
====================

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

    from pysui.sui.sui_pgql.clients import SuiGQLClient, SUI_GRAPHQL_MAINNET
    import pysui.sui.sui_pgql.pgql_query as qn
    from pysui import SuiConfig

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
        # SuiConfig is not necessarily pointing to the same environemnt
        # We use it in beta for alias lookups to Sui addresses
        client_init = SuiGQLClient(gql_rpc_url=SUI_GRAPHQL_MAINNET,config=SuiConfig.default_config(),)
        main(client_init)

=================
Executing Queries
=================

The SuiGQLClient encapsulates the ``gql`` Client and support multiple options to execute a query and
returning results

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
* ``with_query_node`` will execute a ``pysui`` QueryNode and return a dictionary result if no ``encode_fn`` function is defined
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

    from pysui.sui.sui_pgql.clients import SuiGQLClient, SUI_GRAPHQL_MAINNET
    from pysui import SuiConfig

    def main(client: SuiGQLClient):
        """Configuration and protocol information."""
        _QUERY = """
            query {
                chainIdentifier
                checkpointConnection (last: 1) {
                    nodes {
                        sequenceNumber
                        timestamp
                    }
                }
                serviceConfig {
                    enabledFeatures
                    maxQueryDepth
                    maxQueryNodes
                    maxDbQueryCost
                    maxPageSize
                    requestTimeoutMs
                    maxQueryPayloadSize
                }
            protocolConfig {
                protocolVersion
                configs {
                    key
                    value
                }
                featureFlags {
                    key
                    value
                }
                }
            }
        """
        qres = client.execute_query(with_string=_QUERY)
        print(qres)

    if __name__ == "__main__":
        # SuiConfig is not necessarily pointing to the same environemnt
        # We use it in beta for alias lookups to Sui addresses
        client_init = SuiGQLClient(gql_rpc_url=SUI_GRAPHQL_MAINNET,config=SuiConfig.default_config(),)
        main(client_init)

-----------------------
DocumentNode queries
-----------------------

``DocumentNode`` queries are those that use the ``gql`` intermediate step of convering a query string to a DocumentNode
using ``gql`` functions.

.. code-block:: python

    #
    """DocumentNode query example."""

    from gql import Client, gql
    from pysui.sui.sui_pgql.clients import SuiGQLClient, SUI_GRAPHQL_MAINNET
    from pysui import SuiConfig

    def main(client: SuiGQLClient):
        """Configuration and protocol information."""
        _QUERY = # Same query string as used above
        qres = client.execute_query(with_document_node=gql(_QUERY))
        print(qres)

    if __name__ == "__main__":
        # SuiConfig is not necessarily pointing to the same environemnt
        # We use it in beta for alias lookups to Sui addresses
        client_init = SuiGQLClient(gql_rpc_url=SUI_GRAPHQL_MAINNET,config=SuiConfig.default_config(),)
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

#. If the QueryNode has property ``owner`` it is first checked if the value is an alias and will resolve, otherwise the value is validated as a Sui address
#. The QueryNode's ``as_document_node`` is called to return a DocumentNode
#. The result is checked and if it is the ``PGQL_NoOp`` type, a ``NoopGQL`` object is returned, otherwise...
#. The DocumentNode is submitted for execution and ``gql`` returns a Python dict of the result
#. A check is then made to see if either ``encode_fn`` is provided or if the QueryNode provides an ``encode_fn`` the function is called to prepare the result and returns
#. Otherwise the Python dict is returned

================================
Creating PGQL_QueryNode queries
================================

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
