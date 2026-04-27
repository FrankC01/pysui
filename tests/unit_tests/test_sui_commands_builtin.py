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
    GetCheckpointByDigest,
    GetCheckpointBySequence,
    GetCoinMetaData,
    GetCoins,
    GetCurrentValidators,
    GetDelegatedStakes,
    GetDynamicFields,
    GetEpoch,
    GetEvents,
    GetFilteredTx,
    GetFunction,
    GetFunctions,
    GetGas,
    GetLatestCheckpoint,
    GetLatestSuiSystemState,
    GetModule,
    GetMoveDataType,
    GetMultipleObjects,
    GetMultiplePastObjects,
    GetMultipleTx,
    GetNameServiceAddress,
    GetNameServiceNames,
    GetObject,
    GetObjectsOwnedByAddress,
    GetPackage,
    GetPackageVersions,
    GetPastObject,
    GetServiceInfo,
    GetStaked,
    GetStructure,
    GetStructures,
    GetTx,
    GetTxKind,
    SimulateTransaction,
    SimulateTransactionKind,
    SubscribeCheckpoint,
    VerifySignature,
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

    def test_get_latest_sui_system_state(self):
        assert isinstance(GetLatestSuiSystemState(), SuiCommand)

    def test_get_current_validators(self):
        assert isinstance(GetCurrentValidators(), SuiCommand)

    def test_get_latest_checkpoint(self):
        assert isinstance(GetLatestCheckpoint(), SuiCommand)

    def test_get_checkpoint_by_sequence(self):
        assert isinstance(GetCheckpointBySequence(sequence_number=42), SuiCommand)

    def test_get_checkpoint_by_digest(self):
        assert isinstance(GetCheckpointByDigest(digest=DIGEST), SuiCommand)

    def test_get_tx(self):
        assert isinstance(GetTx(digest=DIGEST), SuiCommand)

    def test_get_tx_kind(self):
        assert isinstance(GetTxKind(digest=DIGEST), SuiCommand)

    def test_get_multiple_tx(self):
        assert isinstance(GetMultipleTx(transactions=[DIGEST]), SuiCommand)

    def test_get_filtered_tx(self):
        assert isinstance(GetFilteredTx(tx_filter={"sender": ADDR}), SuiCommand)

    def test_get_events(self):
        assert isinstance(GetEvents(event_filter={"sender": ADDR}), SuiCommand)

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

    def test_get_service_info(self):
        assert isinstance(GetServiceInfo(), SuiCommand)

    def test_subscribe_checkpoint(self):
        assert isinstance(SubscribeCheckpoint(), SuiCommand)

    def test_verify_signature(self):
        assert isinstance(
            VerifySignature(
                message_type="Transaction",
                message=b"msg",
                signature=b"sig",
            ),
            SuiCommand,
        )

    def test_simulate_transaction(self):
        assert isinstance(SimulateTransaction(tx_bytestr=b"txdata"), SuiCommand)


# ---------------------------------------------------------------------------
# gql_requires_paging
# ---------------------------------------------------------------------------


class TestPagingFlags:
    def test_get_current_validators_paging_true(self):
        assert GetCurrentValidators.gql_requires_paging is True

    def test_get_structures_paging_true(self):
        assert GetStructures.gql_requires_paging is True

    def test_get_functions_paging_true(self):
        assert GetFunctions.gql_requires_paging is True

    def test_get_coins_paging_false(self):
        assert GetCoins.gql_requires_paging is False

    def test_get_gas_paging_false(self):
        assert GetGas.gql_requires_paging is False

    def test_get_object_paging_false(self):
        assert GetObject.gql_requires_paging is False


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

    def test_get_latest_sui_system_state(self):
        assert _is_grpc(GetLatestSuiSystemState().grpc_request())

    def test_get_current_validators(self):
        assert _is_grpc(GetCurrentValidators().grpc_request())

    def test_get_latest_checkpoint(self):
        assert _is_grpc(GetLatestCheckpoint().grpc_request())

    def test_get_checkpoint_by_sequence(self):
        assert _is_grpc(GetCheckpointBySequence(sequence_number=100).grpc_request())

    def test_get_checkpoint_by_digest(self):
        assert _is_grpc(GetCheckpointByDigest(digest=DIGEST).grpc_request())

    def test_get_tx(self):
        assert _is_grpc(GetTx(digest=DIGEST).grpc_request())

    def test_get_tx_kind(self):
        assert _is_grpc(GetTxKind(digest=DIGEST).grpc_request())

    def test_get_multiple_tx(self):
        assert _is_grpc(GetMultipleTx(transactions=[DIGEST]).grpc_request())

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

    def test_get_service_info(self):
        assert _is_grpc(GetServiceInfo().grpc_request())

    def test_subscribe_checkpoint(self):
        assert _is_grpc(SubscribeCheckpoint().grpc_request())

    def test_verify_signature(self):
        assert _is_grpc(
            VerifySignature(
                message_type="Transaction",
                message=b"msg",
                signature=b"sig",
            ).grpc_request()
        )

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

    def test_get_latest_sui_system_state(self):
        assert _is_gql(GetLatestSuiSystemState().gql_node())

    def test_get_current_validators(self):
        assert _is_gql(GetCurrentValidators().gql_node())

    def test_get_latest_checkpoint(self):
        node = GetLatestCheckpoint().gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetLatestCheckpointSequence)

    def test_get_checkpoint_by_sequence(self):
        node = GetCheckpointBySequence(sequence_number=99).gql_node()
        assert _is_gql(node)
        assert node.sequence_number == 99

    def test_get_tx(self):
        node = GetTx(digest=DIGEST).gql_node()
        assert _is_gql(node)
        assert node.digest == DIGEST

    def test_get_tx_kind(self):
        node = GetTxKind(digest=DIGEST).gql_node()
        assert _is_gql(node)
        assert node.digest == DIGEST

    def test_get_filtered_tx(self):
        node = GetFilteredTx(tx_filter={"sender": ADDR}).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetFilteredTx)

    def test_get_events(self):
        node = GetEvents(event_filter={"sender": ADDR}).gql_node()
        assert _is_gql(node)
        assert isinstance(node, pgql_query.GetEvents)

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
        assert isinstance(node, pgql_query.SimulateTransaction)


# ---------------------------------------------------------------------------
# EC-3: correct side raises NotImplementedError
# ---------------------------------------------------------------------------


class TestEC3Commands:
    # gRPC-only: gql_node raises
    def test_get_checkpoint_by_digest_gql_raises(self):
        cmd = GetCheckpointByDigest(digest=DIGEST)
        with pytest.raises(NotImplementedError):
            cmd.gql_node()

    def test_get_checkpoint_by_digest_grpc_ok(self):
        assert _is_grpc(GetCheckpointByDigest(digest=DIGEST).grpc_request())

    def test_get_multiple_tx_gql_raises(self):
        cmd = GetMultipleTx(transactions=[DIGEST])
        with pytest.raises(NotImplementedError):
            cmd.gql_node()

    def test_get_multiple_tx_grpc_ok(self):
        assert _is_grpc(GetMultipleTx(transactions=[DIGEST]).grpc_request())

    def test_get_service_info_gql_raises(self):
        cmd = GetServiceInfo()
        with pytest.raises(NotImplementedError):
            cmd.gql_node()

    def test_get_service_info_grpc_ok(self):
        assert _is_grpc(GetServiceInfo().grpc_request())

    def test_subscribe_checkpoint_gql_raises(self):
        cmd = SubscribeCheckpoint()
        with pytest.raises(NotImplementedError):
            cmd.gql_node()

    def test_subscribe_checkpoint_grpc_ok(self):
        assert _is_grpc(SubscribeCheckpoint().grpc_request())

    def test_verify_signature_gql_raises(self):
        cmd = VerifySignature(
            message_type="Transaction", message=b"msg", signature=b"sig"
        )
        with pytest.raises(NotImplementedError):
            cmd.gql_node()

    def test_verify_signature_grpc_ok(self):
        assert _is_grpc(
            VerifySignature(
                message_type="Transaction", message=b"msg", signature=b"sig"
            ).grpc_request()
        )

    # GQL-only: grpc_request raises
    def test_get_filtered_tx_grpc_raises(self):
        cmd = GetFilteredTx(tx_filter={"sender": ADDR})
        with pytest.raises(NotImplementedError):
            cmd.grpc_request()

    def test_get_filtered_tx_gql_ok(self):
        assert _is_gql(GetFilteredTx(tx_filter={"sender": ADDR}).gql_node())

    def test_get_events_grpc_raises(self):
        cmd = GetEvents(event_filter={"sender": ADDR})
        with pytest.raises(NotImplementedError):
            cmd.grpc_request()

    def test_get_events_gql_ok(self):
        assert _is_gql(GetEvents(event_filter={"sender": ADDR}).gql_node())


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
