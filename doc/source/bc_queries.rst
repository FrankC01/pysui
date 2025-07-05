==================
Blockchain Queries
==================


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
| gRPC      | :doc:`Requests <grpc_requests_list>` |
+-----------+--------------------------------------+
| GraphQL   | :doc:`Query Nodes <graphql_qnodes>`  |
+-----------+--------------------------------------+

JSON RPC fetch object
---------------------

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

gRPC fetch object
------------------

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

GraphQL fetch object
--------------------

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

GraphQL query variations
------------------------

The SuiGQLClient encapsulates the ``gql`` Client and supports additional
options to form and execute a query returning results

.. code-block:: Python

    # Execute a query in a string
    def execute_query_string(
        self,
        *,
        string: str,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """Execute a GraphQL string query."""

    # Execute a gql DocumentNode
    def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """Execute a gql library document node."""

* ``execute_query_string`` convert a GraphQL query string to a gql
  `DocumentNode <https://gql.readthedocs.io/en/stable/usage/basic_usage.html#>`_
  and execute, returning a dictionary result by default
* ``execute_document_node`` will execute a gql DocumentNode and return a
  dictionary result if no ``encode_fn`` function is defined
* ``encode_fn`` is an explict callable for encoding a query result that takes
  a dictionary and returns Any. If specified along with a ``pysui`` QueryNode,
  it will override the encode_fn method

String queries
++++++++++++++

**String** queries are just that: A string describing the query. When submitted
to the ``SuiGQLClient.execute_query(with_string="query string")`` it will
convert the sting to a **DocumentNode**, execute the query and either return
the raw result or invoke the ``encode_fn`` if provided.

.. code-block:: Python

    #
    """String query example."""
    from pysui import PysuiConfiguration, SyncGqlClient

    def main(client: SyncGqlClient):
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
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP )
        client_init = SyncGqlClient(pysui_config=cfg)
        main(client_init)

DocumentNode queries
++++++++++++++++++++

**DocumentNode** queries are those that use the ``gql`` intermediate step of
convering a query string to a DocumentNode using ``gql`` functions.

.. code-block:: Python

    #
    """DocumentNode query example."""

    from gql import gql
    from pysui import PysuiConfiguration, SyncGqlClient

    def main(client: SyncGqlClient):
        """Execute a DocumentNode as result of `gql` compilation."""
        _QUERY = """...""" # Same query string as used above
        qres = client.execute_document_node(with_node=gql(_QUERY))
        print(qres)

    if __name__ == "__main__":
        # Initialize synchronous client
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP )
        client_init = SyncGqlClient(pysui_config=cfg)
        main(client_init)

pysui QueryNode queries
+++++++++++++++++++++++

pysui QueryNodes are those that subclass ``PGQL_QueryNode``. ``pysui`` provides
a number of predefined QueryNode queries that attempt to achieve parity with
most pysui SDK Builders, however some may not be supported.

pysui QueryNodes (such as ``GetCoins`` above) take zero or more parameters
depending on the query, and some provide paging control for large results.
All pysui can QueryNodes provide an ``NODE.encode_fn(dict)`` static method
to encode the dictionary result, from executing, to a encoding style of
their own. This can be overriden as noted above.


pysui QueryNodes leverage gql's `DSL <https://gql.readthedocs.io/en/stable/advanced/dsl_module.html#>`_ to
construct queries, fragments and inline fragments. Once constructed, pysui
QueryNodes can be submitted to the client (SuiGQLClient or AsyncSuiGQLClient)
``execute_query`` method.

When passing a QueryNode to ``execute_query`` a few things happen prior to
submitting:

#. The QueryNode's ``as_document_node`` is called to return a DocumentNode
#. The result is checked and if it is the ``PGQL_NoOp`` type, a ``NoopGQL``
   object is returned, otherwise...
#. The DocumentNode is submitted for execution and ``gql`` returns a Python
   dict of the result
#. A check is then made to see if either ``encode_fn`` is provided or if the
   QueryNode provides an ``encode_fn`` the function is called to prepare the
   result and returns
#. Otherwise the Python dict is returned


Creating PGQL_QueryNode queries
+++++++++++++++++++++++++++++++

Notes:

#. During the execute step, if a QueryNode has public property ``owner`` it is
    first checked if the value is an alias and will resolve it to the
    associated Sui address, otherwise the value is validated as a Sui
    address literal.
#. In the ``as_document_node`` call it does not have to be constructed
    using DSL as the example below in Step 2 shows. It is
    only required that the method returns a DocumentNode.


Step 1
^^^^^^

Note the required and optional methods from ``PGQL_QueryNode``:

.. code-block:: Python

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

Step 2
^^^^^^

Derive and implement your construct. This example is a predefined pysui
QueryNode that uses the ``gql`` DSL with the schema. It also has defined
an encoding type.

.. code-block:: Python

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
