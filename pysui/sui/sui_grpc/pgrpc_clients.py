#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Clients"""

import asyncio
from collections.abc import Callable
import dataclasses
import logging
from typing import Any, Awaitable, ClassVar, Optional, TypeAlias, Union, Literal, TYPE_CHECKING
import traceback
import urllib.parse as urlparse

if TYPE_CHECKING:
    from pysui.sui.sui_common.txb_signing import SigningMultiSig
    from pysui.sui.sui_common.executors.serial_executor import PysuiSerialExecutor
    from pysui.sui.sui_common.executors.exec_types import ExecutorContext

import betterproto2
import dataclasses_json
from deprecated.sphinx import deprecated
from grpclib.const import Status as GRPCStatus
from grpclib.exceptions import GRPCError

from pysui import SDK_CURRENT_VERSION
from pysui.sui.sui_common.client import PysuiClient
from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.sui_command import SuiCommand

import pysui.sui.sui_grpc.pgrpc_absreq as absreq
from pysui.sui.sui_grpc.pgrpc_requests import GetEpoch


import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot


from grpclib.client import Channel

from pysui import SuiRpcResult, PysuiConfiguration
from pysui.sui.sui_common.types import TransactionConstraints

logger = logging.getLogger("pgrpc_client")


_TXCONSTRAINTS = list(TransactionConstraints.__dataclass_fields__.keys())


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ProtocolConfig:
    """gRPC protocol configuration container holding transaction constraints."""

    transaction_constraints: TransactionConstraints


def _map_pconstraints(in_bound: sui_prot.ProtocolConfig):
    """Extract protocol constraints in parity with GraphQL model."""
    ordered_list: list = []
    for item in _TXCONSTRAINTS:
        if res := getattr(in_bound, item, None):
            ordered_list.append(int(res))
        elif res := in_bound.feature_flags.get(item, None):
            ordered_list.append(int(res))
        elif res := in_bound.attributes.get(item, None):
            ordered_list.append(int(res))
        else:
            ordered_list.append(res)
    return ProtocolConfig(TransactionConstraints(*ordered_list))


class GrpcProtocolClient(AsyncClientBase, PysuiClient):
    """Asynchronous gRPC client."""

    _protocol: ClassVar[str] = "grpc"

    def __init__(
        self, *, pysui_config: PysuiConfiguration, default_header: dict | None = None
    ):
        """Initializes client.

        :param pysui_config: Configuration for interfaces
        :type pysui_config: PysuiConfiguration
        :parm grpc_node_url: gRPC URL
        """
        super().__init__(pysui_config=pysui_config, default_header=default_header)

        if url := _clean_url(self._pysui_config.active_group.active_profile.url):
            self._channel: Channel = Channel(host=url[0], port=url[1], ssl=True)
        else:
            raise ValueError(
                f"{pysui_config.active_group.active_profile.url} in {self._pysui_config.active_profile} is not valid URL"
            )
        self._channels: list[Channel] = []
        self._protocol_config: ProtocolConfig = None

    @property
    async def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        result = await self.execute_grpc_request(request=GetEpoch())
        if result.is_ok():
            return result.result_data.epoch.reference_gas_price
        raise ValueError(f"Error accessing gRPC {result.result_string}")

    async def protocol(self, epoch_number: Optional[int] = None) -> ProtocolConfig:
        """Fetch the protocol constraints."""
        result = await self.execute_grpc_request(
            request=GetEpoch(
                epoch_number=epoch_number,
                field_mask=["protocol_config"],
            )
        )
        if result.is_ok() and hasattr(result.result_data.epoch, "protocol_config"):
            self._protocol_config = _map_pconstraints(
                result.result_data.epoch.protocol_config
            )
            return self._protocol_config
        raise ValueError(f"protocol fetch returned {result.result_string}")

    async def close(self):
        """Close the base gRPC channel"""
        for channel in self._channels:
            channel.close()
        self._channel.close()

    async def __aenter__(self) -> "GrpcProtocolClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and close channel."""
        await self.close()

    async def transaction(
        self,
        **kwargs,
    ) -> Any:
        """Return a unified AsyncSuiTransaction for the gRPC protocol.

        :param compress_inputs: Reuse identical inputs, defaults to True
        :type compress_inputs: Optional[bool], optional
        :param initial_sender: Initial sender of transactions, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param initial_sponsor: Initial sponsor of transactions, defaults to None
        :type initial_sponsor: Union[str, SigningMultiSig], optional
        :param builder: Move call parameter builder, defaults to None
        :type builder: Optional[Any], optional
        :param merge_gas_budget: Global gas budget for each transaction, defaults to False
        :type merge_gas_budget: Optional[bool], optional
        :return: Unified async transaction builder
        :rtype: AsyncSuiTransaction
        """
        from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

        kwargs["client"] = self
        return AsyncSuiTransaction(**kwargs)

    async def serial_executor_with_coins(
        self,
        sender: Union[str, "SigningMultiSig"],
        *,
        coins: Optional[Union[list[str], list[sui_prot.Object]]] = None,
        min_balance_threshold: int = 10_000_000,
        on_coins_low: Optional[Callable[["ExecutorContext"], Awaitable[Optional[list]]]] = None,
        on_failure: Literal["continue", "exit"] = "continue",
    ) -> "tuple[PysuiSerialExecutor, str]":
        """Async factory: create a PysuiSerialExecutor pre-seeded with gas coins.

        Delegates to PysuiSerialExecutor.with_coins(). Returns (executor, primary_coin_id).
        """
        from pysui.sui.sui_common.executors.serial_executor import (
            PysuiSerialExecutor,
        )

        return await PysuiSerialExecutor.with_coins(
            client=self,
            sender=sender,
            coins=coins,
            min_balance_threshold=min_balance_threshold,
            on_coins_low=on_coins_low,
            on_failure=on_failure,
        )

    async def parallel_executor(self, **kwargs) -> Any:
        """Return a gRPC parallel transaction executor.

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
        import pysui.sui.sui_grpc.grpc_parallel_exec as pexec

        kwargs["client"] = self
        return pexec.GrpcParallelTransactionExecutor(**kwargs)

    async def _dispatch_grpc_request(
        self, request: absreq.PGRPC_Request, **kwargs
    ) -> SuiRpcResult:
        """Resolve gRPC service from request and execute it.

        :param request: Pysui gRPC request
        :type request: PGRPC_Request
        :return: Results of execution
        :rtype: SuiRpcResult
        """
        kwargs["metadata"] = self._default_header | kwargs.get("metadata", {})
        srv_fn: Callable[[betterproto2.Message], betterproto2.Message]
        srv_req: betterproto2.Message
        match request.service:
            case absreq.Service.STATE:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.StateServiceStub(self._channel)
                )
            case absreq.Service.LEDGER:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.LedgerServiceStub(self._channel)
                )
            case absreq.Service.TRANSACTION:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.TransactionExecutionServiceStub(self._channel)
                )
            case absreq.Service.MOVEPACKAGE:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.MovePackageServiceStub(self._channel)
                )
            # Subscriptions are called synchronously on first fetch
            case absreq.Service.SUBSCRIPTION:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.SubscriptionServiceStub(self._channel)
                )
                try:
                    logger.info("Dispatching %s", type(request).__name__)
                    logger.debug("Request detail: %s", request)
                    result = srv_fn(srv_req, **kwargs)
                    logger.info("Success")
                    return SuiRpcResult(True, None, result)
                except (GRPCError, ValueError, asyncio.exceptions.CancelledError) as e:
                    traceback_str = traceback.format_exc()
                    logger.error(traceback_str)
                    return SuiRpcResult(False, e.args)

            case absreq.Service.SIGNATURE:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.SignatureVerificationServiceStub(self._channel)
                )
            case absreq.Service.NAMESERVICE:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.NameServiceStub(self._channel)
                )
            case _:
                raise NotImplementedError(f"{request.service} not implemented.")

        try:
            logger.info("Dispatching %s", type(request).__name__)
            logger.debug("Request detail: %s", request)
            result = await srv_fn(srv_req, **kwargs)
            logger.info("Success")
            if hasattr(request, "render"):
                result = request.render(result)
            return SuiRpcResult(True, None, result)
        except GRPCError as e:
            if e.status == GRPCStatus.NOT_FOUND and getattr(request, "not_found_as_none", False):
                return SuiRpcResult(True, None, None)
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            return SuiRpcResult(False, e.args)
        except (ValueError, AttributeError) as e:
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            return SuiRpcResult(False, e.args)

    @deprecated(
        version="0.99.0",
        reason=(
            "Use AsyncClientBase.execute(command=...) with a SuiCommand instance instead. "
            "No removal timeline set."
        ),
    )
    async def execute_grpc_request(
        self, *, request: absreq.PGRPC_Request, **kwargs
    ) -> SuiRpcResult:
        """Execute a raw gRPC request directly.

        kwargs can include:
            timeout: "float | None" = None,
            deadline: "grpclib.metadata.Deadline | None" = None,
            metadata: "dict | None" = None, # Sets additional headers

        :param request: Pysui gRPC request
        :type request: PGRPC_Request
        :return: Results of execution
        :rtype: SuiRpcResult
        """
        return await self._dispatch_grpc_request(request, **kwargs)

    async def execute(
        self,
        *,
        command: SuiCommand,
        timeout: float | None = None,
        headers: dict | None = None,
    ) -> SuiRpcResult:
        """Execute a SuiCommand against the gRPC protocol.

        :param command: A SuiCommand instance describing the operation
        :param timeout: Optional timeout in seconds
        :param headers: Optional headers/metadata passed to the transport
        :return: SuiRpcResult wrapping the response or error
        :rtype: SuiRpcResult
        """
        if not isinstance(command, SuiCommand):
            return SuiRpcResult(
                False, f"Expected SuiCommand, got {type(command).__name__}", None
            )
        try:
            request = command.grpc_request()
        except NotImplementedError:
            return SuiRpcResult(False, "Command not supported by gRPC", None)
        except (ValueError, TypeError) as exc:
            return SuiRpcResult(False, str(exc), None)
        kwargs: dict = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if headers is not None:
            kwargs["metadata"] = headers

        return await self._dispatch_grpc_request(request, **kwargs)



def _clean_url(url: str) -> tuple[str | None, int | None] | None:
    """Clean up and separate url from port.

    :param url: Inbound URL
    :type url: str
    :return: A URL and Port tuple
    :rtype: tuple[str | None, int | None] | None
    """
    try:
        up: urlparse.ParseResultBytes = urlparse.urlparse(url)
        if up.netloc:
            url_out = up.netloc.split(":")[0]
            port_out = up.port
            return url_out, port_out
        elif up.scheme:
            url_out = up.scheme
            port_out = int(up.path)
            return url_out, port_out
        else:
            return ()
    except ValueError:
        return ()
