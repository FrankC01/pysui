#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: gas selection re-architecture (0.99.x).

Verifies the canonical gas use-cases end-to-end against a live devnet/testnet
node.  All tests require a funded address; the faucet test must pass first.
"""

import asyncio

import pytest

from pysui import AsyncClientBase
import pysui.sui.sui_common.sui_commands as cmd

from tests.integration_tests.conftest import SETTLE_SECS, CentralBank, GasBank

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="sui_integration"),
]


# ---------------------------------------------------------------------------
# UC1 — Fully automatic gas selection (no budget, no coins specified)
# ---------------------------------------------------------------------------


@pytest.mark.order(1)
async def test_uc1_gql_auto_gas_transfer_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """UC1 (GQL): transfer_objects with no budget/coins — auto gas selection succeeds."""
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
    # Transfer bank-provided coin to self; gas auto-selected from remaining coins.
    await txer.transfer_objects(
        transfers=[coins[0]],
        recipient=addr,
    )
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC1 GQL transfer failed: {result.result_string}"


@pytest.mark.order(2)
async def test_uc1_grpc_auto_gas_transfer_executes(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """UC1 (gRPC): transfer_objects with no budget/coins — auto gas selection succeeds."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="transfer_coin_to_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    addr = str(grpc_client.config.active_address)

    txer = await grpc_client.transaction()
    await txer.transfer_objects(
        transfers=[coins[0]],
        recipient=addr,
    )
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC1 gRPC transfer failed: {result.result_string}"


# ---------------------------------------------------------------------------
# UC7 — Pure address-balance gas (use_account_for_gas=True, no GasCoin in PTB)
# ---------------------------------------------------------------------------


@pytest.mark.order(3)
async def test_uc7_gql_address_balance_gas_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """UC7 (GQL): use_account_for_gas=True with no GasCoin PTB — empty payment succeeds."""
    await asyncio.sleep(SETTLE_SECS)
    _, coins = await central_bank.withdraw(
        pattern_id="transfer_coin_to_self_accum",
        gas_source=GasBank.ACCOUNT,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=0,
    )
    addr = str(gql_client.config.active_address)

    txer = await gql_client.transaction()
    # Transfer bank-provided coin to self — no txer.gas reference, so UC7 path applies.
    await txer.transfer_objects(
        transfers=[coins[0]],
        recipient=addr,
    )
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(
            **await txer.build_and_sign(use_account_for_gas=True)
        )
    )
    assert result.is_ok(), f"UC7 GQL address-balance gas failed: {result.result_string}"


# ---------------------------------------------------------------------------
# UC12 — PTB draws from gas source (split_coin(coin=txer.gas, amounts=[N]))
# ---------------------------------------------------------------------------


@pytest.mark.order(4)
async def test_uc12_gql_split_gas_coin_executes(
    gql_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """UC12 (GQL): split_coin(txer.gas) — gas_source_draw inflation allows execution."""
    await asyncio.sleep(SETTLE_SECS)
    await central_bank.withdraw(
        pattern_id="split_gas_1m_transfer_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[],
        sui_draw=0,
    )
    addr = str(gql_client.config.active_address)
    txer = await gql_client.transaction()
    # Split 0.001 SUI from gas coin; budget must cover fee + split amount.
    split_res = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
    await txer.transfer_objects(transfers=[split_res], recipient=addr)
    result = await gql_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC12 GQL split-gas failed: {result.result_string}"


@pytest.mark.order(5)
async def test_uc12_grpc_split_gas_coin_executes(
    grpc_client: AsyncClientBase,
    central_bank: CentralBank,
) -> None:
    """UC12 (gRPC): split_coin(txer.gas) — gas_source_draw inflation allows execution."""
    await asyncio.sleep(SETTLE_SECS)
    await central_bank.withdraw(
        pattern_id="split_gas_1m_transfer_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[],
        sui_draw=0,
    )
    addr = str(grpc_client.config.active_address)
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[1_000_000])
    await txer.transfer_objects(transfers=[split_res], recipient=addr)
    result = await grpc_client.execute(
        command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"UC12 gRPC split-gas failed: {result.result_string}"
