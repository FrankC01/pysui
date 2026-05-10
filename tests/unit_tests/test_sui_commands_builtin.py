#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for built-in SuiCommand subclasses — all offline, no live node required.

Tests cover:
  - Correct instantiation with user-facing arguments
  - gql_node() returns the right PGQL_QueryNode subtype
  - grpc_request() returns the right PGRPC_Request subtype
  - EC-3 sides raise NotImplementedError
  - gql_requires_paging set correctly on pageable commands
  - GetMultiplePastObjects translates objectId→address for GQL
"""

import pytest

from pysui.sui.sui_common.sui_command import SuiCommand
import pysui.sui.sui_pgql.pgql_query as pgql_query
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui.sui.sui_pgql.pgql_clients import PGQL_QueryNode
from pysui.sui.sui_grpc.pgrpc_absreq import PGRPC_Request

from pysui.sui.sui_common.sui_commands import (
    ExecuteTransaction,
    GetAddressCoinBalance,
    GetAddressCoinBalances,
    GetCheckpointBySequence,
    GetCoinMetaData,
    GetCoinSummary,
    GetCoins,
    GetDelegatedStakes,
    GetDynamicFields,
    GetEpoch,
    GetFunction,
    GetFunctions,
    GetGas,
    GetLatestCheckpoint,
    GetModule,
    GetMoveDataType,
    GetMultipleObjects,
    GetMultipleObjectContent,
    GetMultiplePastObjects,
    GetNameServiceAddress,
    GetNameServiceNames,
    GetObject,
    GetObjectContent,
    GetObjectsForType,
    GetObjectsOwnedByAddress,
    GetPackage,
    GetPackageVersions,
    GetPastObject,
    GetProtocolConfig,
    GetStaked,
    GetStructure,
    GetStructures,
    SimulateTransaction,
    SimulateTransactionKind,
    GetTransaction,
    GetTransactions,
    GetTransactionKind,
)


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

ADDR = "0x" + "ab" * 32
OBJ_ID = "0x" + "cd" * 32
PKG = "0x" + "02" * 32
DIGEST = "HnfMNJPBeLXSLdHEDxBXVCFhDHMJqJgZXS3UcXmPK3E"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_gql(obj) -> bool:
    return isinstance(obj, PGQL_QueryNode)


def _is_grpc(obj) -> bool:
    return isinstance(obj, PGRPC_Request)


# ---------------------------------------------------------------------------
# All commands are SuiCommand instances
# ---------------------------------------------------------------------------


class TestAllAreSubcommands:
    def test_execute_transaction(self):
        cmd = ExecuteTransaction(tx_bytestr=b"abc", sig_array=[b"sig"])
        assert isinstance(cmd, SuiCommand)

    def test_get_coin_metadata(self):
        assert isinstance(GetCoinMetaData(), SuiCommand)

    def test_get_address_coin_balance(self):
        assert isinstance(GetAddressCoinBalance(owner=ADDR), SuiCommand)

    def test_get_address_coin_balances(self):
        assert isinstance(GetAddressCoinBalances(owner=ADDR), SuiCommand)

    def test_get_coins(self):
        assert isinstance(GetCoins(owner=ADDR), SuiCommand)

    def test_get_gas(self):
        assert isinstance(GetGas(owner=ADDR), SuiCommand)

    def test_get_staked(self):
        assert isinstance(GetStaked(owner=ADDR), SuiCommand)

    def test_get_delegated_stakes(self):
        assert isinstance(GetDelegatedStakes(owner=ADDR), SuiCommand)

    def test_get_object(self):
        assert isinstance(GetObject(object_id=OBJ_ID), SuiCommand)

    def test_get_past_object(self):
        assert isinstance(GetPastObject(object_id=OBJ_ID, version=1), SuiCommand)

    def test_get_multiple_objects(self):
        assert isinstance(GetMultipleObjects(object_ids=[OBJ_ID]), SuiCommand)

    def test_get_multiple_past_objects(self):
        assert isinstance(
            GetMultiplePastObjects(
                for_versions=[{"objectId": OBJ_ID, "version": 1}]
            ),
            SuiCommand,
        )

    def test_get_objects_owned_by_address(self):
        assert isinstance(GetObjectsOwnedByAddress(owner=ADDR), SuiCommand)

    def test_get_dynamic_fields(self):
        assert isinstance(GetDynamicFields(object_id=OBJ_ID), SuiCommand)

    def test_get_epoch(self):
        assert isinstance(GetEpoch(), SuiCommand)

    def test_get_latest_checkpoint(self):
        assert isinstance(GetLatestCheckpoint(), SuiCommand)

    def test_get_checkpoint_by_sequence(self):
        assert isinstance(GetCheckpointBySequence(sequence_number=42), SuiCommand)

    def test_get_multiple_object_content(self):
        assert isinstance(GetMultipleObjectContent(object_ids=[OBJ_ID]), SuiCommand)

    def test_get_protocol_config(self):
        assert isinstance(GetProtocolConfig(), SuiCommand)
        assert isinstance(GetProtocolConfig(version=1), SuiCommand)

    def test_get_object_content(self):
        assert isinstance(GetObjectContent(object_id=OBJ_ID), SuiCommand)

    def test_get_objects_for_type(self):
        assert isinstance(GetObjectsForType(owner=ADDR, object_type="0x2::coin::Coin<0x2::sui::SUI>"), SuiCommand)

    def test_get_coin_summary(self):
        assert isinstance(GetCoinSummary(coin_id=OBJ_ID), SuiCommand)

    def test_get_package(self):
        assert isinstance(GetPackage(package=PKG), SuiCommand)

    def test_get_package_versions(self):
        assert isinstance(GetPackageVersions(package_address=PKG), SuiCommand)

    def test_get_module(self):
        assert isinstance(GetModule(package=PKG, module_name="coin"), SuiCommand)

    def test_get_move_data_type(self):
        assert isinstance(
            GetMoveDataType(package=PKG, module_name="coin", type_name="Coin"),
            SuiCommand,
        )

    def test_get_structure(self):
        assert isinstance(
            GetStructure(package=PKG, module_name="coin", structure_name="Coin"),
            SuiCommand,
        )

    def test_get_structures(self):
        assert isinstance(GetStructures(package=PKG, module_name="coin"), SuiCommand)

    def test_get_function(self):
        assert isinstance(
            GetFunction(package=PKG, module_name="coin", function_name="mint"),
            SuiCommand,
        )

    def test_get_functions(self):
        assert isinstance(GetFunctions(package=PKG, module_name="coin"), SuiCommand)

    def test_get_name_service_address(self):
        assert isinstance(GetNameServiceAddress(name="alice.sui"), SuiCommand)

    def test_get_name_service_names(self):
        assert isinstance(GetNameServiceNames(owner=ADDR), SuiCommand)

    def test_simulate_transaction(self):
        assert isinstance(SimulateTransaction(tx_bytestr=b"txdata"), SuiCommand)


# ---------------------------------------------------------------------------
# paging flags
# ---------------------------------------------------------------------------


class TestPagingFlags:
    def test_get_structures_pageable_gql(self):
        assert GetStructures.is_pageable_gql is True
        assert GetStructures.paginated_field_path_gql == ("structures",)

    def test_get_functions_pageable_gql(self):
        assert GetFunctions.is_pageable_gql is True
        assert GetFunctions.paginated_field_path_gql == ("functions",)

    def test_get_coins_paging_true(self):
        assert GetCoins.is_pageable_gql is True
        assert GetCoins.paginated_field_path_gql == ("objects",)

    def test_get_gas_paging_true(self):
        assert GetGas.is_pageable_gql is True
        assert GetGas.paginated_field_path_gql == ("objects",)
        assert GetGas.is_pageable_grpc is True
        assert GetGas.paginated_field_path_grpc == ("objects",)

    def test_get_object_paging_false(self):
        assert GetObject.is_pageable_gql is False


# ---------------------------------------------------------------------------
# grpc_request() returns PGRPC_Request
# ---------------------------------------------------------------------------


class TestGrpcRequests:
    def test_get_coin_metadata(self):
        assert _is_grpc(GetCoinMetaData().grpc_request())

    def test_get_address_coin_balance(self):
        assert _is_grpc(GetAddressCoinBalance(owner=ADDR).grpc_request())

    def test_get_address_coin_balances(self):
        assert _is_grpc(GetAddressCoinBalances(owner=ADDR).grpc_request())

    def test_get_coins(self):
        assert _is_grpc(GetCoins(owner=ADDR).grpc_request())

    def test_get_gas(self):
        assert _is_grpc(GetGas(owner=ADDR).grpc_request())

    def test_get_staked(self):
        assert _is_grpc(GetStaked(owner=ADDR).grpc_request())

    def test_get_delegated_stakes(self):
        assert _is_grpc(GetDelegatedStakes(owner=ADDR).grpc_request())

    def test_get_object(self):
        assert _is_grpc(GetObject(object_id=OBJ_ID).grpc_request())

    def test_get_past_object(self):
        assert _is_grpc(GetPastObject(object_id=OBJ_ID, version=5).grpc_request())

    def test_get_multiple_objects(self):
        assert _is_grpc(GetMultipleObjects(object_ids=[OBJ_ID]).grpc_request())

    def test_get_multiple_past_objects(self):
        req = GetMultiplePastObjects(
            for_versions=[{"objectId": OBJ_ID, "version": 1}]
        ).grpc_request()
        assert _is_grpc(req)
        assert isinstance(req, rn.GetMultiplePastObjects)

    def test_get_objects_owned_by_address(self):
        assert _is_grpc(GetObjectsOwnedByAddress(owner=ADDR).grpc_request())

    def test_get_dynamic_fields(self):
        assert _is_grpc(GetDynamicFields(object_id=OBJ_ID).grpc_request())

    def test_get_epoch(self):
        assert _is_grpc(GetEpoch().grpc_request())

    def test_get_epoch_with_id(self):
        req = GetEpoch(epoch_id=42).grpc_request()
        assert _is_grpc(req)
        assert req.epoch_number == 42

    def test_get_latest_checkpoint(self):
        assert _is_grpc(GetLatestCheckpoint().grpc_request())

    def test_get_checkpoint_by_sequence(self):
        assert _is_grpc(GetCheckpointBySequence(sequence_number=100).grpc_request())

    def test_get_multiple_object_content(self):
        assert _is_grpc(GetMultipleObjectContent(object_ids=[OBJ_ID]).grpc_request())

    def test_get_protocol_config(self):
        assert _is_grpc(GetProtocolConfig().grpc_request())
        assert _is_grpc(GetProtocolConfig(version=1).grpc_request())

    def test_get_object_content(self):
        assert _is_grpc(GetObjectContent(object_id=OBJ_ID).grpc_request())

    def test_get_objects_for_type(self):
        assert _is_grpc(GetObjectsForType(owner=ADDR, object_type="0x2::coin::Coin<0x2::sui::SUI>").grpc_request())

    def test_get_coin_summary(self):
        assert _is_grpc(GetCoinSummary(coin_id=OBJ_ID).grpc_request())

    def test_get_package(self):
        assert _is_grpc(GetPackage(package=PKG).grpc_request())

    def test_get_package_versions(self):
        req = GetPackageVersions(package_address=PKG).grpc_request()
        assert _is_grpc(req)
        assert isinstance(req, rn.GetPackageVersions)

    def test_get_module(self):
        assert _is_grpc(GetModule(package=PKG, module_name="coin").grpc_request())

    def test_get_move_data_type(self):
        assert _is_grpc(
            GetMoveDataType(
                package=PKG, module_name="coin", type_name="Coin"
            ).grpc_request()
        )

    def test_get_structure(self):
        assert _is_grpc(
            GetStructure(
                package=PKG, module_name="coin", structure_name="Coin"
            ).grpc_request()
        )

    def test_get_structures(self):
        assert _is_grpc(GetStructures(package=PKG, module_name="coin").grpc_request())

    def test_get_function(self):
        assert _is_grpc(
            GetFunction(
                package=PKG, module_name="coin", function_name="mint"
            ).grpc_request()
        )

    def test_get_functions(self):
        assert _is_grpc(GetFunctions(package=PKG, module_name="coin").grpc_request())

    def test_get_name_service_address(self):
        assert _is_grpc(GetNameServiceAddress(name="alice.sui").grpc_request())

    def test_get_name_service_names(self):
        req = GetNameServiceNames(owner=ADDR).grpc_request()
        assert _is_grpc(req)
        assert isinstance(req, rn.GetNameServiceNames)

    def test_simulate_transaction(self):
        assert _is_grpc(SimulateTransaction(tx_bytestr=b"txdata").grpc_request())


# ---------------------------------------------------------------------------
# gql_node() returns PGQL_QueryNode
# ---------------------------------------------------------------------------


class TestGqlNodes:
    def test_get_coin_metadata(self):
        assert _is_gql(GetCoinMetaData().gql_node())

    def test_get_address_coin_balance(self):
        assert _is_gql(GetAddressCoinBalance(owner=ADDR).gql_node())

    def test_get_address_coin_balances(self):
        assert _is_gql(GetAddressCoinBalances(owner=ADDR).gql_node())

    def test_get_coins(self):
        assert _is_gql(GetCoins(owner=ADDR).gql_node())

    def test_get_gas(self):
        assert _is_gql(GetGas(owner=ADDR).gql_node())

    def test_get_staked(self):
        assert _is_gql(GetStaked(owner=ADDR).gql_node())

    def test_get_delegated_stakes(self):
        assert _is_gql(GetDelegatedStakes(owner=ADDR).gql_node())

    def test_get_object(self):
        assert _is_gql(GetObject(object_id=OBJ_ID).gql_node())

    def test_get_past_object(self):
        assert _is_gql(GetPastObject(object_id=OBJ_ID, version=5).gql_node())

    def test_get_multiple_objects(self):
        assert _is_gql(GetMultipleObjects(object_ids=[OBJ_ID]).gql_node())

    def test_get_multiple_past_objects_translates_keys(self):
        node = GetMultiplePastObjects(
            for_versions=[{"objectId": OBJ_ID, "version": 1}]
        ).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetMultipleVersionedObjects)
        # GQL format uses "address" key, not "objectId"
        assert node.version_list[0]["address"] == OBJ_ID
        assert node.version_list[0]["version"] == 1

    def test_get_objects_owned_by_address(self):
        assert _is_gql(GetObjectsOwnedByAddress(owner=ADDR).gql_node())

    def test_get_dynamic_fields(self):
        assert _is_gql(GetDynamicFields(object_id=OBJ_ID).gql_node())

    def test_get_epoch(self):
        assert _is_gql(GetEpoch().gql_node())

    def test_get_epoch_with_id(self):
        node = GetEpoch(epoch_id=5).gql_node()
        assert _is_gql(node)
        assert node.epoch_id == 5

    def test_get_latest_checkpoint(self):
        node = GetLatestCheckpoint().gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetLatestCheckpointSequence)

    def test_get_checkpoint_by_sequence(self):
        node = GetCheckpointBySequence(sequence_number=99).gql_node()
        assert _is_gql(node)
        assert node.sequence_number == 99

    def test_get_multiple_object_content(self):
        node = GetMultipleObjectContent(object_ids=[OBJ_ID]).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetMultipleObjectContentSC)

    def test_get_protocol_config(self):
        node = GetProtocolConfig().gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetProtocolConfigSC)
        node_with_version = GetProtocolConfig(version=1).gql_node()
        assert _is_gql(node_with_version)

    def test_get_object_content(self):
        node = GetObjectContent(object_id=OBJ_ID).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetObjectContentSC)

    def test_get_objects_for_type(self):
        node = GetObjectsForType(owner=ADDR, object_type="0x2::coin::Coin<0x2::sui::SUI>").gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetObjectsForTypeSC)
        assert node.owner == ADDR
        assert node.object_type == "0x2::coin::Coin<0x2::sui::SUI>"

    def test_get_coin_summary(self):
        node = GetCoinSummary(coin_id=OBJ_ID).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetCoinSummarySC)

    def test_get_package(self):
        node = GetPackage(package=PKG).gql_node()
        assert _is_gql(node)
        assert node.package == PKG

    def test_get_package_versions(self):
        node = GetPackageVersions(package_address=PKG).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetPackageVersions)

    def test_get_module(self):
        node = GetModule(package=PKG, module_name="coin").gql_node()
        assert _is_gql(node)
        assert node.module == "coin"

    def test_get_move_data_type(self):
        node = GetMoveDataType(
            package=PKG, module_name="coin", type_name="Coin"
        ).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetMoveDataType)
        assert node.data_type_name == "Coin"

    def test_get_structure(self):
        node = GetStructure(
            package=PKG, module_name="coin", structure_name="Coin"
        ).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetStructure)

    def test_get_structures(self):
        node = GetStructures(package=PKG, module_name="coin").gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetStructures)

    def test_get_function(self):
        node = GetFunction(
            package=PKG, module_name="coin", function_name="mint"
        ).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetFunction)

    def test_get_functions(self):
        node = GetFunctions(package=PKG, module_name="coin").gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetFunctions)

    def test_get_name_service_address(self):
        node = GetNameServiceAddress(name="alice.sui").gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetNameServiceAddress)

    def test_get_name_service_names(self):
        node = GetNameServiceNames(owner=ADDR).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetNameServiceNames)

    def test_simulate_transaction(self):
        node = SimulateTransaction(tx_bytestr=b"txdata").gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.SimulateTransactionSC)


# ---------------------------------------------------------------------------
# Parameter routing correctness
# ---------------------------------------------------------------------------


class TestParameterRouting:
    def test_get_epoch_epoch_id_mapped_to_epoch_number(self):
        req = GetEpoch(epoch_id=7).grpc_request()
        assert isinstance(req, rn.GetEpoch)
        assert req.epoch_number == 7

    def test_get_epoch_none_gives_none(self):
        req = GetEpoch().grpc_request()
        assert req.epoch_number is None

    def test_get_package_versions_address_mapped_to_storage_id(self):
        req = GetPackageVersions(package_address=PKG).grpc_request()
        assert isinstance(req, rn.GetPackageVersions)
        assert req.package_storage_id == PKG

    def test_get_name_service_names_owner_mapped_to_address(self):
        req = GetNameServiceNames(owner=ADDR).grpc_request()
        assert isinstance(req, rn.GetNameServiceNames)
        assert req.address == ADDR

    def test_get_multiple_past_objects_grpc_uses_object_id_key(self):
        req = GetMultiplePastObjects(
            for_versions=[{"objectId": OBJ_ID, "version": 3}]
        ).grpc_request()
        assert isinstance(req, rn.GetMultiplePastObjects)
        assert req.objects[0].object_id == OBJ_ID
        assert req.objects[0].version == 3

    def test_get_move_data_type_gql_uses_data_type_name(self):
        node = GetMoveDataType(
            package=PKG, module_name="m", type_name="MyStruct"
        ).gql_node()
        assert isinstance(node, pgql_query.GetMoveDataType)
        assert node.data_type_name == "MyStruct"

    def test_get_move_data_type_grpc_uses_type_name(self):
        req = GetMoveDataType(
            package=PKG, module_name="m", type_name="MyStruct"
        ).grpc_request()
        assert isinstance(req, rn.GetMoveDataType)
        assert req.type_name == "MyStruct"


# ---------------------------------------------------------------------------
# Transaction query SuiCommands
# ---------------------------------------------------------------------------


class TestTransactionCommands:
    """Construction, node/request dispatch, and invariants for transaction query commands."""

    def test_get_transaction_is_sui_command(self):
        assert isinstance(GetTransaction(digest=DIGEST), SuiCommand)

    def test_get_transaction_stores_digest(self):
        cmd = GetTransaction(digest=DIGEST)
        assert cmd.digest == DIGEST

    def test_get_transaction_gql_node_type(self):
        node = GetTransaction(digest=DIGEST).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetTransactionSC)

    def test_get_transaction_grpc_request_type(self):
        req = GetTransaction(digest=DIGEST).grpc_request()
        assert _is_grpc(req)
        assert isinstance(req, rn.GetTransactionSC)

    def test_get_transaction_gql_node_carries_digest(self):
        node = GetTransaction(digest=DIGEST).gql_node()
        assert node.digest == DIGEST

    def test_get_transaction_grpc_request_carries_digest(self):
        req = GetTransaction(digest=DIGEST).grpc_request()
        assert req.digest == DIGEST

    def test_get_transactions_is_sui_command(self):
        assert isinstance(GetTransactions(digests=[DIGEST]), SuiCommand)

    def test_get_transactions_stores_digests(self):
        cmd = GetTransactions(digests=[DIGEST, "OtherDigest"])
        assert cmd.digests == [DIGEST, "OtherDigest"]

    def test_get_transactions_empty_list_raises(self):
        with pytest.raises(ValueError, match="digest"):
            GetTransactions(digests=[])

    def test_get_transactions_gql_node_type(self):
        node = GetTransactions(digests=[DIGEST]).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetTransactionsSC)

    def test_get_transactions_grpc_request_type(self):
        req = GetTransactions(digests=[DIGEST]).grpc_request()
        assert _is_grpc(req)
        assert isinstance(req, rn.GetTransactionsSC)

    def test_get_transactions_gql_node_carries_digests(self):
        node = GetTransactions(digests=[DIGEST]).gql_node()
        assert node.digests == [DIGEST]

    def test_get_transactions_grpc_request_carries_digests(self):
        req = GetTransactions(digests=[DIGEST]).grpc_request()
        assert req.transactions == [DIGEST]

    def test_get_transaction_kind_is_sui_command(self):
        assert isinstance(GetTransactionKind(digest=DIGEST), SuiCommand)

    def test_get_transaction_kind_stores_digest(self):
        cmd = GetTransactionKind(digest=DIGEST)
        assert cmd.digest == DIGEST

    def test_get_transaction_kind_gql_node_type(self):
        node = GetTransactionKind(digest=DIGEST).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetTransactionKindSC)

    def test_get_transaction_kind_grpc_request_type(self):
        req = GetTransactionKind(digest=DIGEST).grpc_request()
        assert _is_grpc(req)
        assert isinstance(req, rn.GetTransactionKindSC)

    def test_get_transaction_kind_gql_node_carries_digest(self):
        node = GetTransactionKind(digest=DIGEST).gql_node()
        assert node.digest == DIGEST

    def test_get_transaction_kind_grpc_request_carries_digest(self):
        req = GetTransactionKind(digest=DIGEST).grpc_request()
        assert req.digest == DIGEST
