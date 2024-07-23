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
from gql.client import ReconnectingAsyncClientSession

import httpx

from gql.transport.httpx import HTTPXAsyncTransport

from gql.transport import exceptions as texc
from gql.dsl import (
    DSLSchema,
)
from graphql import DocumentNode, print_ast
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.utilities.print_schema import print_schema
from graphql.language.printer import print_ast

# from graphql.language.printer import print_ast


from pysui import SuiConfig, SuiRpcResult, PysuiConfiguration
from pysui.sui.sui_pgql.pgql_validators import TypeValidator
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_pgql.pgql_configs import pgql_config, SuiConfigGQL
import pysui.sui.sui_pgql.pgql_schema as scm
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


@versionchanged(
    version="0.64.0",
    reason="BREAKING previous properteries now take schema version option",
)
class BaseSuiGQLClient:
    """Base GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        schema: scm.Schema,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """."""

        self._pysui_config: PysuiConfiguration = pysui_config
        self._schema: scm.Schema = schema
        self._default_header = default_header if default_header else {}
        # Schema persist
        if write_schema:
            def_config: dict[str, Any] = schema.schema_set[schema.default_version]
            def_env = def_config[scm.Schema.RPC_CFG].gqlEnvironment
            def_schm = def_config[scm.Schema.DSCHEMA]
            fname = f"./{def_env}_schema-{def_config[scm.Schema.BUILD]}.graphql"
            with open(fname, "w", encoding="utf8") as inner_file:
                inner_file.write(print_schema(getattr(def_schm, "_schema")))

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    @property
    def config(self) -> PysuiConfiguration:
        """Fetch the Pysui configuration."""
        return self._pysui_config

    def current_gas_price(self, for_version: Optional[str] = None) -> int:
        """Fetch the current epoch gas price."""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]
        return int(
            def_config[scm.Schema.RPC_CFG].checkpoints.nodes[0].reference_gas_price
        )

    def rpc_config(self, for_version: Optional[str] = None) -> SuiConfigGQL:
        """Fetch the graphql configuration."""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]
        return def_config[scm.Schema.RPC_CFG]

    def protocol(
        self, for_version: Optional[str] = None
    ) -> pgql_type.TransactionConstraints:
        """Fetch the protocol constraint block."""
        def_config = self.rpc_config(for_version)
        return def_config.protocolConfig

    def url(self, for_version: Optional[str] = None) -> str:
        """Fetch the active GraphQL URL."""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]
        return def_config[scm.Schema.GURL]

    def client(self, for_version: Optional[str] = None) -> Client:
        """Fetch the graphql client."""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]
        return def_config[scm.Schema.GCLIENT]

    async def async_client(
        self, for_version: Optional[str] = None
    ) -> ReconnectingAsyncClientSession:
        """Fetch the graphql async client."""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]
        if session := def_config.get(scm.Schema.ASYNCSESS):
            return session
        def_config[scm.Schema.ASYNCSESS] = await def_config[
            scm.Schema.GCLIENT
        ].connect_async(reconnecting=True)
        return def_config[scm.Schema.ASYNCSESS]

    def chain_id(self, for_version: Optional[str] = None) -> str:
        """Fetch the chain identifier."""
        return self.rpc_config(for_version).chainIdentifier

    @property
    def chain_environment(self) -> str:
        """Fetch which environment (testnet, devenet) operating with."""
        return self.rpc_config().gqlEnvironment

    def schema_version(self, for_version: Optional[str] = None) -> str:
        """Returns Sui GraphQL schema long version."""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]

        return def_config[scm.Schema.BUILD]

    @property
    def base_schema_version(self) -> str:
        """Returns the default schema version (schema version without patch)"""
        return self._schema.default_version

    def schema(self, for_version: Optional[str] = None) -> DSLSchema:
        """Return the specific DSLSchema for configuration"""
        def_config: dict[str, Any] = self._schema.schema_set[
            for_version or self._schema.default_version
        ]
        return def_config[scm.Schema.DSCHEMA]

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
            dnode_sc = qnode.schema_constraint
            dnode_sc = dnode_sc or schema_constraint
            dnode = qnode.as_document_node(self.schema(dnode_sc))
            if isinstance(dnode, DocumentNode):
                return dnode, dnode_sc
            else:
                raise ValueError("QueryNode did not produce a gql DocumentNode")
        else:
            raise ValueError("Not a valid PGQL_QueryNode")

    @versionadded(version="0.60.0", reason="Support query inspection")
    def query_node_to_string(
        self, *, query_node: PGQL_QueryNode, schema_constraint: Union[str, None] = None
    ) -> str:
        """."""
        self._qnode_owner(query_node)
        return print_ast(query_node.as_document_node(self.schema(schema_constraint)))


class SuiGQLClient(BaseSuiGQLClient):
    """Synchronous pysui GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        schema_version: Optional[str] = None,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """Sui GraphQL Client initializer."""
        gurl = pysui_config.url
        genv = pysui_config.active_env
        # gurl, genv = BaseSuiGQLClient._resolve_url(config, schema_version)
        super().__init__(
            pysui_config=pysui_config,
            schema=scm.load_schema_cache(gurl, genv, schema_version),
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
            sres = self.client(schema_constraint).execute(
                node, extra_args=with_headers or self._default_header
            )
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
        except (Exception, ValueError) as ve:
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

            return self._execute(qdoc_node, _sc_constraint, with_headers, encode_fn)
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )


class AsyncSuiGQLClient(BaseSuiGQLClient):
    """Asynchronous pysui GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        schema_version: Optional[str] = None,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """Async Sui GraphQL Client initializer."""
        gurl = pysui_config.url
        genv = pysui_config.active_env
        scm_mgr: scm.Schema = scm.load_schema_cache(gurl, genv, schema_version)
        for _sver, sblock in scm_mgr.schema_set.items():
            sblock[scm.Schema.GCLIENT].close_sync()
            sblock[scm.Schema.GCLIENT] = Client(
                transport=HTTPXAsyncTransport(
                    url=sblock[scm.Schema.GURL],
                    verify=True,
                    http2=True,
                    timeout=120.0,
                ),
            )
        super().__init__(
            pysui_config=pysui_config,
            schema=scm_mgr,
            write_schema=write_schema,
            default_header=default_header,
        )
        self._slock = asyncio.Semaphore()

    @property
    def session(self) -> Any:
        return self._session

    async def close(self) -> None:
        """Close the connection."""
        aclient = self.client()
        await aclient.close_async()

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
                _session = await self.async_client(for_version=schema_constraint)
                sres = await _session.execute(
                    node, extra_args=with_headers or self._default_header
                )

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
            httpx.UnsupportedProtocol,
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
                qdoc_node, _sc_constraint, with_headers, encode_fn
            )

        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )
