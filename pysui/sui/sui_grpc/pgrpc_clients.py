#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Clients"""

from typing import Optional, TypeAlias
from collections.abc import Callable
import abc
import base64
import urllib.parse as urlparse
import traceback
import betterproto2

from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
from grpclib.client import Channel
from pysui import SuiRpcResult, PysuiConfiguration

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base

import logging

logger = logging.getLogger()

# import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2alpha as v2alpha

LedgerClient: TypeAlias = "_SuiLedgerClient"
TxClient: TypeAlias = "_SuiTransactionClient"
# AlphaDataClient: TypeAlias = "_SuiAlphaDataClient"


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
        """Close the base gRPC channel"""
        for channel in self._channels:
            channel.close()
        self._channel.close()

    def ledger_client(self, *, grpc_url: Optional[str] = None) -> LedgerClient:
        """Return a new instance of a Ledger service client.

        :param grpc_url: URL of service if not same as SuiGrpcClient, defaults to None
        :type grpc_url: Optional[str], optional
        :return: A Ledger Service client
        :rtype: LedgerClient
        """
        url = _clean_url(grpc_url)
        channel = self._channel
        if url:
            channel = Channel(host=url[0], port=url[1], ssl=True)
            self._channels.append(channel)
        return _SuiLedgerClient(channel)

    def transaction_client(self, *, grpc_url: Optional[str] = None) -> TxClient:
        """Return a new instance of a Transaction service client.

        :param grpc_url: URL of service if not same as SuiGrpcClient, defaults to None
        :type grpc_url: Optional[str], optional
        :return: A Transaction Service client
        :rtype: TxClient
        """
        url = _clean_url(grpc_url)
        channel = self._channel
        if url:
            channel = Channel(host=url[0], port=url[1], ssl=True)
            self._channels.append(channel)
        return _SuiTransactionClient(channel)

    # def alpha_data_client(
    #     self, *, grpc_url: Optional[str] = None
    # ) -> "_SuiAlphaDataClient":
    #     """."""
    #     url = _clean_url(grpc_url)
    #     channel = self._channel
    #     if url:
    #         channel = Channel(host=url[0], port=url[1], ssl=True)
    #         self._channels.append(channel)
    #     return _SuiAlphaDataClient(channel)


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


class GrpcServiceClient(abc.ABC):
    """Abstract base class for gRPC service clients.."""

    def __init__(self):
        """Initializer."""

    async def _execute(
        self,
        fn: Callable[[betterproto2.Message], betterproto2.Message],
        request: betterproto2.Message,
        **kwargs,
    ) -> SuiRpcResult:
        """Submit the execution of the gRPC message

        :param fn: Specific service function
        :type fn: Callable[[betterproto2.Message], betterproto2.Message]
        :param request: The associated request message for service
        :type request: betterproto2.Message
        :return: A result status including either a response (success) or error string
        :rtype: SuiRpcResult
        """
        try:
            logger.debug(f"Request {request}")
            result = await fn(request, **kwargs)
            logger.debug(f"Success {result}")
            return SuiRpcResult(True, None, result)
        except Exception as e:
            traceback_str = traceback.format_exc()
            logger.error(traceback_str)
            return SuiRpcResult(False, e.args)


class _SuiLedgerClient(GrpcServiceClient):
    """gRPC LedgerService client."""

    def __init__(self, channel: Channel):
        self._service = v2base.LedgerServiceStub(channel)
        super().__init__()

    async def get_service_info(self, **kwargs) -> SuiRpcResult:
        """Return gRPC service information.

        :return: Query result v2base.GetServiceInfoResponse if successful
        :rtype: SuiRpcResult
        """
        return await self._execute(
            self._service.get_service_info, v2base.GetServiceInfoRequest(), **kwargs
        )

    async def get_checkpoint(
        self,
        check_point: Optional[int] = None,
        digest: Optional[str] = None,
        read_mask: Optional[list[str]] = None,
        **kwargs,
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        args = (
            {"sequence_number": check_point}
            if check_point and isinstance(check_point, int)
            else {"digest": digest}
        )
        return await self._execute(
            self._service.get_checkpoint,
            v2base.GetCheckpointRequest(**args, read_mask=field_mask),
            **kwargs,
        )

    async def get_epoch(
        self,
        *,
        epoch_id: int,
        read_mask: Optional[list[str]] = None,
        **kwargs,
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        return await self._execute(
            self._service.get_epoch,
            v2base.GetEpochRequest(epoch_id, field_mask),
            **kwargs,
        )

    async def get_object(
        self,
        *,
        object_id: str,
        version: Optional[int] = None,
        read_mask: Optional[list[str]] = None,
        **kwargs,
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        request = v2base.GetObjectRequest(object_id, version, field_mask)
        return await self._execute(self._service.get_object, request, **kwargs)

    async def get_objects(
        self,
        *,
        object_ids: list[str],
        read_mask: Optional[list[str]] = None,
        **kwargs,
    ):
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        objs = [v2base.GetObjectRequest(x, y) for x, y in object_ids]
        return await self._execute(
            self._service.batch_get_objects,
            v2base.BatchGetObjectsRequest(objs, field_mask),
            **kwargs,
        )

    async def get_transaction(
        self, *, digest: str, read_mask: Optional[list[str]] = None, **kwargs
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        return await self._execute(
            self._service.get_transaction,
            v2base.GetTransactionRequest(digest, field_mask),
            **kwargs,
        )

    async def get_transactions(
        self,
        *,
        digests: list[str],
        read_mask: Optional[list[str]] = None,
        **kwargs,
    ) -> SuiRpcResult:
        """."""
        field_mask = FieldMask(read_mask) if read_mask else None
        return await self._execute(
            self._service.batch_get_transactions,
            v2base.BatchGetTransactionsRequest(digests, field_mask),
            **kwargs,
        )


class _SuiTransactionClient(GrpcServiceClient):
    """Service client for Transaction processing."""

    def __init__(self, channel: Channel):
        """Initialize."""
        self._service = v2base.TransactionExecutionServiceStub(channel)
        super().__init__()

    async def execute_transaction(
        self,
        *,
        tx_bytestr: str,
        sig_array: list[str],
        read_mask: Optional[list[str]] = None,
        **kwargs,
    ) -> SuiRpcResult:
        """Submit transaction for execution.

        :param tx_bytestr: base64 encoded TransactionData
        :type tx_bytestr: str
        :param sig_array: List of base64 encoded transaction signatures.
        :type sig_array: list[str]
        :param read_mask: List of fields to include in response results
        :type read_mask: Optional[list[str]], optional
        :return: Results of execution.
        :rtype: SuiRpcResult
        """
        field_mask = FieldMask(read_mask) if read_mask else None
        sigs = [
            v2base.UserSignature(bcs=v2base.Bcs(value=base64.b64decode(x)))
            for x in sig_array
        ]
        tx_bytes = base64.b64decode(tx_bytestr)
        request = v2base.ExecuteTransactionRequest(
            v2base.Transaction(bcs=v2base.Bcs(value=tx_bytes)),
            sigs,
            field_mask,
        )
        return await self._execute(
            self._service.execute_transaction,
            request,
            **kwargs,
        )


# class _SuiAlphaDataClient(GrpcServiceClient):
#     """."""

#     def __init__(self, channel: Channel):
#         """."""
#         self._service = v2alpha.LiveDataServiceStub(channel)
#         super().__init__()

#     async def get_owned_objects(
#         self,
#         *,
#         owner: str,
#         # read_mask: Optional[list[str]] = None,
#         **kwargs,
#     ) -> SuiRpcResult:
#         """."""
#         # field_mask = FieldMask(read_mask) if read_mask else None
#         return await self._execute(
#             self._service.list_owned_objects,
#             v2alpha.ListOwnedObjectsRequest(owner),
#             **kwargs,
#         )
