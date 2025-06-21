#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Clients"""

from typing import Optional, TypeAlias
from collections.abc import Callable
import urllib.parse as urlparse
import traceback
import betterproto2

from pysui.sui.sui_common.client import PysuiClient

import pysui.sui.sui_grpc.pgrpc_absreq as absreq

# Need conditional around these
from pysui.sui.sui_grpc.pgrpc_requests import GetEpoch

if absreq.CURRENT_VERSION[1] == 87:
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2alpha as v2alpha
else:
    raise ValueError("HARD STOP")

from grpclib.client import Channel

from pysui import SuiRpcResult, PysuiConfiguration


import logging

logger = logging.getLogger()


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
                pass
            case absreq.Service.LEDGER:
                srv_fn, srv_req = request.to_request(
                    stub=v2base.LedgerServiceStub(self._channel)
                )
            case absreq.Service.TRANSACTION:
                pass
            case absreq.Service.MOVEPACKAGE:
                pass
            case absreq.Service.SUBSCRIPTION:
                pass
            case absreq.Service.SIGNATURE:
                pass
            case _:
                raise NotImplementedError(f"{request.service} not implemented.")

        try:
            logger.info(f"Request {request}")
            result = await srv_fn(srv_req, **kwargs)
            logger.info("Success")
            return SuiRpcResult(True, None, result)
        except Exception as e:
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
