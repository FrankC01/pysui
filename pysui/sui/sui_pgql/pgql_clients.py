#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL clients."""


from abc import ABC, abstractmethod
import logging
import asyncio
from typing import Callable, Any, Optional, Union
from deprecated.sphinx import versionchanged, versionadded, deprecated
from gql import Client, gql
import httpx

from gql.transport.httpx import HTTPXTransport
from gql.transport.httpx import HTTPXAsyncTransport

from gql.transport import exceptions as texc
from gql.dsl import (
    DSLSchema,
)
from graphql import DocumentNode, print_ast, GraphQLSchema
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.utilities.print_schema import print_schema
from graphql.language.printer import print_ast


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
    def schema_constraint(self, sc_version: str) -> None:
        """schema_constraint Sets the schema version constraint on the QueryNode.

        The content of the string must be `YYYY.MAJOR.MINOR` (e.g. '2024.2.0')

        :param sc_version: The schema version to constrain the query to.
        :type sc_version: str
        """
        self._SCHEMA_CONSTRAINT = sc_version

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

    # TODO: Move these to constants
    _SUI_GRAPHQL_MAINNET: str = "https://sui-mainnet.mystenlabs.com/graphql"
    _SUI_GRAPHQL_TESTNET: str = "https://sui-testnet.mystenlabs.com/graphql"
    _SUI_GRAPHQL_DEVNET: str = "https://sui-devnet.mystenlabs.com/graphql/stable"
    _SCHEMA_HEADER_KEY: str = "X-Sui-RPC-Version"

    @classmethod
    def _resolve_url(
        cls, sui_config: SuiConfig, schema_version: Optional[str] = None
    ) -> list[str, str]:
        """Resolve the GraphQL RPC Url."""
        check_url = (
            sui_config.graphql_url if sui_config.graphql_url else sui_config.rpc_url
        )
        match check_url:
            case cnst.MAINNET_SUI_URL:
                url = cls._SUI_GRAPHQL_MAINNET
                env_prefix = "mainnet"
            case cnst.TESTNET_SUI_URL:
                url = cls._SUI_GRAPHQL_TESTNET
                env_prefix = "testnet"
            case cnst.DEVNET_SUI_URL:
                url = cls._SUI_GRAPHQL_DEVNET
                env_prefix = "devnet"
            # Support QGL url configs
            case cls._SUI_GRAPHQL_MAINNET:
                url = check_url
                env_prefix = "mainnet"
            case cls._SUI_GRAPHQL_TESTNET:
                url = check_url
                env_prefix = "testnet"
            case cls._SUI_GRAPHQL_DEVNET:
                url = check_url
                env_prefix = "devnet"
            case _:
                raise ValueError(f"Can not resolve {check_url} to GraphQL RPC host.")
        # TODO: When schema versions are in effect, review return
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
        default_header: Optional[dict] = None,
    ):
        """."""

        self._sui_config: SuiConfig = sui_config
        self._inner_client: Client = gql_client
        self._url: str = gql_client.transport.url
        self._version: str = version
        self._base_version = version[: version.index("-")]
        self._schema: DSLSchema = schema
        self._rpc_config: SuiConfigGQL = rpc_config
        self._default_header = default_header if default_header else {"headers": None}
        # Schema persist
        if write_schema:
            fname = f"./{self._rpc_config.gqlEnvironment}_schema-{version}.graphql"
            with open(fname, "w", encoding="utf8") as inner_file:
                inner_file.write(print_schema(self._inner_client.schema))

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
    def base_schema_version(self) -> str:
        """Returns the header version (schema version without patch)"""
        return self._base_version

    @property
    def client_headers(self) -> dict:
        return self._default_header.copy()

    @property
    def schema(self) -> DSLSchema:
        """schema Return the DSLSchema for configuration

        :return: DSLSchema for Sui Schema version associated with connection.
        :rtype: DSLSchema
        """
        return self._schema

    def _qnode_owner(self, qnode: PGQL_QueryNode):
        """."""
        if hasattr(qnode, "owner"):
            resolved_owner = TypeValidator.check_owner(
                getattr(qnode, "owner"), self.config
            )
            setattr(qnode, "owner", resolved_owner)

    def _qnode_pre_run(
        self, qnode: PGQL_QueryNode, schema_constraint: Union[str, None] = None
    ) -> Union[DocumentNode, ValueError]:
        """."""
        if issubclass(type(qnode), PGQL_QueryNode):
            self._qnode_owner(qnode)
            # TODO If schema constrained than pass the correct schema
            # to the document builder
            if qnode.schema_constraint:
                pass
            dnode = qnode.as_document_node(self.schema)
            if isinstance(dnode, DocumentNode):
                return dnode, qnode.schema_constraint
            else:
                raise ValueError("QueryNode did not produce a gql DocumentNode")
        else:
            raise ValueError("Not a valid PGQL_QueryNode")

    @versionadded(version="0.60.0", reason="Support query inspection")
    def query_node_to_string(
        self, qnode: PGQL_QueryNode, schema_constraint: Union[str, None] = None
    ) -> str:
        """."""
        self._qnode_owner(qnode)
        return print_ast(qnode.as_document_node(self.schema))


class SuiGQLClient(BaseSuiGQLClient):
    """Synchronous pysui GraphQL client."""

    def __init__(
        self,
        *,
        config: SuiConfig,
        schema_version: Optional[str] = None,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """Sui GraphQL Client initializer."""
        # Resolve GraphQL URL
        gurl, genv = BaseSuiGQLClient._resolve_url(config, schema_version)
        # Build Sync Client
        _iclient: Client = Client(
            transport=HTTPXTransport(
                url=gurl,
                verify=True,
                http2=True,
                timeout=120.0,
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
            default_header=default_header,
        )

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    def _execute(
        self,
        node: DocumentNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node

        :param node: GQL DocumentNode
        :type node: DocumentNode
        :param schema_constraint: Should run against specific schema
        :type schema_constraint: Optional[str]
        :param with_headers: Add extra arguments for http client headers
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            # hdr = {}
            hdr = self.client_headers
            hdr = hdr if not with_headers else hdr.update(with_headers)
            sres = self.client.execute(node, extra_args=hdr)
            return SuiRpcResult(True, None, sres if not encode_fn else encode_fn(sres))

        except texc.TransportQueryError as gte:
            return SuiRpcResult(
                False,
                f"TransportQueryError {gte.errors}",
                pgql_type.ErrorGQL.from_query(gte.errors),
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
        except TypeError as te:
            return SuiRpcResult(
                False, "TypeError", pgql_type.ErrorGQL.from_query(te.args)
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
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(string, str):
            return self._execute(
                gql(string), schema_constraint, with_headers, encode_fn
            )
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for DocumentNode processing"
    )
    def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(with_node, DocumentNode):
            return self._execute(with_node, schema_constraint, with_headers, encode_fn)
        else:
            return SuiRpcResult(False, "Not a valid gql DocumentNode", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        try:
            qdoc_node, _sc_constraint = self._qnode_pre_run(
                with_node, schema_constraint
            )
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return self._execute(qdoc_node, schema_constraint, with_headers, encode_fn)
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )


class AsyncSuiGQLClient(BaseSuiGQLClient):
    """Asynchronous pysui GraphQL client."""

    def __init__(
        self,
        *,
        config: SuiConfig,
        schema_version: Optional[str] = None,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """Async Sui GraphQL Client initializer."""
        gurl, genv = BaseSuiGQLClient._resolve_url(config, schema_version)

        _iclient: Client = Client(
            transport=HTTPXTransport(
                url=gurl,
                verify=True,
                http2=True,
                timeout=120.0,
            ),
            fetch_schema_from_transport=True,
        )
        with _iclient as session:
            _version: str = session.transport.response_headers["x-sui-rpc-version"]
            _schema: DSLSchema = DSLSchema(_iclient.schema)
            qstr, fndeser = pgql_config()
            _rpc_config = fndeser(session.execute(gql(qstr)))
            _rpc_config.gqlEnvironment = genv
        _iclient.close_sync()

        super().__init__(
            sui_config=config,
            gql_client=Client(
                transport=HTTPXAsyncTransport(
                    url=gurl,
                    verify=True,
                    http2=True,
                    timeout=120.0,
                ),
                fetch_schema_from_transport=True,
            ),
            version=_version,
            schema=_schema,
            rpc_config=_rpc_config,
            write_schema=write_schema,
            default_header=default_header,
        )
        self._session = None
        self._slock = asyncio.Semaphore()

    @property
    def session(self) -> Any:
        return self._session

    async def close(self) -> None:
        """Close the connection."""
        await self.client.close_async()

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    async def _execute(
        self,
        node: DocumentNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node

        :param node: GQL DocumentNode
        :type node: DocumentNode
        :param schema_constraint: Should run against specific schema
        :type schema_constraint: Optional[Union[str, None]]
        :param with_headers: Add extra arguments for http client headers
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            async with self._slock:
                if not self.session:
                    self._session = await self.client.connect_async(reconnecting=True)
                hdr = self.client_headers
                hdr = hdr if not with_headers else hdr.update(with_headers)
                sres = await self.session.execute(node, extra_args=hdr)
                return SuiRpcResult(
                    True, None, sres if not encode_fn else encode_fn(sres)
                )
            # async with self.client as aclient:
            #     sres = await aclient.execute(node, extra_args=hdr)
            #     return SuiRpcResult(
            #         True, None, sres if not encode_fn else encode_fn(sres)
            #     )

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
        except TypeError as te:
            return SuiRpcResult(
                False, "TypeError", pgql_type.ErrorGQL.from_query(te.args)
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
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(string, str):
            return await self._execute(
                gql(string), schema_constraint, with_headers, encode_fn
            )
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for DocumentNode processing"
    )
    async def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        if isinstance(with_node, DocumentNode):
            return await self._execute(
                with_node, schema_constraint, with_headers, encode_fn
            )
        else:
            return SuiRpcResult(False, "Not a valid gql DocumentNode", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    async def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        schema_constraint: Optional[str] = None,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """."""
        try:
            qdoc_node, _sc_constraint = self._qnode_pre_run(
                with_node, schema_constraint
            )
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return await self._execute(
                qdoc_node, schema_constraint, with_headers, encode_fn
            )
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )
