#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: core PTB commands (move_call, transfer_objects, split_coin,
merge_coins, make_move_vector, pay_service, get_service × GQL + gRPC).

SERIAL EXECUTION REQUIRED — do not run with -n / --dist flags.
Sui equivocation: parallel txns on the same non-shared object lock those
objects until the next epoch.

Test order (use pytest-order markers for explicit sequencing):
  1-2:   move_call
  3-6:   transfer_objects (self + other address)
  7-8:   split_coin
  9-10:  merge_coins
  17-18: merge_coins negative tests
  19-20: move_call negative tests (insufficient gas)
"""

import asyncio

import pytest
import pytest_asyncio

from pysui import AsyncClientBase
import pysui.sui.sui_common.sui_commands as cmd

from tests.integration_tests.conftest import (
    SETTLE_SECS,
    CentralBank,
    GasBank,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="sui_integration"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_gql_success(result, label: str) -> None:
    """Two-layer assertion: transport OK + on-chain SUCCESS."""
    assert result.is_ok(), f"{label} transport error: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        f"{label} on-chain execution failed"
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
async def test_move_call_gql_send_funds_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """move_call (GQL): 0x2::coin::send_funds deposits to address accumulator."""
    await asyncio.sleep(SETTLE_SECS)
    await central_bank.withdraw(
        pattern_id="split_gas_500k_send_funds",
        gas_source=GasBank.COIN,
        gas_fee=1_000_000,
        sui_coins=[],
        sui_draw=500_000,
    )
    txer = await gql_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, gql_client.config.active_address],
    )
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL move_call send_funds")


@pytest.mark.order(2)
async def test_move_call_grpc_send_funds_executes(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """move_call (gRPC): 0x2::coin::send_funds deposits to address accumulator."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="split_nongascoin_500k_send_funds_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[500_000],
        sui_draw=0,
    )
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=coins[0], amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, grpc_client.config.active_address],
    )
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC move_call send_funds")


# ---------------------------------------------------------------------------
# 2. transfer_objects
# ---------------------------------------------------------------------------


@pytest.mark.order(3)
async def test_transfer_objects_gql_self_transfer_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """transfer_objects (GQL): transfer a coin object to self."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="transfer_coin_to_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    addr = str(gql_client.config.active_address)

    txer = await gql_client.transaction()
    await txer.transfer_objects(transfers=[coins[0]], recipient=addr)
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL transfer_objects self")


@pytest.mark.order(4)
async def test_transfer_objects_grpc_self_transfer_executes(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """transfer_objects (gRPC): transfer a coin object to self."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="transfer_coin_to_self_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    addr = str(grpc_client.config.active_address)

    txer = await grpc_client.transaction()
    await txer.transfer_objects(transfers=[coins[0]], recipient=addr)
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC transfer_objects self")


@pytest.mark.order(5)
async def test_transfer_objects_gql_to_other_address_executes(
    gql_client: AsyncClientBase,
    recipient_address: str,
    central_bank: CentralBank,
) -> None:
    """transfer_objects (GQL): transfer a coin to a different address."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="transfer_coin_to_other",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    txer = await gql_client.transaction()
    await txer.transfer_objects(
        transfers=[coins[0]], recipient=recipient_address
    )
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL transfer_objects to other")


@pytest.mark.order(6)
async def test_transfer_objects_grpc_to_other_address_executes(
    grpc_client: AsyncClientBase,
    recipient_address: str,
    central_bank: CentralBank,
) -> None:
    """transfer_objects (gRPC): transfer a coin to a different address."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="transfer_coin_to_other_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    txer = await grpc_client.transaction()
    await txer.transfer_objects(
        transfers=[coins[0]], recipient=recipient_address
    )
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC transfer_objects to other")


# ---------------------------------------------------------------------------
# 3. split_coin
# ---------------------------------------------------------------------------


@pytest.mark.order(7)
async def test_split_coin_gql_from_non_gas_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """split_coin (GQL): split 1 MIST from a non-gas coin and transfer result to self."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="split_nongascoin_1k_transfer_self",
        gas_source=GasBank.COIN,
        gas_fee=2_976_000,
        sui_coins=[1_000],
        sui_draw=0,
    )
    addr = str(gql_client.config.active_address)

    txer = await gql_client.transaction()
    split_res = await txer.split_coin(coin=coins[0], amounts=[1_000])
    await txer.transfer_objects(transfers=[split_res], recipient=addr)
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL split_coin")


@pytest.mark.order(8)
async def test_split_coin_grpc_from_non_gas_executes(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """split_coin (gRPC): split 1 MIST from a non-gas coin and transfer result to self."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="split_nongascoin_1k_transfer_self_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=2_976_000,
        sui_coins=[1_000],
        sui_draw=0,
    )
    addr = str(grpc_client.config.active_address)

    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=coins[0], amounts=[1_000])
    await txer.transfer_objects(transfers=[split_res], recipient=addr)
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC split_coin")


# ---------------------------------------------------------------------------
# 4. merge_coins
# ---------------------------------------------------------------------------


@pytest.mark.order(9)
async def test_merge_coins_gql_into_gas_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """merge_coins (GQL): merge one faucet coin into txer.gas."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="merge_coin_into_gas",
        gas_source=GasBank.COIN,
        gas_fee=1_000_000,
        sui_coins=[None],
        sui_draw=0,
    )
    txer = await gql_client.transaction()
    await txer.merge_coins(merge_to=txer.gas, merge_from=[coins[0]])
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL merge_coins")


@pytest.mark.order(10)
async def test_merge_coins_grpc_into_gas_executes(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """merge_coins (gRPC): merge coins[0] into coins[1] (txer.gas incompatible with use_account_for_gas)."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="merge_coin_to_coin_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[None, None],
        sui_draw=0,
    )
    txer = await grpc_client.transaction()
    await txer.merge_coins(merge_to=coins[1], merge_from=[coins[0]])
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC merge_coins")


# ---------------------------------------------------------------------------
# Negative tests — transport-rejection layer (node rejects before execution)
# ---------------------------------------------------------------------------


@pytest.mark.order(17)
async def test_merge_coins_gql_same_object_rejected(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """merge_coins (GQL): merging a coin into itself fails on-chain."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="merge_same_object_negative",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    coin_id = coins[0]
    txer = await gql_client.transaction()
    await txer.merge_coins(merge_to=coin_id, merge_from=[coin_id])
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"Unexpected transport error: {result.result_string}"
    assert not result.result_data.transaction.effects.status.success, (
        "Expected on-chain failure for same-object merge"
    )


@pytest.mark.order(18)
async def test_merge_coins_grpc_same_object_rejected(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """merge_coins (gRPC): merging a coin into itself fails on-chain."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="merge_same_object_negative_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    coin_id = coins[0]
    txer = await grpc_client.transaction()
    await txer.merge_coins(merge_to=coin_id, merge_from=[coin_id])
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    assert result.is_ok(), f"Unexpected transport error: {result.result_string}"
    assert not result.result_data.transaction.effects.status.success, (
        "Expected on-chain failure for same-object merge"
    )


# ---------------------------------------------------------------------------
# Negative tests — execution-failure layer (node accepts, on-chain fails)
# ---------------------------------------------------------------------------


@pytest.mark.order(19)
async def test_move_call_gql_insufficient_gas_fails(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """move_call (GQL): gas_budget=1 causes on-chain InsufficientGas execution failure."""
    await asyncio.sleep(SETTLE_SECS)
    await central_bank.withdraw(
        pattern_id="split_gas_500k_send_funds_budget1_fail",
        gas_source=GasBank.COIN,
        gas_fee=1_000_000,
        sui_coins=[],
        sui_draw=0,
    )
    txer = await gql_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, gql_client.config.active_address],
    )
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(
            **await txer.build_and_sign(gas_budget="1")
        )
    )
    if result.is_ok():
        assert not result.result_data.transaction.effects.status.success, (
            "Expected on-chain failure with gas_budget=1, got SUCCESS"
        )


@pytest.mark.order(20)
async def test_move_call_grpc_insufficient_gas_fails(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """move_call (gRPC): gas_budget=1 causes on-chain InsufficientGas execution failure."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="split_nongascoin_500k_send_funds_budget1_fail_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[500_000],
        sui_draw=0,
    )
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=coins[0], amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[split_res, grpc_client.config.active_address],
    )
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(
            **await txer.build_and_sign(gas_budget="1", use_account_for_gas=True)
        )
    )
    if result.is_ok():
        assert not result.result_data.transaction.effects.status.success, (
            "Expected on-chain failure with gas_budget=1, got success"
        )
