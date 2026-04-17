#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pytest fixtures and helpers for pysui integration tests."""

import asyncio

import httpx
import pytest
import pytest_asyncio

from pysui import AsyncGqlClient, PysuiConfiguration, SuiGrpcClient
from pysui.sui.sui_common.config.confgroup import SUI_GQL_RPC_GROUP, SUI_GRPC_GROUP
from pysui.sui.sui_constants import DEVNET_FAUCET_URLV1, TESTNET_FAUCET_URLV1

_FAUCET_BY_PROFILE: dict[str, str] = {
    "devnet": DEVNET_FAUCET_URLV1,
    "testnet": TESTNET_FAUCET_URLV1,
}


def _faucet_url_for(cfg: PysuiConfiguration) -> str | None:
    """Return the faucet URL for the active profile, or None for mainnet/local."""
    return _FAUCET_BY_PROFILE.get(cfg.active_group.active_profile.profile_name)


SETTLE_SECS: float = 2.0


async def json_faucet(faucet_url: str, address: str, settle_secs: float = SETTLE_SECS) -> None:
    """POST to the Sui JSON faucet and wait for gas to land on-chain.

    :raises pytest.skip.Exception: If the faucet rate-limits the request (HTTP 429).
    :raises AssertionError: If the faucet returns an error payload.
    """
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            faucet_url,
            headers={"Content-Type": "application/json"},
            json={"FixedAmountRequest": {"recipient": address}},
        )
    if resp.status_code == 429:
        pytest.skip(f"Faucet rate-limited: {resp.text}")
    data = resp.json()
    # v1 faucet: {"task": "...", "error": null}
    # legacy faucet: {"status": "Success"}
    error = data.get("error") or (
        "status" in data and data["status"] != "Success" and data.get("status")
    )
    assert not error, f"Faucet error: {resp.text}"
    await asyncio.sleep(settle_secs)


async def fund_accumulator_gql(client: AsyncGqlClient, amount: int = 1_000_000) -> None:
    """Deposit `amount` MIST from gas coin into the address accumulator balance (GQL).

    Required before use_account_for_gas=True (UC7): the faucet gives coin objects,
    not accumulator balance; this call runs 0x2::coin::send_funds to fund it.
    """
    import pysui.sui.sui_pgql.pgql_query as qn

    txer = client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[amount])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[scres, client.config.active_address],
    )
    result = await client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"fund_accumulator_gql failed: {result.result_string}"
    await asyncio.sleep(SETTLE_SECS)


@pytest.fixture
def gql_cfg() -> PysuiConfiguration:
    """Load the real GQL group config from ~/.pysui/PysuiConfig.json."""
    cfg = PysuiConfiguration(group_name=SUI_GQL_RPC_GROUP)
    if not _faucet_url_for(cfg):
        pytest.skip("No faucet for active profile — mainnet or local")
    return cfg


@pytest_asyncio.fixture
async def gql_client(gql_cfg: PysuiConfiguration) -> AsyncGqlClient:
    """Async GQL client for the active devnet/testnet profile."""
    client = AsyncGqlClient(pysui_config=gql_cfg)
    yield client
    await client.close()


@pytest.fixture
def grpc_cfg() -> PysuiConfiguration:
    """Load the real gRPC group config from ~/.pysui/PysuiConfig.json."""
    cfg = PysuiConfiguration(group_name=SUI_GRPC_GROUP)
    if not _faucet_url_for(cfg):
        pytest.skip("No faucet for active profile — mainnet or local")
    return cfg


@pytest_asyncio.fixture
async def grpc_client(grpc_cfg: PysuiConfiguration) -> SuiGrpcClient:
    """gRPC client for the active devnet/testnet profile.

    Must be an async fixture so SuiGrpcClient (which captures the event loop
    via grpclib Channel at __init__ time) is created in the test's loop.
    """
    client = SuiGrpcClient(pysui_config=grpc_cfg)
    yield client
    client.close()
