#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: SuiCommand getter and transaction-query commands.

These tests exercise the GQL SC-sibling encode_fn path and the gRPC path for
all read-only SuiCommand subclasses and transaction-query SuiCommands.  They
query only stable framework objects (0x2, 0x5, 0x6) and the active address's
owned objects, plus a live transaction submitted by the TxnDigests fixture.

Run in isolation:
    pytest tests/integration_tests/test_suicommands.py

Commands covered:
  Checkpoints  : GetLatestCheckpoint, GetCheckpointBySequence
  Package/mod  : GetPackage, GetModule, GetMoveDataType, GetStructure, GetFunction
  Paged        : GetStructures (SC paging), GetFunctions (SC paging)
  Objects      : GetObject, GetMultipleObjects
  Owned        : GetCoins, GetGas, GetObjectsOwnedByAddress
  High-complex : GetDynamicFields
  System state : GetLatestSuiSystemState, GetCurrentValidators
  Transactions : GetTransaction, GetTransactions, GetTransactionKind
"""

import asyncio
import base64

import pytest

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui import client_factory, GroupProtocol, PysuiConfiguration, AsyncClientBase
from tests.integration_tests.conftest import SETTLE_SECS, CentralBank, GasBank
from pysui.sui.sui_grpc.pgrpc_requests import MoveStructuresGRPC, MoveFunctionsGRPC
from pysui.sui.sui_common.sui_commands import (
    ExecuteTransaction,
    GetCheckpointBySequence,
    GetCoins,
    GetCurrentValidators,
    GetDynamicFields,
    GetFunction,
    GetFunctions,
    GetGas,
    GetLatestCheckpoint,
    GetLatestSuiSystemState,
    GetModule,
    GetMoveDataType,
    GetMultipleObjects,
    GetObject,
    GetObjectsOwnedByAddress,
    GetPackage,
    GetStructure,
    GetStructures,
    GetTransaction,
    GetTransactions,
    GetTransactionKind,
    VerifyPersonalMessageSignature,
    VerifyTransactionSignature,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="sui_integration"),
]

# Stable framework objects available on all Sui networks.
_FRAMEWORK = "0x2"
_FRAMEWORK_MODULE = "coin"
_FRAMEWORK_STRUCT = "Coin"
_FRAMEWORK_FN = "split"
_SYSTEM_STATE_OBJ = (
    "0x0000000000000000000000000000000000000000000000000000000000000005"
)
_CLOCK_OBJ = (
    "0x0000000000000000000000000000000000000000000000000000000000000006"
)

# Valid-format (32-byte base58) digest that does not exist on any network.
_NONEXISTENT_DIGEST = "4vJ9JU1bJJE96FWSJKvHsmmFADCg4gpZQff4P3bkLKi"


# ---------------------------------------------------------------------------
# Checkpoint queries
# ---------------------------------------------------------------------------


@pytest.mark.order(1)
async def test_get_latest_checkpoint_gql(gql_session_client: AsyncClientBase) -> None:
    """GetLatestCheckpoint via GQL SC sibling returns GetCheckpointResponse."""
    result = await gql_session_client.execute(command=GetLatestCheckpoint())
    assert result.is_ok(), f"GetLatestCheckpoint GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetCheckpointResponse)
    assert result.result_data.checkpoint is not None
    assert result.result_data.checkpoint.sequence_number is not None


@pytest.mark.order(2)
async def test_get_latest_checkpoint_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetLatestCheckpoint via gRPC returns GetCheckpointResponse."""
    result = await grpc_session_client.execute(command=GetLatestCheckpoint())
    assert result.is_ok(), f"GetLatestCheckpoint gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetCheckpointResponse)
    assert result.result_data.checkpoint is not None


@pytest.mark.order(3)
async def test_get_checkpoint_by_sequence_gql(
    gql_session_client: AsyncClientBase,
) -> None:
    """GetCheckpointBySequence(1) via GQL SC sibling returns GetCheckpointResponse."""
    result = await gql_session_client.execute(
        command=GetCheckpointBySequence(sequence_number=1)
    )
    assert result.is_ok(), f"GetCheckpointBySequence GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetCheckpointResponse)
    assert result.result_data.checkpoint is not None


@pytest.mark.order(4)
async def test_get_checkpoint_by_sequence_grpc(
    grpc_session_client: AsyncClientBase,
) -> None:
    """GetCheckpointBySequence(1) via gRPC returns GetCheckpointResponse."""
    result = await grpc_session_client.execute(
        command=GetCheckpointBySequence(sequence_number=1)
    )
    assert result.is_ok(), f"GetCheckpointBySequence gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetCheckpointResponse)


# ---------------------------------------------------------------------------
# Package / module / datatype / function queries
# ---------------------------------------------------------------------------


@pytest.mark.order(5)
async def test_get_package_gql(gql_session_client: AsyncClientBase) -> None:
    """GetPackage(0x2) via GQL SC sibling returns GetPackageResponse."""
    result = await gql_session_client.execute(command=GetPackage(package=_FRAMEWORK))
    assert result.is_ok(), f"GetPackage GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetPackageResponse)
    assert result.result_data.package is not None


@pytest.mark.order(6)
async def test_get_package_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetPackage(0x2) via gRPC returns GetPackageResponse."""
    result = await grpc_session_client.execute(command=GetPackage(package=_FRAMEWORK))
    assert result.is_ok(), f"GetPackage gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetPackageResponse)


@pytest.mark.order(7)
async def test_get_module_gql(gql_session_client: AsyncClientBase) -> None:
    """GetModule(0x2, coin) via GQL SC sibling returns Module."""
    result = await gql_session_client.execute(
        command=GetModule(package=_FRAMEWORK, module_name=_FRAMEWORK_MODULE)
    )
    assert result.is_ok(), f"GetModule GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.Module)


@pytest.mark.order(8)
async def test_get_module_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetModule(0x2, coin) via gRPC returns Module."""
    result = await grpc_session_client.execute(
        command=GetModule(package=_FRAMEWORK, module_name=_FRAMEWORK_MODULE)
    )
    assert result.is_ok(), f"GetModule gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.Module)


@pytest.mark.order(9)
async def test_get_move_datatype_gql(gql_session_client: AsyncClientBase) -> None:
    """GetMoveDataType(0x2::coin::Coin) via GQL SC sibling returns GetDatatypeResponse."""
    result = await gql_session_client.execute(
        command=GetMoveDataType(
            package=_FRAMEWORK,
            module_name=_FRAMEWORK_MODULE,
            type_name=_FRAMEWORK_STRUCT,
        )
    )
    assert result.is_ok(), f"GetMoveDataType GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetDatatypeResponse)
    assert result.result_data.datatype is not None


@pytest.mark.order(10)
async def test_get_move_datatype_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetMoveDataType(0x2::coin::Coin) via gRPC returns GetDatatypeResponse."""
    result = await grpc_session_client.execute(
        command=GetMoveDataType(
            package=_FRAMEWORK,
            module_name=_FRAMEWORK_MODULE,
            type_name=_FRAMEWORK_STRUCT,
        )
    )
    assert result.is_ok(), f"GetMoveDataType gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetDatatypeResponse)


@pytest.mark.order(11)
async def test_get_structure_gql(gql_session_client: AsyncClientBase) -> None:
    """GetStructure(0x2::coin::Coin) via GQL SC sibling returns GetDatatypeResponse."""
    result = await gql_session_client.execute(
        command=GetStructure(
            package=_FRAMEWORK,
            module_name=_FRAMEWORK_MODULE,
            structure_name=_FRAMEWORK_STRUCT,
        )
    )
    assert result.is_ok(), f"GetStructure GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetDatatypeResponse)
    assert result.result_data.datatype is not None


@pytest.mark.order(12)
async def test_get_structure_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetStructure(0x2::coin::Coin) via gRPC returns GetDatatypeResponse."""
    result = await grpc_session_client.execute(
        command=GetStructure(
            package=_FRAMEWORK,
            module_name=_FRAMEWORK_MODULE,
            structure_name=_FRAMEWORK_STRUCT,
        )
    )
    assert result.is_ok(), f"GetStructure gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetDatatypeResponse)


@pytest.mark.order(13)
async def test_get_function_gql(gql_session_client: AsyncClientBase) -> None:
    """GetFunction(0x2::coin::split) via GQL SC sibling returns GetFunctionResponse."""
    result = await gql_session_client.execute(
        command=GetFunction(
            package=_FRAMEWORK,
            module_name=_FRAMEWORK_MODULE,
            function_name=_FRAMEWORK_FN,
        )
    )
    assert result.is_ok(), f"GetFunction GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetFunctionResponse)
    assert result.result_data.function is not None


@pytest.mark.order(14)
async def test_get_function_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetFunction(0x2::coin::split) via gRPC returns GetFunctionResponse."""
    result = await grpc_session_client.execute(
        command=GetFunction(
            package=_FRAMEWORK,
            module_name=_FRAMEWORK_MODULE,
            function_name=_FRAMEWORK_FN,
        )
    )
    assert result.is_ok(), f"GetFunction gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.GetFunctionResponse)


# ---------------------------------------------------------------------------
# Paged queries — pageable SuiCommands (execute_for_all accumulates all pages)
# ---------------------------------------------------------------------------


@pytest.mark.order(15)
async def test_get_structures_gql_paged(gql_session_client: AsyncClientBase) -> None:
    """GetStructures(0x2::coin) via GQL SC paging branch returns MoveStructuresGRPC."""
    result = await gql_session_client.execute(
        command=GetStructures(package=_FRAMEWORK, module_name=_FRAMEWORK_MODULE)
    )
    assert result.is_ok(), f"GetStructures GQL paged: {result.result_string}"
    assert isinstance(result.result_data, MoveStructuresGRPC)
    assert len(result.result_data.structures) > 0


@pytest.mark.order(16)
async def test_get_structures_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetStructures(0x2::coin) via gRPC returns MoveStructuresGRPC."""
    result = await grpc_session_client.execute(
        command=GetStructures(package=_FRAMEWORK, module_name=_FRAMEWORK_MODULE)
    )
    assert result.is_ok(), f"GetStructures gRPC: {result.result_string}"
    assert isinstance(result.result_data, MoveStructuresGRPC)
    assert len(result.result_data.structures) > 0


@pytest.mark.order(17)
async def test_get_functions_gql_paged(gql_session_client: AsyncClientBase) -> None:
    """GetFunctions(0x2::coin) via GQL SC paging branch returns MoveFunctionsGRPC."""
    result = await gql_session_client.execute(
        command=GetFunctions(package=_FRAMEWORK, module_name=_FRAMEWORK_MODULE)
    )
    assert result.is_ok(), f"GetFunctions GQL paged: {result.result_string}"
    assert isinstance(result.result_data, MoveFunctionsGRPC)
    assert len(result.result_data.functions) > 0


@pytest.mark.order(18)
async def test_get_functions_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetFunctions(0x2::coin) via gRPC returns MoveFunctionsGRPC."""
    result = await grpc_session_client.execute(
        command=GetFunctions(package=_FRAMEWORK, module_name=_FRAMEWORK_MODULE)
    )
    assert result.is_ok(), f"GetFunctions gRPC: {result.result_string}"
    assert isinstance(result.result_data, MoveFunctionsGRPC)
    assert len(result.result_data.functions) > 0


# ---------------------------------------------------------------------------
# Object queries — stable shared objects (Clock, SuiSystemState)
# ---------------------------------------------------------------------------


@pytest.mark.order(19)
async def test_get_object_gql(gql_session_client: AsyncClientBase) -> None:
    """GetObject(0x6 Clock) via GQL SC sibling returns Object."""
    result = await gql_session_client.execute(command=GetObject(object_id=_CLOCK_OBJ))
    assert result.is_ok(), f"GetObject GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.Object)


@pytest.mark.order(20)
async def test_get_object_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetObject(0x6 Clock) via gRPC SC sibling returns Object (same as GQL path)."""
    result = await grpc_session_client.execute(command=GetObject(object_id=_CLOCK_OBJ))
    assert result.is_ok(), f"GetObject gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.Object)


@pytest.mark.order(21)
async def test_get_multiple_objects_gql(gql_session_client: AsyncClientBase) -> None:
    """GetMultipleObjects([0x5, 0x6]) via GQL SC sibling returns BatchGetObjectsResponse."""
    result = await gql_session_client.execute(
        command=GetMultipleObjects(object_ids=[_SYSTEM_STATE_OBJ, _CLOCK_OBJ])
    )
    assert result.is_ok(), f"GetMultipleObjects GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.BatchGetObjectsResponse)
    assert len(result.result_data.objects) == 2


@pytest.mark.order(22)
async def test_get_multiple_objects_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetMultipleObjects([0x5, 0x6]) via gRPC returns BatchGetObjectsResponse."""
    result = await grpc_session_client.execute(
        command=GetMultipleObjects(object_ids=[_SYSTEM_STATE_OBJ, _CLOCK_OBJ])
    )
    assert result.is_ok(), f"GetMultipleObjects gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.BatchGetObjectsResponse)
    assert len(result.result_data.objects) == 2


# ---------------------------------------------------------------------------
# Owned-object queries — active address (empty list is a valid success)
# ---------------------------------------------------------------------------


@pytest.mark.order(23)
async def test_get_coins_gql(gql_session_client: AsyncClientBase) -> None:
    """GetCoins for active address via GQL SC sibling returns ListOwnedObjectsResponse."""
    owner = gql_session_client.config.active_address
    result = await gql_session_client.execute(command=GetCoins(owner=owner))
    assert result.is_ok(), f"GetCoins GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListOwnedObjectsResponse)


@pytest.mark.order(24)
async def test_get_coins_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetCoins for active address via gRPC returns ListOwnedObjectsResponse."""
    owner = grpc_session_client.config.active_address
    result = await grpc_session_client.execute(command=GetCoins(owner=owner))
    assert result.is_ok(), f"GetCoins gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListOwnedObjectsResponse)


@pytest.mark.order(25)
async def test_get_gas_gql(gql_session_client: AsyncClientBase) -> None:
    """GetGas for active address via GQL SC sibling returns ListOwnedObjectsResponse."""
    owner = gql_session_client.config.active_address
    result = await gql_session_client.execute(command=GetGas(owner=owner))
    assert result.is_ok(), f"GetGas GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListOwnedObjectsResponse)


@pytest.mark.order(26)
async def test_get_gas_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetGas for active address via gRPC returns ListOwnedObjectsResponse."""
    owner = grpc_session_client.config.active_address
    result = await grpc_session_client.execute(command=GetGas(owner=owner))
    assert result.is_ok(), f"GetGas gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListOwnedObjectsResponse)


@pytest.mark.order(27)
async def test_get_objects_owned_by_address_gql(
    gql_session_client: AsyncClientBase,
) -> None:
    """GetObjectsOwnedByAddress for active address via GQL SC sibling returns ListOwnedObjectsResponse."""
    owner = gql_session_client.config.active_address
    result = await gql_session_client.execute(
        command=GetObjectsOwnedByAddress(owner=owner)
    )
    assert result.is_ok(), f"GetObjectsOwnedByAddress GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListOwnedObjectsResponse)


@pytest.mark.order(28)
async def test_get_objects_owned_by_address_grpc(
    grpc_session_client: AsyncClientBase,
) -> None:
    """GetObjectsOwnedByAddress for active address via gRPC returns ListOwnedObjectsResponse."""
    owner = grpc_session_client.config.active_address
    result = await grpc_session_client.execute(
        command=GetObjectsOwnedByAddress(owner=owner)
    )
    assert result.is_ok(), f"GetObjectsOwnedByAddress gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListOwnedObjectsResponse)


# ---------------------------------------------------------------------------
# Step 9 — High complexity SC siblings
# ---------------------------------------------------------------------------


@pytest.mark.order(29)
async def test_get_dynamic_fields_gql(gql_session_client: AsyncClientBase) -> None:
    """GetDynamicFields(0x5 SuiSystemState) via GQL SC sibling returns ListDynamicFieldsResponse."""
    result = await gql_session_client.execute(
        command=GetDynamicFields(object_id=_SYSTEM_STATE_OBJ)
    )
    assert result.is_ok(), f"GetDynamicFields GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ListDynamicFieldsResponse)


# ---------------------------------------------------------------------------
# System state / validator queries — devnet baseline
# ---------------------------------------------------------------------------


@pytest.mark.order(30)
async def test_get_latest_sui_system_state_gql(gql_session_client: AsyncClientBase) -> None:
    """GetLatestSuiSystemState via GQL SC sibling returns SystemState."""
    result = await gql_session_client.execute(command=GetLatestSuiSystemState())
    assert result.is_ok(), f"GetLatestSuiSystemState GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.SystemState)
    assert result.result_data.epoch is not None


@pytest.mark.order(31)
async def test_get_latest_sui_system_state_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetLatestSuiSystemState via gRPC SC sibling returns SystemState."""
    result = await grpc_session_client.execute(command=GetLatestSuiSystemState())
    assert result.is_ok(), f"GetLatestSuiSystemState gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.SystemState)
    assert result.result_data.epoch is not None


@pytest.mark.order(32)
async def test_get_current_validators_gql(gql_session_client: AsyncClientBase) -> None:
    """GetCurrentValidators via GQL SC paging branch returns list[Validator] (devnet)."""
    result = await gql_session_client.execute(command=GetCurrentValidators())
    assert result.is_ok(), f"GetCurrentValidators GQL: {result.result_string}"
    assert isinstance(result.result_data, list)
    assert len(result.result_data) > 0
    assert isinstance(result.result_data[0], sui_prot.Validator)


@pytest.mark.order(33)
async def test_get_current_validators_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetCurrentValidators via gRPC SC sibling returns list[Validator] (devnet)."""
    result = await grpc_session_client.execute(command=GetCurrentValidators())
    assert result.is_ok(), f"GetCurrentValidators gRPC: {result.result_string}"
    assert isinstance(result.result_data, list)
    assert len(result.result_data) > 0
    assert isinstance(result.result_data[0], sui_prot.Validator)


# ---------------------------------------------------------------------------
# Validator paging — testnet (fresh isolated config; page size = 20)
# A broken paging loop returns exactly 20 validators (one page).
# A working loop returns > 20 (multiple pages accumulated).
# ---------------------------------------------------------------------------

_TESTNET_PAGE_SIZE = 20


@pytest.mark.order(34)
async def test_get_current_validators_gql_testnet() -> None:
    """GetCurrentValidators via GQL on testnet accumulates multiple pages (> 20 validators)."""
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        profile_name="testnet",
    )
    client = client_factory(cfg, protocol=GroupProtocol.GRAPHQL)
    try:
        result = await client.execute_for_all(command=GetCurrentValidators())
        assert result.is_ok(), f"GetCurrentValidators GQL testnet: {result.result_string}"
        assert isinstance(result.result_data, list)
        assert isinstance(result.result_data[0], sui_prot.Validator)
        assert len(result.result_data) > _TESTNET_PAGE_SIZE, (
            f"Paging did not fire: expected > {_TESTNET_PAGE_SIZE} validators, "
            f"got {len(result.result_data)}"
        )
    finally:
        await client.close()


@pytest.mark.order(35)
async def test_get_current_validators_grpc_testnet() -> None:
    """GetCurrentValidators via gRPC on testnet returns > 20 validators."""
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        profile_name="testnet",
    )
    client = client_factory(cfg, protocol=GroupProtocol.GRPC)
    try:
        result = await client.execute_for_all(command=GetCurrentValidators())
        assert result.is_ok(), f"GetCurrentValidators gRPC testnet: {result.result_string}"
        assert isinstance(result.result_data, list)
        assert isinstance(result.result_data[0], sui_prot.Validator)
        assert len(result.result_data) > _TESTNET_PAGE_SIZE, (
            f"Expected > {_TESTNET_PAGE_SIZE} validators on testnet, "
            f"got {len(result.result_data)}"
        )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Transaction query tests — require txn_digests fixture (live PTBs submitted
# once per session; digest1 via GQL, digest2 via gRPC)
# ---------------------------------------------------------------------------


@pytest.mark.order(36)
async def test_get_transaction_gql(txn_digests, gql_session_client: AsyncClientBase) -> None:
    """GetTransaction(digest1) via GQL returns ExecutedTransaction."""
    result = await gql_session_client.execute(
        command=GetTransaction(digest=txn_digests.digest1)
    )
    assert result.is_ok(), f"GetTransaction GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ExecutedTransaction)


@pytest.mark.order(37)
async def test_get_transaction_grpc(txn_digests, grpc_session_client: AsyncClientBase) -> None:
    """GetTransaction(digest1) via gRPC returns ExecutedTransaction."""
    result = await grpc_session_client.execute(
        command=GetTransaction(digest=txn_digests.digest1)
    )
    assert result.is_ok(), f"GetTransaction gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ExecutedTransaction)


@pytest.mark.order(38)
async def test_get_transaction_not_found_gql(gql_session_client: AsyncClientBase) -> None:
    """GetTransaction with non-existent digest via GQL returns is_ok() with None."""
    result = await gql_session_client.execute(
        command=GetTransaction(digest=_NONEXISTENT_DIGEST)
    )
    assert result.is_ok(), f"GetTransaction not-found GQL: {result.result_string}"
    assert result.result_data is None


@pytest.mark.order(39)
async def test_get_transaction_not_found_grpc(grpc_session_client: AsyncClientBase) -> None:
    """GetTransaction with non-existent digest via gRPC returns is_ok() with None."""
    result = await grpc_session_client.execute(
        command=GetTransaction(digest=_NONEXISTENT_DIGEST)
    )
    assert result.is_ok(), f"GetTransaction not-found gRPC: {result.result_string}"
    assert result.result_data is None


@pytest.mark.order(40)
async def test_get_transactions_mixed_gql(
    txn_digests, gql_session_client: AsyncClientBase
) -> None:
    """GetTransactions([digest1, nonexistent, digest2]) via GQL returns list of 3; slot 1 is None."""
    result = await gql_session_client.execute(
        command=GetTransactions(
            digests=[txn_digests.digest1, _NONEXISTENT_DIGEST, txn_digests.digest2]
        )
    )
    assert result.is_ok(), f"GetTransactions mixed GQL: {result.result_string}"
    assert isinstance(result.result_data, list)
    assert len(result.result_data) == 3
    assert result.result_data[1] is None


@pytest.mark.order(41)
async def test_get_transactions_mixed_grpc(
    txn_digests, grpc_session_client: AsyncClientBase
) -> None:
    """GetTransactions([digest1, nonexistent, digest2]) via gRPC returns list of 3; slot 1 is None."""
    result = await grpc_session_client.execute(
        command=GetTransactions(
            digests=[txn_digests.digest1, _NONEXISTENT_DIGEST, txn_digests.digest2]
        )
    )
    assert result.is_ok(), f"GetTransactions mixed gRPC: {result.result_string}"
    assert isinstance(result.result_data, list)
    assert len(result.result_data) == 3
    assert result.result_data[1] is None


@pytest.mark.order(42)
def test_get_transactions_none_slot_gql(txn_digests) -> None:
    """GetTransactions([digest1, None, digest2]) raises ValueError at construction — None is invalid."""
    with pytest.raises(ValueError):
        GetTransactions(digests=[txn_digests.digest1, None, txn_digests.digest2])  # type: ignore[list-item]


@pytest.mark.order(43)
def test_get_transactions_none_slot_grpc(txn_digests) -> None:
    """GetTransactions([digest1, None, digest2]) raises ValueError at construction — None is invalid."""
    with pytest.raises(ValueError):
        GetTransactions(digests=[txn_digests.digest1, None, txn_digests.digest2])  # type: ignore[list-item]


@pytest.mark.order(44)
def test_get_transactions_empty_raises() -> None:
    """GetTransactions([]) raises ValueError at construction."""
    with pytest.raises(ValueError):
        GetTransactions(digests=[])


@pytest.mark.order(45)
async def test_get_transaction_kind_gql(
    txn_digests, gql_session_client: AsyncClientBase
) -> None:
    """GetTransactionKind(digest1) via GQL returns TransactionKind."""
    result = await gql_session_client.execute(
        command=GetTransactionKind(digest=txn_digests.digest1)
    )
    assert result.is_ok(), f"GetTransactionKind GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.TransactionKind)


@pytest.mark.order(46)
async def test_get_transaction_kind_grpc(
    txn_digests, grpc_session_client: AsyncClientBase
) -> None:
    """GetTransactionKind(digest1) via gRPC returns TransactionKind."""
    result = await grpc_session_client.execute(
        command=GetTransactionKind(digest=txn_digests.digest1)
    )
    assert result.is_ok(), f"GetTransactionKind gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.TransactionKind)


# ---------------------------------------------------------------------------
# ExecuteTransaction GQL SC — verify ExecuteTransactionSC encode_fn path
# ---------------------------------------------------------------------------


@pytest.mark.order(47)
async def test_execute_transaction_gql_changed_objects(
    gql_session_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """ExecuteTransaction via GQL returns ExecutedTransaction with changed_objects.

    PTB: split_coin(gas, [1_000]) + transfer_objects([split], active_address).
    The split creates one new coin — verifies DOES_NOT_EXIST input_state mapping in
    ExecuteTransactionSC.encode_fn().
    """
    await asyncio.sleep(SETTLE_SECS)
    await central_bank.withdraw(
        pattern_id="split_gas_1k_transfer_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[],
        sui_draw=0,
    )
    txer = await gql_session_client.transaction()
    split = await txer.split_coin(coin=txer.gas, amounts=[1_000])
    await txer.transfer_objects(
        transfers=[split], recipient=gql_session_client.config.active_address
    )
    result = await gql_session_client.execute(
        command=ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"ExecuteTransaction GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.ExecutedTransaction), (
        f"expected ExecutedTransaction, got {type(result.result_data)}"
    )
    assert result.result_data.digest, "digest is empty"
    assert result.result_data.effects is not None, "effects field is None"
    assert result.result_data.effects.status is not None, "status is None"
    assert result.result_data.effects.status.success, (
        "on-chain execution failed"
    )
    new_objs = [
        co
        for co in result.result_data.effects.changed_objects
        if co.input_state == sui_prot.ChangedObjectInputObjectState.DOES_NOT_EXIST
    ]
    assert new_objs, (
        f"expected >= 1 newly created object (split coin); "
        f"changed_objects={result.result_data.effects.changed_objects}"
    )


# ---------------------------------------------------------------------------
# Signature verification — VerifyTransactionSignature, VerifyPersonalMessageSignature
# ---------------------------------------------------------------------------


@pytest.mark.order(48)
async def test_verify_transaction_signature_gql(
    gql_session_client: AsyncClientBase,
) -> None:
    """VerifyTransactionSignature via GQL returns VerifySignatureResponse with is_valid=True.

    Builds and signs a split-coin PTB without executing it, then verifies the
    transaction signature using the active address as the expected author.
    """
    txer = await gql_session_client.transaction()
    split = await txer.split_coin(coin=txer.gas, amounts=[1_000])
    await txer.transfer_objects(
        transfers=[split], recipient=gql_session_client.config.active_address
    )
    signed = await txer.build_and_sign()
    result = await gql_session_client.execute(
        command=VerifyTransactionSignature(
            message=signed["tx_bytestr"],
            signature=signed["sig_array"][0],
            author=str(gql_session_client.config.active_address),
        )
    )
    assert result.is_ok(), f"VerifyTransactionSignature GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.VerifySignatureResponse)
    assert result.result_data.is_valid is True


@pytest.mark.order(49)
async def test_verify_transaction_signature_grpc(
    grpc_session_client: AsyncClientBase,
) -> None:
    """VerifyTransactionSignature via gRPC returns VerifySignatureResponse with is_valid=True.

    Builds and signs a split-coin PTB without executing it, then verifies the
    transaction signature using the active address as the expected author.
    """
    txer = await grpc_session_client.transaction()
    split = await txer.split_coin(coin=txer.gas, amounts=[1_000])
    await txer.transfer_objects(
        transfers=[split], recipient=grpc_session_client.config.active_address
    )
    signed = await txer.build_and_sign()
    result = await grpc_session_client.execute(
        command=VerifyTransactionSignature(
            message=signed["tx_bytestr"],
            signature=signed["sig_array"][0],
            author=str(grpc_session_client.config.active_address),
        )
    )
    assert result.is_ok(), f"VerifyTransactionSignature gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.VerifySignatureResponse)
    assert result.result_data.is_valid is True


@pytest.mark.order(50)
async def test_verify_personal_message_signature_gql(
    gql_session_client: AsyncClientBase,
) -> None:
    """VerifyPersonalMessageSignature via GQL returns VerifySignatureResponse with is_valid=True."""
    author = str(gql_session_client.config.active_address)
    pm_b64 = base64.b64encode(b"Hello from pysui").decode()
    keypair = gql_session_client.config.keypair_for_address(address=author)
    pm_sig_b64 = keypair.sign_personal_message(pm_b64)
    result = await gql_session_client.execute(
        command=VerifyPersonalMessageSignature(
            message=pm_b64,
            signature=pm_sig_b64,
            author=author,
        )
    )
    assert result.is_ok(), f"VerifyPersonalMessageSignature GQL: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.VerifySignatureResponse)
    assert result.result_data.is_valid is True


@pytest.mark.order(51)
async def test_verify_personal_message_signature_grpc(
    grpc_session_client: AsyncClientBase,
) -> None:
    """VerifyPersonalMessageSignature via gRPC returns VerifySignatureResponse with is_valid=True."""
    author = str(grpc_session_client.config.active_address)
    pm_b64 = base64.b64encode(b"Hello from pysui").decode()
    keypair = grpc_session_client.config.keypair_for_address(address=author)
    pm_sig_b64 = keypair.sign_personal_message(pm_b64)
    result = await grpc_session_client.execute(
        command=VerifyPersonalMessageSignature(
            message=pm_b64,
            signature=pm_sig_b64,
            author=author,
        )
    )
    assert result.is_ok(), f"VerifyPersonalMessageSignature gRPC: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.VerifySignatureResponse)
    assert result.result_data.is_valid is True


@pytest.mark.order(52)
async def test_verify_transaction_signature_invalid_gql(
    gql_session_client: AsyncClientBase,
) -> None:
    """VerifyTransactionSignature GQL with a corrupted signature exercises the capture_errors lift.

    Builds and signs a real PTB, then flips a byte in the signature to produce an
    invalid signature. The GQL server returns a partial-error response; the
    capture_errors path should lift this into SuiRpcResult(ok=True) with is_valid=False
    and a non-None reason string.
    """
    txer = await gql_session_client.transaction()
    split = await txer.split_coin(coin=txer.gas, amounts=[1_000])
    await txer.transfer_objects(
        transfers=[split], recipient=gql_session_client.config.active_address
    )
    signed = await txer.build_and_sign()
    raw = bytearray(base64.b64decode(signed["sig_array"][0]))
    raw[10] ^= 0xFF
    bad_sig = base64.b64encode(bytes(raw)).decode()
    result = await gql_session_client.execute(
        command=VerifyTransactionSignature(
            message=signed["tx_bytestr"],
            signature=bad_sig,
            author=str(gql_session_client.config.active_address),
        )
    )
    assert result.is_ok(), f"capture_errors lift failed: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.VerifySignatureResponse)
    assert result.result_data.is_valid is False
    assert result.result_data.reason is not None


@pytest.mark.order(53)
async def test_verify_transaction_signature_invalid_grpc(
    grpc_session_client: AsyncClientBase,
) -> None:
    """VerifyTransactionSignature gRPC with a corrupted signature returns is_valid=False."""
    txer = await grpc_session_client.transaction()
    split = await txer.split_coin(coin=txer.gas, amounts=[1_000])
    await txer.transfer_objects(
        transfers=[split], recipient=grpc_session_client.config.active_address
    )
    signed = await txer.build_and_sign()
    raw = bytearray(base64.b64decode(signed["sig_array"][0]))
    raw[10] ^= 0xFF
    bad_sig = base64.b64encode(bytes(raw)).decode()
    result = await grpc_session_client.execute(
        command=VerifyTransactionSignature(
            message=signed["tx_bytestr"],
            signature=bad_sig,
            author=str(grpc_session_client.config.active_address),
        )
    )
    assert result.is_ok(), f"VerifyTransactionSignature gRPC invalid: {result.result_string}"
    assert isinstance(result.result_data, sui_prot.VerifySignatureResponse)
    assert result.result_data.is_valid is False
