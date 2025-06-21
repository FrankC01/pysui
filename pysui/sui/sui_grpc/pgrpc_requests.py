#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Requests"""


from typing import Callable, Optional

import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.sui.sui_grpc.pgrpc_absreq as absreq

if absreq.CURRENT_VERSION[1] >= 87:
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2alpha as v2alpha
else:
    raise ValueError("HARD STOP")


class GetServiceInfo(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.GetServiceInfoResponse

    def __init__(self) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)

    def to_request(
        self,
        *,
        stub: v2base.LedgerServiceStub,
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_service_info, v2base.GetServiceInfoRequest()


class GetCheckpoint(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.Checkpoint

    def __init__(
        self,
        *,
        sequence: Optional[int] = None,
        digest: Optional[str] = None,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.sequence = sequence
        self.digest = digest
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_checkpoint, v2base.GetCheckpointRequest(
            sequence_number=self.sequence, digest=self.digest, read_mask=self.field_mask
        )


class GetEpoch(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.Epoch

    def __init__(
        self,
        *,
        epoch_number: Optional[int] = None,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.epoch_number = epoch_number
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_epoch, v2base.GetEpochRequest(
            epoch=self.epoch_number, read_mask=self.field_mask
        )


class GetObject(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.Object

    def __init__(
        self,
        *,
        object_id: str,
        version: Optional[int] = None,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.object_id = object_id
        self.version = version
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_object, v2base.GetObjectRequest(
            object_id=self.object_id, version=self.version, read_mask=self.field_mask
        )


class GetObjects(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.BatchGetObjectsResponse

    def __init__(
        self,
        *,
        objects: tuple[str, Optional[int]],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.objects = objects
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        o_list = [v2base.GetObjectRequest(x, y) for x, y in self.objects]
        return stub.batch_get_objects, v2base.BatchGetObjectsRequest(
            requests=o_list, read_mask=self.field_mask
        )


class GetTransaction(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.ExecutedTransaction

    def __init__(
        self,
        *,
        digest: str,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.digest = digest
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_transaction, v2base.GetTransactionRequest(
            digest=self.digest, read_mask=self.field_mask
        )


class GetTransactions(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.BatchGetTransactionsResponse

    def __init__(
        self,
        *,
        transactions: list[str],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.transactions = transactions
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_transactions, v2base.BatchGetTransactionsRequest(
            digests=self.transactions, read_mask=self.field_mask
        )
