========
GraphQL
========

``pysui`` supports the Sui GraphQL RPC as a transport protocol available on
devnet, testnet, and mainnet. New code should use the async client obtained via
:py:func:`pysui.sui.sui_common.factory.client_factory`; a synchronous client
is also available for scripts that cannot use ``asyncio``.

Running the Sample
------------------

``pgql_a_example.py`` is included in the project repository (not installed via
PyPI) and covers a variety of patterns — data queries, transaction building,
execution, and simulation. It serves as a reference for exploring available
options and may be run optionally from an activated virtual environment:

.. code-block:: shell

    python pgql_a_example.py

Client Setup
------------

Use :py:func:`pysui.sui.sui_common.factory.client_factory` to obtain an
async GraphQL client bound to the active configuration group. See
:doc:`PysuiConfiguration <pyconfig>` for configuration details.

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, client_factory

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)  # returns AsyncSuiGQLClient
        # client.config.active_address, client.execute_query_node(...), etc.

    if __name__ == "__main__":
        asyncio.run(main())

A synchronous client is also available for scripts that cannot use ``asyncio``:

.. code-block:: python

    from pysui import PysuiConfiguration
    from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient

    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    client = SuiGQLClient(pysui_config=cfg)

Schema
------

To write a copy of the live Sui GraphQL schema to the current directory:

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration
    from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = AsyncSuiGQLClient(pysui_config=cfg, write_schema=True)
        print(f"Schema written to: {client.base_schema_version}.graphql")

    if __name__ == "__main__":
        asyncio.run(main())

HTTP Client Headers
-------------------

Global HTTP headers can be set at client construction and overridden
per-query. If not provided, headers default to ``None``.

.. code-block:: python
   :emphasize-lines: 5,13

    import asyncio
    from pysui import PysuiConfiguration, AsyncSuiGQLClient
    import pysui.sui.sui_pgql.pgql_query as qn

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = AsyncSuiGQLClient(
            pysui_config=cfg,
            default_header={"headers": {"from": "youremail@acme.org"}},
        )
        # Per-call override — merged with the global header
        result = await client.execute_query_node(
            with_node=qn.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            ),
            with_headers={"headers": {"from": "otheremail@coyote.org"}},
        )

    if __name__ == "__main__":
        asyncio.run(main())

Query Methods
-------------

The GraphQL client exposes three execution paths:

``execute_query_string``
    Accepts a raw GraphQL query string, converts it to a ``GraphQLRequest``,
    and executes it. Returns a ``SuiRpcResult`` containing a dict by default.

``execute_document_node``
    Accepts a ``gql`` ``GraphQLRequest`` (e.g. the output of ``gql(string)``).
    Returns a ``SuiRpcResult`` containing a dict by default.

``execute_query_node``
    Accepts a pysui ``PGQL_QueryNode``. The node's ``as_document_node``
    method is called to build the ``GraphQLRequest``, then the result is
    encoded via the node's ``encode_fn`` if one is provided.

String Queries
++++++++++++++

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, AsyncSuiGQLClient

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

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = AsyncSuiGQLClient(pysui_config=cfg)
        result = await client.execute_query_string(string=_QUERY)
        print(result)

    if __name__ == "__main__":
        asyncio.run(main())

GraphQL Request Queries
+++++++++++++++++++++++

.. code-block:: python
   :linenos:

    import asyncio
    from gql import gql
    from pysui import PysuiConfiguration, AsyncSuiGQLClient

    _QUERY = """..."""  # same query string as above

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = AsyncSuiGQLClient(pysui_config=cfg)
        result = await client.execute_document_node(with_node=gql(_QUERY))
        print(result)

    if __name__ == "__main__":
        asyncio.run(main())

pysui QueryNode Queries
++++++++++++++++++++++++

pysui ships a library of pre-built :doc:`QueryNodes <graphql_queries>` that
map to common Sui queries. Each QueryNode:

- Takes typed constructor parameters
- Provides an ``encode_fn`` static method that converts the raw dict result
  into a typed dataclass
- Supports paging where the underlying query returns paginated data

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, AsyncSuiGQLClient
    import pysui.sui.sui_pgql.pgql_query as qn

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = AsyncSuiGQLClient(pysui_config=cfg)
        result = await client.execute_query_node(
            with_node=qn.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            )
        )
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(main())

During ``execute_query_node`` pysui:

1. Calls the QueryNode's ``as_document_node`` to obtain a ``GraphQLRequest``
2. Returns a ``NoopGQL`` immediately if the node is ``PGQL_NoOp``
3. Submits the request; ``gql`` returns a Python dict
4. Invokes the QueryNode's ``encode_fn`` (if defined) to produce a typed result
5. Otherwise returns the raw dict

An ``owner`` property on a QueryNode is resolved against the active
address alias table before submission.

Creating a Custom QueryNode
++++++++++++++++++++++++++++

**Step 1 — understand the base class interface:**

.. code-block:: python

    from abc import abstractmethod
    from typing import Optional, Callable, Union, Any
    from gql import GraphQLRequest
    from gql.dsl import DSLSchema

    import pysui.sui.sui_pgql.pgql_types as pgql_type

    class PGQL_QueryNode(ABC):
        """Base QueryNode class."""

        @abstractmethod
        def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
            """Build and return a gql GraphQLRequest.

            The method is not required to use the DSL — it only needs to
            return a valid ``GraphQLRequest``.
            """

        @staticmethod
        def encode_fn() -> Union[Callable[[dict], Union[pgql_type.PGQL_Type, Any]], None]:
            """Return the result encoding function, or None for a raw dict."""
            return None

**Step 2 — derive and implement:**

.. code-block:: python
   :linenos:

    from typing import Optional, Callable
    from gql import GraphQLRequest
    from gql.dsl import DSLQuery, dsl_gql, DSLSchema

    from pysui.sui.sui_pgql.pgql_clients import PGQL_QueryNode
    import pysui.sui.sui_pgql.pgql_types as pgql_type

    class GetCoinMetaData(PGQL_QueryNode):
        """Fetch metadata for a specific coin type."""

        def __init__(self, *, coin_type: Optional[str] = "0x2::sui::SUI") -> None:
            """QueryNode initializer.

            :param coin_type: The coin type string, defaults to "0x2::sui::SUI"
            :type coin_type: str, optional
            """
            self.coin_type = coin_type

        def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
            """Build the DocumentNode."""
            qres = schema.Query.coinMetadata(coinType=self.coin_type).select(
                schema.CoinMetadata.decimals,
                schema.CoinMetadata.name,
                schema.CoinMetadata.symbol,
                schema.CoinMetadata.description,
                schema.CoinMetadata.iconUrl,
                schema.CoinMetadata.supply,
                object_data=schema.CoinMetadata.asMoveObject.select(
                    schema.MoveObject.asObject.select(
                        meta_object_id=schema.Object.location
                    )
                ),
            )
            return dsl_gql(DSLQuery(qres))

        @staticmethod
        def encode_fn() -> Callable[[dict], pgql_type.SuiCoinMetadataGQL]:
            """Return the encoder that produces a SuiCoinMetadataGQL instance."""
            return pgql_type.SuiCoinMetadataGQL.from_query
