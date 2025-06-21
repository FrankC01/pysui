#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Requests"""


from typing import Callable, Optional

import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.sui.sui_grpc.pgrpc_absreq as absreq

if absreq.CURRENT_VERSION[1] == 87:
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2alpha as v2alpha
else:
    raise ValueError("HARD STOP")


class GetServiceInfo(absreq.PGRPC_Request):

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

    def result_fields(self) -> list[str]:
        """result_fields Returns a list of fields in the response to it's request.

        :return: list of field names
        :rtype: list[str]
        """
        return super()._result_fields(v2base.GetServiceInfoResponse)


class GetCheckpoint(absreq.PGRPC_Request):

    def __init__(
        self,
        *,
        sequence: Optional[int] = None,
        digest: Optional[str] = None,
        field_mask: Optional[list[str]] = None,
    ):
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

    def result_fields(self) -> list[str]:
        """result_fields Returns a list of fields in the response to it's request.

        :return: list of field names
        :rtype: list[str]
        """
        return super()._result_fields(v2base.Checkpoint)


class GetEpoch(absreq.PGRPC_Request):

    def __init__(
        self,
        *,
        epock_number: Optional[int] = None,
        field_mask: Optional[list[str]] = None,
    ):
        super().__init__(absreq.Service.LEDGER)
        self.epock_number = epock_number
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_epoch, v2base.GetEpochRequest(
            epoch=self.epock_number, read_mask=self.field_mask
        )

    def result_fields(self) -> list[str]:
        """result_fields Returns a list of fields in the response to it's request.

        :return: list of field names
        :rtype: list[str]
        """
        return super()._result_fields(v2base.Epoch)
