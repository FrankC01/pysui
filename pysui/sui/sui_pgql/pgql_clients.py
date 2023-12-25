#    Copyright Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-

"""Sui GraphQL clients."""


from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, Union
from gql import Client, gql

# TODO: Replace with HTTPX equivalents
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.aiohttp import AIOHTTPTransport

from gql.transport import exceptions as texc
from gql.dsl import (
    DSLSchema,
)
from graphql import DocumentNode, print_ast, GraphQLSchema
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.utilities.print_schema import print_schema


from pysui import SuiConfig, SuiRpcResult
from pysui.sui.sui_pgql.pgql_validators import TypeValidator
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_pgql.pgql_configs import pgql_config, SuiConfigGQL
import pysui.sui.sui_constants as cnst


class PGQL_QueryNode(ABC):
    """Base query class."""

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

        :return: A function taking a dictionary as input and returning a PGQL_Type or Any, or None
        :rtype: Union[Callable[[dict], Union[pgql_type.PGQL_Type, Any]], None]
        """
        return None


class PGQL_NoOp(PGQL_QueryNode):
    """Noop query class."""

    def as_document_node(self) -> DocumentNode:
        """Returns a gql DocumentNode ready to execute.

        This must be implemented in subclasses.
        """
        return None


class PGQL_Fragment(ABC):
    """Base Fragment class."""


class BaseSuiGQLClient:
    """Base GraphQL client."""

    _GRAPH_QL_SCHEMA: DSLSchema = None
    _SUI_GRAPHQL_MAINNET: str = "https://graphql-beta.mainnet.sui.io"
    _SUI_GRAPHQL_TESTNET: str = "https://graphql-beta.testnet.sui.io"

    @classmethod
    def _set_schema(cls, schema: DSLSchema) -> None:
        cls._GRAPH_QL_SCHEMA = schema

    def __init__(
        self,
        *,
        url_str: str,
        sui_config: SuiConfig,
        version: str,
        schema: GraphQLSchema,
        rpc_config: SuiConfigGQL,
    ):
        """."""
        self._url: str = url_str
        self._sui_config: SuiConfig = sui_config
        self._version: str = version
        self._rpc_config: SuiConfigGQL = rpc_config
        self._raw_schema: GraphQLSchema = schema
        self._set_schema(DSLSchema(schema))

    @property
    def config(self) -> SuiConfig:
        """Fetch the graphql client."""
        return self._sui_config

    @property
    def rpc_config(self) -> SuiConfigGQL:
        """Fetch the graphql configuration."""
        return self._rpc_config

    @property
    def url(self) -> str:
        """Fetch the active URL."""
        return self._url

    @property
    def chain_id(self) -> str:
        """Fetch the chain identifier."""
        return self._rpc_config.chainIdentifier

    @property
    def version(self) -> str:
        """Return the Sui GraphQL RPC Version

        :return: _description_
        :rtype: str
        """
        return self._version

    @property
    def schema(self) -> DSLSchema:
        """schema Return the DSLSchema for configuration

        :return: DSLSchema for Sui Schema version associated with connection.
        :rtype: DSLSchema
        """
        return self._GRAPH_QL_SCHEMA

    def _qnode_pre_run(self, qnode: PGQL_QueryNode) -> Union[DocumentNode, ValueError]:
        """."""
        if issubclass(type(qnode), PGQL_QueryNode):
            if hasattr(qnode, "owner"):
                resolved_owner = TypeValidator.check_owner(
                    getattr(qnode, "owner"), self.config
                )
                setattr(qnode, "owner", resolved_owner)
            dnode = qnode.as_document_node(self.schema)
            if isinstance(dnode, DocumentNode):
                return dnode
            else:
                ValueError("QueryNode did not produce a gql DocumentNode")
        else:
            raise ValueError("Not a valid PGQL_QueryNode")


class SuiGQLClient(BaseSuiGQLClient):
    """Synchronous pysui GraphQL client."""

    def __init__(
        self,
        *,
        write_schema: Optional[bool] = False,
        config: SuiConfig,
    ):
        """Sui GraphQL Client initializer."""
        gql_rpc_url: str = None

        match config.rpc_url:
            case cnst.MAINNET_SUI_URL:
                gql_rpc_url = self._SUI_GRAPHQL_MAINNET
            case cnst.TESTNET_SUI_URL:
                gpl_rpc_URL = self._SUI_GRAPHQL_TESTNET
            case _:
                raise ValueError(
                    f"Found {config.rpc_url}. URL must be mainnet or testnet sui url."
                )

        self._rpc_client: Client = Client(
            transport=RequestsHTTPTransport(
                # Url will be supplied from SuiConfig?
                url=gql_rpc_url,
                verify=True,
                retries=3,
            ),
            fetch_schema_from_transport=True,
        )

        with self._rpc_client as session:
            gql_version = session.transport.response_headers["x-sui-rpc-version"]
            # Enable/disable
            if write_schema:
                mver = "_".join(gql_version.split("."))
                fname = f"./latest_schema{mver}.graqhql"
                with open(fname, "w", encoding="utf8") as inner_file:
                    inner_file.write(print_schema(self._rpc_client.schema))

        rpc_config: SuiConfigGQL = None
        with self._rpc_client as session:
            qstr, fndeser = pgql_config()
            rpc_config = fndeser(session.execute(gql(qstr)))

        super().__init__(
            url_str=gql_rpc_url,
            sui_config=config,
            version=gql_version,
            schema=self._rpc_client.schema,
            rpc_config=rpc_config,
        )

    @property
    def client(self) -> Client:
        """Fetch the graphql client."""
        return self._rpc_client

    def execute_query(
        self,
        *,
        with_string: Optional[str] = None,
        with_document_node: Optional[DocumentNode] = None,
        with_query_node: Optional[PGQL_QueryNode] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> Any:
        """Executes a GraphQL query and returns raw result.

        with_string and with_document_node and with_query_node are mutually exclusive.
        with_string takes precedence, then with_document_node then with_query_node. If none is
        specific an error is returned.

        :param with_string: A python string query, defaults to None
        :type with_string: Optional[str], optional
        :param with_document_node: A gql DocumentNode query, defaults to None
        :type with_document_node: Optional[DocumentNode], optional
        :param with_query_node: A pysui GraphQL QueryNode, defaults to None
        :type with_query_node: Optional[PGQL_QueryNode], optional
        :param encode_fn: Encoding function taking dict as arg and returning Any, defaults to None
            This can be used on any 'with_' option. If used in addition to with_query_node it
            will override the builder property of same name if defined
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: Raw result (dict) or type returned defined by serialization function
        :rtype: Any
        """
        try:
            if with_string:
                if isinstance(with_string, str):
                    sres = self.client.execute(gql(with_string))
                    return SuiRpcResult(
                        True, None, sres if not encode_fn else encode_fn(sres)
                    )
                else:
                    raise ValueError("Expected a str for with_string argument.")
            elif with_document_node:
                if isinstance(with_document_node, DocumentNode):
                    dres = self.client.execute(with_document_node)
                    return SuiRpcResult(
                        True, None, dres if not encode_fn else encode_fn(dres)
                    )
                else:
                    raise ValueError("Not a valid gql DocumentNode")
            elif with_query_node:
                qdoc_node = self._qnode_pre_run(with_query_node)
                if isinstance(qdoc_node, PGQL_NoOp):
                    return pgql_type.NoopGQL.from_query()
                encode_fn = encode_fn or with_query_node.encode_fn()
                qres = self.client.execute(qdoc_node)
                return SuiRpcResult(
                    True, None, qres if not encode_fn else encode_fn(qres)
                )
            else:
                raise ValueError(
                    "Call requires python str, gql.DocumentNode, or PGQL_QueryNode types"
                )
        except texc.TransportQueryError as gte:
            return SuiRpcResult(
                False, "TransportQueryError", pgql_type.ErrorGQL.from_query(gte.errors)
            )
        except GraphQLSyntaxError as gqe:
            return SuiRpcResult(
                False,
                "GraphQLSyntaxError",
                pgql_type.ErrorGQL.from_query(gqe.formatted),
            )
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )


class AsyncSuiGQLClient(BaseSuiGQLClient):
    """Asynchronous pysui GraphQL client."""

    def __init__(
        self,
        *,
        write_schema: Optional[bool] = False,
        config: SuiConfig,
    ):
        """Async Sui GraphQL Client initializer."""
        gql_rpc_url: str = None
        match config.rpc_url:
            case cnst.MAINNET_SUI_URL:
                gql_rpc_url = self._SUI_GRAPHQL_MAINNET
            case cnst.TESTNET_SUI_URL:
                gpl_rpc_URL = self._SUI_GRAPHQL_TESTNET
            case _:
                raise ValueError(
                    f"Found {config.rpc_url}. URL must be mainnet or testnet sui url."
                )

        # Get sync client to populate all applicable properties
        s_client = SuiGQLClient(
            write_schema=write_schema,
            config=config,
        )

        # Create async client
        self._rpc_client: Client = Client(
            transport=AIOHTTPTransport(
                # Url will be supplied from SuiConfig?
                url=gql_rpc_url,
            ),
            schema=s_client._raw_schema,
        )

        # Initialize our base with copies of sync
        super().__init__(
            url_str=s_client.url,
            sui_config=s_client.config,
            version=s_client.version,
            schema=s_client._raw_schema,
            rpc_config=s_client.rpc_config,
        )

    @property
    def client(self) -> Client:
        """Fetch the graphql client."""
        return self._rpc_client

    async def execute_query(
        self,
        *,
        with_string: Optional[str] = None,
        with_document_node: Optional[DocumentNode] = None,
        with_query_node: Optional["PGQL_QueryNode"] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> dict:
        """Executes a GraphQL query and returns raw result.

        with_string and with_document_node and with_query_node are mutually exclusive.
        with_string takes precedence, then with_document_node then with_query_node. If none is
        specific an error is returned.

        :param with_string: A python string query, defaults to None
        :type with_string: Optional[str], optional
        :param with_document_node: A gql DocumentNode query, defaults to None
        :type with_document_node: Optional[DocumentNode], optional
        :param with_query_node: A pysui GraphQL QueryNode, defaults to None
        :type with_query_node: Optional[PGQL_QueryNode], optional
        :param encode_fn: Encode function taking dict as arg and returning Any, defaults to None
            This can be used on any 'with_' option. If used in addition to with_query_node it
            will override the builder property of same name if defined
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: Raw result (dict) or type returned defined by serialization function
        :rtype: Any
        """
        try:
            async with self.client as aclient:
                if with_string:
                    if isinstance(with_string, str):
                        sres = await aclient.execute(gql(with_string))
                        return SuiRpcResult(
                            True, None, sres if not encode_fn else encode_fn(sres)
                        )
                    else:
                        raise ValueError("Expected a str for with_string argument.")
                elif with_document_node:
                    if isinstance(with_document_node, DocumentNode):
                        dres = await aclient.execute(with_document_node)
                        return SuiRpcResult(
                            True, None, dres if not encode_fn else encode_fn(dres)
                        )
                    else:
                        raise ValueError("Not a valid gql DocumentNode")
                elif with_query_node:
                    qdoc_node = self._qnode_pre_run(with_query_node)
                    if isinstance(qdoc_node, PGQL_NoOp):
                        return pgql_type.NoopGQL.from_query()
                    encode_fn = encode_fn or with_query_node.encode_fn()
                    qres = await aclient.execute(qdoc_node)
                    return SuiRpcResult(
                        True, None, qres if not encode_fn else encode_fn(qres)
                    )
                else:
                    raise ValueError(
                        "Call requires python str, gql.DocumentNode, or PGQL_QueryNode types"
                    )
        except texc.TransportQueryError as gte:
            return SuiRpcResult(
                False, "TransportQueryError", pgql_type.ErrorGQL.from_query(gte.errors)
            )
        except GraphQLSyntaxError as gqe:
            return SuiRpcResult(
                False,
                "GraphQLSyntaxError",
                pgql_type.ErrorGQL.from_query(gqe.formatted),
            )
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )
