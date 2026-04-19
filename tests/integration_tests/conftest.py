#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pytest fixtures and helpers for pysui integration tests.

IMPORTANT: All integration tests must run serially.
Sui equivocation: parallel txns on the same non-shared object lock those objects
until the next epoch. Do NOT run with -n / --dist flags.

RECOMMENDED TEST ENVIRONMENT: devnet
  - Faucet dispenses 10 SUI per request (vs 1 SUI on testnet).
  - Faucet responds faster and tolerates back-to-back requests without rate-limiting.
  - Testnet faucet rate-limits aggressively; consecutive requests will fail with HTTP 429,
    leaving the session under-funded mid-run and causing non-deterministic test failures.
  - To run against testnet, pre-fund your testnet wallet to at least 5 SUI before starting
    the suite (do not rely on the faucet during the run).
  - Mainnet and local node profiles are skipped automatically (no faucet configured).
"""

import asyncio
import math
import os
import re
import shutil
from pathlib import Path
from typing import NamedTuple, Optional

import httpx
import pytest
import pytest_asyncio

from pysui import AsyncGqlClient, PysuiConfiguration, SuiGrpcClient
from pysui.sui.sui_common.config.confgroup import SUI_GQL_RPC_GROUP, SUI_GRPC_GROUP
from pysui.sui.sui_constants import DEVNET_FAUCET_URLV1, TESTNET_FAUCET_URLV1
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 import ChangedObjectInputObjectState


_FAUCET_BY_PROFILE: dict[str, str] = {
    "devnet": DEVNET_FAUCET_URLV1,
    "testnet": TESTNET_FAUCET_URLV1,
}

SETTLE_SECS: float = 2.0

# Gas preflight thresholds — minimum balances required before any test runs
_TARGET_COIN_MIST: int = 10_000_000_000   # 10 SUI in coin objects per sender address
_TARGET_ACCUM_MIST: int = 10_000_000_000  # 10 SUI in address accumulator per sender address
_FAUCET_PER_CALL_MIST: int = 10_000_000_000  # devnet: 10 SUI delivered per faucet call

_SUI_TEST_SRC: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sui-test"
)


def _faucet_url_for(cfg: PysuiConfiguration) -> str | None:
    """Return faucet URL for the active profile, or None for mainnet/local."""
    return _FAUCET_BY_PROFILE.get(cfg.active_group.active_profile.profile_name)


def _sui_binary_available(cfg: PysuiConfiguration) -> bool:
    """Return True if the sui CLI binary is configured and present on disk."""
    binary = getattr(cfg.model, "sui_binary", None)
    return bool(binary and os.path.isfile(binary))


# Guard: refuse to start if xdist parallelism is accidentally enabled.
def pytest_collection_modifyitems(config, items):
    if not config.pluginmanager.hasplugin("xdist"):
        return
    try:
        n = config.getoption("numprocesses")
        if n and str(n) not in ("0", "no"):
            pytest.exit(
                "Integration tests must run serially — remove -n / --numprocesses flags",
                returncode=1,
            )
    except (ValueError, AttributeError):
        pass


# ---------------------------------------------------------------------------
# Faucet / funding helpers
# ---------------------------------------------------------------------------


async def json_faucet(
    faucet_url: str, address: str, settle_secs: float = SETTLE_SECS
) -> None:
    """POST to the Sui JSON faucet and wait for gas to land on-chain.

    :raises pytest.skip.Exception: If faucet rate-limits (HTTP 429).
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
    error = data.get("error") or (
        "status" in data and data["status"] != "Success" and data.get("status")
    )
    assert not error, f"Faucet error: {resp.text}"
    await asyncio.sleep(settle_secs)


async def fund_accumulator_gql(
    client: AsyncGqlClient,
    amount: int = 1_000_000,
    recipient: Optional[str] = None,
) -> None:
    """Deposit `amount` MIST into an address accumulator balance via GQL client.

    Uses 0x2::coin::send_funds.  recipient defaults to client's own active address.
    The client's coin objects pay for the transaction gas AND supply the deposited amount.
    """
    target = recipient or client.config.active_address
    txer = client.transaction(merge_gas_budget=True)
    scres = await txer.split_coin(coin=txer.gas, amounts=[amount])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[scres, target],
    )
    result = await client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"fund_accumulator_gql failed: {result.result_string}"
    await asyncio.sleep(SETTLE_SECS)


# ---------------------------------------------------------------------------
# Move.toml chain ID helper (pure — testable offline)
# ---------------------------------------------------------------------------


def update_move_toml_chain_id(toml_path: Path, chain_id: str) -> None:
    """Replace the devnet chain ID in Move.toml with `chain_id` in place."""
    content = toml_path.read_text()
    content = re.sub(
        r'(devnet\s*=\s*")[^"]*(")', f'\\g<1>{chain_id}\\g<2>', content
    )
    toml_path.write_text(content)


# ---------------------------------------------------------------------------
# PublishedPackage result type
# ---------------------------------------------------------------------------


class PublishedPackage(NamedTuple):
    """Addresses returned from a publish session fixture."""

    pkg_addr: str
    cap_id: str
    parm_obj_id: str


# ---------------------------------------------------------------------------
# Publish result extraction helpers
# ---------------------------------------------------------------------------


async def _gql_extract_publish_result(
    result_data, client: AsyncGqlClient
) -> PublishedPackage:
    """Return PublishedPackage from a GQL ExecutionResultGQL via wait_for_transaction."""
    tx_result = await client.wait_for_transaction(
        digest=result_data.digest, poll_interval=1
    )
    assert tx_result.is_ok(), f"wait_for_transaction failed: {tx_result.result_string}"
    changes = tx_result.result_data.object_changes().nodes

    pkg_addr = next(
        (n.address for n in changes if n.output_state and n.output_state.is_package()),
        None,
    )
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
    # ParmObject is created by init() and transferred to sender at publish time.
    # init() in parms.move MUST remain intact for this fixture to work.
    parm_obj_id = next(
        (
            n.address
            for n in changes
            if n.created
            and n.output_state
            and n.output_state.is_object()
            and n.output_state.as_move_content
            and "ParmObject" in n.output_state.as_move_content.object_type
        ),
        None,
    )
    assert pkg_addr, "Could not find published package address in object changes"
    assert cap_id, "Could not find UpgradeCap in object changes"
    assert parm_obj_id, (
        "Could not find ParmObject in object changes — "
        "parms::init() must transfer ParmObject to sender"
    )
    return PublishedPackage(pkg_addr=pkg_addr, cap_id=cap_id, parm_obj_id=parm_obj_id)


def _grpc_extract_publish_result(result_data) -> PublishedPackage:
    """Return PublishedPackage from a gRPC ExecuteTransactionResponse."""
    effects = result_data.transaction.effects

    pkg_addr = next(
        (
            co.object_id
            for co in effects.changed_objects
            if co.input_state == ChangedObjectInputObjectState.DOES_NOT_EXIST
            and co.object_type == "package"
        ),
        None,
    )
    cap_id = next(
        (
            co.object_id
            for co in effects.changed_objects
            if co.input_state == ChangedObjectInputObjectState.DOES_NOT_EXIST
            and co.object_type
            and co.object_type.endswith("UpgradeCap")
        ),
        None,
    )
    # ParmObject is created by init() and transferred to sender at publish time.
    # init() in parms.move MUST remain intact for this fixture to work.
    parm_obj_id = next(
        (
            co.object_id
            for co in effects.changed_objects
            if co.input_state == ChangedObjectInputObjectState.DOES_NOT_EXIST
            and co.object_type
            and co.object_type.endswith("ParmObject")
        ),
        None,
    )
    assert pkg_addr, "Could not find published package address in changed_objects"
    assert cap_id, "Could not find UpgradeCap in changed_objects"
    assert parm_obj_id, (
        "Could not find ParmObject in changed_objects — "
        "parms::init() must transfer ParmObject to sender"
    )
    return PublishedPackage(pkg_addr=pkg_addr, cap_id=cap_id, parm_obj_id=parm_obj_id)


# ---------------------------------------------------------------------------
# Config fixtures (session-scoped — safe to share; must not mutate active_address)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def gql_cfg() -> PysuiConfiguration:
    """GQL group config for the active devnet/testnet profile."""
    cfg = PysuiConfiguration(group_name=SUI_GQL_RPC_GROUP)
    if not _faucet_url_for(cfg):
        pytest.skip("No faucet for active profile — mainnet or local")
    return cfg


@pytest.fixture(scope="session")
def grpc_cfg() -> PysuiConfiguration:
    """gRPC group config for the active devnet/testnet profile."""
    cfg = PysuiConfiguration(group_name=SUI_GRPC_GROUP)
    if not _faucet_url_for(cfg):
        pytest.skip("No faucet for active profile — mainnet or local")
    return cfg


# ---------------------------------------------------------------------------
# Session-scoped clients — for fixtures that must survive across many tests
# (publish, upgrade, pay_service/get_service, etc.)
# WARNING: Do not mutate cfg.active_group.using_address on these clients.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def gql_session_client(gql_cfg: PysuiConfiguration) -> AsyncGqlClient:
    """Long-lived GQL client shared across the session."""
    client = AsyncGqlClient(pysui_config=gql_cfg)
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def grpc_session_client(grpc_cfg: PysuiConfiguration) -> SuiGrpcClient:
    """Long-lived gRPC client shared across the session."""
    client = SuiGrpcClient(pysui_config=grpc_cfg)
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Session gas preflight — runs once, ensures wallet is funded before any test
# ---------------------------------------------------------------------------


async def _faucet_to_target(faucet_url: str, address: str, current_mist: int) -> None:
    """Call faucet enough times to bring `address` coin balance up to _TARGET_COIN_MIST.

    Rate-limit (429) responses stop further attempts — tests run with whatever was funded.
    """
    shortfall = _TARGET_COIN_MIST - current_mist
    if shortfall <= 0:
        return
    calls = math.ceil(shortfall / _FAUCET_PER_CALL_MIST)
    for _ in range(calls):
        try:
            await json_faucet(faucet_url, address)
        except pytest.skip.Exception:
            break


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def ensure_session_gas(
    gql_session_client: AsyncGqlClient,
    grpc_session_client: SuiGrpcClient,
    gql_cfg: PysuiConfiguration,
) -> None:
    """Preflight: ensure each sender address has >= 10 SUI in coins and >= 10 SUI in accumulator.

    Uses gRPC for balance queries (faster). GQL client funds all accumulators via send_funds.
    Deduplicates addresses — if both clients share an active address, it is funded once.
    Two passes: coins first (so GQL wallet has funds), then accumulators.
    """
    faucet_url = _faucet_url_for(gql_cfg)
    gql_address = gql_session_client.config.active_address
    grpc_address = grpc_session_client.config.active_address
    # Preserve order; deduplicate so a shared address is funded once.
    addresses = list(dict.fromkeys([gql_address, grpc_address]))

    # Pass 1 — top up coin objects for all sender addresses via faucet.
    for address in addresses:
        result = await grpc_session_client.execute(
            request=rn.GetAddressCoinBalance(owner=address, coin_type="0x2::sui::SUI")
        )
        assert result.is_ok(), f"GetAddressCoinBalance failed for {address}: {result.result_string}"
        await _faucet_to_target(faucet_url, address, result.result_data.balance.coin_balance)

    # Pass 2 — top up address accumulator for all sender addresses.
    #           GQL client's coin objects pay for each send_funds transaction.
    for address in addresses:
        result = await grpc_session_client.execute(
            request=rn.GetAddressCoinBalance(owner=address, coin_type="0x2::sui::SUI")
        )
        assert result.is_ok(), f"GetAddressCoinBalance failed for {address}: {result.result_string}"
        shortfall = _TARGET_ACCUM_MIST - result.result_data.balance.address_balance
        if shortfall > 0:
            await fund_accumulator_gql(gql_session_client, amount=shortfall, recipient=address)


# ---------------------------------------------------------------------------
# Function-scoped clients — for simple per-test isolation
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def gql_client(
    gql_cfg: PysuiConfiguration, ensure_session_gas: None
) -> AsyncGqlClient:
    """Per-test GQL client."""
    client = AsyncGqlClient(pysui_config=gql_cfg)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def grpc_client(
    grpc_cfg: PysuiConfiguration, ensure_session_gas: None
) -> SuiGrpcClient:
    """Per-test gRPC client.

    Created as an async fixture so SuiGrpcClient (which captures the event loop
    via grpclib Channel at __init__ time) is created in the test's loop.
    """
    client = SuiGrpcClient(pysui_config=grpc_cfg)
    yield client
    client.close()


# ---------------------------------------------------------------------------
# Recipient address (second keystore address for transfer-to-other tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def recipient_address(gql_cfg: PysuiConfiguration) -> str:
    """A second address from the active keystore (skips if only one address)."""
    addrs = gql_cfg.active_group.address_list
    active = gql_cfg.active_group.using_address
    others = [a for a in addrs if a != active]
    if not others:
        pytest.skip("No second address in keystore — recipient tests skipped")
    return others[0]


# ---------------------------------------------------------------------------
# Move project path with refreshed devnet chain ID (session-scoped)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def sui_test_project_path(
    grpc_session_client: SuiGrpcClient,
    tmp_path_factory,
) -> str:
    """Copy tests/sui-test to a tmp dir, updating Move.toml devnet chain ID."""
    result = await grpc_session_client.execute(request=rn.GetServiceInfo())
    assert result.is_ok(), f"GetServiceInfo failed: {result.result_string}"
    chain_id = result.result_data.chain_id

    dst = tmp_path_factory.mktemp("sui-test-project")
    shutil.copytree(_SUI_TEST_SRC, str(dst), dirs_exist_ok=True)
    update_move_toml_chain_id(dst / "Move.toml", chain_id)
    return str(dst)


# ---------------------------------------------------------------------------
# Publish session fixtures — compile and publish sui-test once per session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def published_gql(
    gql_session_client: AsyncGqlClient,
    gql_cfg: PysuiConfiguration,
    sui_test_project_path: str,
    ensure_session_gas: None,
) -> PublishedPackage:
    """Publish the sui-test contract once per session (GQL). Yields PublishedPackage."""
    if not _sui_binary_available(gql_cfg):
        pytest.skip("sui CLI binary not configured — publish tests skipped")
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_session_client.transaction()
    cap_result = await txer.publish(project_path=sui_test_project_path)
    await txer.transfer_objects(
        transfers=[cap_result],
        recipient=gql_session_client.config.active_address,
    )
    result = await gql_session_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"GQL publish failed: {result.result_string}"
    assert result.result_data.status == "SUCCESS", (
        f"GQL publish on-chain failure: {result.result_data.execution_error}"
    )
    await asyncio.sleep(SETTLE_SECS)
    return await _gql_extract_publish_result(result.result_data, gql_session_client)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def published_grpc(
    grpc_session_client: SuiGrpcClient,
    grpc_cfg: PysuiConfiguration,
    sui_test_project_path: str,
    ensure_session_gas: None,
) -> PublishedPackage:
    """Publish the sui-test contract once per session (gRPC). Yields PublishedPackage."""
    if not _sui_binary_available(grpc_cfg):
        pytest.skip("sui CLI binary not configured — publish tests skipped")
    txer = await grpc_session_client.transaction()
    cap_result = await txer.publish(project_path=sui_test_project_path)
    await txer.transfer_objects(
        transfers=[cap_result],
        recipient=grpc_session_client.config.active_address,
    )
    result = await grpc_session_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    assert result.is_ok(), f"gRPC publish failed: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        "gRPC publish on-chain execution failed"
    )
    await asyncio.sleep(SETTLE_SECS)
    return _grpc_extract_publish_result(result.result_data)
