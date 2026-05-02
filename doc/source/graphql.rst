========
GraphQL
========

``pysui`` supports the Sui GraphQL RPC as a transport protocol available on
devnet, testnet, and mainnet. New code should use the async client obtained via
:py:func:`pysui.sui.sui_common.factory.client_factory`.

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
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, client_factory

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(cfg) as client:
            # Protocol-agnostic dispatch via SuiCommand
            result = await client.execute(
                command=cmd.GetCoins(owner=client.config.active_address)
            )
            if result.is_ok():
                print(result.result_data)
            else:
                print(result.result_string)

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
    from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = GqlProtocolClient(pysui_config=cfg, write_schema=True)
        print(f"Schema written to: {client.base_schema_version}.graphql")

    if __name__ == "__main__":
        asyncio.run(main())

HTTP Client Headers
-------------------

Global HTTP headers can be set at client construction and overridden
per-call. If not provided, headers default to ``None``.

.. code-block:: python
   :emphasize-lines: 5,13

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, GqlProtocolClient

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = GqlProtocolClient(
            pysui_config=cfg,
            default_header={"headers": {"from": "youremail@acme.org"}},
        )
        # Per-call override — merged with the global header
        result = await client.execute(
            command=cmd.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            ),
            headers={"headers": {"from": "otheremail@coyote.org"}},
        )
        if result.is_ok():
            print(result.result_data)
        else:
            print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(main())

Query Methods
-------------

The GraphQL client exposes four execution paths:

``execute(command=...)``
    **Primary path.** Accepts a :py:class:`~pysui.sui.sui_common.sui_command.SuiCommand`
    instance and dispatches to the appropriate GQL query internally.  Works identically
    on both ``GqlProtocolClient`` and ``GrpcProtocolClient`` — see :doc:`sui_commands` for
    the full command list.

``execute_query_string``
    **protocol-level access.** Accepts a raw GraphQL query string, converts it to a
    ``GraphQLRequest``, and executes it. Returns a ``SuiRpcResult`` containing a dict
    by default.  Use when no ``SuiCommand`` equivalent exists.

``execute_document_node``
    **protocol-level access.** Accepts a ``gql`` ``GraphQLRequest`` (e.g. the output of
    ``gql(string)``). Returns a ``SuiRpcResult`` containing a dict by default.

``execute_query_node`` *(deprecated)*
    Accepts a pysui ``PGQL_QueryNode``. The node's ``as_document_node``
    method is called to build the ``GraphQLRequest``, then the result is
    encoded via the node's ``encode_fn`` if one is provided.
    Prefer ``execute(command=...)`` for standard queries.

String Queries
++++++++++++++

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, GqlProtocolClient

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
        client = GqlProtocolClient(pysui_config=cfg)
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
    from pysui import PysuiConfiguration, GqlProtocolClient

    _QUERY = """..."""  # same query string as above

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = GqlProtocolClient(pysui_config=cfg)
        result = await client.execute_document_node(with_node=gql(_QUERY))
        if result.is_ok():
            print(result.result_data)
        else:
            print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(main())

pysui QueryNode Queries *(deprecated path)*
++++++++++++++++++++++++++++++++++++++++++++

``execute_query_node`` is deprecated. For standard queries use
``execute(command=...)`` with a :doc:`SuiCommand <sui_commands>` subclass instead.
``execute_query_node`` remains available as an protocol-level access for custom
``PGQL_QueryNode`` subclasses with no ``SuiCommand`` equivalent.

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, GqlProtocolClient
    import pysui.sui.sui_pgql.pgql_query as qn

    async def main():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = GqlProtocolClient(pysui_config=cfg)
        # Protocol-level access: custom QueryNode with no SuiCommand equivalent
        result = await client.execute_query_node(
            with_node=qn.GetObjectContent(
                object_id="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
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

Transaction Building
+++++++++++++++++++++

Build and execute transactions using the unified transaction infrastructure:

.. code-block:: python
   :linenos:

    import asyncio
    import pysui.sui.sui_common.sui_commands as cmd
    from pysui import PysuiConfiguration, client_factory

    async def transaction_example():
        """Build and execute a simple transaction."""
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        async with client_factory(cfg) as client:
            # Create transaction via client
            txn = await client.transaction()

            # Add transaction commands
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
            await txn.transfer_objects(
                transfers=[coin],
                recipient=cfg.active_address
            )

            # Build and sign
            build_result = await txn.build_and_sign()
            result = await client.execute(
                command=cmd.ExecuteTransaction(**build_result)
            )
            if result.is_ok():
                print(result.result_data)
            else:
                print(result.result_string)

    if __name__ == "__main__":
        asyncio.run(transaction_example())

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
