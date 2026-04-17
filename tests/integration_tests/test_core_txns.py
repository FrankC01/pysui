#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: core transaction commands (7 × GQL + gRPC).

All tests require a funded devnet/testnet address.  publish/publish_upgrade
tests also require the `sui` CLI binary configured in PysuiConfig.json.

Test order:
  move_call, transfer_objects, split_coin, merge_coins — no contract needed
  publish                                               — compiles tests/sui-test/
  make_move_vector                                      — depends on publish fixture
  publish_upgrade                                       — depends on publish fixture
"""

import asyncio
import os

import pytest
import pytest_asyncio

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui import AsyncGqlClient, SuiGrpcClient
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_gas_objects as gql_get_coins,
    async_get_all_owned_objects as gql_get_objects,
)
from pysui.sui.sui_grpc.pgrpc_utils import (
    async_get_all_owned_gas_objects as grpc_get_coins,
)
from pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 import ChangedObjectInputObjectState

from tests.integration_tests.conftest import SETTLE_SECS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SUIPARM_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sui-test"
)


def _sui_binary_available(cfg) -> bool:
    """Return True if sui CLI binary is configured and on disk."""
    binary = getattr(cfg.model, "sui_binary", None)
    return bool(binary and os.path.isfile(binary))


async def _gql_upgrade_cap_from_publish(
    result_data, client: AsyncGqlClient
) -> tuple[str, str]:
    """Return (pkg_address, upgrade_cap_id) from a GQL publish ExecutionResultGQL."""
    tx_result = await client.execute_query_node(
        with_node=qn.GetTx(digest=result_data.digest)
    )
    assert tx_result.is_ok(), f"GetTx failed: {tx_result.result_string}"
    changes = tx_result.result_data.object_changes().nodes
    # Package is in a node with no as_move_content (is_package)
    pkg_addr = next(
        (
            n.address
            for n in changes
            if n.output_state and n.output_state.is_package()
        ),
        None,
    )
    # UpgradeCap is a created object with object_type containing "UpgradeCap"
    cap_id = next(
        (
            n.address
            for n in changes
            if n.created
            and n.output_state
            and n.output_state.is_object()
            and n.output_state.as_move_content
            and "UpgradeCap" in n.output_state.as_move_content.object_type
        ),
        None,
    )
    assert pkg_addr, "Could not find published package address in object changes"
    assert cap_id, "Could not find UpgradeCap in object changes"
    return pkg_addr, cap_id


def _grpc_upgrade_cap_from_publish(result_data) -> tuple[str, str]:
    """Return (pkg_address, upgrade_cap_id) from a gRPC publish ExecuteTransactionResponse."""
    effects = result_data.transaction.effects
    # Package: created, type == None or empty (packages have no object_type in ChangedObject)
    pkg_addr = next(
        (
            co.object_id
            for co in effects.changed_objects
            if co.input_state == ChangedObjectInputObjectState.DOES_NOT_EXIST
            and (not co.object_type)
        ),
        None,
    )
    # UpgradeCap: created object whose type contains "UpgradeCap"
    cap_id = next(
        (
            co.object_id
            for co in effects.changed_objects
            if co.input_state == ChangedObjectInputObjectState.DOES_NOT_EXIST
            and co.object_type
            and "UpgradeCap" in co.object_type
        ),
        None,
    )
    assert pkg_addr, "Could not find published package address in changed_objects"
    assert cap_id, "Could not find UpgradeCap in changed_objects"
    return pkg_addr, cap_id


# ---------------------------------------------------------------------------
# Session fixtures for publish (sui CLI required)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def published_gql(gql_client: AsyncGqlClient, gql_cfg):
    """Publish sui-test contract once per session (GQL). Yields (pkg_addr, cap_id)."""
    if not _sui_binary_available(gql_cfg):
        pytest.skip("sui CLI binary not configured — publish tests skipped")
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    cap_result = await txer.publish(project_path=_SUIPARM_PATH)
    await txer.transfer_objects(
        transfers=[cap_result], recipient=gql_client.config.active_address
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL publish failed: {result.result_string}"
    await asyncio.sleep(SETTLE_SECS)
    yield await _gql_upgrade_cap_from_publish(result.result_data, gql_client)


@pytest_asyncio.fixture(scope="session")
async def published_grpc(grpc_client: SuiGrpcClient, grpc_cfg):
    """Publish sui-test contract once per session (gRPC). Yields (pkg_addr, cap_id)."""
    if not _sui_binary_available(grpc_cfg):
        pytest.skip("sui CLI binary not configured — publish tests skipped")
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    cap_result = await txer.publish(project_path=_SUIPARM_PATH)
    await txer.transfer_objects(
        transfers=[cap_result], recipient=grpc_client.config.active_address
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC publish failed: {result.result_string}"
    await asyncio.sleep(SETTLE_SECS)
    yield _grpc_upgrade_cap_from_publish(result.result_data)


# ---------------------------------------------------------------------------
# 1. move_call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_move_call_gql_send_funds_executes(gql_client: AsyncGqlClient) -> None:
    """move_call (GQL): 0x2::coin::send_funds deposits to address accumulator."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, gql_client.config.active_address],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL move_call failed: {result.result_string}"


@pytest.mark.asyncio
async def test_move_call_grpc_send_funds_executes(grpc_client: SuiGrpcClient) -> None:
    """move_call (gRPC): 0x2::coin::send_funds deposits to address accumulator."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, grpc_client.config.active_address],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC move_call failed: {result.result_string}"


# ---------------------------------------------------------------------------
# 2. transfer_objects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transfer_objects_gql_self_transfer_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """transfer_objects (GQL): transfer a coin object to self."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 2, "Need at least 2 coins"

    txer = gql_client.transaction()
    await txer.transfer_objects(transfers=[coins[0].coin_object_id], recipient=addr)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL transfer_objects failed: {result.result_string}"


@pytest.mark.asyncio
async def test_transfer_objects_grpc_self_transfer_executes(
    grpc_client: SuiGrpcClient,
) -> None:
    """transfer_objects (gRPC): transfer a coin object to self."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 2, "Need at least 2 coins"

    txer = await grpc_client.transaction()
    await txer.transfer_objects(transfers=[coins[0].object_id], recipient=addr)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC transfer_objects failed: {result.result_string}"


# ---------------------------------------------------------------------------
# 3. split_coin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_split_coin_gql_from_non_gas_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """split_coin (GQL): split 1 MIST from a non-gas coin and transfer result to self."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 2, "Need at least 2 coins"

    txer = gql_client.transaction()
    split_res = await txer.split_coin(coin=coins[0].coin_object_id, amounts=[1_000])
    await txer.transfer_objects(transfers=split_res, recipient=addr)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL split_coin failed: {result.result_string}"


@pytest.mark.asyncio
async def test_split_coin_grpc_from_non_gas_executes(
    grpc_client: SuiGrpcClient,
) -> None:
    """split_coin (gRPC): split 1 MIST from a non-gas coin and transfer result to self."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 2, "Need at least 2 coins"

    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=coins[0].object_id, amounts=[1_000])
    await txer.transfer_objects(transfers=split_res, recipient=addr)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC split_coin failed: {result.result_string}"


# ---------------------------------------------------------------------------
# 4. merge_coins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merge_coins_gql_into_gas_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """merge_coins (GQL): merge one faucet coin into txer.gas."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 2, "Need at least 2 coins to merge"

    txer = gql_client.transaction()
    await txer.merge_coins(
        merge_to=txer.gas, merge_from=[coins[0].coin_object_id]
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL merge_coins failed: {result.result_string}"


@pytest.mark.asyncio
async def test_merge_coins_grpc_into_gas_executes(
    grpc_client: SuiGrpcClient,
) -> None:
    """merge_coins (gRPC): merge one faucet coin into txer.gas."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 2, "Need at least 2 coins to merge"

    txer = await grpc_client.transaction()
    await txer.merge_coins(
        merge_to=txer.gas, merge_from=[coins[0].object_id]
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC merge_coins failed: {result.result_string}"


# ---------------------------------------------------------------------------
# 5. publish
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_gql_contract_executes(
    published_gql: tuple[str, str],
) -> None:
    """publish (GQL): sui-test contract published; UpgradeCap present."""
    pkg_addr, cap_id = published_gql
    assert pkg_addr, "No package address returned from publish"
    assert cap_id, "No UpgradeCap returned from publish"


@pytest.mark.asyncio
async def test_publish_grpc_contract_executes(
    published_grpc: tuple[str, str],
) -> None:
    """publish (gRPC): sui-test contract published; UpgradeCap present."""
    pkg_addr, cap_id = published_grpc
    assert pkg_addr, "No package address returned from publish"
    assert cap_id, "No UpgradeCap returned from publish"


# ---------------------------------------------------------------------------
# 6. make_move_vector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_make_move_vector_gql_swap_ab_executes(
    gql_client: AsyncGqlClient,
    published_gql: tuple[str, str],
) -> None:
    """make_move_vector (GQL): build Coin vector, pass to swap_a_b, transfer result."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr, _ = published_gql
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 3, "Need at least 3 coins for make_move_vector test"

    txer = gql_client.transaction()
    vec_arg = await txer.make_move_vector(
        items=[coins[0].coin_object_id, coins[1].coin_object_id],
        item_type="0x2::coin::Coin<0x2::sui::SUI>",
    )
    swap_result = await txer.move_call(
        target=f"{pkg_addr}::parms::swap_a_b",
        type_arguments=["0x2::sui::SUI"],
        arguments=[vec_arg],
    )
    await txer.transfer_objects(transfers=[swap_result], recipient=addr)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL make_move_vector failed: {result.result_string}"


@pytest.mark.asyncio
async def test_make_move_vector_grpc_swap_ab_executes(
    grpc_client: SuiGrpcClient,
    published_grpc: tuple[str, str],
) -> None:
    """make_move_vector (gRPC): build Coin vector, pass to swap_a_b, transfer result."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr, _ = published_grpc
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 3, "Need at least 3 coins for make_move_vector test"

    txer = await grpc_client.transaction()
    vec_arg = await txer.make_move_vector(
        items=[coins[0].object_id, coins[1].object_id],
        item_type="0x2::coin::Coin<0x2::sui::SUI>",
    )
    swap_result = await txer.move_call(
        target=f"{pkg_addr}::parms::swap_a_b",
        type_arguments=["0x2::sui::SUI"],
        arguments=[vec_arg],
    )
    await txer.transfer_objects(transfers=[swap_result], recipient=addr)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC make_move_vector failed: {result.result_string}"


# ---------------------------------------------------------------------------
# 7. publish_upgrade
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_upgrade_gql_version_increments(
    gql_client: AsyncGqlClient,
    published_gql: tuple[str, str],
) -> None:
    """publish_upgrade (GQL): upgrade sui-test; UpgradeCap.version becomes 2."""
    await asyncio.sleep(SETTLE_SECS)
    _, cap_id = published_gql

    txer = gql_client.transaction()
    await txer.publish_upgrade(project_path=_SUIPARM_PATH, upgrade_cap=cap_id)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL publish_upgrade failed: {result.result_string}"
    await asyncio.sleep(SETTLE_SECS)

    # Verify UpgradeCap.version == 2
    cap_result = await gql_client.execute_query_node(
        with_node=qn.GetObject(object_id=cap_id)
    )
    assert cap_result.is_ok(), f"GetObject(UpgradeCap) failed: {cap_result.result_string}"
    version = cap_result.result_data.content.get("version")
    assert version == 2, f"Expected UpgradeCap.version == 2, got {version}"


@pytest.mark.asyncio
async def test_publish_upgrade_grpc_version_increments(
    grpc_client: SuiGrpcClient,
    published_grpc: tuple[str, str],
) -> None:
    """publish_upgrade (gRPC): upgrade sui-test; UpgradeCap.version becomes 2."""
    await asyncio.sleep(SETTLE_SECS)
    _, cap_id = published_grpc

    txer = await grpc_client.transaction()
    await txer.publish_upgrade(project_path=_SUIPARM_PATH, upgrade_cap=cap_id)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"gRPC publish_upgrade failed: {result.result_string}"
    await asyncio.sleep(SETTLE_SECS)

    # Verify UpgradeCap.version == 2
    cap_result = await grpc_client.execute(
        request=rn.GetObject(object_id=cap_id)
    )
    assert cap_result.is_ok(), f"GetObject(UpgradeCap) failed: {cap_result.result_string}"
    jdict = cap_result.result_data.json.to_dict()["structValue"]["fields"]
    version = jdict.get("version", {}).get("numberValue")
    assert version == 2, f"Expected UpgradeCap.version == 2, got {version}"
