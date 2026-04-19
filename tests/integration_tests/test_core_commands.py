#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: core PTB commands (7 commands × GQL + gRPC).

SERIAL EXECUTION REQUIRED — do not run with -n / --dist flags.
Sui equivocation: parallel txns on the same non-shared object lock those
objects until the next epoch.

Test order (use pytest-order markers for explicit sequencing):
  1-4:  non-publish commands (move_call, transfer_objects, split_coin, merge_coins)
  5-6:  publish verification tests (depend on published_gql / published_grpc fixtures)
  7-8:  make_move_vector (depends on publish)
  9-10: publish_upgrade (depends on publish)
  11-12: transfer to other address (depends on second address in keystore)
  13-20: negative tests (transport-rejection and execution-failure cases)
  21-22: pay_service → get_service lifecycle (depends on ParmObject from publish)
"""

import asyncio

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

from tests.integration_tests.conftest import (
    SETTLE_SECS,
    PublishedPackage,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="sui_integration"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_gql_success(result, label: str) -> None:
    """Two-layer GQL assertion: transport OK + on-chain SUCCESS."""
    assert result.is_ok(), f"{label} transport error: {result.result_string}"
    assert result.result_data.status == "SUCCESS", (
        f"{label} on-chain failure: status={result.result_data.status} "
        f"error={result.result_data.execution_error}"
    )


def _assert_grpc_success(result, label: str) -> None:
    """Two-layer gRPC assertion: transport OK + on-chain success."""
    assert result.is_ok(), f"{label} transport error: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        f"{label} on-chain execution failed"
    )


# ---------------------------------------------------------------------------
# 1. move_call
# ---------------------------------------------------------------------------


@pytest.mark.order(1)
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
    _assert_gql_success(result, "GQL move_call send_funds")


@pytest.mark.order(2)
async def test_move_call_grpc_send_funds_executes(grpc_client: SuiGrpcClient) -> None:
    """move_call (gRPC): 0x2::coin::send_funds deposits to address accumulator."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 1, "Need at least 1 coin for send_funds split"
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=coins[0].object_id, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, grpc_client.config.active_address],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC move_call send_funds")


# ---------------------------------------------------------------------------
# 2. transfer_objects
# ---------------------------------------------------------------------------


@pytest.mark.order(3)
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
    _assert_gql_success(result, "GQL transfer_objects self")


@pytest.mark.order(4)
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
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC transfer_objects self")


@pytest.mark.order(5)
async def test_transfer_objects_gql_to_other_address_executes(
    gql_client: AsyncGqlClient,
    recipient_address: str,
) -> None:
    """transfer_objects (GQL): transfer a coin to a different address."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 2, "Need at least 2 coins"

    txer = gql_client.transaction()
    await txer.transfer_objects(
        transfers=[coins[0].coin_object_id], recipient=recipient_address
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL transfer_objects to other")


@pytest.mark.order(6)
async def test_transfer_objects_grpc_to_other_address_executes(
    grpc_client: SuiGrpcClient,
    recipient_address: str,
) -> None:
    """transfer_objects (gRPC): transfer a coin to a different address."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 2, "Need at least 2 coins"

    txer = await grpc_client.transaction()
    await txer.transfer_objects(
        transfers=[coins[0].object_id], recipient=recipient_address
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC transfer_objects to other")


# ---------------------------------------------------------------------------
# 3. split_coin
# ---------------------------------------------------------------------------


@pytest.mark.order(7)
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
    _assert_gql_success(result, "GQL split_coin")


@pytest.mark.order(8)
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
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC split_coin")


# ---------------------------------------------------------------------------
# 4. merge_coins
# ---------------------------------------------------------------------------


@pytest.mark.order(9)
async def test_merge_coins_gql_into_gas_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """merge_coins (GQL): merge one faucet coin into txer.gas."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 2, "Need at least 2 coins to merge"

    txer = gql_client.transaction()
    await txer.merge_coins(merge_to=txer.gas, merge_from=[coins[0].coin_object_id])
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL merge_coins")


@pytest.mark.order(10)
async def test_merge_coins_grpc_into_gas_executes(
    grpc_client: SuiGrpcClient,
) -> None:
    """merge_coins (gRPC): merge one faucet coin into txer.gas."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 2, "Need at least 2 coins to merge"

    txer = await grpc_client.transaction()
    await txer.merge_coins(merge_to=txer.gas, merge_from=[coins[0].object_id])
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC merge_coins")


# ---------------------------------------------------------------------------
# 5. publish
# ---------------------------------------------------------------------------


@pytest.mark.order(11)
async def test_publish_gql_contract_executes(
    published_gql: PublishedPackage,
) -> None:
    """publish (GQL): sui-test contract published; package, UpgradeCap, ParmObject present."""
    assert published_gql.pkg_addr, "No package address"
    assert published_gql.cap_id, "No UpgradeCap"
    assert published_gql.parm_obj_id, "No ParmObject"


@pytest.mark.order(12)
async def test_publish_grpc_contract_executes(
    published_grpc: PublishedPackage,
) -> None:
    """publish (gRPC): sui-test contract published; package, UpgradeCap, ParmObject present."""
    assert published_grpc.pkg_addr, "No package address"
    assert published_grpc.cap_id, "No UpgradeCap"
    assert published_grpc.parm_obj_id, "No ParmObject"


# ---------------------------------------------------------------------------
# 6. make_move_vector
# ---------------------------------------------------------------------------


@pytest.mark.order(13)
async def test_make_move_vector_gql_swap_ab_executes(
    gql_client: AsyncGqlClient,
    published_gql: PublishedPackage,
) -> None:
    """make_move_vector (GQL): negative test — swap_a_b returns vector<Coin<T>> which
    lacks `store`, so transfer_objects on it must fail on-chain."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr
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
    assert result.is_ok(), f"GQL make_move_vector transport error: {result.result_string}"
    assert result.result_data.status == "FAILURE", (
        f"Expected on-chain FAILURE (vector lacks store), got {result.result_data.status}"
    )


@pytest.mark.order(14)
async def test_make_move_vector_grpc_swap_ab_executes(
    grpc_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
) -> None:
    """make_move_vector (gRPC): negative test — swap_a_b returns vector<Coin<T>> which
    lacks `store`, so transfer_objects on it must fail on-chain."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr
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
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    assert result.is_ok(), f"gRPC make_move_vector transport error: {result.result_string}"
    assert not result.result_data.transaction.effects.status.success, (
        "Expected on-chain failure (vector lacks store), but transaction succeeded"
    )


# ---------------------------------------------------------------------------
# 7. publish_upgrade
# ---------------------------------------------------------------------------


@pytest.mark.order(15)
async def test_publish_upgrade_gql_version_increments(
    gql_client: AsyncGqlClient,
    published_gql: PublishedPackage,
    sui_test_project_path: str,
) -> None:
    """publish_upgrade (GQL): upgrade sui-test; UpgradeCap.version becomes 2."""
    await asyncio.sleep(SETTLE_SECS)
    cap_id = published_gql.cap_id

    txer = gql_client.transaction()
    await txer.publish_upgrade(
        project_path=sui_test_project_path, upgrade_cap=cap_id
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL publish_upgrade")
    await asyncio.sleep(SETTLE_SECS)

    cap_result = await gql_client.execute_query_node(
        with_node=qn.GetObject(object_id=cap_id)
    )
    assert cap_result.is_ok(), f"GetObject(UpgradeCap) failed: {cap_result.result_string}"
    # content dict contains Move-level UpgradeCap fields; "version" starts at 1 and
    # increments on each upgrade. Accessor may return int or nested dict depending
    # on GQL response shape — TODO: stabilize this accessor.
    version = cap_result.result_data.content.get("version")
    assert int(version) == 2, f"Expected UpgradeCap.version == 2, got {version}"


@pytest.mark.order(16)
async def test_publish_upgrade_grpc_version_increments(
    grpc_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
    sui_test_project_path: str,
) -> None:
    """publish_upgrade (gRPC): upgrade sui-test; UpgradeCap.version becomes 2."""
    await asyncio.sleep(SETTLE_SECS)
    cap_id = published_grpc.cap_id

    txer = await grpc_client.transaction()
    await txer.publish_upgrade(
        project_path=sui_test_project_path, upgrade_cap=cap_id
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC publish_upgrade")
    await asyncio.sleep(SETTLE_SECS)

    cap_result = await grpc_client.execute(
        request=rn.GetObject(object_id=cap_id)
    )
    assert cap_result.is_ok(), f"GetObject(UpgradeCap) failed: {cap_result.result_string}"
    # Object.json is a google.protobuf.Value; UpgradeCap.version is a string_value in betterproto2.
    version_val = cap_result.result_data.object.json.struct_value.fields["version"]
    version = version_val.string_value or version_val.number_value
    assert int(version) == 2, f"Expected UpgradeCap.version == 2, got {version!r}"


# ---------------------------------------------------------------------------
# 8. pay_service → get_service lifecycle (ordered: pay must run before get)
# ---------------------------------------------------------------------------


@pytest.mark.order(17)
async def test_pay_service_gql_executes(
    gql_session_client: AsyncGqlClient,
    published_gql: PublishedPackage,
) -> None:
    """pay_service (GQL): deposit EServiceFee MIST into ParmObject.service balance."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr
    parm_obj_id = published_gql.parm_obj_id
    addr = str(gql_session_client.config.active_address)
    txer = gql_session_client.transaction()
    pay_coin = await txer.split_coin(coin=txer.gas, amounts=[1_000_100])
    await txer.move_call(
        target=f"{pkg_addr}::parms::pay_service",
        arguments=[parm_obj_id, pay_coin],
    )
    await txer.merge_coins(merge_to=txer.gas, merge_from=[pay_coin])
    result = await gql_session_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL pay_service")


@pytest.mark.order(18)
async def test_get_service_gql_executes(
    gql_session_client: AsyncGqlClient,
    published_gql: PublishedPackage,
) -> None:
    """get_service (GQL): withdraw all from service balance and transfer result coin."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr
    parm_obj_id = published_gql.parm_obj_id
    addr = str(gql_session_client.config.active_address)

    txer = gql_session_client.transaction()
    coin_result = await txer.move_call(
        target=f"{pkg_addr}::parms::get_service",
        arguments=[parm_obj_id, None],
    )
    await txer.transfer_objects(transfers=[coin_result], recipient=addr)
    result = await gql_session_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL get_service")


@pytest.mark.order(19)
async def test_pay_service_grpc_executes(
    grpc_session_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
) -> None:
    """pay_service (gRPC): deposit EServiceFee MIST into ParmObject.service balance."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr
    parm_obj_id = published_grpc.parm_obj_id
    addr = str(grpc_session_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_session_client)
    assert len(coins) >= 1, "Need at least 1 coin for pay_service split"
    source_coin = coins[0].object_id
    txer = await grpc_session_client.transaction()
    pay_coin = await txer.split_coin(coin=source_coin, amounts=[1_000_100])
    await txer.move_call(
        target=f"{pkg_addr}::parms::pay_service",
        arguments=[parm_obj_id, pay_coin],
    )
    await txer.merge_coins(merge_to=source_coin, merge_from=[pay_coin])
    result = await grpc_session_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC pay_service")


@pytest.mark.order(20)
async def test_get_service_grpc_executes(
    grpc_session_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
) -> None:
    """get_service (gRPC): withdraw all from service balance and transfer result coin."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr
    parm_obj_id = published_grpc.parm_obj_id
    addr = str(grpc_session_client.config.active_address)

    txer = await grpc_session_client.transaction()
    coin_result = await txer.move_call(
        target=f"{pkg_addr}::parms::get_service",
        arguments=[parm_obj_id, None],
    )
    await txer.transfer_objects(transfers=[coin_result], recipient=addr)
    result = await grpc_session_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC get_service")


# ---------------------------------------------------------------------------
# Negative tests — transport-rejection layer (node rejects before execution)
# ---------------------------------------------------------------------------


@pytest.mark.order(21)
async def test_merge_coins_gql_same_object_rejected(
    gql_client: AsyncGqlClient,
) -> None:
    """merge_coins (GQL): merging a coin into itself fails on-chain."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 1, "Need at least 1 coin"

    coin_id = coins[0].coin_object_id
    txer = gql_client.transaction()
    await txer.merge_coins(merge_to=coin_id, merge_from=[coin_id])
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    # Chain accepts the tx at transport but rejects on-chain
    assert result.is_ok(), f"Unexpected transport error: {result.result_string}"
    assert result.result_data.status != "SUCCESS", (
        "Expected on-chain failure for same-object merge"
    )


@pytest.mark.order(22)
async def test_merge_coins_grpc_same_object_rejected(
    grpc_client: SuiGrpcClient,
) -> None:
    """merge_coins (gRPC): merging a coin into itself fails on-chain."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 1, "Need at least 1 coin"

    coin_id = coins[0].object_id
    txer = await grpc_client.transaction()
    await txer.merge_coins(merge_to=coin_id, merge_from=[coin_id])
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    # Chain accepts the tx at transport but rejects on-chain
    assert result.is_ok(), f"Unexpected transport error: {result.result_string}"
    assert not result.result_data.transaction.effects.status.success, (
        "Expected on-chain failure for same-object merge"
    )


# ---------------------------------------------------------------------------
# Negative tests — execution-failure layer (node accepts, on-chain fails)
# ---------------------------------------------------------------------------


@pytest.mark.order(23)
async def test_move_call_gql_insufficient_gas_fails(
    gql_client: AsyncGqlClient,
) -> None:
    """move_call (GQL): gas_budget=1 causes on-chain InsufficientGas execution failure."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, gql_client.config.active_address],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(
            **await txer.build_and_sign(gas_budget="1")
        )
    )
    # May be transport-rejected (budget too low) or execution-failed
    if result.is_ok():
        assert result.result_data.status != "SUCCESS", (
            "Expected on-chain failure with gas_budget=1, got SUCCESS"
        )


@pytest.mark.order(24)
async def test_move_call_grpc_insufficient_gas_fails(
    grpc_client: SuiGrpcClient,
) -> None:
    """move_call (gRPC): gas_budget=1 causes on-chain InsufficientGas execution failure."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, grpc_client.config.active_address],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(
            **await txer.build_and_sign(gas_budget="1", use_account_for_gas=True)
        )
    )
    if result.is_ok():
        assert not result.result_data.transaction.effects.status.success, (
            "Expected on-chain failure with gas_budget=1, got success"
        )
