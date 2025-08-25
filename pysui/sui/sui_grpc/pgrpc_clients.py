#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Clients"""

from collections.abc import Callable
import dataclasses
import logging
from typing import Optional, TypeAlias
import traceback
import urllib.parse as urlparse

import betterproto2
import dataclasses_json
from grpclib.exceptions import GRPCError

from pysui import SDK_CURRENT_VERSION
from pysui.sui.sui_common.client import PysuiClient

from pysui.sui.sui_grpc.pgrpc_async_txn import AsyncSuiTransaction
import pysui.sui.sui_grpc.pgrpc_absreq as absreq
from pysui.sui.sui_grpc.pgrpc_requests import GetEpoch

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot

from grpclib.client import Channel

from pysui import SuiRpcResult, PysuiConfiguration
from pysui.sui.sui_pgql.pgql_types import TransactionConstraints

logger = logging.getLogger("pgrpc_client")


_TXCONSTRAINTS = list(TransactionConstraints.__dataclass_fields__.keys())


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ProtocolConfig:
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
            raise ValueError(f"{item} not found in gRPC protocol configuration.")

    return ProtocolConfig(TransactionConstraints(*ordered_list))


class SuiGrpcClient(PysuiClient):
    """Asynchronous gRPC client."""

    def __init__(
        self, *, pysui_config: PysuiConfiguration, default_header: dict | None = None
    ):
        """Initializes client.

        :param pysui_config: Configuration for interfaces
        :type pysui_config: PysuiConfiguration
        :parm grpc_node_url: gRPC URL
        """
        self._pysui_config: PysuiConfiguration = pysui_config

        if url := _clean_url(self._pysui_config.active_group.active_profile.url):
            self._channel: Channel = Channel(host=url[0], port=url[1], ssl=True)
        else:
            raise ValueError(
                f"{pysui_config.active_group.active_profile.url} in {self._pysui_config.active_profile} is not valid URL"
            )
        self._channels: list[Channel] = []
        self._protocol_config: ProtocolConfig = None
        self._default_header = default_header or dict()

    @property
    async def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        result = await self.execute(request=GetEpoch())
        if result.is_ok():
            return result.result_data.epoch.reference_gas_price
        raise ValueError(f"Error accessing gRPC {result.result_string}")

    async def protocol(self, epoch_number: Optional[int] = None) -> ProtocolConfig:
        """Fetch the protocol constraints."""
        result = await self.execute(
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

    def close(self):
        """Close the base gRPC channel"""
        for channel in self._channels:
            channel.close()
        self._channel.close()

    async def transaction(
        self,
        **kwargs,
    ) -> AsyncSuiTransaction:
        """transaction _summary_

        :param compress_inputs: reuse same inputs, defaults to True
        :type compress_inputs: Optional[bool], optional
        :param initial_sender: initial sender of transactions, defaults to None
        :type initial_sender: Union[str, SigningMultiSig], optional
        :param initial_sponsor: initial sponser of transactions, defaults to None
        :type initial_sponsor: Union[str, SigningMultiSig], optional
        :param builder: move call parameter builder, defaults to None
        :type builder: Optional[Any], optional
        :param arg_parser: transaction command argument parser validator, defaults to None
        :type arg_parser: Optional[Any], optional
        :param merge_gas_budget: global gas budget for each transaction, defaults to False
        :type merge_gas_budget: Optional[bool], optional
        :return: gRPC Transaction builder
        :rtype: AsyncSuiTransaction
        """
        kwargs["client"] = self
        kwargs["txn_constraints"] = await self.protocol()
        kwargs["gas_price"] = await self.current_gas_price
        return AsyncSuiTransaction(**kwargs)

    async def execute(self, *, request: absreq.PGRPC_Request, **kwargs) -> SuiRpcResult:
        """execute calls the request's service

        kwargs can include:
            timeout: "float | None" = None,
            deadline: "grpclib.metadata.Deadline | None" = None,
            metadata: "dict | None" = None, # Sets additional headers

        :param request: Pysui gRPC request
        :type request: PGRPC_Request
        :return: Results of execution
        :rtype: SuiRpcResult
        """
        kwargs["metadata"] = self._default_header | kwargs.get("metadata", {})
        srv_fn: Callable[[betterproto2.Message], betterproto2.Message]
        srv_req: betterproto2.Message
        match request.service:
            case absreq.Service.LIVEDATA:
                srv_fn, srv_req = request.to_request(
                    stub=sui_prot.LiveDataServiceStub(self._channel)
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
                    logger.info(f"Request {request}")
                    result = srv_fn(srv_req, **kwargs)
                    logger.info("Success")
                    return SuiRpcResult(True, None, result)
                except (GRPCError, ValueError) as e:
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
            logger.info(f"Request {request}")
            result = await srv_fn(srv_req, **kwargs)
            logger.info("Success")
            if hasattr(request, "render"):
                result = request.render(result)
            return SuiRpcResult(True, None, result)
        except (GRPCError, ValueError) as e:
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            return SuiRpcResult(False, e.args)


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
