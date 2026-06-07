#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Requests"""

import base58
import base64
import dataclasses
from typing import Callable, Optional
from deprecated.sphinx import versionadded
import dataclasses_json
import betterproto2
import pysui.sui.sui_grpc.pgrpc_absreq as absreq
from pysui.sui.sui_bcs.bcs import TransactionKind
from pysui.sui.sui_bcs import bcs

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_common.shared_types import ObjectSummary, ObjectSummaryList
from pysui.sui.sui_common.instrumentation import (
    instrumented,
    sync_instrumented,
    sync_measure,
)


class GetServiceInfo(absreq.PGRPC_Request):
    """Query the service for general information about its current state."""

    RESULT_TYPE = sui_prot.GetServiceInfoResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetServiceInfo.__init__")
    def __init__(self) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetServiceInfo.to_request")
    def to_request(
        self,
        *,
        stub: sui_prot.LedgerServiceStub,
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_service_info, sui_prot.GetServiceInfoRequest()


class GetChainIdentifierSC(GetServiceInfo):
    """SC variant: extract chain_id from GetServiceInfoResponse."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetChainIdentifierSC.render")
    def render(self, obj: sui_prot.GetServiceInfoResponse) -> str:
        """Extract chain identifier from service info response."""
        return obj.chain_id or ""


class GetCheckpoint(absreq.PGRPC_Request):
    """Query for retrieving current or specific checkpoints."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetCheckpointResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetCheckpoint.__init__")
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
        self.field_mask = self._field_mask(field_mask) or self._field_mask(["*"])

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetCheckpoint.to_request")
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_checkpoint, sui_prot.GetCheckpointRequest(
            sequence_number=self.sequence, digest=self.digest, read_mask=self.field_mask
        )


class GetLatestCheckpoint(GetCheckpoint):
    """Alias for GetCheckpoint."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetLatestCheckpoint.__init__")
    def __init__(self, *, field_mask=None):
        """Initializer."""
        super().__init__(sequence=None, digest=None, field_mask=field_mask)


class GetCheckpointBySequence(GetCheckpoint):
    """Alias for GetCheckpoint"""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetCheckpointBySequence.__init__"
    )
    def __init__(self, *, sequence_number: int, field_mask=None):
        """Initializer."""
        super().__init__(sequence=sequence_number, digest=None, field_mask=field_mask)


class GetCheckpointByDigest(GetCheckpoint):
    """Alias for GetCheckpoint"""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetCheckpointByDigest.__init__"
    )
    def __init__(self, *, digest: str, field_mask=None):
        """Initializer."""
        super().__init__(sequence=None, digest=digest, field_mask=field_mask)


class GetEpoch(absreq.PGRPC_Request):
    """Query for retrieving current or speciic Epochs."""

    RESULT_TYPE: betterproto2.Message = sui_prot.Epoch

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetEpoch.__init__")
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

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetEpoch.to_request")
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_epoch, sui_prot.GetEpochRequest(
            epoch=self.epoch_number, read_mask=self.field_mask
        )


class GetLatestSuiSystemState(GetEpoch):
    """GetLatestSuiSystemState return the current Sui system state."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetLatestSuiSystemState.__init__"
    )
    def __init__(self):
        """Initializer."""
        super().__init__(field_mask=["system_state"])

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetLatestSuiSystemState.render"
    )
    def render(self, gepoch: sui_prot.GetEpochResponse) -> sui_prot.SystemState:
        """Render the response payload into a SystemState message."""
        return gepoch.epoch.system_state


class GetLatestSuiSystemStateSC(GetLatestSuiSystemState):
    """SC variant of GetLatestSuiSystemState — satisfies SuiCommand sibling contract."""


class GetCurrentValidators(GetEpoch):
    """Return all the currently active validators"""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetCurrentValidators.__init__"
    )
    def __init__(self):
        """Initializer."""
        super().__init__(field_mask=["system_state.validators.active_validators"])


class GetCurrentValidatorsSC(GetCurrentValidators):
    """SC variant: render extracts active_validators list from Epoch response."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetCurrentValidatorsSC.render"
    )
    def render(self, gepoch: sui_prot.GetEpochResponse) -> "ValidatorsResult":
        """Extract active validators from epoch system state."""
        return ValidatorsResult(
            validators=gepoch.epoch.system_state.validators.active_validators,
            next_page_token=None,
        )


class GetBasicCurrentEpochInfo(GetEpoch):
    """GetEpoch narrowed to the four fields needed for gas and expiry building."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetBasicCurrentEpochInfo.__init__"
    )
    def __init__(self):
        """Initializer."""
        super().__init__(field_mask=["epoch", "reference_gas_price", "start", "end"])

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetBasicCurrentEpochInfo.render"
    )
    def render(self, gepoch: sui_prot.GetEpochResponse) -> sui_prot.Epoch:
        """Return the Epoch message directly."""
        return gepoch.epoch


class GetProtocolConfig(GetEpoch):
    """GetProtocolConfig returns the protocol configuration for a specific version or current."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ProtocolConfig

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetProtocolConfig.__init__")
    def __init__(self, *, version: Optional[int] = None):
        """Initializer.

        :param version: Protocol version to retrieve, defaults to None (current)
        :type version: Optional[int]
        """
        super().__init__(epoch_number=version, field_mask=["protocol_config"])

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetProtocolConfig.render")
    def render(self, gepoch: sui_prot.GetEpochResponse) -> sui_prot.ProtocolConfig:
        """Return the ProtocolConfig message from the response."""
        return gepoch.epoch.protocol_config


OBJECT_DEFAULT_FIELDS: list[str] = [
    "owner",
    "version",
    "object_id",
    "object_type",
    "digest",
    "balance",
    "display",
    "json",
    "previous_transaction",
]


class GetObject(absreq.PGRPC_Request):
    """Query to retrieve the current version of an object."""

    RESULT_TYPE: betterproto2.Message = sui_prot.Object

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObject.__init__")
    def __init__(
        self,
        *,
        object_id: str,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.object_id = object_id
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObject.to_request")
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_object, sui_prot.GetObjectRequest(
            object_id=self.object_id, read_mask=self.field_mask
        )


class GetPastObject(absreq.PGRPC_Request):
    """Query to retrieve a specific version of an object."""

    RESULT_TYPE: betterproto2.Message = sui_prot.Object

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPastObject.__init__")
    def __init__(
        self,
        *,
        object_id: str,
        version: int,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.object_id = object_id
        self.version = version
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPastObject.to_request")
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_object, sui_prot.GetObjectRequest(
            object_id=self.object_id, version=self.version, read_mask=self.field_mask
        )


class GetObjectSC(GetObject):
    """SC variant: unwraps GetObjectResponse → Object (canonical shape)."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObjectSC.__init__")
    def __init__(
        self, *, object_id: str, field_mask: Optional[list[str]] = None
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            object_id=object_id, field_mask=field_mask if field_mask else ["*"]
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObjectSC.render")
    def render(self, obj: sui_prot.GetObjectResponse) -> sui_prot.Object:
        """Extract the inner Object from the gRPC wrapper."""
        return obj.object


class GetPastObjectSC(GetPastObject):
    """SC variant: unwraps GetObjectResponse → Object (canonical shape)."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPastObjectSC.__init__")
    def __init__(
        self, *, object_id: str, version: int, field_mask: Optional[list[str]] = None
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            object_id=object_id,
            version=version,
            field_mask=field_mask if field_mask else ["*"],
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPastObjectSC.render")
    def render(self, obj: sui_prot.GetObjectResponse) -> sui_prot.Object:
        """Extract the inner Object from the gRPC wrapper."""
        return obj.object


class GetMultipleObjects(absreq.PGRPC_Request):
    """Query to retrieve multiple objects current state."""

    RESULT_TYPE: betterproto2.Message = sui_prot.BatchGetObjectsResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjects.__init__")
    def __init__(
        self,
        *,
        object_ids: list[str],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        if len(object_ids) > 50:
            raise ValueError(f"Max object ids 50, {len(object_ids)} submitted.")
        super().__init__(absreq.Service.LEDGER)
        self.objects = [sui_prot.GetObjectRequest(obj, None) for obj in object_ids]
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjects.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_objects, sui_prot.BatchGetObjectsRequest(
            requests=self.objects, read_mask=self.field_mask
        )


class GetMultipleObjectsSC(GetMultipleObjects):
    """SC variant for GetMultipleObjects SuiCommand: returns all object fields."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjectsSC.__init__"
    )
    def __init__(
        self,
        *,
        object_ids: list[str],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            object_ids=object_ids,
            field_mask=field_mask if field_mask else ["*"],
        )


_SUMMARY_FIELD_MASK = ["owner", "version", "object_id", "digest"]


class GetMultipleObjectsSummarySC(GetMultipleObjects):
    """SC variant: normalizes BatchGetObjectsResponse → ObjectSummaryList."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjectsSummarySC.__init__"
    )
    def __init__(self, *, object_ids: list[str]) -> None:
        """Initializer."""
        super().__init__(object_ids=object_ids, field_mask=_SUMMARY_FIELD_MASK)

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultipleObjectsSummarySC.render"
    )
    def render(self, resp: sui_prot.BatchGetObjectsResponse) -> ObjectSummaryList:
        """Convert gRPC batch response to ObjectSummaryList."""
        entries: list[ObjectSummary] = []
        for obj_result in resp.objects:
            obj = obj_result.object
            if obj is None:
                continue
            oid_str: str = obj.object_id or ""
            version: int = obj.version or 0
            digest_str: str = obj.digest or ""
            owner_kind: str = (
                obj.owner.kind.name
                if obj.owner and obj.owner.kind is not None
                else "OWNER_KIND_UNKNOWN"
            )
            if owner_kind == "SHARED":
                entries.append(
                    ObjectSummary(
                        objectId=oid_str,
                        version=str(version),
                        digest=digest_str,
                        owner=None,
                        initialSharedVersion=str(obj.owner.version or 0),
                    )
                )
            elif owner_kind in ("ADDRESS", "OBJECT"):
                entries.append(
                    ObjectSummary(
                        objectId=oid_str,
                        version=str(version),
                        digest=digest_str,
                        owner=obj.owner.address if owner_kind == "ADDRESS" else None,
                    )
                )
            else:
                entries.append(
                    ObjectSummary(
                        objectId=oid_str,
                        version=str(version),
                        digest=digest_str,
                        owner=None,
                    )
                )
        return ObjectSummaryList(objects=entries)


class GetObjectSummarySC(GetObject):
    """SC variant: resolves a single object to ObjectSummary."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObjectSummarySC.__init__")
    def __init__(self, *, object_id: str) -> None:
        """Initializer."""
        super().__init__(object_id=object_id, field_mask=_SUMMARY_FIELD_MASK)

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObjectSummarySC.render")
    def render(self, resp: sui_prot.GetObjectResponse) -> ObjectSummary:
        """Convert gRPC GetObjectResponse to ObjectSummary."""
        obj = resp.object
        oid_str: str = obj.object_id or ""
        version: int = obj.version or 0
        digest_str: str = obj.digest or ""
        owner_kind: str = (
            obj.owner.kind.name
            if obj.owner and obj.owner.kind is not None
            else "OWNER_KIND_UNKNOWN"
        )
        if owner_kind == "SHARED":
            return ObjectSummary(
                objectId=oid_str,
                version=str(version),
                digest=digest_str,
                owner=None,
                initialSharedVersion=str(obj.owner.version or 0),
            )
        elif owner_kind in ("ADDRESS", "OBJECT"):
            return ObjectSummary(
                objectId=oid_str,
                version=str(version),
                digest=digest_str,
                owner=obj.owner.address if owner_kind == "ADDRESS" else None,
            )
        else:
            return ObjectSummary(
                objectId=oid_str,
                version=str(version),
                digest=digest_str,
                owner=None,
            )


class GetDynamicFields(absreq.PGRPC_Request):
    """Get dynamic fields of object."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListDynamicFieldsResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetDynamicFields.__init__")
    def __init__(
        self,
        object_id: str,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
        field_mask: Optional[list[str]] = None,
    ):
        """Initializer."""
        super().__init__(absreq.Service.STATE)
        self.parent = object_id
        self.page_size = page_size
        self.page_token = page_token
        self.field_mask = (
            self._field_mask(field_mask) if field_mask else self._field_mask(["*"])
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetDynamicFields.to_request")
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.list_dynamic_fields, sui_prot.ListDynamicFieldsRequest(
            parent=self.parent,
            page_size=self.page_size,
            page_token=self.page_token,
            read_mask=self.field_mask,
        )


class GetMultiplePastObjects(absreq.PGRPC_Request):
    """Retrieve information about multiple objects by object ids."""

    RESULT_TYPE: betterproto2.Message = sui_prot.BatchGetObjectsResponse

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultiplePastObjects.__init__"
    )
    def __init__(
        self,
        *,
        for_versions: list[dict[str, str | int]],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """QueryNode initializer to fetch past object information for a list of object keys.

        Where each ``dict`` entry must have the following keys::

            {
                "objectId": str,  # Object id
                "version": int    # Version to fetch
            }

        :param for_versions: The list of object and version dictionaries
        :type for_versions: list[dict]

        """
        if len(for_versions) > 50:
            raise ValueError(f"Max object ids 50, {len(for_versions)} submitted.")
        super().__init__(absreq.Service.LEDGER)
        self.objects = []
        for entry in for_versions:
            self.objects.append(
                sui_prot.GetObjectRequest(entry["objectId"], entry["version"])
            )
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultiplePastObjects.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_objects, sui_prot.BatchGetObjectsRequest(
            requests=self.objects, read_mask=self.field_mask
        )


class GetMultiplePastObjectsSC(GetMultiplePastObjects):
    """SC variant for GetMultiplePastObjects SuiCommand: returns all object fields."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetMultiplePastObjectsSC.__init__"
    )
    def __init__(
        self,
        *,
        object_versions: list[tuple[str, int]],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer with full field mask."""
        for_versions = [
            {"objectId": obj_id, "version": version}
            for obj_id, version in object_versions
        ]
        super().__init__(
            for_versions=for_versions,
            field_mask=field_mask if field_mask else ["*"],
        )


@sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests._is_coin_reservation")
def _is_coin_reservation(obj: sui_prot.Object) -> bool:
    """Return True if obj is a synthetic coin reservation rather than a real Sui object."""
    if obj.version == 0:
        return True
    if obj.digest:
        digest_bytes = base58.b58decode(obj.digest)
        return len(digest_bytes) >= 32 and digest_bytes[12:32] == b"\xac" * 20
    return False


class GetObjectsOwnedByAddress(absreq.PGRPC_Request):
    """Query to retrieve owned object by type."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListOwnedObjectsResponse

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetObjectsOwnedByAddress.__init__"
    )
    def __init__(
        self,
        *,
        owner: str,
        object_type: Optional[str] = None,
        field_mask: Optional[list[str]] = None,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.STATE)
        self.owner = owner
        self.object_type = object_type
        self.page_size = page_size
        self.page_token = page_token
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetObjectsOwnedByAddress.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.list_owned_objects, sui_prot.ListOwnedObjectsRequest(
            owner=self.owner,
            object_type=self.object_type,
            read_mask=self.field_mask,
            page_size=self.page_size,
            page_token=self.page_token,
        )

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetObjectsOwnedByAddress.render"
    )
    def render(
        self, resp: sui_prot.ListOwnedObjectsResponse
    ) -> sui_prot.ListOwnedObjectsResponse:
        """Filter out synthetic coin reservation objects."""
        resp.objects = [o for o in resp.objects if not _is_coin_reservation(o)]
        return resp


class GetObjectsOwnedByAddressSC(GetObjectsOwnedByAddress):
    """SC variant for GetObjectsOwnedByAddress SuiCommand: returns all object fields."""

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetObjectsOwnedByAddressSC.__init__"
    )
    def __init__(
        self,
        *,
        owner: str,
        object_type: Optional[str] = None,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            owner=owner,
            object_type=object_type,
            field_mask=["*"],
            page_size=page_size,
            page_token=page_token,
        )


class GetObjectsForTypeSC(GetObjectsOwnedByAddress):
    """SC variant for GetObjectsForType SuiCommand: returns all object fields."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetObjectsForTypeSC.__init__")
    def __init__(
        self,
        *,
        owner: str,
        object_type: Optional[str] = None,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            owner=owner,
            object_type=object_type,
            field_mask=["*"],
            page_size=page_size,
            page_token=page_token,
        )


class GetCoins(GetObjectsOwnedByAddress):
    """Query Sui coin objects by type owned by address using GetOwnedObjects."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetCoins.__init__")
    def __init__(
        self,
        *,
        owner,
        coin_type: Optional[str] = None,
        field_mask: Optional[list[str]] = None,
        page_size=None,
        page_token=None,
    ):
        """Initializer."""
        super().__init__(
            owner=owner,
            object_type=coin_type or "0x2::coin::Coin<0x2::sui::SUI>",
            field_mask=field_mask,
            page_size=page_size,
            page_token=page_token,
        )


class GetCoinsSC(GetCoins):
    """SC variant for GetCoins SuiCommand: returns all object fields."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetCoinsSC.__init__")
    def __init__(
        self,
        *,
        owner: str,
        coin_type: Optional[str] = None,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            owner=owner,
            coin_type=coin_type,
            field_mask=["*"],
            page_size=page_size,
            page_token=page_token,
        )


class GetGas(GetObjectsOwnedByAddress):
    """Query Sui gas objects owned by address using GetCoins."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetGas.__init__")
    def __init__(
        self,
        *,
        owner,
        field_mask: Optional[list[str]] = None,
        page_size=None,
        page_token=None,
    ):
        """Initializer."""
        super().__init__(
            owner=owner,
            object_type="0x2::coin::Coin<0x2::sui::SUI>",
            field_mask=field_mask,
            page_size=page_size,
            page_token=page_token,
        )


class GetGasSC(GetGas):
    """SC variant for GetGas SuiCommand: returns all object fields."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetGasSC.__init__")
    def __init__(
        self,
        *,
        owner: str,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer with full field mask."""
        super().__init__(
            owner=owner,
            field_mask=["*"],
            page_size=page_size,
            page_token=page_token,
        )


class GetStaked(GetObjectsOwnedByAddress):
    """Query staked coin objects owned by address using GetOwnedObjects."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetStaked.__init__")
    def __init__(
        self,
        *,
        owner,
        field_mask: Optional[list[str]] = None,
        page_size=None,
        page_token=None,
    ):
        """Initializer."""
        super().__init__(
            owner=owner,
            object_type="0x3::staking_pool::StakedSui",
            field_mask=field_mask,
            page_size=page_size,
            page_token=page_token,
        )


class GetDelegatedStakes(GetStaked):
    """Alias for GetStaked."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetDelegatedStakes.__init__")
    def __init__(
        self,
        *,
        owner,
        field_mask: Optional[list[str]] = None,
        page_size=None,
        page_token=None,
    ):
        """Initializer"""
        super().__init__(
            owner=owner,
            field_mask=field_mask,
            page_size=page_size,
            page_token=page_token,
        )


class GetCoinMetaData(absreq.PGRPC_Request):
    """Query to return information on specific coin type."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetCoinInfoResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetCoinMetaData.__init__")
    def __init__(
        self,
        *,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.STATE)
        self.coin_type = coin_type

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetCoinMetaData.to_request")
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_coin_info, sui_prot.GetCoinInfoRequest(
            coin_type=self.coin_type,
        )


@versionadded(version="0.97.0", reason="Parity with GraphQL.")
class GetAddressCoinBalance(absreq.PGRPC_Request):
    """Query to fetch the total address and coin balance for specific coin type."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetBalanceResponse

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetAddressCoinBalance.__init__"
    )
    def __init__(
        self,
        *,
        owner: str,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.STATE)
        self.owner = owner
        self.coin_type = coin_type

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetAddressCoinBalance.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_balance, sui_prot.GetBalanceRequest(
            owner=self.owner, coin_type=self.coin_type
        )


@versionadded(version="0.97.0", reason="Parity with GraphQL.")
class GetAddressCoinBalances(absreq.PGRPC_Request):
    """Query to retrieve the total balance for all types for owner."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListBalancesResponse

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetAddressCoinBalances.__init__"
    )
    def __init__(
        self,
        *,
        owner: str,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.STATE)
        self.owner = owner
        self.page_size = page_size
        self.page_token = page_token

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetAddressCoinBalances.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.list_balances, sui_prot.ListBalancesRequest(
            owner=self.owner,
            page_size=self.page_size,
            page_token=self.page_token,
        )


class GetTransaction(absreq.PGRPC_Request):
    """Query to retrieve transaction details by it's digest."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ExecutedTransaction

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransaction.__init__")
    def __init__(
        self,
        *,
        digest: str,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.digest = digest
        self.field_mask = (
            self._field_mask(field_mask)
            if field_mask
            else self._field_mask(["transaction", "effects"])
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransaction.to_request")
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_transaction, sui_prot.GetTransactionRequest(
            digest=self.digest, read_mask=self.field_mask
        )


class GetTransactions(absreq.PGRPC_Request):
    """Query to retrieve multiple transaction details by their digests."""

    RESULT_TYPE: betterproto2.Message = sui_prot.BatchGetTransactionsResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactions.__init__")
    def __init__(
        self,
        *,
        transactions: list[str],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)
        self.transactions = transactions
        self.field_mask = self._field_mask(field_mask) or self._field_mask(["*"])

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactions.to_request")
    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_transactions, sui_prot.BatchGetTransactionsRequest(
            digests=self.transactions, read_mask=self.field_mask
        )


class GetTransactionSC(GetTransaction):
    """SC sibling: unwraps GetTransactionResponse → ExecutedTransaction | None."""

    not_found_as_none: bool = True

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactionSC.__init__")
    def __init__(self, *, digest: str, field_mask: Optional[list[str]] = None) -> None:
        """Initializer — fetches all ExecutedTransaction fields by default."""
        super().__init__(
            digest=digest,
            field_mask=field_mask
            or [
                "digest",
                "transaction",
                "signatures",
                "effects",
                "events",
                "checkpoint",
                "timestamp",
                "balance_changes",
                "objects.objects.bcs",
            ],
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactionSC.render")
    def render(
        self, obj: sui_prot.GetTransactionResponse
    ) -> sui_prot.ExecutedTransaction | None:
        """Extract ExecutedTransaction from gRPC wrapper; None for non-existent digest."""
        return obj.transaction


class GetTransactionsSC(GetTransactions):
    """SC sibling: unwraps BatchGetTransactionsResponse → list[ExecutedTransaction | None]."""

    not_found_as_none: bool = True

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactionsSC.__init__")
    def __init__(
        self,
        *,
        transactions: list[str],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer — fetches all ExecutedTransaction fields by default."""
        super().__init__(
            transactions=transactions,
            field_mask=field_mask
            or [
                "digest",
                "transaction",
                "signatures",
                "effects",
                "events",
                "checkpoint",
                "timestamp",
                "balance_changes",
                "objects.objects.bcs",
            ],
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactionsSC.render")
    def render(
        self, obj: sui_prot.BatchGetTransactionsResponse
    ) -> list[sui_prot.ExecutedTransaction | None]:
        """Extract transaction from each result slot; None preserved at original index."""
        return [item.transaction for item in obj.transactions]


class GetTransactionKindSC(GetTransaction):
    """SC sibling: field-masks to transaction.kind, extracts TransactionKind."""

    not_found_as_none: bool = True

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetTransactionKindSC.__init__"
    )
    def __init__(self, *, digest: str) -> None:
        """Initializer."""
        super().__init__(digest=digest, field_mask=["transaction.kind"])

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetTransactionKindSC.render")
    def render(
        self, obj: sui_prot.GetTransactionResponse
    ) -> sui_prot.TransactionKind | None:
        """Extract TransactionKind from nested gRPC response; None if digest not found."""
        if obj.transaction is None:
            return None
        return obj.transaction.transaction.kind


class ExecuteTransaction(absreq.PGRPC_Request):
    """Executes a signed transaction block on the chain."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ExecuteTransactionResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.ExecuteTransaction.__init__")
    def __init__(
        self,
        *,
        tx_bytestr: str | bytes,
        sig_array: list[str | bytes],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.TRANSACTION)

        self.transaction = sui_prot.Transaction(
            bcs=(
                sui_prot.Bcs(value=tx_bytestr, name="Transaction")
                if isinstance(tx_bytestr, bytes)
                else sui_prot.Bcs(value=base64.b64decode(tx_bytestr))
            )
        )
        self.signatures: list[sui_prot.UserSignature] = []
        for sig in sig_array:
            if isinstance(sig, str):
                self.signatures.append(
                    sui_prot.UserSignature(
                        bcs=sui_prot.Bcs(
                            value=base64.b64decode(sig), name="UserSignature"
                        )
                    )
                )
            else:
                self.signatures.append(
                    sui_prot.UserSignature(
                        bcs=sui_prot.Bcs(value=sig, name="UserSignature")
                    )
                )
        self.field_mask = self._field_mask(field_mask) or self._field_mask(["*"])

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.ExecuteTransaction.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.TransactionExecutionServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.execute_transaction, sui_prot.ExecuteTransactionRequest(
            transaction=self.transaction,
            signatures=self.signatures,
            read_mask=self.field_mask,
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.ExecuteTransaction.render")
    def render(
        self, response: sui_prot.ExecuteTransactionResponse
    ) -> sui_prot.ExecutedTransaction | None:
        """Unwrap ExecuteTransactionResponse to ExecutedTransaction."""
        return response.transaction


class SimulateTransaction(absreq.PGRPC_Request):
    """Simulates executnig a transaction block on the chain."""

    RESULT_TYPE: betterproto2.Message = sui_prot.SimulateTransactionResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.SimulateTransaction.__init__")
    def __init__(
        self,
        *,
        transaction: str | bytes,
        checks_enabled: Optional[bool] = True,
        gas_selection: Optional[bool] = True,
        field_mask: Optional[list[str]] = None,
    ):
        """."""
        super().__init__(absreq.Service.TRANSACTION)
        with sync_measure("grpc.SimulateTransaction.init"):
            transaction = (
                transaction
                if isinstance(transaction, bytes)
                else base64.b64decode(transaction)
            )
            self.transaction = sui_prot.Transaction(
                bcs=(sui_prot.Bcs(value=transaction, name="Transaction"))
            )
            self.checks_enables = (
                sui_prot.SimulateTransactionRequestTransactionChecks.ENABLED
                if checks_enabled
                else sui_prot.SimulateTransactionRequestTransactionChecks.DISABLED
            )
            self.gas_selection = gas_selection
            self.field_mask = self._field_mask(field_mask) or self._field_mask(["*"])

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.SimulateTransaction.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Build the gRPC request tuple (stub_method, request_message)."""
        simtdata = sui_prot.SimulateTransactionRequest(
            transaction=self.transaction,
            checks=self.checks_enables,
            do_gas_selection=self.gas_selection,
            read_mask=self.field_mask,
        )
        return stub.simulate_transaction, simtdata


@versionadded(version="0.99.0", reason="Replaces deprecated SimulateTransactionLKind.")
class SimulateTransactionKind(absreq.PGRPC_Request):
    """Simulates executing a transaction block (from a TransactionKind) on the chain."""

    RESULT_TYPE: betterproto2.Message = sui_prot.SimulateTransactionResponse

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.SimulateTransactionKind.__init__"
    )
    def __init__(
        self,
        *,
        transaction: TransactionKind,
        sender: str,
        checks_enabled: Optional[bool] = True,
        gas_selection: Optional[bool] = True,
        txn_expires_after: Optional[int] = None,
        field_mask: Optional[list[str]] = None,
    ):
        """__init__ Initialize SimulateTransactionKind request.

        :param transaction: The programmable TransactionKind BCS object
        :type transaction: TransactionKind
        :param sender: Sui address of the transaction sender
        :type sender: str
        :param checks_enabled: Whether to enable transaction checks, defaults to True
        :type checks_enabled: Optional[bool]
        :param gas_selection: Whether to perform gas selection, defaults to True
        :type gas_selection: Optional[bool]
        :param txn_expires_after: Epoch after which transaction expires, defaults to None
        :type txn_expires_after: Optional[int]
        :param field_mask: Field mask for response filtering, defaults to ["*"]
        :type field_mask: Optional[list[str]]
        """
        super().__init__(absreq.Service.TRANSACTION)
        with sync_measure("grpc.SimulateTransactionKind.init"):
            prgrm_txn = transaction.value
            inputs: list[sui_prot.Input] = []
            cmds: list[sui_prot.Command] = []
            trx_exp = None
            for input in prgrm_txn.Inputs:
                if input.enum_name == "Pure":
                    inputs.append(
                        sui_prot.Input(
                            kind=sui_prot.InputInputKind.PURE, pure=bytes(input.value)
                        )
                    )
                elif input.enum_name == "Object":
                    oarg = input.value
                    inputs.append(oarg.value.to_grpc_input(oarg.enum_name))
                elif input.enum_name == "FundsWithdrawal":
                    fwid: bcs.FundsWithdrawal = input.value
                    inputs.append(fwid.to_grpc_input())
            for cmd in prgrm_txn.Command:
                cmds.append(cmd.value.to_grpc_command())
            if txn_expires_after:
                trx_exp = sui_prot.TransactionExpiration(
                    kind=sui_prot.TransactionExpirationTransactionExpirationKind.EPOCH,
                    epoch=txn_expires_after,
                )
            self.transaction = sui_prot.Transaction(
                kind=sui_prot.TransactionKind(
                    programmable_transaction=sui_prot.ProgrammableTransaction(
                        inputs=inputs, commands=cmds
                    )
                ),
                expiration=trx_exp,
                sender=sender,
            )
            self.checks_enables = (
                sui_prot.SimulateTransactionRequestTransactionChecks.ENABLED
                if checks_enabled
                else sui_prot.SimulateTransactionRequestTransactionChecks.DISABLED
            )
            self.gas_selection = gas_selection
            self.field_mask = self._field_mask(field_mask) or self._field_mask(["*"])

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.SimulateTransactionKind.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.StateServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        req = sui_prot.SimulateTransactionRequest(
            transaction=self.transaction,
            checks=self.checks_enables,
            do_gas_selection=self.gas_selection,
            read_mask=self.field_mask,
        )
        return stub.simulate_transaction, req


# TODO: Test with Devnet
class GetPackageVersions(absreq.PGRPC_Request):
    """Query a Move package's versions by it's storage ID."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListPackageVersionsResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPackageVersions.__init__")
    def __init__(
        self,
        *,
        package_storage_id: str,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_storage_id = package_storage_id
        self.page_size = page_size
        self.page_token = page_token

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetPackageVersions.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.list_package_versions, sui_prot.ListPackageVersionsRequest(
            package_id=self.package_storage_id,
            page_size=self.page_size,
            page_token=self.page_token,
        )


class GetPackage(absreq.PGRPC_Request):
    """Query a Move package by it's ID."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetPackageResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPackage.__init__")
    def __init__(
        self,
        *,
        package: str,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_id = package

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetPackage.to_request")
    def to_request(
        self, *, stub: sui_prot.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_package, sui_prot.GetPackageRequest(package_id=self.package_id)


@versionadded(version="0.99.0", reason="Replaces deprecated GetDataType.")
class GetMoveDataType(absreq.PGRPC_Request):
    """Query a Move module's DataType by its name."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetDatatypeResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetMoveDataType.__init__")
    def __init__(self, *, package: str, module_name: str, type_name: str) -> None:
        """__init__ Initialize GetMoveDataType request.

        :param package: The package ID containing the data type
        :type package: str
        :param module_name: The module name containing the data type
        :type module_name: str
        :param type_name: The data type name
        :type type_name: str
        """
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package = package
        self.module_name = module_name
        self.type_name = type_name

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetMoveDataType.to_request")
    def to_request(
        self, *, stub: sui_prot.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_datatype, sui_prot.GetDatatypeRequest(
            package_id=self.package,
            module_name=self.module_name,
            name=self.type_name,
        )


class GetStructure(GetMoveDataType):
    """Convenience subclass of GetMoveDataType using structure_name parameter."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetStructure.__init__")
    def __init__(self, *, package: str, module_name: str, structure_name: str):
        """Initializer."""
        super().__init__(
            package=package, module_name=module_name, type_name=structure_name
        )


# TODO: Move to gRPC types
@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructuresGRPC:
    """Module DataTypes."""

    structures: list[sui_prot.DatatypeDescriptor]
    next_page_token: Optional[bytes] = None


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionsGRPC:
    """Module Functions."""

    functions: list[sui_prot.FunctionDescriptor]
    next_page_token: Optional[bytes] = None


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorsResult:
    """GQL GetCurrentValidators paging result: one page of active validators."""

    validators: list[sui_prot.Validator]
    next_page_token: Optional[bytes] = None


class GetStructures(GetPackage):
    """Alias for GetDataType."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetStructures.__init__")
    def __init__(self, *, package, module_name: str):
        """Initializer."""
        super().__init__(package=package)
        self.module_name = module_name

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetStructures.render")
    def render(self, package: sui_prot.GetPackageResponse) -> MoveStructuresGRPC:
        """Render the response payload into MoveStructuresGRPC."""
        result = list(
            filter(lambda x: x.name == self.module_name, package.package.modules)
        )
        if result:
            return MoveStructuresGRPC(result[0].datatypes)
        else:
            raise ValueError(
                f"Module '{self.module_name}' not found for {self.package_id}"
            )


class GetFunction(absreq.PGRPC_Request):
    """Query a Move module's function by it's name."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetFunctionResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetFunction.__init__")
    def __init__(self, *, package: str, module_name: str, function_name: str) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package = package
        self.module_name = module_name
        self.function_name = function_name

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetFunction.to_request")
    def to_request(
        self, *, stub: sui_prot.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_function, sui_prot.GetFunctionRequest(
            package_id=self.package,
            module_name=self.module_name,
            name=self.function_name,
        )


class GetFunctions(GetPackage):
    """Alias for GetDataType."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetFunctions.__init__")
    def __init__(self, *, package, module_name: str):
        """Initializer."""
        super().__init__(package=package)
        self.module_name = module_name

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetFunctions.render")
    def render(self, package: sui_prot.GetPackageResponse) -> "MoveFunctionsGRPC":
        """Render the response payload into MoveFunctionsGRPC."""
        result = list(
            filter(lambda x: x.name == self.module_name, package.package.modules)
        )
        if result:
            return MoveFunctionsGRPC(result[0].functions)
        else:
            raise ValueError(
                f"Module '{self.module_name}' not found for {self.package_id}"
            )


class GetModule(GetPackage):
    """Alias for GetDataType."""

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetModule.__init__")
    def __init__(self, *, package, module_name: str):
        """Initializer."""
        super().__init__(package=package)
        self.module_name = module_name

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetModule.render")
    def render(self, package: sui_prot.GetPackageResponse) -> sui_prot.Module:
        """Render the response payload to the matching Module entry."""
        result = list(
            filter(lambda x: x.name == self.module_name, package.package.modules)
        )
        if result:
            return result[0]
        else:
            raise ValueError(
                f"Module '{self.module_name}' not found for {self.package_id}"
            )


class SubscribeCheckpoint(absreq.PGRPC_Request):
    """Subscribe to a feed of checkpoints."""

    RESULT_TYPE: betterproto2.Message = sui_prot.SubscribeCheckpointsResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoint.__init__")
    def __init__(
        self,
        *,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.SUBSCRIPTION)
        self.field_mask = self._field_mask(field_mask)

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoint.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.SubscriptionServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.subscribe_checkpoints, sui_prot.SubscribeCheckpointsRequest(
            read_mask=self.field_mask
        )


class VerifySignature(absreq.PGRPC_Request):
    """Verify a signature."""

    RESULT_TYPE: betterproto2.Message = sui_prot.VerifySignatureResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.VerifySignature.__init__")
    def __init__(
        self,
        *,
        address: str | None = None,
        message_type: str,
        message: str | bytes,
        signature: str | bytes,
    ):
        """__init__ _summary_

        :param message_type: Must be 'PersonalMessage' or 'TransactionData'
        :type message_type: str
        :param message: The message base64 encoded string or bytes
        :type message: str | bytes
        :param signature: The signature base64 encoded string or bytes
        :type signature: str | bytes
        :param address: If provided, this address will be used to compare address derived from signature, defaults to None
        :type address: str | None, optional
        """
        _VALID_TYPES = frozenset({"PersonalMessage", "TransactionData"})
        if message_type not in _VALID_TYPES:
            raise ValueError(
                f"VerifySignature: message_type must be one of "
                f"{sorted(_VALID_TYPES)}, got {message_type!r}"
            )
        super().__init__(absreq.Service.SIGNATURE)
        self.address = address
        self.message_type = message_type
        raw_msg = (
            base64.b64decode(message, validate=True)
            if isinstance(message, str)
            else bytes(message)
        )
        if len(raw_msg) > 131072:
            raise ValueError(
                f"VerifySignature: message exceeds 131072 bytes ({len(raw_msg)})"
            )
        if message_type == "PersonalMessage":
            # BCS encodes [u8] as ULEB128(len) + raw bytes; server calls
            # bcs::from_bytes::<&[u8]>(value) which requires this prefix.
            n, prefix = len(raw_msg), bytearray()
            while True:
                b = n & 0x7F
                n >>= 7
                if n:
                    b |= 0x80
                prefix.append(b)
                if not n:
                    break
            raw_msg = bytes(prefix) + raw_msg
        self.message = sui_prot.Bcs(name=message_type, value=raw_msg)
        sig_bytes = (
            base64.b64decode(signature, validate=True)
            if isinstance(signature, str)
            else bytes(signature)
        )
        if len(sig_bytes) > 1024:
            raise ValueError(
                f"VerifySignature: signature exceeds 1024 bytes ({len(sig_bytes)})"
            )
        self.signature = sui_prot.UserSignature(
            bcs=sui_prot.Bcs(name="UserSignature", value=sig_bytes)
        )

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.VerifySignature.to_request")
    def to_request(
        self, *, stub: sui_prot.SignatureVerificationServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.verify_signature, sui_prot.VerifySignatureRequest(
            message=self.message, signature=self.signature, address=self.address
        )


@versionadded(version="0.99.0", reason="Replaces deprecated NameLookup.")
class GetNameServiceAddress(absreq.PGRPC_Request):
    """Resolve a Sui name-service name to an address."""

    RESULT_TYPE: betterproto2.Message = sui_prot.LookupNameResponse

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetNameServiceAddress.__init__"
    )
    def __init__(self, *, name: str | None = None):
        """GetNameServiceAddress constructor.

        :param name: Name to resolve to an address. Accepts '@name' or 'name.sui' forms, defaults to None
        :type name: str | None, optional
        """
        super().__init__(absreq.Service.NAMESERVICE)
        self.name = name

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetNameServiceAddress.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.NameServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.lookup_name, sui_prot.LookupNameRequest(name=self.name)


@versionadded(version="0.99.0", reason="Replaces deprecated ReverseNameLookup.")
class GetNameServiceNames(absreq.PGRPC_Request):
    """Resolve a Sui address to its name-service name(s)."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ReverseLookupNameResponse

    @sync_instrumented("pysui.sui.sui_grpc.pgrpc_requests.GetNameServiceNames.__init__")
    def __init__(self, *, address: str | None = None):
        """GetNameServiceNames constructor.

        :param address: Address to resolve to a name, defaults to None
        :type address: str | None, optional
        """
        super().__init__(absreq.Service.NAMESERVICE)
        self.address = address

    @sync_instrumented(
        "pysui.sui.sui_grpc.pgrpc_requests.GetNameServiceNames.to_request"
    )
    def to_request(
        self, *, stub: sui_prot.NameServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.reverse_lookup_name, sui_prot.ReverseLookupNameRequest(
            address=self.address
        )
