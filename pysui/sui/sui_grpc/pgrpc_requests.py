#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Requests"""

import base64
from typing import Any, Callable, Optional

from deprecated.sphinx import versionadded, deprecated, versionchanged
import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.sui.sui_grpc.pgrpc_absreq as absreq

if absreq.CURRENT_VERSION[1] >= 87:
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base
    import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2alpha as v2alpha
else:
    raise ValueError("HARD STOP")

# Ledger Service Commands


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
        """Prepare the request for submission."""
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


OBJECT_DEFAULT_FIELDS: list[str] = [
    "owner",
    "version",
    "object_id",
    "object_type",
    "digest",
    "json",
    "previous_transaction",
]


class GetObject(absreq.PGRPC_Request):
    """Get object request."""

    RESULT_TYPE: betterproto2.Message = v2base.Object

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

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_object, v2base.GetObjectRequest(
            object_id=self.object_id, read_mask=self.field_mask
        )


class GetPastObject(absreq.PGRPC_Request):
    """Get object request."""

    RESULT_TYPE: betterproto2.Message = v2base.Object

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

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_object, v2base.GetObjectRequest(
            object_id=self.object_id, version=self.version, read_mask=self.field_mask
        )


class GetMultipleObjects(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.BatchGetObjectsResponse

    def __init__(
        self,
        *,
        objects: list[str],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        if len(objects) > 50:
            raise ValueError(f"Max object ids 50, {len(objects)} submitted.")
        super().__init__(absreq.Service.LEDGER)
        self.objects = [v2base.GetObjectRequest(obj, None) for obj in objects]
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_objects, v2base.BatchGetObjectsRequest(
            requests=self.objects, read_mask=self.field_mask
        )


class GetMultiplePastObjects(absreq.PGRPC_Request):
    """
    Retrieve information about multiple objects by object ids.
    """

    def __init__(
        self,
        *,
        for_versions: list[dict[str, int]],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """QueryNode initializer to fetch past object information for a list of object keys.

        Where each `dict` (key) is of construct:
        {
            objectId:str, # Object id
            version:int   # Version to fetch
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
                v2base.GetObjectRequest(entry["objectId"], entry["version"])
            )
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    def to_request(
        self, *, stub: v2base.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_objects, v2base.BatchGetObjectsRequest(
            requests=self.objects, read_mask=self.field_mask
        )


class GetOwnedObjects(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.ListOwnedObjectsResponse

    def __init__(
        self,
        *,
        owner: str,
        object_type: Optional[str] = None,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LIVEDATA)
        self.owner = owner
        self.object_type = object_type
        self.page_size = page_size
        self.page_token = page_token

    def to_request(
        self, *, stub: v2alpha.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.list_owned_objects, v2alpha.ListOwnedObjectsRequest(
            owner=self.owner,
            object_type=self.object_type,
            page_size=self.page_size,
            page_token=self.page_token,
        )


class GetGas(GetOwnedObjects):
    """Get gas objects owned by address using GetOwnedObjects."""

    def __init__(self, *, owner, page_size=None, page_token=None):
        """Initializer."""
        super().__init__(
            owner=owner,
            object_type="0x2::coin::Coin<0x2::sui::SUI>",
            page_size=page_size,
            page_token=page_token,
        )


class GetStaked(GetOwnedObjects):
    """Get staked coin objects owned by address using GetOwnedObjects."""

    def __init__(self, *, owner, page_size=None, page_token=None):
        """Initializer."""
        super().__init__(
            owner=owner,
            object_type="0x3::staking_pool::StakedSui",
            page_size=page_size,
            page_token=page_token,
        )


class GetCoinInfo(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.GetCoinInfoResponse

    def __init__(
        self,
        *,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LIVEDATA)
        self.coin_type = coin_type

    def to_request(
        self, *, stub: v2alpha.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_coin_info, v2alpha.GetCoinInfoRequest(
            coin_type=self.coin_type,
        )


class GetBalance(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.GetBalanceResponse

    def __init__(
        self,
        *,
        owner: str,
        coin_type: str,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LIVEDATA)
        self.owner = owner
        self.coin_type = coin_type

    def to_request(
        self, *, stub: v2alpha.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_balance, v2alpha.GetBalanceRequest(
            owner=self.owner, coin_type=self.coin_type
        )


class GetBalances(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.ListBalancesResponse

    def __init__(
        self,
        *,
        owner: str,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LIVEDATA)
        self.owner = owner
        self.page_size = page_size
        self.page_token = page_token

    def to_request(
        self, *, stub: v2alpha.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.list_balances, v2alpha.ListBalancesRequest(
            owner=self.owner,
            page_size=self.page_size,
            page_token=self.page_token,
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


class ExecuteTransactions(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2base.ExecuteTransactionResponse

    def __init__(
        self,
        *,
        transaction: str | bytes,
        signatures: list[str | bytes],
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.TRANSACTION)

        self.transaction = v2base.Transaction(
            bcs=(
                v2base.Bcs(value=transaction, name="Transaction")
                if isinstance(transaction, bytes)
                else v2base.Bcs(value=base64.b64decode(transaction))
            )
        )
        self.signatures: list[v2base.UserSignature] = []
        for sig in signatures:
            if isinstance(sig, str):
                self.signatures.append(
                    v2base.UserSignature(
                        bcs=v2base.Bcs(
                            value=base64.b64decode(sig), name="UserSignature"
                        )
                    )
                )
            else:
                self.signatures.append(
                    v2base.UserSignature(
                        bcs=v2base.Bcs(value=sig, name="UserSignature")
                    )
                )
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2base.TransactionExecutionServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.execute_transaction, v2base.ExecuteTransactionRequest(
            transaction=self.transaction,
            signatures=self.signatures,
            read_mask=self.field_mask,
        )


class SimulateTransaction(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.SimulateTransactionResponse

    def __init__(
        self,
        *,
        transaction: str | bytes,
        checks_enabled: Optional[bool] = True,
        gas_selection: Optional[bool] = True,
        field_mask: Optional[list[str]] = None,
    ):
        """."""
        super().__init__(absreq.Service.LIVEDATA)
        self.transaction = v2base.Transaction(
            bcs=(
                v2base.Bcs(value=transaction, name="Transaction")
                if isinstance(transaction, bytes)
                else v2base.Bcs(value=base64.b64decode(transaction))
            )
        )
        self.checks_enables = (
            v2alpha.SimulateTransactionRequestVmChecks.ENABLED
            if checks_enabled
            else v2alpha.SimulateTransactionRequestVmChecks.DISABLED
        )
        self.gas_selection = gas_selection
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2alpha.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        return stub.simulate_transaction, v2alpha.SimulateTransactionRequest(
            transaction=self.transaction,
            checks=self.checks_enables,
            do_gas_selection=self.gas_selection,
            read_mask=self.field_mask,
        )


class GetPackage(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.GetPackageResponse

    def __init__(
        self,
        *,
        package_id: str,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_id = package_id

    def to_request(
        self, *, stub: v2alpha.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_package, v2alpha.GetPackageRequest(package_id=self.package_id)


class GetModule(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.GetModuleResponse

    def __init__(self, *, package_id: str, module_name: str) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_id = package_id
        self.module_name = module_name

    def to_request(
        self, *, stub: v2alpha.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_module, v2alpha.GetModuleRequest(
            package_id=self.package_id, module_name=self.module_name
        )


class GetDataType(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.GetDatatypeResponse

    def __init__(self, *, package_id: str, module_name: str, type_name: str) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_id = package_id
        self.module_name = module_name
        self.type_name = type_name

    def to_request(
        self, *, stub: v2alpha.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_datatype, v2alpha.GetDatatypeRequest(
            package_id=self.package_id,
            module_name=self.module_name,
            name=self.type_name,
        )


class GetFunction(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.GetFunctionResponse

    def __init__(
        self, *, package_id: str, module_name: str, function_name: str
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_id = package_id
        self.module_name = module_name
        self.function_name = function_name

    def to_request(
        self, *, stub: v2alpha.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_function, v2alpha.GetFunctionRequest(
            package_id=self.package_id,
            module_name=self.module_name,
            name=self.function_name,
        )


class SubscribeCheckpoint(absreq.PGRPC_Request):

    RESULT_TYPE: betterproto2.Message = v2alpha.SubscribeCheckpointsResponse

    def __init__(
        self,
        *,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.SUBSCRIPTION)
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: v2alpha.SubscriptionServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.subscribe_checkpoints, v2alpha.SubscribeCheckpointsRequest(
            read_mask=self.field_mask
        )
