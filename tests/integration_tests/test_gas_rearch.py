#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: gas selection re-architecture (0.99.x).

Verifies the canonical gas use-cases end-to-end against a live devnet/testnet
node.  All tests require a funded address; the faucet test must pass first.
"""

import asyncio

import pytest

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui import AsyncGqlClient, SuiGrpcClient
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_gas_objects as gql_get_coins,
)
from pysui.sui.sui_grpc.pgrpc_utils import (
    async_get_all_owned_gas_objects as grpc_get_coins,
)

from tests.integration_tests.conftest import (
    json_faucet,
    _faucet_url_for,
    fund_accumulator_gql,
    SETTLE_SECS,
)

# ---------------------------------------------------------------------------
# Faucet verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_faucet_increases_coin_count(gql_client: AsyncGqlClient) -> None:
    """_json_faucet adds exactly one new SUI coin object to the active address."""
    addr = str(gql_client.config.active_address)
    before = await gql_get_coins(owner=addr, client=gql_client)

    await json_faucet(_faucet_url_for(gql_client.config), addr)

    after = await gql_get_coins(owner=addr, client=gql_client)
    assert len(after) == len(before) + 1, (
        f"Expected {len(before) + 1} coins after faucet, got {len(after)}"
    )


# ---------------------------------------------------------------------------
# UC1 — Fully automatic gas selection (no budget, no coins specified)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uc1_gql_auto_gas_transfer_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """UC1 (GQL): transfer_objects with no budget/coins — auto gas selection succeeds."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert len(coins) >= 2, "Need at least 2 coins: one to transfer, one for gas"

    txer = gql_client.transaction()
    # Transfer first coin to self; gas auto-selected from remaining coins.
    await txer.transfer_objects(
        transfers=[coins[0].coin_object_id],
        recipient=addr,
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC1 GQL transfer failed: {result.result_string}"


@pytest.mark.asyncio
async def test_uc1_grpc_auto_gas_transfer_executes(
    grpc_client: SuiGrpcClient,
) -> None:
    """UC1 (gRPC): transfer_objects with no budget/coins — auto gas selection succeeds."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 2, "Need at least 2 coins: one to transfer, one for gas"

    txer = await grpc_client.transaction()
    await txer.transfer_objects(
        transfers=[coins[0].object_id],
        recipient=addr,
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC1 gRPC transfer failed: {result.result_string}"


# ---------------------------------------------------------------------------
# UC7 — Pure address-balance gas (use_account_for_gas=True, no GasCoin in PTB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uc7_gql_address_balance_gas_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """UC7 (GQL): use_account_for_gas=True with no GasCoin PTB — empty payment succeeds."""
    await asyncio.sleep(SETTLE_SECS)
    await fund_accumulator_gql(gql_client)
    addr = str(gql_client.config.active_address)
    coins = await gql_get_coins(owner=addr, client=gql_client)
    assert coins, "Need at least 1 coin to transfer"

    txer = gql_client.transaction()
    # Transfer a coin to self — no txer.gas reference, so UC7 path applies.
    await txer.transfer_objects(
        transfers=[coins[0].coin_object_id],
        recipient=addr,
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(
            **await txer.build_and_sign(use_account_for_gas=True)
        )
    )
    assert result.is_ok(), f"UC7 GQL address-balance gas failed: {result.result_string}"


# ---------------------------------------------------------------------------
# UC12 — PTB draws from gas source (split_coin(coin=txer.gas, amounts=[N]))
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uc12_gql_split_gas_coin_executes(
    gql_client: AsyncGqlClient,
) -> None:
    """UC12 (GQL): split_coin(txer.gas) — gas_source_draw inflation allows execution."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(gql_client.config.active_address)
    txer = gql_client.transaction()
    # Split 0.001 SUI from gas coin; budget must cover fee + split amount.
    split_res = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
    await txer.transfer_objects(transfers=split_res, recipient=addr)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC12 GQL split-gas failed: {result.result_string}"


@pytest.mark.asyncio
async def test_uc12_grpc_split_gas_coin_executes(
    grpc_client: SuiGrpcClient,
) -> None:
    """UC12 (gRPC): split_coin(txer.gas) — gas_source_draw inflation allows execution."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
    await txer.transfer_objects(transfers=split_res, recipient=addr)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC12 gRPC split-gas failed: {result.result_string}"
