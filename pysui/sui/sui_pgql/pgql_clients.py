#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL clients."""


from abc import ABC, abstractmethod
import logging
import asyncio
from time import sleep
from typing import Callable, Any, Optional, Union
from deprecated.sphinx import versionchanged, versionadded
from gql import Client, gql
from gql.client import ReconnectingAsyncClientSession
from gql.transport import exceptions as texc
from gql.dsl import (
    DSLSchema,
)
from graphql import DocumentNode, print_ast
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.utilities.print_schema import print_schema
from graphql.language.printer import print_ast

import httpx

from pysui import SuiRpcResult, PysuiConfiguration
from pysui.sui.sui_pgql.pgql_validators import TypeValidator
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_pgql.pgql_configs import SuiConfigGQL
import pysui.sui.sui_pgql.pgql_schema as scm

# Standard library logging setup
logger = logging.getLogger("pgql_client")


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


@versionchanged(
    version="0.64.0",
    reason="BREAKING previous properteries now take schema version option",
)
class BaseSuiGQLClient:
    """Base GraphQL client."""

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
            def_env = self._schema.rpc_config.gqlEnvironment
            def_schm = self._schema.dsl_schema
            fname = f"./{def_env}_schema-{self._schema.build_version}.graphql"
            with open(fname, "w", encoding="utf8") as inner_file:
                inner_file.write(print_schema(getattr(def_schm, "_schema")))

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    @property
    def config(self) -> PysuiConfiguration:
        """Fetch the Pysui configuration."""
        return self._pysui_config

    def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        return self._schema.rpc_config.checkpoints.nodes[0].reference_gas_price

    def rpc_config(self) -> SuiConfigGQL:
        """Fetch the graphql configuration."""
        return self._schema.rpc_config

    def protocol(
        self, for_version: Optional[str] = None
    ) -> pgql_type.TransactionConstraints:
        """Fetch the protocol constraint block."""
        return self._schema.rpc_config.protocolConfig

    def url(self) -> str:
        """Fetch the active GraphQL URL."""
        return self._schema._graph_url

    def client(self) -> Client:
        """Fetch the graphql client."""
        return self._schema.client

    async def async_client(self) -> ReconnectingAsyncClientSession:
        """Fetch the graphql async client."""
        return await self._schema.async_session

    def chain_id(self, for_version: Optional[str] = None) -> str:
        """Fetch the chain identifier."""
        return self.rpc_config(for_version).chainIdentifier

    @property
    def chain_environment(self) -> str:
        """Fetch which environment (testnet, devenet) operating with."""
        return self.rpc_config().gqlEnvironment

    def schema_version(self, for_version: Optional[str] = None) -> str:
        """Returns Sui GraphQL schema long version."""
        return self._schema.build_version

    @property
    def base_schema_version(self) -> str:
        """Returns the default schema version (schema version without patch)"""
        return self._schema.base_version

    def schema(self) -> DSLSchema:
        """Return the specific DSLSchema for configuration"""
        return self._schema.dsl_schema

    def _qnode_owner(self, qnode: PGQL_QueryNode):
        """."""
        if hasattr(qnode, "owner"):
            resolved_owner = TypeValidator.check_owner(
                getattr(qnode, "owner"), self.config
            )
            setattr(qnode, "owner", resolved_owner)

    def _qnode_pre_run(self, qnode: PGQL_QueryNode) -> Union[DocumentNode, ValueError]:
        """."""
        if issubclass(type(qnode), PGQL_QueryNode):
            self._qnode_owner(qnode)
            dnode = qnode.as_document_node(self.schema())
            if isinstance(dnode, DocumentNode):
                return dnode
            else:
                raise ValueError("QueryNode did not produce a gql DocumentNode")
        else:
            raise ValueError("Not a valid PGQL_QueryNode")

    @versionadded(version="0.60.0", reason="Support query inspection")
    def query_node_to_string(self, *, query_node: PGQL_QueryNode) -> str:
        """."""
        self._qnode_owner(query_node)
        return print_ast(query_node.as_document_node(self.schema()))


class SuiGQLClient(BaseSuiGQLClient):
    """Synchronous pysui GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """Sui GraphQL Client initializer."""
        gurl = pysui_config.url
        genv = pysui_config.active_profile
        # gurl, genv = BaseSuiGQLClient._resolve_url(config, schema_version)
        super().__init__(
            pysui_config=pysui_config,
            schema=scm.Schema(gql_url=gurl, gql_env=genv),
            write_schema=write_schema,
            default_header=default_header,
        )

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    def _execute(
        self,
        node: DocumentNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node

        :param node: GQL DocumentNode
        :type node: DocumentNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            sres = self.client().execute(
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
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """execute_query_string Executes a GraphQL query string.

        :param string: Well formed GraphQL query string
        :type string: str
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(string, str):
            return self._execute(gql(string), with_headers, encode_fn)
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for DocumentNode processing"
    )
    def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """execute_document_node Executes a gql DocumentNode.

        :param with_node: The gql GraphQL DocumentNode
        :type with_node: DocumentNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(with_node, DocumentNode):
            return self._execute(with_node, with_headers, encode_fn)
        else:
            return SuiRpcResult(False, "Not a valid gql DocumentNode", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """execute_query_node Execute a pysui GraphQL QueryNode.

        :param with_node: The QueryNode for execution
        :type with_node: PGQL_QueryNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            qdoc_node = self._qnode_pre_run(with_node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return self._execute(qdoc_node, with_headers, encode_fn)
        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )

    @versionadded(version="0.75.0", reason="Execution of transaction changes.")
    def wait_for_transaction(
        self, *, digest: str, timeout: int = 60, poll_interval: int = 2
    ) -> SuiRpcResult:
        """wait_for_transaction Wait for a transaction block result to be available over the API.

        :param digest: The digest of the transaction to get effects on
        :type digest: str
        :param timeout: timeout interval in seconds, defaults to 60
        :type timeout: int, optional
        :param poll_interval: poll interval wait in seconds, defaults to 2
        :type poll_interval: int, optional
        :raises Exception: If effects are not retrieved
        :return: Standard Sui Result
        :rtype: SuiRpcResult
        """
        import pysui.sui.sui_pgql.pgql_query as qn

        total_poll = 0
        while True:
            logging.info(f"Polling {digest} for {total_poll} times")
            res = self.execute_query_node(with_node=qn.GetTx(digest=digest))
            if res.is_ok() and not isinstance(res.result_data, pgql_type.NoopGQL):
                return res
            total_poll += poll_interval
            if total_poll < timeout:
                logging.info("Sleeping")
                sleep(poll_interval)
            else:
                raise ValueError("Timeout error while waiting for transaction block.")


class AsyncSuiGQLClient(BaseSuiGQLClient):
    """Asynchronous pysui GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
    ):
        """Async Sui GraphQL Client initializer."""
        scm_mgr: scm.Schema = scm.Schema(
            gql_url=pysui_config.url, gql_env=pysui_config.active_profile
        )
        scm_mgr.set_async_client()

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
        await self._schema._async_client.close_async()
        # aclient = self.async_client()
        # await aclient.close_async()

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    async def _execute(
        self,
        node: DocumentNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node.

        :param node: GQL DocumentNode
        :type node: DocumentNode
        :param with_headers: Add extra arguments for http client headers
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            async with self._slock:
                _session = await self.async_client()
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
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """execute_query_string Executes a GraphQL query string.

        :param string: Well formed GraphQL query string
        :type string: str
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(string, str):
            return await self._execute(gql(string), with_headers, encode_fn)
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for DocumentNode processing"
    )
    async def execute_document_node(
        self,
        *,
        with_node: DocumentNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """execute_document_node Executes a gql DocumentNode.

        :param with_node: The gql GraphQL DocumentNode
        :type with_node: DocumentNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(with_node, DocumentNode):
            return await self._execute(with_node, with_headers, encode_fn)
        else:
            return SuiRpcResult(False, "Not a valid gql DocumentNode", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    async def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
    ) -> SuiRpcResult:
        """execute_query_node Execute a pysui GraphQL QueryNode.

        :param with_node: The QueryNode for execution
        :type with_node: PGQL_QueryNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            qdoc_node = self._qnode_pre_run(with_node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return await self._execute(qdoc_node, with_headers, encode_fn)

        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )

    @versionadded(version="0.73.0", reason="Execution of transaction changes.")
    async def wait_for_transaction(
        self, *, digest: str, timeout: int = 60, poll_interval: int = 2
    ) -> SuiRpcResult:
        """wait_for_transaction Wait for a transaction block result to be available over the API.

        :param digest: The digest of the transaction to get effects on
        :type digest: str
        :param timeout: timeout interval in seconds, defaults to 60
        :type timeout: int, optional
        :param poll_interval: poll interval wait in seconds, defaults to 2
        :type poll_interval: int, optional
        :raises Exception: If effects are not retrieved
        :return: Standard Sui Result
        :rtype: SuiRpcResult
        """
        import pysui.sui.sui_pgql.pgql_query as qn

        total_poll = 0
        while True:
            logging.info(f"Polling {digest} for {total_poll} times")
            res = await self.execute_query_node(with_node=qn.GetTx(digest=digest))
            if res.is_ok() and not isinstance(res.result_data, pgql_type.NoopGQL):
                return res
            total_poll += poll_interval
            if total_poll < timeout:
                logging.info("Sleeping")
                await asyncio.sleep(poll_interval)
            else:
                raise ValueError("Timeout error while waiting for transaction block.")
