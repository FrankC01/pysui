#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Clients"""

from typing import Optional, TypeAlias, Any
from collections.abc import Callable
import abc
import urllib.parse as urlparse
import betterproto
from betterproto.lib.google.protobuf import FieldMask
from grpclib.client import Channel
from pysui import SuiRpcResult, PysuiConfiguration

import pysui.sui.sui_grpc.suimsgs.sui.types as v2types
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base

LedgerClient: TypeAlias = "_SuiLedgerClient"
TxClient: TypeAlias = "_SuiTransactionClient"


class SuiGrpcClient:
    """Asynchronous gRPC client."""

    def __init__(
        self,
        *,
        pysui_config: PysuiConfiguration,
        grpc_node_url: Optional[str] = None,
    ):
        """Initializes client.

        :param pysui_config: Configuration for interfaces
        :type pysui_config: PysuiConfiguration
        """
        self._pysui_config: PysuiConfiguration = pysui_config
        if url := _clean_url(grpc_node_url):
            self._channel: Channel = Channel(host=url[0], port=url[1], ssl=True)
        else:
            pysui_config.model.get_group(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        self._channels: list[Channel] = []

    def close(self):
        """."""
        for channel in self._channels:
            channel.close()
        self._channel.close()

    def ledger_client(self, *, grpc_url: Optional[str] = None) -> "_SuiLedgerClient":
        """."""
        url = _clean_url(grpc_url)
        channel = self._channel
        if url:
            channel = Channel(host=url[0], port=url[1], ssl=True)
            self._channels.append(channel)
        return _SuiLedgerClient(channel)

    def transaction_client(
        self, *, grpc_url: Optional[str] = None
    ) -> "_SuiTransactionClient":
        """."""
        url = _clean_url(grpc_url)
        channel = self._channel
        if url:
            channel = Channel(host=url[0], port=url[1], ssl=True)
            self._channels.append(channel)
        return _SuiTransactionClient(channel)


def _clean_url(url: str) -> tuple[str | None, int | None] | None:
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


class GrpcServiceClient(abc.ABC):
    """."""

    def __init__(self):
        """."""

    async def _execute(
        self,
        fn: Callable[[betterproto.Message], betterproto.Message],
        request: betterproto.Message,
    ) -> SuiRpcResult:
        """."""
        try:
            result = await fn(request)
            return SuiRpcResult(True, None, result)
        except Exception as e:
            return SuiRpcResult(False, e.args)


class _SuiLedgerClient(GrpcServiceClient):
    """."""

    def __init__(self, channel: Channel):
        self._service = v2base.LedgerServiceStub(channel)
        super().__init__()

    async def get_object(
        self,
        *,
        object_id: str,
        version: Optional[int] = None,
        read_mask: Optional[list[str]] = None,
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        request = v2base.GetObjectRequest(object_id, version, field_mask)
        return await self._execute(self._service.get_object, request)

    async def get_transaction(
        self, *, digest: str, read_mask: Optional[list[str]] = None
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        request = v2base.GetTransactionRequest(digest, field_mask)
        return await self._execute(self._service.get_transaction, request)


class _SuiTransactionClient(GrpcServiceClient):
    """."""

    def __init__(self, channel: Channel):
        """."""
        self._service = v2base.TransactionExecutionServiceStub(channel)
        super().__init__()
