#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC Requests"""

import base64
import dataclasses
from typing import Callable, Optional

import dataclasses_json
from deprecated.sphinx import versionadded, deprecated, versionchanged
import betterproto2
from pysui.sui.sui_grpc.suimsgs.google.protobuf import FieldMask
import pysui.sui.sui_grpc.pgrpc_absreq as absreq
from pysui.sui.sui_bcs.bcs import TransactionKind
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot

# Ledger Service Commands


class GetServiceInfo(absreq.PGRPC_Request):
    """Query the service for general information about its current state."""

    RESULT_TYPE = sui_prot.GetServiceInfoResponse

    def __init__(self) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LEDGER)

    def to_request(
        self,
        *,
        stub: sui_prot.LedgerServiceStub,
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_service_info, sui_prot.GetServiceInfoRequest()


class GetCheckpoint(absreq.PGRPC_Request):
    """Query for retrieving current or specific checkpoints."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetCheckpointResponse

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

    def __init__(self, *, field_mask=None):
        super().__init__(sequence=None, digest=None, field_mask=field_mask)


class GetCheckpointBySequence(GetCheckpoint):
    """Alias for GetCheckpoint"""

    def __init__(self, *, sequence_number: int, field_mask=None):
        super().__init__(sequence=sequence_number, digest=None, field_mask=field_mask)


class GetCheckpointByDigest(GetCheckpoint):
    """Alias for GetCheckpoint"""

    def __init__(self, *, digest: str, field_mask=None):
        super().__init__(sequence=None, digest=digest, field_mask=field_mask)


class GetEpoch(absreq.PGRPC_Request):
    """Query for retrieving current or speciic Epochs."""

    RESULT_TYPE: betterproto2.Message = sui_prot.Epoch

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

    def __init__(self):
        super().__init__(field_mask=["system_state"])

    def render(self, gepoch: sui_prot.GetEpochResponse) -> sui_prot.SystemState:
        return gepoch.epoch.system_state


class GetValidatorsApy(GetEpoch):
    """Get list of validator names and apy."""

    def __init__(self):
        super().__init__(field_mask=["system_state.validators"])

    def render(self, gepoch: sui_prot.GetEpochResponse):
        results: list[dict[str, float]] = []
        # TODO: Get correct APY calc
        for validator in gepoch.epoch.system_state.validators.active_validators:
            results.append(
                {
                    "name": validator.name,
                    "address": validator.address,
                    "apy": validator.staking_pool.sui_balance
                    / validator.staking_pool.rewards_pool,
                }
            )
        return results


class GetCurrentValidators(GetEpoch):
    """Return all the currently active validators"""

    def __init__(self):
        super().__init__(field_mask=["system_state.validators.active_validators"])


OBJECT_DEFAULT_FIELDS: list[str] = [
    "owner",
    "version",
    "object_id",
    "object_type",
    "digest",
    "balance",
    "json",
    "previous_transaction",
]


class GetObject(absreq.PGRPC_Request):
    """Query to retrieve the current version of an object."""

    RESULT_TYPE: betterproto2.Message = sui_prot.Object

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
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_object, sui_prot.GetObjectRequest(
            object_id=self.object_id, read_mask=self.field_mask
        )


# TODO: Move to gRPC types
@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectContentBCS:
    """Raw object content BCS string."""

    object_id: str  # Yes
    bcs: str | bytes
    version: int

    def as_bytes(self) -> bytes:
        """Convert BCS to bytes"""
        return self.bcs if isinstance(self.bcs, bytes) else base64.b64decode(self.bcs)


class GetObjectContent(GetObject):
    """Returns a specific object's content BCS string."""

    def __init__(self, *, object_id, as_bytes: Optional[bool] = True):
        super().__init__(
            object_id=object_id, field_mask=["object_id", "bcs", "version"]
        )
        self.as_bytes = as_bytes

    def render(self, obj: sui_prot.GetObjectResponse) -> ObjectContentBCS:
        bcs_res = (
            obj.object.bcs.value
            if self.as_bytes
            else base64.b64encode(obj.object.bcs.value).decode()
        )
        return ObjectContentBCS(obj.object.object_id, bcs_res, obj.object.version)


class GetPastObject(absreq.PGRPC_Request):
    """Query to retrieve a specific version of an object."""

    RESULT_TYPE: betterproto2.Message = sui_prot.Object

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
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """Prepare the request for submission."""
        return stub.get_object, sui_prot.GetObjectRequest(
            object_id=self.object_id, version=self.version, read_mask=self.field_mask
        )


class GetMultipleObjects(absreq.PGRPC_Request):
    """Query to retrieve multiple objects current state."""

    RESULT_TYPE: betterproto2.Message = sui_prot.BatchGetObjectsResponse

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

    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_objects, sui_prot.BatchGetObjectsRequest(
            requests=self.objects, read_mask=self.field_mask
        )


class GetDynamicFields(absreq.PGRPC_Request):
    """Get dynamic fields of object."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListDynamicFieldsResponse

    def __init__(
        self,
        object_id: str,
        page_size: Optional[int] = None,
        page_token: Optional[bytes] = None,
        field_mask: Optional[list[str]] = None,
    ):
        super().__init__(absreq.Service.LIVEDATA)
        self.parent = object_id
        self.page_size = page_size
        self.page_token = page_token
        self.field_mask = self._field_mask(field_mask)

    def to_request(
        self, *, stub: sui_prot.LiveDataServiceStub
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


# TODO: Move to gRPC types
@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectsContentBCS:
    """Raw object content BCS string."""

    objects_data: list[ObjectContentBCS]


class GetMultipleObjectContent(GetMultipleObjects):
    """Returns multiple object's content BCS string."""

    def __init__(self, *, objects: list[str], as_bytes: Optional[bool] = True):
        super().__init__(object_ids=objects, field_mask=["object_id", "bcs"])
        self.as_bytes = as_bytes

    def render(self, objs: sui_prot.BatchGetObjectsResponse) -> list[sui_prot.Bcs]:
        obj_content: list[ObjectContentBCS] = []
        for obj in objs.objects:
            bcs_res = (
                obj.object.bcs.value
                if self.as_bytes
                else base64.b64encode(obj.object.bcs.value).decode()
            )
            obj_content.append(
                ObjectContentBCS(obj.object.object_id, bcs_res, obj.object.version)
            )

        return ObjectsContentBCS(obj_content)


class GetMultiplePastObjects(absreq.PGRPC_Request):
    """Retrieve information about multiple objects by object ids."""

    RESULT_TYPE: betterproto2.Message = sui_prot.BatchGetObjectsResponse

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
                sui_prot.GetObjectRequest(entry["objectId"], entry["version"])
            )
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
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


class GetObjectsOwnedByAddress(absreq.PGRPC_Request):
    """Query to retrieve owned object by type."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListOwnedObjectsResponse

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
        super().__init__(absreq.Service.LIVEDATA)
        self.owner = owner
        self.object_type = object_type
        self.page_size = page_size
        self.page_token = page_token
        self.field_mask = self._field_mask(
            field_mask if field_mask else OBJECT_DEFAULT_FIELDS
        )

    def to_request(
        self, *, stub: sui_prot.LiveDataServiceStub
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


class GetCoins(GetObjectsOwnedByAddress):
    """Query Sui coin objects by type owned by address using GetOwnedObjects."""

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


class GetGas(GetObjectsOwnedByAddress):
    """Query Sui gas objects owned by address using GetCoins."""

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


class GetStaked(GetObjectsOwnedByAddress):
    """Query staked coin objects owned by address using GetOwnedObjects."""

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

    def __init__(
        self,
        *,
        coin_type: Optional[str] = "0x2::sui::SUI",
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.LIVEDATA)
        self.coin_type = coin_type

    def to_request(
        self, *, stub: sui_prot.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_coin_info, sui_prot.GetCoinInfoRequest(
            coin_type=self.coin_type,
        )


class GetBalance(absreq.PGRPC_Request):
    """Query to retrieve the total balance by coin type for owner."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetBalanceResponse

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
        self, *, stub: sui_prot.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_balance, sui_prot.GetBalanceRequest(
            owner=self.owner, coin_type=self.coin_type
        )


class GetAllCoinBalances(absreq.PGRPC_Request):
    """Query to retrieve the total balance for all types for owner."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListBalancesResponse

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
        self, *, stub: sui_prot.LiveDataServiceStub
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

    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_transaction, sui_prot.GetTransactionRequest(
            digest=self.digest, read_mask=self.field_mask
        )


class GetTx(GetTransaction):
    """Alias for GetTransaction."""

    def __init__(self, *, digest, field_mask=None):
        super().__init__(digest=digest, field_mask=field_mask)


class GetTransactions(absreq.PGRPC_Request):
    """Query to retrieve multiple transaction details by their digests."""

    RESULT_TYPE: betterproto2.Message = sui_prot.BatchGetTransactionsResponse

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

    def to_request(
        self, *, stub: sui_prot.LedgerServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.batch_get_transactions, sui_prot.BatchGetTransactionsRequest(
            digests=self.transactions, read_mask=self.field_mask
        )


class GetMultipleTx(GetTransactions):
    """Alias for GetTransactions."""

    def __init__(self, *, transactions, field_mask=None):
        super().__init__(transactions=transactions, field_mask=field_mask)


class GetTxKind(GetTransaction):

    def __init__(self, *, digest):
        super().__init__(digest=digest, field_mask=["transaction.kind"])


class ExecuteTransaction(absreq.PGRPC_Request):
    """Executes a signed transaction block on the chain."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ExecuteTransactionResponse

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
        self.field_mask = self._field_mask(field_mask) or self._field_mask(
            ["transaction", "finality"]
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


class SimulateTransaction(absreq.PGRPC_Request):
    """Simulates executnig a transaction block on the chain."""

    RESULT_TYPE: betterproto2.Message = sui_prot.SimulateTransactionResponse

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

    def to_request(
        self, *, stub: sui_prot.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        simtdata = sui_prot.SimulateTransactionRequest(
            transaction=self.transaction,
            checks=self.checks_enables,
            do_gas_selection=self.gas_selection,
            read_mask=self.field_mask,
        )
        return stub.simulate_transaction, simtdata


class SimulateTransactionLKind(absreq.PGRPC_Request):
    """Simulates executnig a transaction block on the chain."""

    RESULT_TYPE: betterproto2.Message = sui_prot.SimulateTransactionResponse

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
        """."""
        super().__init__(absreq.Service.LIVEDATA)
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
        # tx = sui_prot.Transaction.from_dict(self.transaction.to_dict())
        self.checks_enables = (
            sui_prot.SimulateTransactionRequestTransactionChecks.ENABLED
            if checks_enabled
            else sui_prot.SimulateTransactionRequestTransactionChecks.DISABLED
        )
        self.gas_selection = gas_selection
        self.field_mask = self._field_mask(field_mask) or self._field_mask(["*"])

    def to_request(
        self, *, stub: sui_prot.LiveDataServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        req = sui_prot.SimulateTransactionRequest(
            transaction=self.transaction,
            checks=self.checks_enables,
            do_gas_selection=self.gas_selection,
            read_mask=self.field_mask,
        )
        # print(req.to_json(indent=2))
        return stub.simulate_transaction, req


# TODO: Test with Devnet
class GetPackageVersions(absreq.PGRPC_Request):
    """Query a Move package's versions by it's storage ID."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ListPackageVersionsResponse

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

    def __init__(
        self,
        *,
        package: str,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package_id = package

    def to_request(
        self, *, stub: sui_prot.MovePackageServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.get_package, sui_prot.GetPackageRequest(package_id=self.package_id)


class GetDataType(absreq.PGRPC_Request):
    """Query a Move module's DataType by it's name."""

    RESULT_TYPE: betterproto2.Message = sui_prot.GetDatatypeResponse

    def __init__(self, *, package: str, module_name: str, type_name: str) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package = package
        self.module_name = module_name
        self.type_name = type_name

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


class GetStructure(GetDataType):
    """Alias for GetDataType."""

    def __init__(self, *, package: str, module_name: str, structure_name: str):
        super().__init__(
            package=package, module_name=module_name, type_name=structure_name
        )


# TODO: Move to gRPC types
@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructuresGRPC:
    """Module DataTypes."""

    structures: list[sui_prot.DatatypeDescriptor]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionsGRPC:
    """Module Functions."""

    functions: list[sui_prot.FunctionDescriptor]


class GetStructures(GetPackage):
    """Alias for GetDataType."""

    def __init__(self, *, package, module_name: str):
        super().__init__(package=package)
        self.module_name = module_name

    def render(self, package: sui_prot.GetPackageResponse) -> MoveStructuresGRPC:
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

    def __init__(self, *, package: str, module_name: str, function_name: str) -> None:
        """Initializer."""
        super().__init__(absreq.Service.MOVEPACKAGE)
        self.package = package
        self.module_name = module_name
        self.function_name = function_name

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

    def __init__(self, *, package, module_name: str):
        super().__init__(package=package)
        self.module_name = module_name

    def render(self, package: sui_prot.GetPackageResponse) -> MoveStructuresGRPC:
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

    def __init__(self, *, package, module_name: str):
        super().__init__(package=package)
        self.module_name = module_name

    def render(self, package: sui_prot.GetPackageResponse) -> sui_prot.Module:
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

    def __init__(
        self,
        *,
        field_mask: Optional[list[str]] = None,
    ) -> None:
        """Initializer."""
        super().__init__(absreq.Service.SUBSCRIPTION)
        self.field_mask = self._field_mask(field_mask)

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

    def __init__(
        self,
        *,
        address: str | None = None,
        message_type: str,
        message: str | bytes,
        signature: str | bytes,
    ):
        """__init__ _summary_

        :param message_type: Must be 'PersonalMessage' or 'Transaction'
        :type message_type: str
        :param message: The message base64 encoded string or bytes
        :type message: str | bytes
        :param signature: The signature base64 encoded string or bytes
        :type signature: str | bytes
        :param address: If provided, this address will be used to compare address derived from signature, defaults to None
        :type address: str | None, optional
        """
        super().__init__(absreq.Service.SIGNATURE)
        self.address = address
        self.message_type = message_type
        self.message = sui_prot.Bcs(
            name=message_type,
            value=base64.b64decode(message) if isinstance(message, str) else message,
        )
        self.signature = sui_prot.UserSignature(
            bcs=sui_prot.Bcs(
                name="UserSignature",
                value=(
                    base64.b64decode(signature)
                    if isinstance(signature, str)
                    else signature
                ),
            )
        )

    def to_request(
        self, *, stub: sui_prot.SignatureVerificationServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.verify_signature, sui_prot.VerifySignatureRequest(
            message=self.message, signature=self.signature, address=self.address
        )


class NameLookup(absreq.PGRPC_Request):
    """Do a name lookup."""

    RESULT_TYPE: betterproto2.Message = sui_prot.LookupNameResponse

    def __init__(self, *, name: str | None = None):
        """Name lookup constructor.

        :param name: Name to find address for. Accepts '@name' or 'name.sui' forms, defaults to None
        :type name: str | None, optional
        """
        super().__init__(absreq.Service.NAMESERVICE)
        self.name = name

    def to_request(
        self, *, stub: sui_prot.NameServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.lookup_name, sui_prot.LookupNameRequest(name=self.name)


class ReverseNameLookup(absreq.PGRPC_Request):
    """Do a name lookup from address."""

    RESULT_TYPE: betterproto2.Message = sui_prot.ReverseLookupNameResponse

    def __init__(self, *, address: str | None = None):
        """Reverse Name lookup constructor.

        :param name: Address to find name for, defaults to None
        :type name: str | None, optional
        """
        super().__init__(absreq.Service.NAMESERVICE)
        self.address = address

    def to_request(
        self, *, stub: sui_prot.NameServiceStub
    ) -> tuple[
        Callable[[betterproto2.Message], betterproto2.Message], betterproto2.Message
    ]:
        """."""
        return stub.reverse_lookup_name, sui_prot.ReverseLookupNameRequest(
            address=self.name
        )
