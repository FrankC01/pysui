#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Built-in SuiCommand subclasses — protocol-agnostic Sui operations."""

import base64
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from pysui.sui.sui_bcs.bcs import TransactionKind
from pysui.sui.sui_common.sui_command import SuiCommand
import pysui.sui.sui_grpc.pgrpc_requests as rn
import pysui.sui.sui_pgql.pgql_query as pgql_query
from pysui.sui.sui_pgql.pgql_types import PagingCursor


# ---------------------------------------------------------------------------
# Transaction execution
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class ExecuteTransaction(SuiCommand):
    """Execute a signed transaction on-chain."""

    gql_class: ClassVar[type] = pgql_query.ExecuteTransaction
    grpc_class: ClassVar[type] = rn.ExecuteTransaction

    tx_bytestr: str | bytes
    sig_array: list[str | bytes]

    def gql_node(self) -> pgql_query.ExecuteTransaction:
        """Return GQL execute-transaction mutation node."""
        tx_b64 = (
            self.tx_bytestr
            if isinstance(self.tx_bytestr, str)
            else base64.b64encode(self.tx_bytestr).decode()
        )
        sigs_b64 = [
            s if isinstance(s, str) else base64.b64encode(s).decode()
            for s in self.sig_array
        ]
        return pgql_query.ExecuteTransaction(tx_bytestr=tx_b64, sig_array=sigs_b64)

    def grpc_request(self) -> rn.ExecuteTransaction:
        """Return gRPC execute-transaction request."""
        return rn.ExecuteTransaction(
            tx_bytestr=self.tx_bytestr, sig_array=self.sig_array
        )


@dataclass(kw_only=True)
class SimulateTransaction(SuiCommand):
    """Simulate a serialized transaction (BCS bytes or base64 string)."""

    gql_class: ClassVar[type] = pgql_query.SimulateTransaction
    grpc_class: ClassVar[type] = rn.SimulateTransaction

    tx_bytestr: str | bytes
    checks_enabled: Optional[bool] = True
    gas_selection: Optional[bool] = True

    def gql_node(self) -> pgql_query.SimulateTransaction:
        """Return GQL simulate-transaction query node."""
        return pgql_query.SimulateTransaction(
            tx_bytestr=self.tx_bytestr,
            skip_checks=self.checks_enabled,
            do_gas_selection=self.gas_selection,
        )

    def grpc_request(self) -> rn.SimulateTransaction:
        """Return gRPC simulate-transaction request."""
        return rn.SimulateTransaction(
            transaction=self.tx_bytestr,
            checks_enabled=self.checks_enabled,
            gas_selection=self.gas_selection,
        )


@dataclass(kw_only=True)
class SimulateTransactionKind(SuiCommand):
    """Simulate a TransactionKind (programmable transaction) without committing."""

    gql_class: ClassVar[type] = pgql_query.SimulateTransactionKind
    grpc_class: ClassVar[type] = rn.SimulateTransactionKind

    tx_kind: TransactionKind
    tx_meta: dict  # Must contain "sender": str; optionally "epoch_expiration": int
    checks_enabled: Optional[bool] = True
    gas_selection: Optional[bool] = True

    def gql_node(self) -> pgql_query.SimulateTransactionKind:
        """Return GQL simulate-transaction-kind query node."""
        return pgql_query.SimulateTransactionKind(
            tx_kind=self.tx_kind,
            tx_meta=self.tx_meta,
            skip_checks=self.checks_enabled,
            do_gas_selection=self.gas_selection,
        )

    def grpc_request(self) -> rn.SimulateTransactionKind:
        """Return gRPC simulate-transaction-kind request."""
        sender = self.tx_meta.get("sender")
        if not sender:
            raise ValueError("tx_meta must contain 'sender'")
        return rn.SimulateTransactionKind(
            transaction=self.tx_kind,
            sender=sender,
            checks_enabled=self.checks_enabled,
            gas_selection=self.gas_selection,
            txn_expires_after=self.tx_meta.get("epoch_expiration"),
        )


# ---------------------------------------------------------------------------
# Coin / balance queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetCoinMetaData(SuiCommand):
    """Fetch metadata for a specific coin type."""

    gql_class: ClassVar[type] = pgql_query.GetCoinMetaDataSC
    grpc_class: ClassVar[type] = rn.GetCoinMetaData

    coin_type: Optional[str] = "0x2::sui::SUI"

    def gql_node(self) -> pgql_query.GetCoinMetaDataSC:
        """Return GQL coin-metadata query node."""
        return pgql_query.GetCoinMetaDataSC(coin_type=self.coin_type)

    def grpc_request(self) -> rn.GetCoinMetaData:
        """Return gRPC coin-info request."""
        return rn.GetCoinMetaData(coin_type=self.coin_type)


@dataclass(kw_only=True)
class GetAddressCoinBalance(SuiCommand):
    """Fetch the total balance for a specific coin type owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetAddressCoinBalanceSC
    grpc_class: ClassVar[type] = rn.GetAddressCoinBalance

    owner: str
    coin_type: Optional[str] = "0x2::sui::SUI"

    def gql_node(self) -> pgql_query.GetAddressCoinBalanceSC:
        """Return GQL address-coin-balance query node."""
        return pgql_query.GetAddressCoinBalanceSC(
            owner=self.owner, coin_type=self.coin_type
        )

    def grpc_request(self) -> rn.GetAddressCoinBalance:
        """Return gRPC get-balance request."""
        return rn.GetAddressCoinBalance(owner=self.owner, coin_type=self.coin_type)


@dataclass(kw_only=True)
class GetAddressCoinBalances(SuiCommand):
    """Fetch all coin-type balances for an address."""

    gql_class: ClassVar[type] = pgql_query.GetAddressCoinBalancesSC
    grpc_class: ClassVar[type] = rn.GetAddressCoinBalances

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetAddressCoinBalancesSC:
        """Return GQL address-coin-balances query node."""
        return pgql_query.GetAddressCoinBalancesSC(
            owner=self.owner, next_page=self.next_page
        )

    def grpc_request(self) -> rn.GetAddressCoinBalances:
        """Return gRPC list-balances request (first page)."""
        return rn.GetAddressCoinBalances(owner=self.owner)


@dataclass(kw_only=True)
class GetCoins(SuiCommand):
    """Fetch all coin objects of a specific type owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetCoinsSC
    grpc_class: ClassVar[type] = rn.GetCoins

    owner: str
    coin_type: Optional[str] = "0x2::coin::Coin<0x2::sui::SUI>"
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetCoinsSC:
        """Return GQL coins query node."""
        return self.gql_class(
            owner=self.owner,
            coin_type=self.coin_type,
            next_page=self.next_page,
        )

    def grpc_request(self) -> rn.GetCoins:
        """Return gRPC get-owned-objects request filtered to coin type."""
        return rn.GetCoins(owner=self.owner, coin_type=self.coin_type)


@dataclass(kw_only=True)
class GetGas(SuiCommand):
    """Fetch all SUI gas coin objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetGasSC
    grpc_class: ClassVar[type] = rn.GetGas

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetGasSC:
        """Return GQL gas-coins query node."""
        return self.gql_class(owner=self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetGas:
        """Return gRPC get-gas request."""
        return rn.GetGas(owner=self.owner)


@dataclass(kw_only=True)
class GetStaked(SuiCommand):
    """Fetch all staked SUI coin objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetDelegatedStakesSC
    grpc_class: ClassVar[type] = rn.GetStaked

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetDelegatedStakesSC:
        """Return GQL staked-coins query node."""
        return self.gql_class(self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetStaked:
        """Return gRPC get-staked request."""
        return rn.GetStaked(owner=self.owner)


@dataclass(kw_only=True)
class GetDelegatedStakes(SuiCommand):
    """Fetch all delegated-stake (StakedSui) objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetDelegatedStakesSC
    grpc_class: ClassVar[type] = rn.GetDelegatedStakes

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetDelegatedStakesSC:
        """Return GQL delegated-stakes query node."""
        return self.gql_class(self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetDelegatedStakes:
        """Return gRPC get-delegated-stakes request."""
        return rn.GetDelegatedStakes(owner=self.owner)


# ---------------------------------------------------------------------------
# Object queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetObject(SuiCommand):
    """Fetch the current state of a single object."""

    gql_class: ClassVar[type] = pgql_query.GetObjectSC
    grpc_class: ClassVar[type] = rn.GetObjectSC

    object_id: str

    def gql_node(self) -> pgql_query.GetObjectSC:
        """Return GQL object query node."""
        return self.gql_class(object_id=self.object_id)

    def grpc_request(self) -> rn.GetObjectSC:
        """Return gRPC get-object request."""
        return self.grpc_class(object_id=self.object_id)


@dataclass(kw_only=True)
class GetPastObject(SuiCommand):
    """Fetch a specific version of an object."""

    gql_class: ClassVar[type] = pgql_query.GetPastObjectSC
    grpc_class: ClassVar[type] = rn.GetPastObjectSC

    object_id: str
    version: int

    def gql_node(self) -> pgql_query.GetPastObjectSC:
        """Return GQL past-object query node."""
        return self.gql_class(object_id=self.object_id, version=self.version)

    def grpc_request(self) -> rn.GetPastObjectSC:
        """Return gRPC get-past-object request."""
        return self.grpc_class(object_id=self.object_id, version=self.version)


@dataclass(kw_only=True)
class GetMultipleObjects(SuiCommand):
    """Fetch the current state of multiple objects by ID list."""

    gql_class: ClassVar[type] = pgql_query.GetMultipleObjectsSC
    grpc_class: ClassVar[type] = rn.GetMultipleObjects

    object_ids: list[str]

    def gql_node(self) -> pgql_query.GetMultipleObjectsSC:
        """Return GQL multi-object query node."""
        return self.gql_class(object_ids=self.object_ids)

    def grpc_request(self) -> rn.GetMultipleObjects:
        """Return gRPC batch-get-objects request."""
        return rn.GetMultipleObjects(object_ids=self.object_ids)


@dataclass(kw_only=True)
class GetMultiplePastObjects(SuiCommand):
    """Fetch specific versions of multiple objects.

    Each entry in ``for_versions`` must be a dict with keys ``"objectId"`` (str)
    and ``"version"`` (int).
    """

    gql_class: ClassVar[type] = pgql_query.GetMultipleVersionedObjectsSC
    grpc_class: ClassVar[type] = rn.GetMultiplePastObjects

    for_versions: list[dict]

    def gql_node(self) -> pgql_query.GetMultipleVersionedObjectsSC:
        """Return GQL multi-versioned-objects query node."""
        gql_versions = [
            {"address": d["objectId"], "version": d["version"]}
            for d in self.for_versions
        ]
        return self.gql_class(for_versions=gql_versions)

    def grpc_request(self) -> rn.GetMultiplePastObjects:
        """Return gRPC batch-get-past-objects request."""
        return rn.GetMultiplePastObjects(for_versions=self.for_versions)


@dataclass(kw_only=True)
class GetObjectsOwnedByAddress(SuiCommand):
    """Fetch all objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetObjectsOwnedByAddressSC
    grpc_class: ClassVar[type] = rn.GetObjectsOwnedByAddress

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetObjectsOwnedByAddressSC:
        """Return GQL owned-objects query node."""
        return self.gql_class(owner=self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetObjectsOwnedByAddress:
        """Return gRPC list-owned-objects request."""
        return rn.GetObjectsOwnedByAddress(owner=self.owner)


@dataclass(kw_only=True)
class GetDynamicFields(SuiCommand):
    """Fetch dynamic fields of an object."""

    gql_class: ClassVar[type] = pgql_query.GetDynamicFieldsSC
    grpc_class: ClassVar[type] = rn.GetDynamicFields

    object_id: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetDynamicFieldsSC:
        """Return GQL dynamic-fields query node."""
        return self.gql_class(
            object_id=self.object_id, next_page=self.next_page
        )

    def grpc_request(self) -> rn.GetDynamicFields:
        """Return gRPC list-dynamic-fields request."""
        return rn.GetDynamicFields(object_id=self.object_id)


# ---------------------------------------------------------------------------
# Epoch / system state
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetEpoch(SuiCommand):
    """Fetch epoch information by ID, or the current epoch if no ID is given."""

    gql_class: ClassVar[type] = pgql_query.GetEpochSC
    grpc_class: ClassVar[type] = rn.GetEpoch

    epoch_id: Optional[int] = None

    def gql_node(self) -> pgql_query.GetEpochSC:
        """Return GQL epoch query node."""
        return pgql_query.GetEpochSC(epoch_id=self.epoch_id)

    def grpc_request(self) -> rn.GetEpoch:
        """Return gRPC get-epoch request."""
        return rn.GetEpoch(epoch_number=self.epoch_id)


class GetBasicCurrentEpochInfo(SuiCommand):
    """Fetch the minimal current epoch fields needed for gas and expiry building."""

    gql_class: ClassVar[type] = pgql_query.GetBasicCurrentEpochInfoSC
    grpc_class: ClassVar[type] = rn.GetBasicCurrentEpochInfo

    def gql_node(self) -> pgql_query.GetBasicCurrentEpochInfoSC:
        """Return GQL basic-epoch-info SC query node."""
        return pgql_query.GetBasicCurrentEpochInfoSC()

    def grpc_request(self) -> rn.GetBasicCurrentEpochInfo:
        """Return gRPC basic-epoch-info request."""
        return rn.GetBasicCurrentEpochInfo()


# ---------------------------------------------------------------------------
# Checkpoint queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetLatestCheckpoint(SuiCommand):
    """Fetch the latest checkpoint."""

    gql_class: ClassVar[type] = pgql_query.GetLatestCheckpointSequenceSC
    grpc_class: ClassVar[type] = rn.GetLatestCheckpoint

    def gql_node(self) -> pgql_query.GetLatestCheckpointSequenceSC:
        """Return GQL latest-checkpoint-sequence query node."""
        return self.gql_class()

    def grpc_request(self) -> rn.GetLatestCheckpoint:
        """Return gRPC get-latest-checkpoint request."""
        return rn.GetLatestCheckpoint()


@dataclass(kw_only=True)
class GetCheckpointBySequence(SuiCommand):
    """Fetch a checkpoint by sequence number."""

    gql_class: ClassVar[type] = pgql_query.GetCheckpointBySequenceSC
    grpc_class: ClassVar[type] = rn.GetCheckpointBySequence

    sequence_number: int

    def gql_node(self) -> pgql_query.GetCheckpointBySequenceSC:
        """Return GQL checkpoint-by-sequence query node."""
        return self.gql_class(sequence_number=self.sequence_number)

    def grpc_request(self) -> rn.GetCheckpointBySequence:
        """Return gRPC get-checkpoint-by-sequence request."""
        return rn.GetCheckpointBySequence(sequence_number=self.sequence_number)


@dataclass(kw_only=True)
class GetMultipleObjectContent(SuiCommand):
    """Fetch BCS content for multiple objects."""

    gql_class: ClassVar[type] = pgql_query.GetMultipleObjectContentSC
    grpc_class: ClassVar[type] = rn.GetMultipleObjects

    object_ids: list[str]

    def gql_node(self) -> pgql_query.GetMultipleObjectContentSC:
        """Return GraphQL query node."""
        return self.gql_class(object_ids=self.object_ids)

    def grpc_request(self) -> rn.GetMultipleObjects:
        """Return gRPC batch-get-objects request with contents field mask."""
        return rn.GetMultipleObjects(object_ids=self.object_ids, field_mask=["contents"])


@dataclass(kw_only=True)
class GetProtocolConfig(SuiCommand):
    """Fetch protocol configuration for a specific version or current."""

    gql_class: ClassVar[type] = pgql_query.GetProtocolConfigSC
    grpc_class: ClassVar[type] = rn.GetProtocolConfig

    version: Optional[int] = None

    def gql_node(self) -> pgql_query.GetProtocolConfigSC:
        """Return GraphQL query node."""
        return self.gql_class(version=self.version)

    def grpc_request(self) -> rn.GetProtocolConfig:
        """Return gRPC get-protocol-config request."""
        return rn.GetProtocolConfig(version=self.version)


@dataclass(kw_only=True)
class GetObjectContent(SuiCommand):
    """Fetch BCS content for a single object."""

    gql_class: ClassVar[type] = pgql_query.GetObjectContentSC
    grpc_class: ClassVar[type] = rn.GetObject

    object_id: str

    def gql_node(self) -> pgql_query.GetObjectContentSC:
        """Return GraphQL query node."""
        return self.gql_class(object_id=self.object_id)

    def grpc_request(self) -> rn.GetObject:
        """Return gRPC get-object request with contents field mask."""
        return rn.GetObject(object_id=self.object_id, field_mask=["contents"])


@dataclass(kw_only=True)
class GetObjectsForType(SuiCommand):
    """Fetch all objects of a specific type owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetObjectsForTypeSC
    grpc_class: ClassVar[type] = rn.GetObjectsOwnedByAddress

    owner: str
    object_type: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetObjectsForTypeSC:
        """Return GraphQL query node."""
        return self.gql_class(owner=self.owner, object_type=self.object_type, next_page=self.next_page)

    def grpc_request(self) -> rn.GetObjectsOwnedByAddress:
        """Return gRPC list-owned-objects request with type filter."""
        return rn.GetObjectsOwnedByAddress(owner=self.owner, object_type=self.object_type)


@dataclass(kw_only=True)
class GetCoinSummary(SuiCommand):
    """Fetch coin object summary (balance and metadata without content)."""

    gql_class: ClassVar[type] = pgql_query.GetCoinSummarySC
    grpc_class: ClassVar[type] = rn.GetObject

    coin_id: str

    def gql_node(self) -> pgql_query.GetCoinSummarySC:
        """Return GraphQL query node."""
        return self.gql_class(coin_id=self.coin_id)

    def grpc_request(self) -> rn.GetObject:
        """Return gRPC get-object request with balance and metadata field masks."""
        return rn.GetObject(object_id=self.coin_id, field_mask=["object_id", "version", "digest", "balance"])


# ---------------------------------------------------------------------------
# Move package / module queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetPackage(SuiCommand):
    """Fetch a Move package by ID."""

    gql_class: ClassVar[type] = pgql_query.GetPackageSC
    grpc_class: ClassVar[type] = rn.GetPackage

    package: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetPackageSC:
        """Return GQL package query node."""
        return self.gql_class(package=self.package, next_page=self.next_page)

    def grpc_request(self) -> rn.GetPackage:
        """Return gRPC get-package request."""
        return rn.GetPackage(package=self.package)


@dataclass(kw_only=True)
class GetPackageVersions(SuiCommand):
    """Fetch all versions of a Move package sharing the same original ID."""

    gql_class: ClassVar[type] = pgql_query.GetPackageVersionsSC
    grpc_class: ClassVar[type] = rn.GetPackageVersions

    package_address: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetPackageVersionsSC:
        """Return GQL package-versions query node."""
        return pgql_query.GetPackageVersionsSC(
            package_address=self.package_address, next_page=self.next_page
        )

    def grpc_request(self) -> rn.GetPackageVersions:
        """Return gRPC list-package-versions request."""
        return rn.GetPackageVersions(package_storage_id=self.package_address)


@dataclass(kw_only=True)
class GetModule(SuiCommand):
    """Fetch a Move module's structure and function definitions."""

    gql_class: ClassVar[type] = pgql_query.GetModuleSC
    grpc_class: ClassVar[type] = rn.GetModule

    package: str
    module_name: str

    def gql_node(self) -> pgql_query.GetModuleSC:
        """Return GQL module query node."""
        return self.gql_class(package=self.package, module_name=self.module_name)

    def grpc_request(self) -> rn.GetModule:
        """Return gRPC get-module request."""
        return rn.GetModule(package=self.package, module_name=self.module_name)


@dataclass(kw_only=True)
class GetMoveDataType(SuiCommand):
    """Fetch a Move struct or enum by name."""

    gql_class: ClassVar[type] = pgql_query.GetMoveDataTypeSC
    grpc_class: ClassVar[type] = rn.GetMoveDataType

    package: str
    module_name: str
    type_name: str

    def gql_node(self) -> pgql_query.GetMoveDataTypeSC:
        """Return GQL move-datatype query node."""
        return self.gql_class(
            package=self.package,
            module_name=self.module_name,
            data_type_name=self.type_name,
        )

    def grpc_request(self) -> rn.GetMoveDataType:
        """Return gRPC get-datatype request."""
        return rn.GetMoveDataType(
            package=self.package,
            module_name=self.module_name,
            type_name=self.type_name,
        )


@dataclass(kw_only=True)
class GetStructure(SuiCommand):
    """Fetch a specific Move struct by name."""

    gql_class: ClassVar[type] = pgql_query.GetStructureSC
    grpc_class: ClassVar[type] = rn.GetStructure

    package: str
    module_name: str
    structure_name: str

    def gql_node(self) -> pgql_query.GetStructureSC:
        """Return GQL structure query node."""
        return self.gql_class(
            package=self.package,
            module_name=self.module_name,
            structure_name=self.structure_name,
        )

    def grpc_request(self) -> rn.GetStructure:
        """Return gRPC get-structure request."""
        return rn.GetStructure(
            package=self.package,
            module_name=self.module_name,
            structure_name=self.structure_name,
        )


@dataclass(kw_only=True)
class GetStructures(SuiCommand):
    """Fetch all structs in a Move module (auto-paginated on GraphQL)."""

    gql_class: ClassVar[type] = pgql_query.GetStructuresSC
    grpc_class: ClassVar[type] = rn.GetStructures
    gql_requires_paging: ClassVar[bool] = True
    gql_page_list_path: ClassVar[tuple[str, ...]] = ("object", "asMovePackage", "module", "structs", "nodes")

    package: str
    module_name: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetStructuresSC:
        """Return GQL structures query node."""
        return self.gql_class(
            package=self.package,
            module_name=self.module_name,
            next_page=self.next_page,
        )

    def grpc_request(self) -> rn.GetStructures:
        """Return gRPC get-structures request (flat, no paging)."""
        return rn.GetStructures(package=self.package, module_name=self.module_name)


@dataclass(kw_only=True)
class GetFunction(SuiCommand):
    """Fetch a specific Move function by name."""

    gql_class: ClassVar[type] = pgql_query.GetFunctionSC
    grpc_class: ClassVar[type] = rn.GetFunction

    package: str
    module_name: str
    function_name: str

    def gql_node(self) -> pgql_query.GetFunctionSC:
        """Return GQL function query node."""
        return self.gql_class(
            package=self.package,
            module_name=self.module_name,
            function_name=self.function_name,
        )

    def grpc_request(self) -> rn.GetFunction:
        """Return gRPC get-function request."""
        return rn.GetFunction(
            package=self.package,
            module_name=self.module_name,
            function_name=self.function_name,
        )


@dataclass(kw_only=True)
class GetFunctions(SuiCommand):
    """Fetch all functions in a Move module (auto-paginated on GraphQL)."""

    gql_class: ClassVar[type] = pgql_query.GetFunctionsSC
    grpc_class: ClassVar[type] = rn.GetFunctions
    gql_requires_paging: ClassVar[bool] = True
    gql_page_list_path: ClassVar[tuple[str, ...]] = ("object", "asMovePackage", "module", "functions", "nodes")

    package: str
    module_name: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetFunctionsSC:
        """Return GQL functions query node."""
        return self.gql_class(
            package=self.package,
            module_name=self.module_name,
            next_page=self.next_page,
        )

    def grpc_request(self) -> rn.GetFunctions:
        """Return gRPC get-functions request (flat, no paging)."""
        return rn.GetFunctions(package=self.package, module_name=self.module_name)


# ---------------------------------------------------------------------------
# Name service
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetNameServiceAddress(SuiCommand):
    """Resolve a Sui name-service name to an address."""

    gql_class: ClassVar[type] = pgql_query.GetNameServiceAddressSC
    grpc_class: ClassVar[type] = rn.GetNameServiceAddress

    name: str

    def gql_node(self) -> pgql_query.GetNameServiceAddressSC:
        """Return GQL name-service-address query node."""
        return pgql_query.GetNameServiceAddressSC(name=self.name)

    def grpc_request(self) -> rn.GetNameServiceAddress:
        """Return gRPC lookup-name request."""
        return rn.GetNameServiceAddress(name=self.name)


@dataclass(kw_only=True)
class GetNameServiceNames(SuiCommand):
    """Resolve an address to its Sui name-service name(s)."""

    gql_class: ClassVar[type] = pgql_query.GetNameServiceNamesSC
    grpc_class: ClassVar[type] = rn.GetNameServiceNames

    owner: str

    def gql_node(self) -> pgql_query.GetNameServiceNamesSC:
        """Return GQL name-service-names query node."""
        return pgql_query.GetNameServiceNamesSC(owner=self.owner)

    def grpc_request(self) -> rn.GetNameServiceNames:
        """Return gRPC reverse-lookup-name request."""
        return rn.GetNameServiceNames(address=self.owner)


