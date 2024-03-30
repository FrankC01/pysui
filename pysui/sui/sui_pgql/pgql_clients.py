#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL clients."""


from abc import ABC, abstractmethod
import logging
from typing import Callable, Any, Optional, Union
from deprecated.sphinx import versionchanged, versionadded, deprecated
from gql import Client, gql
import httpx

# TODO: Replace with HTTPX equivalents
from gql.transport.httpx import HTTPXTransport
from gql.transport.httpx import HTTPXAsyncTransport

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

# Standard library logging setup
logger = logging.getLogger("pysui.pgql_client")
if not logging.getLogger().handlers:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


class PGQL_QueryNode(ABC):
    """Base query class."""

    _SCHEMA_CONSTRAINT: str = None

    @property
    def schema_constraint(self) -> Union[str, None]:
        """Retreive schema constraint"""
        return self._SCHEMA_CONSTRAINT

    @schema_constraint.setter
    def schema_constraint(self, sc_name: str) -> None:
        """Set the schema constraint."""
        self._SCHEMA_CONSTRAINT = sc_name

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

    _SUI_GRAPHQL_MAINNET: str = "https://sui-mainnet.mystenlabs.com/graphql"
    _SUI_GRAPHQL_TESTNET: str = "https://sui-testnet.mystenlabs.com/graphql"
    _UNIQUE_VERSIONS: list[str] = ["2024_1_3-517d6c06d0707c458c0a66bd6ff9f341c472106c"]

    @classmethod
    def _resolve_url(cls, sui_config: SuiConfig) -> list[str, str]:
        """Resolve the GraphQL RPC Url."""
        match sui_config.rpc_url:
            case cnst.MAINNET_SUI_URL:
                url = cls._SUI_GRAPHQL_MAINNET
                env_prefix = "mainnet"
            case cnst.TESTNET_SUI_URL:
                url = cls._SUI_GRAPHQL_TESTNET
                env_prefix = "testnet"
            # Support QGL url configs
            case cls._SUI_GRAPHQL_MAINNET:
                url = cls._SUI_GRAPHQL_MAINNET
                env_prefix = "mainnet"
            case cls._SUI_GRAPHQL_TESTNET:
                url = cls._SUI_GRAPHQL_TESTNET
                env_prefix = "testnet"
            case _:
                raise ValueError(
                    f"Found {sui_config.rpc_url}. GraphQL URL is only active on testnet."
                )
        return [url, env_prefix]

    def __init__(
        self,
        *,
        sui_config: SuiConfig,
        gql_client: Client,
        version: str,
        schema: DSLSchema,
        rpc_config: SuiConfigGQL,
        write_schema: Optional[bool] = False,
    ):
        """."""

        self._sui_config: SuiConfig = sui_config
        self._inner_client: Client = gql_client
        self._url: str = gql_client.transport.url
        self._version: str = version
        self._schema: DSLSchema = schema
        self._rpc_config: SuiConfigGQL = rpc_config
        mver = "_".join(self._version.split("."))
        # TODO: When Sui begins maintaining earlier versions
        # this will effect query choices, etc.
        if write_schema:
            fname = f"./{self._rpc_config.gqlEnvironment}_schema-{mver}.graphql"
            with open(fname, "w", encoding="utf8") as inner_file:
                inner_file.write(print_schema(self._inner_client.schema))
        elif mver not in self._UNIQUE_VERSIONS:
            print(f"New version not recognized {mver}")

    @property
    def config(self) -> SuiConfig:
        """Fetch the graphql client."""
        return self._sui_config

    @property
    def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        return int(self._rpc_config.checkpoints.nodes[0].reference_gas_price)

    @property
    def rpc_config(self) -> SuiConfigGQL:
        """Fetch the graphql configuration."""
        return self._rpc_config

    @property
    def protocol(self) -> pgql_type.TransactionConstraints:
        """Fetch the protocol constraint block."""
        return self.rpc_config.protocolConfig

    @property
    def url(self) -> str:
        """Fetch the active GraphQL URL."""
        return self._url

    @property
    def client(self) -> Client:
        """Fetch the graphql client."""
        return self._inner_client

    @property
    def chain_id(self) -> str:
        """Fetch the chain identifier."""
        return self._rpc_config.chainIdentifier

    @property
    def chain_environment(self) -> str:
        """Fetch which environment (testnet, devenet) operating with."""
        return self._rpc_config.gqlEnvironment

    @property
    def schema_version(self) -> str:
        """Return Sui GraphQL schema version."""
        return self._version

    @property
    def schema(self) -> DSLSchema:
        """schema Return the DSLSchema for configuration

        :return: DSLSchema for Sui Schema version associated with connection.
        :rtype: DSLSchema
        """
        return self._schema

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
                raise ValueError("QueryNode did not produce a gql DocumentNode")
        else:
            raise ValueError("Not a valid PGQL_QueryNode")


class SuiGQLClient(BaseSuiGQLClient):
    """Synchronous pysui GraphQL client."""

    def __init__(
        self,
        *,
        config: SuiConfig,
        write_schema: Optional[bool] = False,
    ):
        """Sui GraphQL Client initializer."""
        # Resolve GraphQL URL
        gurl, genv = BaseSuiGQLClient._resolve_url(config)
        # Build Sync Client
        _iclient: Client = Client(
            transport=HTTPXTransport(
                url=gurl,
                verify=True,
            ),
            fetch_schema_from_transport=True,
        )
        with _iclient as session:
            _version: str = session.transport.response_headers["x-sui-rpc-version"]
            _schema: DSLSchema = DSLSchema(_iclient.schema)
            qstr, fndeser = pgql_config()
            _rpc_config = fndeser(session.execute(gql(qstr)))
            _rpc_config.gqlEnvironment = genv

        super().__init__(
            sui_config=config,
            gql_client=_iclient,
            version=_version,
            schema=_schema,
            rpc_config=_rpc_config,
            write_schema=write_schema,
        )

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    def _execute(
        self,
        node: DocumentNode,
        schema_constraint: Optional[Union[str, None]],
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node

        :param node: GQL DocumentNode
        :type node: DocumentNode
        :param schema_constraint: Should run against specific schema
        :type schema_constraint: Optional[Union[str, None]]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            sres = self.client.execute(node)
            return SuiRpcResult(True, None, sres if not encode_fn else encode_fn(sres))

        except texc.TransportQueryError as gte:
            return SuiRpcResult(
                False, "TransportQueryError", pgql_type.ErrorGQL.from_query(gte.errors)
            )
        except (
            httpx.HTTPError,
            httpx.InvalidURL,
            httpx.CookieConflict,
        ) as hexc:
            return SuiRpcResult(
                False, f"HTTPX error: {hexc.__class__.__name__}", vars(hexc)
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

    @versionadded(version="0.56.0", reason="Unique function for string processing")
    def execute_query_string(
        self,
        *,
        string: str,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(string, str):
            return self._execute(gql(string), schema_constraint, encode_fn)
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for DocumentNode processing"
    )
    def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(with_node, DocumentNode):
            return self._execute(with_node, schema_constraint, encode_fn)
        else:
            return SuiRpcResult(False, "Not a valid gql DocumentNode", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        try:
            qdoc_node = self._qnode_pre_run(with_node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return self._execute(qdoc_node, schema_constraint, encode_fn)
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )

    @deprecated(
        version="0.56.0",
        reason="Use explicit execute for type (str,DocumentNode,PGQL_QueryNode. This will be deleted in version 0.60.0)",
    )
    def execute_query(
        self,
        *,
        with_string: Optional[str] = None,
        with_document_node: Optional[DocumentNode] = None,
        with_query_node: Optional[PGQL_QueryNode] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
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
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """

        if with_string:
            return self.execute_query_string(string=with_string, encode_fn=encode_fn)
        elif with_document_node:
            return self.execute_document_node(
                with_node=with_document_node, encode_fn=encode_fn
            )
        elif with_query_node:
            return self.execute_query_node(
                with_node=with_query_node, encode_fn=encode_fn
            )
        return SuiRpcResult(
            False,
            "Call requires python str, gql.DocumentNode, or PGQL_QueryNode types",
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
        gurl, genv = BaseSuiGQLClient._resolve_url(config)

        _iclient: Client = Client(
            transport=HTTPXTransport(
                url=gurl,
                verify=True,
            ),
            fetch_schema_from_transport=True,
        )
        with _iclient as session:
            _version: str = session.transport.response_headers["x-sui-rpc-version"]
            _schema: DSLSchema = DSLSchema(_iclient.schema)
            qstr, fndeser = pgql_config()
            _rpc_config = fndeser(session.execute(gql(qstr)))
            _rpc_config.gqlEnvironment = genv

        super().__init__(
            sui_config=config,
            gql_client=Client(
                transport=HTTPXAsyncTransport(
                    url=gurl,
                ),
                fetch_schema_from_transport=True,
            ),
            version=_version,
            schema=_schema,
            rpc_config=_rpc_config,
            write_schema=write_schema,
        )

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    async def _execute(
        self,
        node: DocumentNode,
        schema_constraint: Optional[Union[str, None]],
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node

        :param node: GQL DocumentNode
        :type node: DocumentNode
        :param schema_constraint: Should run against specific schema
        :type schema_constraint: Optional[Union[str, None]]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            async with self.client as aclient:
                sres = await aclient.execute(node)
                return SuiRpcResult(
                    True, None, sres if not encode_fn else encode_fn(sres)
                )

        except texc.TransportQueryError as gte:
            return SuiRpcResult(
                False, "TransportQueryError", pgql_type.ErrorGQL.from_query(gte.errors)
            )
        except (
            httpx.HTTPError,
            httpx.InvalidURL,
            httpx.CookieConflict,
        ) as hexc:
            return SuiRpcResult(
                False, f"HTTPX error: {hexc.__class__.__name__}", vars(hexc)
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

    @versionadded(version="0.56.0", reason="Unique function for string processing")
    async def execute_query_string(
        self,
        *,
        string: str,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(string, str):
            return await self._execute(gql(string), schema_constraint, encode_fn)
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for DocumentNode processing"
    )
    async def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(with_node, DocumentNode):
            return await self._execute(with_node, schema_constraint, encode_fn)
        else:
            return SuiRpcResult(False, "Not a valid gql DocumentNode", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    async def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        schema_constraint: Optional[Union[str, None]] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        try:
            qdoc_node = self._qnode_pre_run(with_node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return await self._execute(qdoc_node, schema_constraint, encode_fn)
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )

    @deprecated(
        version="0.56.0",
        reason="Use explicit execute for type (str,DocumentNode,PGQL_QueryNode. This will be deleted in version 0.60.0)",
    )
    async def execute_query(
        self,
        *,
        with_string: Optional[str] = None,
        with_document_node: Optional[DocumentNode] = None,
        with_query_node: Optional[PGQL_QueryNode] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
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
        if with_string:
            return await self.execute_query_string(
                schema_constraint=with_string, encode_fn=encode_fn
            )
        elif with_document_node:
            return await self.execute_document_node(
                with_node=with_document_node, encode_fn=encode_fn
            )
        elif with_query_node:
            return await self.execute_query_node(
                with_node=with_query_node, encode_fn=encode_fn
            )
        return SuiRpcResult(
            False,
            "Call requires python str, gql.DocumentNode, or PGQL_QueryNode types",
        )
