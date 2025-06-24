#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Clients"""

from typing import Optional, TypeAlias
from collections.abc import Callable
import urllib.parse as urlparse
import traceback
import betterproto2
from grpclib.exceptions import GRPCError

from pysui.sui.sui_common.client import PysuiClient

import pysui.sui.sui_grpc.pgrpc_absreq as absreq

# Need conditional around these
from pysui.sui.sui_grpc.pgrpc_requests import GetEpoch

if absreq.CURRENT_VERSION[1] >= 87:
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2alpha as v2alpha
else:
    raise ValueError("HARD STOP")

from grpclib.client import Channel

from pysui import SuiRpcResult, PysuiConfiguration


import logging

logger = logging.getLogger()

from pysui.sui.sui_pgql.pgql_types import TransactionConstraints

_TXCONSTRAINTS = list(TransactionConstraints.__dataclass_fields__.keys())


def _map_pconstraints(in_bound: v2base.ProtocolConfig):
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

    return TransactionConstraints(*ordered_list)


class SuiGrpcClient(PysuiClient):
    """Asynchronous gRPC client."""

    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
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

    @property
    async def current_gas_price(self) -> int:
        """Fetch the current epoch gas price."""
        result = await self.execute(request=GetEpoch())
        return result.result_data.reference_gas_price

    async def protocol(self, for_version: Optional[str] = None):
        """Fetch the protocol constraints."""
        result = await self.execute(
            request=GetEpoch(
                epoch_number=int(for_version) if for_version else None,
                field_mask=["protocol_config"],
            )
        )
        if result.is_ok() and result.result_data.protocol_config:
            return _map_pconstraints(result.result_data.protocol_config)
        raise ValueError(f"protocol fetch returned {result.result_string}")

    def close(self):
        """Close the base gRPC channel"""
        for channel in self._channels:
            channel.close()
        self._channel.close()

    async def execute(self, *, request: absreq.PGRPC_Request, **kwargs) -> SuiRpcResult:
        """execute calls the request's service

        :param request: Pysui gRPC request
        :type request: PGRPC_Request
        :return: Results of execution
        :rtype: SuiRpcResult
        """
        srv_fn: Callable[[betterproto2.Message], betterproto2.Message]
        srv_req: betterproto2.Message
        match request.service:
            case absreq.Service.LIVEDATA:
                srv_fn, srv_req = request.to_request(
                    stub=v2alpha.LiveDataServiceStub(self._channel)
                )
            case absreq.Service.LEDGER:
                srv_fn, srv_req = request.to_request(
                    stub=v2base.LedgerServiceStub(self._channel)
                )
            case absreq.Service.TRANSACTION:
                srv_fn, srv_req = request.to_request(
                    stub=v2base.TransactionExecutionServiceStub(self._channel)
                )
            case absreq.Service.MOVEPACKAGE:
                srv_fn, srv_req = request.to_request(
                    stub=v2alpha.MovePackageServiceStub(self._channel)
                )
            # Subscriptions are called synchronously on first fetch
            case absreq.Service.SUBSCRIPTION:
                srv_fn, srv_req = request.to_request(
                    stub=v2alpha.SubscriptionServiceStub(self._channel)
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
                    stub=v2alpha.SignatureVerificationServiceStub(self._channel)
                )
            case _:
                raise NotImplementedError(f"{request.service} not implemented.")

        try:
            logger.info(f"Request {request}")
            result = await srv_fn(srv_req, **kwargs)
            logger.info("Success")
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
