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

    gql_class: ClassVar[type] = pgql_query.GetCoins
    grpc_class: ClassVar[type] = rn.GetCoins

    owner: str
    coin_type: Optional[str] = "0x2::coin::Coin<0x2::sui::SUI>"
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetCoins:
        """Return GQL coins query node."""
        return pgql_query.GetCoins(
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

    gql_class: ClassVar[type] = pgql_query.GetGas
    grpc_class: ClassVar[type] = rn.GetGas

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetGas:
        """Return GQL gas-coins query node."""
        return pgql_query.GetGas(owner=self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetGas:
        """Return gRPC get-gas request."""
        return rn.GetGas(owner=self.owner)


@dataclass(kw_only=True)
class GetStaked(SuiCommand):
    """Fetch all staked SUI coin objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetDelegatedStakes
    grpc_class: ClassVar[type] = rn.GetStaked

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetDelegatedStakes:
        """Return GQL staked-coins query node."""
        return pgql_query.GetDelegatedStakes(self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetStaked:
        """Return gRPC get-staked request."""
        return rn.GetStaked(owner=self.owner)


@dataclass(kw_only=True)
class GetDelegatedStakes(SuiCommand):
    """Fetch all delegated-stake (StakedSui) objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetDelegatedStakes
    grpc_class: ClassVar[type] = rn.GetDelegatedStakes

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetDelegatedStakes:
        """Return GQL delegated-stakes query node."""
        return pgql_query.GetDelegatedStakes(self.owner, next_page=self.next_page)

    def grpc_request(self) -> rn.GetDelegatedStakes:
        """Return gRPC get-delegated-stakes request."""
        return rn.GetDelegatedStakes(owner=self.owner)


# ---------------------------------------------------------------------------
# Object queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetObject(SuiCommand):
    """Fetch the current state of a single object."""

    gql_class: ClassVar[type] = pgql_query.GetObject
    grpc_class: ClassVar[type] = rn.GetObject

    object_id: str

    def gql_node(self) -> pgql_query.GetObject:
        """Return GQL object query node."""
        return pgql_query.GetObject(object_id=self.object_id)

    def grpc_request(self) -> rn.GetObject:
        """Return gRPC get-object request."""
        return rn.GetObject(object_id=self.object_id)


@dataclass(kw_only=True)
class GetPastObject(SuiCommand):
    """Fetch a specific version of an object."""

    gql_class: ClassVar[type] = pgql_query.GetPastObject
    grpc_class: ClassVar[type] = rn.GetPastObject

    object_id: str
    version: int

    def gql_node(self) -> pgql_query.GetPastObject:
        """Return GQL past-object query node."""
        return pgql_query.GetPastObject(object_id=self.object_id, version=self.version)

    def grpc_request(self) -> rn.GetPastObject:
        """Return gRPC get-past-object request."""
        return rn.GetPastObject(object_id=self.object_id, version=self.version)


@dataclass(kw_only=True)
class GetMultipleObjects(SuiCommand):
    """Fetch the current state of multiple objects by ID list."""

    gql_class: ClassVar[type] = pgql_query.GetMultipleObjects
    grpc_class: ClassVar[type] = rn.GetMultipleObjects

    object_ids: list[str]

    def gql_node(self) -> pgql_query.GetMultipleObjects:
        """Return GQL multi-object query node."""
        return pgql_query.GetMultipleObjects(object_ids=self.object_ids)

    def grpc_request(self) -> rn.GetMultipleObjects:
        """Return gRPC batch-get-objects request."""
        return rn.GetMultipleObjects(object_ids=self.object_ids)


@dataclass(kw_only=True)
class GetMultiplePastObjects(SuiCommand):
    """Fetch specific versions of multiple objects.

    Each entry in ``for_versions`` must be a dict with keys ``"objectId"`` (str)
    and ``"version"`` (int).
    """

    gql_class: ClassVar[type] = pgql_query.GetMultipleVersionedObjects
    grpc_class: ClassVar[type] = rn.GetMultiplePastObjects

    for_versions: list[dict]

    def gql_node(self) -> pgql_query.GetMultipleVersionedObjects:
        """Return GQL multi-versioned-objects query node."""
        gql_versions = [
            {"address": d["objectId"], "version": d["version"]}
            for d in self.for_versions
        ]
        return pgql_query.GetMultipleVersionedObjects(for_versions=gql_versions)

    def grpc_request(self) -> rn.GetMultiplePastObjects:
        """Return gRPC batch-get-past-objects request."""
        return rn.GetMultiplePastObjects(for_versions=self.for_versions)


@dataclass(kw_only=True)
class GetObjectsOwnedByAddress(SuiCommand):
    """Fetch all objects owned by an address."""

    gql_class: ClassVar[type] = pgql_query.GetObjectsOwnedByAddress
    grpc_class: ClassVar[type] = rn.GetObjectsOwnedByAddress

    owner: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetObjectsOwnedByAddress:
        """Return GQL owned-objects query node."""
        return pgql_query.GetObjectsOwnedByAddress(
            owner=self.owner, next_page=self.next_page
        )

    def grpc_request(self) -> rn.GetObjectsOwnedByAddress:
        """Return gRPC list-owned-objects request."""
        return rn.GetObjectsOwnedByAddress(owner=self.owner)


@dataclass(kw_only=True)
class GetDynamicFields(SuiCommand):
    """Fetch dynamic fields of an object."""

    gql_class: ClassVar[type] = pgql_query.GetDynamicFields
    grpc_class: ClassVar[type] = rn.GetDynamicFields

    object_id: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetDynamicFields:
        """Return GQL dynamic-fields query node."""
        return pgql_query.GetDynamicFields(
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


@dataclass(kw_only=True)
class GetLatestSuiSystemState(SuiCommand):
    """Fetch the latest Sui system state."""

    gql_class: ClassVar[type] = pgql_query.GetLatestSuiSystemState
    grpc_class: ClassVar[type] = rn.GetLatestSuiSystemState

    def gql_node(self) -> pgql_query.GetLatestSuiSystemState:
        """Return GQL latest-system-state query node."""
        return pgql_query.GetLatestSuiSystemState()

    def grpc_request(self) -> rn.GetLatestSuiSystemState:
        """Return gRPC get-system-state request."""
        return rn.GetLatestSuiSystemState()


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


@dataclass(kw_only=True)
class GetCurrentValidators(SuiCommand):
    """Fetch the active validator set from the current epoch."""

    gql_class: ClassVar[type] = pgql_query.GetCurrentValidators
    grpc_class: ClassVar[type] = rn.GetCurrentValidators
    gql_requires_paging: ClassVar[bool] = True

    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetCurrentValidators:
        """Return GQL current-validators query node."""
        return pgql_query.GetCurrentValidators(next_page=self.next_page)

    def grpc_request(self) -> rn.GetCurrentValidators:
        """Return gRPC get-current-validators request (flat, no paging)."""
        return rn.GetCurrentValidators()


# ---------------------------------------------------------------------------
# Checkpoint queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetLatestCheckpoint(SuiCommand):
    """Fetch the latest checkpoint."""

    gql_class: ClassVar[type] = pgql_query.GetLatestCheckpointSequence
    grpc_class: ClassVar[type] = rn.GetLatestCheckpoint

    def gql_node(self) -> pgql_query.GetLatestCheckpointSequence:
        """Return GQL latest-checkpoint-sequence query node."""
        return pgql_query.GetLatestCheckpointSequence()

    def grpc_request(self) -> rn.GetLatestCheckpoint:
        """Return gRPC get-latest-checkpoint request."""
        return rn.GetLatestCheckpoint()


@dataclass(kw_only=True)
class GetCheckpointBySequence(SuiCommand):
    """Fetch a checkpoint by sequence number."""

    gql_class: ClassVar[type] = pgql_query.GetCheckpointBySequence
    grpc_class: ClassVar[type] = rn.GetCheckpointBySequence

    sequence_number: int

    def gql_node(self) -> pgql_query.GetCheckpointBySequence:
        """Return GQL checkpoint-by-sequence query node."""
        return pgql_query.GetCheckpointBySequence(sequence_number=self.sequence_number)

    def grpc_request(self) -> rn.GetCheckpointBySequence:
        """Return gRPC get-checkpoint-by-sequence request."""
        return rn.GetCheckpointBySequence(sequence_number=self.sequence_number)


@dataclass(kw_only=True)
class GetCheckpointByDigest(SuiCommand):
    """Fetch a checkpoint by digest (gRPC only)."""

    gql_class: ClassVar[type] = None
    grpc_class: ClassVar[type] = rn.GetCheckpointByDigest

    digest: str

    def gql_node(self):
        """Not supported by GraphQL."""
        raise NotImplementedError("GetCheckpointByDigest is not supported by GraphQL")

    def grpc_request(self) -> rn.GetCheckpointByDigest:
        """Return gRPC get-checkpoint-by-digest request."""
        return rn.GetCheckpointByDigest(digest=self.digest)


# ---------------------------------------------------------------------------
# Transaction queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetTx(SuiCommand):
    """Fetch a single transaction by digest."""

    gql_class: ClassVar[type] = pgql_query.GetTx
    grpc_class: ClassVar[type] = rn.GetTx

    digest: str

    def gql_node(self) -> pgql_query.GetTx:
        """Return GQL transaction query node."""
        return pgql_query.GetTx(digest=self.digest)

    def grpc_request(self) -> rn.GetTx:
        """Return gRPC get-transaction request."""
        return rn.GetTx(digest=self.digest)


@dataclass(kw_only=True)
class GetTxKind(SuiCommand):
    """Fetch the transaction kind for a given digest."""

    gql_class: ClassVar[type] = pgql_query.GetTxKind
    grpc_class: ClassVar[type] = rn.GetTxKind

    digest: str

    def gql_node(self) -> pgql_query.GetTxKind:
        """Return GQL transaction-kind query node."""
        return pgql_query.GetTxKind(self.digest)

    def grpc_request(self) -> rn.GetTxKind:
        """Return gRPC get-tx-kind request."""
        return rn.GetTxKind(digest=self.digest)


@dataclass(kw_only=True)
class GetMultipleTransactions(SuiCommand):
    """Fetch multiple transactions by digest list."""

    gql_class: ClassVar[type] = pgql_query.GetMultipleTransactionsSC
    grpc_class: ClassVar[type] = rn.GetTransactions

    digests: list[str]

    def gql_node(self) -> pgql_query.GetMultipleTransactionsSC:
        """Return GraphQL query node."""
        return self.gql_class(digests=self.digests)

    def grpc_request(self) -> rn.GetTransactions:
        """Return gRPC batch-get-transactions request."""
        return rn.GetTransactions(transactions=self.digests)


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


@dataclass(kw_only=True)
class GetFilteredTx(SuiCommand):
    """Fetch transactions matching a TransactionBlockFilter (GraphQL only)."""

    gql_class: ClassVar[type] = pgql_query.GetFilteredTx
    grpc_class: ClassVar[type] = None

    tx_filter: dict
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetFilteredTx:
        """Return GQL filtered-transactions query node."""
        return pgql_query.GetFilteredTx(
            tx_filter=self.tx_filter, next_page=self.next_page
        )

    def grpc_request(self):
        """Not supported by gRPC."""
        raise NotImplementedError("GetFilteredTx is not supported by gRPC")


# ---------------------------------------------------------------------------
# Event queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetEvents(SuiCommand):
    """Fetch events matching a filter (GraphQL only)."""

    gql_class: ClassVar[type] = pgql_query.GetEvents
    grpc_class: ClassVar[type] = None

    event_filter: dict
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetEvents:
        """Return GQL events query node."""
        return pgql_query.GetEvents(
            event_filter=self.event_filter, next_page=self.next_page
        )

    def grpc_request(self):
        """Not supported by gRPC."""
        raise NotImplementedError("GetEvents is not supported by gRPC")


# ---------------------------------------------------------------------------
# Move package / module queries
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetPackage(SuiCommand):
    """Fetch a Move package by ID."""

    gql_class: ClassVar[type] = pgql_query.GetPackage
    grpc_class: ClassVar[type] = rn.GetPackage

    package: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetPackage:
        """Return GQL package query node."""
        return pgql_query.GetPackage(package=self.package, next_page=self.next_page)

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

    gql_class: ClassVar[type] = pgql_query.GetModule
    grpc_class: ClassVar[type] = rn.GetModule

    package: str
    module_name: str

    def gql_node(self) -> pgql_query.GetModule:
        """Return GQL module query node."""
        return pgql_query.GetModule(package=self.package, module_name=self.module_name)

    def grpc_request(self) -> rn.GetModule:
        """Return gRPC get-module request."""
        return rn.GetModule(package=self.package, module_name=self.module_name)


@dataclass(kw_only=True)
class GetMoveDataType(SuiCommand):
    """Fetch a Move struct or enum by name."""

    gql_class: ClassVar[type] = pgql_query.GetMoveDataType
    grpc_class: ClassVar[type] = rn.GetMoveDataType

    package: str
    module_name: str
    type_name: str

    def gql_node(self) -> pgql_query.GetMoveDataType:
        """Return GQL move-datatype query node."""
        return pgql_query.GetMoveDataType(
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

    gql_class: ClassVar[type] = pgql_query.GetStructure
    grpc_class: ClassVar[type] = rn.GetStructure

    package: str
    module_name: str
    structure_name: str

    def gql_node(self) -> pgql_query.GetStructure:
        """Return GQL structure query node."""
        return pgql_query.GetStructure(
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

    gql_class: ClassVar[type] = pgql_query.GetStructures
    grpc_class: ClassVar[type] = rn.GetStructures
    gql_requires_paging: ClassVar[bool] = True

    package: str
    module_name: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetStructures:
        """Return GQL structures query node."""
        return pgql_query.GetStructures(
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

    gql_class: ClassVar[type] = pgql_query.GetFunction
    grpc_class: ClassVar[type] = rn.GetFunction

    package: str
    module_name: str
    function_name: str

    def gql_node(self) -> pgql_query.GetFunction:
        """Return GQL function query node."""
        return pgql_query.GetFunction(
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

    gql_class: ClassVar[type] = pgql_query.GetFunctions
    grpc_class: ClassVar[type] = rn.GetFunctions
    gql_requires_paging: ClassVar[bool] = True

    package: str
    module_name: str
    next_page: Optional[PagingCursor] = None

    def gql_node(self) -> pgql_query.GetFunctions:
        """Return GQL functions query node."""
        return pgql_query.GetFunctions(
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


# ---------------------------------------------------------------------------
# gRPC-only commands (EC-3)
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class GetServiceInfo(SuiCommand):
    """Query general service information (gRPC only)."""

    gql_class: ClassVar[type] = None
    grpc_class: ClassVar[type] = rn.GetServiceInfo

    def gql_node(self):
        """Not supported by GraphQL."""
        raise NotImplementedError("GetServiceInfo is not supported by GraphQL")

    def grpc_request(self) -> rn.GetServiceInfo:
        """Return gRPC get-service-info request."""
        return rn.GetServiceInfo()


@dataclass(kw_only=True)
class SubscribeCheckpoint(SuiCommand):
    """Subscribe to a live checkpoint feed (gRPC streaming only)."""

    gql_class: ClassVar[type] = None
    grpc_class: ClassVar[type] = rn.SubscribeCheckpoint

    def gql_node(self):
        """Not supported by GraphQL."""
        raise NotImplementedError("SubscribeCheckpoint is not supported by GraphQL")

    def grpc_request(self) -> rn.SubscribeCheckpoint:
        """Return gRPC subscribe-checkpoints request."""
        return rn.SubscribeCheckpoint()


@dataclass(kw_only=True)
class VerifySignature(SuiCommand):
    """Verify a signature against a message.

    gRPC supports all signature types (Ed25519, Secp256k1, Secp256r1, MultiSig, Passkey, zkLogin).
    GraphQL support is pending mainnet availability of the verifySignature field.
    """

    gql_class: ClassVar[type] = None
    grpc_class: ClassVar[type] = rn.VerifySignature

    message_type: str
    message: str | bytes
    signature: str | bytes
    address: Optional[str] = None

    def gql_node(self):
        """Not supported by GraphQL — verifySignature is not yet available on mainnet."""
        raise NotImplementedError(
            "Command not supported by GraphQL"
        )

    def grpc_request(self) -> rn.VerifySignature:
        """Return gRPC verify-signature request."""
        return rn.VerifySignature(
            address=self.address,
            message_type=self.message_type,
            message=self.message,
            signature=self.signature,
        )
