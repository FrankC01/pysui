#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL clients."""


from abc import ABC, abstractmethod
import logging
import asyncio
from time import sleep
from typing import Callable, Any, Optional, Union
from deprecated.sphinx import versionchanged, versionadded, deprecated

from gql import Client, gql, GraphQLRequest
from gql.client import ReconnectingAsyncClientSession
from gql.transport import exceptions as texc
from gql.dsl import (
    DSLSchema,
)

from graphql import GraphQLError, print_ast
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.utilities.print_schema import print_schema
from graphql.language.printer import print_ast

import httpx

from pysui import SuiRpcResult, PysuiConfiguration
from pysui.sui.sui_common.client import PysuiClient
from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.sui_command import SuiCommand
from pysui.sui.sui_pgql.pgql_validators import TypeValidator
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_pgql.pgql_configs import SuiConfigGQL
import pysui.sui.sui_pgql.pgql_schema as scm

# Standard library logging setup
logger = logging.getLogger("pgql_client")


class PGQL_QueryNode(ABC):
    """Base query class."""

    @abstractmethod
    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Returns a gql GraphQLRequest ready to execute.

        This must be implemented in subclasses.

        :param schema: The current Sui GraphQL schema
        :type schema: DSLSchema
        :return: A query processed into a gql GraphQLRequest
        :rtype: GraphQLRequest
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

    def as_document_node(self) -> GraphQLRequest:
        """Returns a gql GraphQLRequest ready to execute.

        This must be implemented in subclasses.
        """
        return None


class PGQL_Fragment(ABC):
    """Base Fragment class."""


@versionchanged(
    version="0.64.0",
    reason="BREAKING previous properteries now take schema version option",
)
class BaseSuiGQLClient(PysuiClient):
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

        super().__init__(pysui_config=pysui_config, default_header=default_header)
        self._schema: scm.Schema = schema

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
    def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        return self._schema.rpc_config.checkpoint.reference_gas_price

    def rpc_config(self) -> SuiConfigGQL:
        """Fetch the graphql configuration."""
        return self._schema.rpc_config

    def protocol(
        self, for_version: Optional[str] = None
    ) -> pgql_type.TransactionConstraints:
        """Fetch the protocol constraint block."""
        return self._schema.rpc_config.protocolConfigs

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
        return self._schema.rpc_config.chainIdentifier
        # return self.rpc_config(for_version).chainIdentifier

    @property
    def chain_environment(self) -> str:
        """Fetch which environment (testnet, devenet, etc.) operating with."""
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

    def _qnode_pre_run(
        self, qnode: PGQL_QueryNode
    ) -> Union[GraphQLRequest, ValueError]:
        """."""
        if issubclass(type(qnode), PGQL_QueryNode):
            self._qnode_owner(qnode)
            dnode = qnode.as_document_node(self.schema())
            if isinstance(dnode, GraphQLRequest):
                return dnode
            else:
                raise ValueError("QueryNode did not produce a gql GraphQLRequest")
        else:
            raise ValueError("Not a valid PGQL_QueryNode")

    @versionadded(version="0.60.0", reason="Support query inspection")
    def query_node_to_string(self, *, query_node: PGQL_QueryNode) -> str:
        """."""
        self._qnode_owner(query_node)
        qres = query_node.as_document_node(self.schema())
        qres_prnt: str = print_ast(qres.document)
        return qres_prnt


class SuiGQLClient(BaseSuiGQLClient):
    """Synchronous pysui GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    @versionchanged(
        version="0.85.0",
        reason="Proxy support https://github.com/FrankC01/pysui/issues/311",
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    @deprecated(
        version="0.98.0",
        reason="SuiGQLClient (synchronous) is deprecated. Use client_factory(PysuiConfiguration()) which returns an async client. SuiGQLClient will be removed in a future release.",
    )
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
        proxies: Optional[dict] = None,
        timeout: float | None = None,
    ):
        """Sui GraphQL Client initializer."""
        gurl = pysui_config.url
        genv = pysui_config.active_profile
        super().__init__(
            pysui_config=pysui_config,
            schema=scm.Schema(
                gql_url=gurl, gql_env=genv, proxies=proxies, timeout=timeout
            ),
            write_schema=write_schema,
            default_header=default_header,
        )

    @versionadded(version="0.87.0", reason="Parity with JSON RPC and gRPC client.")
    def transaction(self, **kwargs) -> Any:
        """Return a synchronous SuiTransaction.

        :param initial_sender: The address of the sender of the transaction, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to False
        :type compress_inputs: bool,optional
        :param merge_gas_budget: If True will take available gas not in use for paying for transaction, defaults to False
        :type merge_gas_budget: bool, optional
        :param use_account_for_gas: Enable using address account balance for gas, defaults to False
        :type use_account_for_gas: Optional[bool], optional
        """
        import pysui.sui.sui_pgql.pgql_sync_txn as synctxn

        kwargs["client"] = self
        return synctxn.SuiTransaction(**kwargs)

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    def _execute(
        self,
        node: GraphQLRequest,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node

        :param node: GQL GraphQLRequest
        :type node: GraphQLRequest
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            extra_args = with_headers or self._default_header
            extra_args["timeout"] = timeout or self._schema.timeout
            sres = self.client().execute(node, extra_args=extra_args)
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
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    def execute_query_string(
        self,
        *,
        string: str,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """execute_query_string Executes a GraphQL query string.

        :param string: Well formed GraphQL query string
        :type string: str
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :param timeout: Timeout for execution overriding default set for client, defaults to None
        :type timeout: Optional[float], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(string, str):
            return self._execute(gql(string), with_headers, encode_fn, timeout)
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for GraphQLRequest processing"
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    def execute_document_node(
        self,
        *,
        with_node: GraphQLRequest,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """execute_document_node Executes a gql GraphQLRequest.

        :param with_node: The gql GraphQL GraphQLRequest
        :type with_node: GraphQLRequest
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :param timeout: Timeout for execution overriding default set for client, defaults to None
        :type timeout: Optional[float], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(with_node, GraphQLRequest):
            return self._execute(with_node, with_headers, encode_fn, timeout)
        else:
            return SuiRpcResult(False, "Not a valid gql GraphQLRequest", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """execute_query_node Execute a pysui GraphQL QueryNode.

        :param with_node: The QueryNode for execution
        :type with_node: PGQL_QueryNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :param timeout: Timeout for execution overriding default set for client, defaults to None
        :type timeout: Optional[float], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            qdoc_node = self._qnode_pre_run(with_node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return self._execute(qdoc_node, with_headers, encode_fn, timeout)
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
            res = self.execute_query_node(with_node=qn.GetTransactionSC(digest=digest))
            if res.is_ok() and res.result_data is not None:
                return res
            total_poll += poll_interval
            if total_poll < timeout:
                logging.info("Sleeping")
                sleep(poll_interval)
            else:
                raise ValueError("Timeout error while waiting for transaction block.")


class GqlProtocolClient(AsyncClientBase, BaseSuiGQLClient):
    """Asynchronous pysui GraphQL client."""

    @versionchanged(
        version="0.65.0", reason="BREAKING Uses PysuiConfiguration instead of SuiConfig"
    )
    @versionchanged(
        version="0.85.0",
        reason="Proxy support https://github.com/FrankC01/pysui/issues/311",
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        write_schema: Optional[bool] = False,
        default_header: Optional[dict] = None,
        proxies: Optional[dict] = None,
        timeout: float | None = None,
    ):
        """Async Sui GraphQL Client initializer."""
        scm_mgr: scm.Schema = scm.Schema(
            gql_url=pysui_config.url,
            gql_env=pysui_config.active_profile,
            proxies=proxies,
            timeout=timeout,
        )
        scm_mgr.set_async_client(proxies)

        super().__init__(
            pysui_config=pysui_config,
            schema=scm_mgr,
            write_schema=write_schema,
            default_header=default_header,
        )
        self._slock = asyncio.Semaphore()

    @versionadded(version="0.87.0", reason="Parity with JSON RPC and gRPC client.")
    async def transaction(self, **kwargs) -> Any:
        """Return an asynchronous SuiTransaction.

        :param initial_sender: The address of the sender of the transaction, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param compress_inputs: Reuse identical inputs, defaults to False
        :type compress_inputs: bool,optional
        :param merge_gas_budget: If True will take available gas not in use for paying for transaction, defaults to False
        :type merge_gas_budget: bool, optional
        """
        import pysui.sui.sui_pgql.pgql_async_txn as asynctxn

        kwargs["client"] = self
        return asynctxn.AsyncSuiTransaction(**kwargs)

    async def serial_executor(self, **kwargs) -> Any:
        """Return a GQL serial transaction executor.

        The caller owns the executor lifecycle — calling client.close() does not
        drain or close executor resources. Concurrent serial_executor() calls over
        the same sender will race on coin selection if both use coin-object gas.

        :param sender: The address of the transaction sender
        :type sender: Union[str, SigningMultiSig]
        :param sponsor: Optional sponsor address, defaults to None
        :type sponsor: Union[str, SigningMultiSig], optional
        :param default_gas_budget: Default gas budget per transaction, defaults to 50_000_000
        :type default_gas_budget: int, optional
        """
        import pysui.sui.sui_pgql.pgql_serial_exec as sexec

        kwargs["client"] = self
        return sexec.GqlSerialTransactionExecutor(**kwargs)

    async def parallel_executor(self, **kwargs) -> Any:
        """Return a GQL parallel transaction executor.

        The caller owns the executor lifecycle — calling client.close() does not
        drain or close executor resources. Concurrent parallel_executor() calls over
        the same sender will race on coin selection if both use coin-object gas.

        :param sender: The address of the transaction sender
        :type sender: Union[str, SigningMultiSig]
        :param sponsor: Optional sponsor address, defaults to None
        :type sponsor: Union[str, SigningMultiSig], optional
        :param default_gas_budget: Default gas budget per transaction, defaults to 50_000_000
        :type default_gas_budget: int, optional
        """
        import pysui.sui.sui_pgql.pgql_parallel_exec as pexec

        kwargs["client"] = self
        return pexec.GqlParallelTransactionExecutor(**kwargs)

    @property
    def session(self) -> Any:
        """Return the underlying GraphQL transport session."""
        return self._session

    async def close(self) -> None:
        """Close the connection."""
        if self._schema._async_client:
            try:
                await self._schema._async_client.close_async()
            except AttributeError:
                pass

    async def __aenter__(self) -> "GqlProtocolClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and close connection."""
        await self.close()

    @versionadded(
        version="0.56.0", reason="Common node execution with exception handling"
    )
    async def _execute(
        self,
        node: GraphQLRequest,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """_execute Execute a GQL Document Node.

        :param node: GQL GraphQLRequest
        :type node: GraphQLRequest
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
                extra_args = with_headers or self._default_header
                extra_args["timeout"] = timeout or self._schema.timeout
                sres = await _session.execute(node, extra_args=extra_args)

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
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    async def execute_query_string(
        self,
        *,
        string: str,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """execute_query_string Executes a GraphQL query string.

        :param string: Well formed GraphQL query string
        :type string: str
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :param timeout: Timeout for execution overriding default set for client, defaults to None
        :type timeout: Optional[float], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(string, str):
            return await self._execute(gql(string), with_headers, encode_fn, timeout)
        else:
            return SuiRpcResult(False, "ValueError:Expected string", string)

    @versionadded(
        version="0.56.0", reason="Unique function for GraphQLRequest processing"
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    async def execute_document_node(
        self,
        *,
        with_node: GraphQLRequest,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """execute_document_node Executes a gql GraphQLRequest.

        :param with_node: The gql GraphQL GraphQLRequest
        :type with_node: GraphQLRequest
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :param timeout: Timeout for execution overriding default set for client, defaults to None
        :type timeout: Optional[float], optional
        :return: SuiRpcResult cointaining status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        if isinstance(with_node, GraphQLRequest):
            return await self._execute(with_node, with_headers, encode_fn, timeout)
        else:
            return SuiRpcResult(False, "Not a valid gql GraphQLRequest", with_node)

    @versionadded(
        version="0.56.0", reason="Unique function for PGQL_QueryNode processing"
    )
    @versionchanged(version="0.89.0", reason="Added timeout argument")
    @deprecated(
        version="0.99.0",
        reason=(
            "Use AsyncClientBase.execute(command=...) with a SuiCommand instance instead. "
            "No removal timeline set."
        ),
    )
    async def execute_query_node(
        self,
        *,
        with_node: PGQL_QueryNode,
        with_headers: Optional[dict] = None,
        encode_fn: Optional[Callable[[dict], Any]] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """Execute a pysui GraphQL QueryNode.

        :param with_node: The QueryNode for execution
        :type with_node: PGQL_QueryNode
        :param with_headers: Add extra arguments for http client headers, default to None
        :type with_headers: Optional[dict]
        :param encode_fn: Encoding function, defaults to None
        :type encode_fn: Optional[Callable[[dict], Any]], optional
        :param timeout: Timeout for execution overriding default set for client, defaults to None
        :type timeout: Optional[float], optional
        :return: SuiRpcResult containing status and raw result (dict) or that defined by serialization function
        :rtype: SuiRpcResult
        """
        try:
            qdoc_node = self._qnode_pre_run(with_node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = encode_fn or with_node.encode_fn()
            return await self._execute(qdoc_node, with_headers, encode_fn, timeout)

        except ValueError as ve:
            return SuiRpcResult(
                False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
            )

    async def execute(
        self,
        *,
        command: SuiCommand,
        timeout: float | None = None,
        headers: dict | None = None,
    ) -> SuiRpcResult:
        """Execute a SuiCommand against the GraphQL protocol.

        :param command: A SuiCommand instance describing the operation
        :param timeout: Optional timeout in seconds
        :param headers: Optional HTTP headers passed to the transport
        :return: SuiRpcResult wrapping the response or error
        :rtype: SuiRpcResult
        """
        if not isinstance(command, SuiCommand):
            return SuiRpcResult(
                False, f"Expected SuiCommand, got {type(command).__name__}", None
            )
        try:
            node = command.gql_node()
        except NotImplementedError:
            return SuiRpcResult(False, "Command not supported by GraphQL", None)

        if not command.gql_requires_paging:
            return await self._execute_gql_node(
                node, with_headers=headers, timeout=timeout
            )

        if command.gql_page_list_path:
            # SC paging: fetch raw dicts per page, accumulate list, encode once at end.
            # gql_page_list_path navigates to the container whose "nodes" key holds items
            # and whose "cursor" key holds PageInfo.
            path = command.gql_page_list_path
            accumulated: list = []
            while True:
                try:
                    qdoc_node = self._qnode_pre_run(node)
                except ValueError as ve:
                    return SuiRpcResult(
                        False, "ValueError", pgql_type.ErrorGQL.from_query(ve.args)
                    )
                result = await self._execute(qdoc_node, headers, None, timeout)
                if not result.is_ok():
                    return result
                parent = result.result_data
                for key in path[:-1]:
                    parent = parent[key]
                accumulated.extend(parent.get(path[-1], []))
                cursor_info = parent.get("cursor", {})
                if cursor_info.get("hasNextPage", False):
                    command.next_page = pgql_type.PagingCursor(
                        hasNextPage=True,
                        endCursor=cursor_info.get("endCursor"),
                    )
                    node = command.gql_node()
                else:
                    break
            return SuiRpcResult(True, None, node.encode_fn()(accumulated))

        # Legacy paging: encode each page individually, accumulate decoded .data lists.
        collection: list = []
        result = await self._execute_gql_node(node, with_headers=headers, timeout=timeout)
        while True:
            if not result.is_ok():
                return result
            data = result.result_data
            collection.extend(getattr(data, "data", [data]))
            cursor = getattr(data, "next_cursor", None)
            if cursor and getattr(cursor, "hasNextPage", False):
                command.next_page = cursor
                node = command.gql_node()
                result = await self._execute_gql_node(
                    node, with_headers=headers, timeout=timeout
                )
            else:
                break
        return SuiRpcResult(True, None, collection)

    async def _execute_gql_node(
        self,
        node: PGQL_QueryNode,
        with_headers: Optional[dict] = None,
        timeout: float | None = None,
    ) -> SuiRpcResult:
        """Internal: run a PGQL_QueryNode through _qnode_pre_run and _execute."""
        try:
            qdoc_node = self._qnode_pre_run(node)
            if isinstance(qdoc_node, PGQL_NoOp):
                return SuiRpcResult(True, None, pgql_type.NoopGQL.from_query())
            encode_fn = node.encode_fn()
            return await self._execute(qdoc_node, with_headers, encode_fn, timeout)
        except (ValueError, GraphQLError) as ve:
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
        from pysui.sui.sui_common.sui_commands import GetTransaction

        total_poll = 0
        while True:
            logging.info(f"Polling {digest} for {total_poll} times")
            res = await self.execute(command=GetTransaction(digest=digest))
            if res.is_ok() and res.result_data is not None:
                return res
            total_poll += poll_interval
            if total_poll < timeout:
                logging.info("Sleeping")
                await asyncio.sleep(poll_interval)
            else:
                raise ValueError("Timeout error while waiting for transaction block.")
