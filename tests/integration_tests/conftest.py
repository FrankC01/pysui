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
from enum import Enum
from pathlib import Path
from typing import AsyncGenerator, NamedTuple

import httpx
import pytest
import pytest_asyncio

from pysui import AsyncClientBase, PysuiConfiguration, client_factory
from pysui.sui.sui_common.config.confgroup import SUI_GQL_RPC_GROUP, SUI_GRPC_GROUP
from pysui.sui.sui_constants import DEVNET_FAUCET_URLV1, TESTNET_FAUCET_URLV1
from pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 import ChangedObjectInputObjectState
import pysui.sui.sui_common.sui_commands as cmd


_FAUCET_BY_PROFILE: dict[str, str] = {
    "devnet": DEVNET_FAUCET_URLV1,
    "testnet": TESTNET_FAUCET_URLV1,
}

SETTLE_SECS: float = 2.0

# Bank budget constants — minimum balances the central bank maintains
REQUIRED_COIN_BUDGET: int = 1_000_000_000   # 1 SUI — fat coin reserve
REQUIRED_ADDR_BUDGET: int = 1_000_000_000   # 1 SUI — address balance reserve
FAUCET_AMOUNT_MIST: int   = 10_000_000_000  # 10 SUI per faucet call

BANK_SPLIT_FEE: int    = 1_988_000   # Tier B cost of the bank's own coin-split PTB
BANK_SPLIT_AMOUNT: int = 1_000       # Default MIST per coin when caller passes None

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


def _extract_publish_result(changed_objects) -> PublishedPackage:
    """Return PublishedPackage from an ExecutedTransaction effects.changed_objects list."""
    pkg_addr = next(
        (
            co.object_id
            for co in changed_objects
            if co.input_state == ChangedObjectInputObjectState.DOES_NOT_EXIST
            and co.object_type == "package"
        ),
        None,
    )
    cap_id = next(
        (
            co.object_id
            for co in changed_objects
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
            for co in changed_objects
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
async def gql_session_client(gql_cfg: PysuiConfiguration) -> AsyncGenerator[AsyncClientBase, None]:
    """Long-lived GQL client shared across the session."""
    client = client_factory(gql_cfg)
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def grpc_session_client(grpc_cfg: PysuiConfiguration) -> AsyncGenerator[AsyncClientBase, None]:
    """Long-lived gRPC client shared across the session."""
    client = client_factory(grpc_cfg)
    yield client
    await client.close()


# ---------------------------------------------------------------------------
# GasBank enum and CentralBank class
# ---------------------------------------------------------------------------


class GasBank(str, Enum):
    """Gas source selector — members compare equal to their string values."""
    COIN    = "coin"     # fat coin fund — PTB gas paid from txer.gas
    ACCOUNT = "account"  # address balance fund — PTB gas paid from addr balance


class CentralBank:
    """Session-scoped gas bank for the integration test suite.

    Instantiated once by the central_bank fixture after bank_session_setup()
    confirms both balances are funded. Tests that call bank.withdraw() declare
    central_bank: CentralBank as a fixture parameter; all other tests benefit
    from the autouse setup without declaring anything.

    withdraw() call signature matches scratch/gas_management_xref.json exactly:
        ok, coins = await central_bank.withdraw(
            pattern_id="transfer_coin_to_self",
            gas_source=GasBank.COIN,
            gas_fee=1_988_000,
            sui_coins=[None],
            sui_draw=0,
        )
    """

    def __init__(
        self,
        client: AsyncClientBase,
        fat_coin_id: str,
        coin_balance: int = REQUIRED_COIN_BUDGET,
        addr_balance: int = REQUIRED_ADDR_BUDGET,
    ) -> None:
        self._client = client
        self._fat_coin_id = fat_coin_id
        self._coin_balance = coin_balance
        self._addr_balance = addr_balance
        self._address: str = str(client.config.active_address)

    async def withdraw(
        self,
        pattern_id: str,
        gas_source: str,
        gas_fee: int,
        sui_coins: list[int | None],
        sui_draw: int = 0,
    ) -> tuple[bool, list | None]:
        """Withdraw gas resources for a single test.

        If sui_coins is non-empty: executes a split_coin + transfer_objects PTB
        from the fat coin and returns the newly created coin objects. Callers
        wire these into their own PTBs via coins[0], coins[1], etc.

        If sui_coins is empty (Form2/Form3 patterns): confirms gas coverage only;
        no PTB executed; returns (True, None).

        The bank's own split PTB ALWAYS uses fat coin gas. For Form1+Form3 DUAL
        patterns (gas_source=ACCOUNT with non-empty sui_coins), addr_debit here
        accounts only for the test's own future PTB gas — not the bank's PTB.

        Raises RuntimeError on coverage failure or on-chain execution failure.
        """
        resolved = [a if a is not None else BANK_SPLIT_AMOUNT for a in sui_coins]
        coins_total = sum(resolved)
        bank_overhead = BANK_SPLIT_FEE if resolved else 0

        if gas_source == GasBank.COIN:
            coin_debit = gas_fee + sui_draw + bank_overhead + coins_total
            addr_debit = 0
            if self._coin_balance < coin_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}]: "
                    f"need {coin_debit:,} MIST from fat coin, have {self._coin_balance:,}"
                )
        elif resolved:
            # Form1+Form3 DUAL: fat coin produces coins; addr pays test PTB gas
            coin_debit = bank_overhead + coins_total
            addr_debit = gas_fee
            if self._coin_balance < coin_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}]: "
                    f"need {coin_debit:,} MIST from fat coin, have {self._coin_balance:,}"
                )
            if self._addr_balance < addr_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}]: "
                    f"need {addr_debit:,} MIST from addr balance, have {self._addr_balance:,}"
                )
        else:
            # Form3 only: test gas entirely from addr balance; no bank PTB needed
            coin_debit = 0
            addr_debit = gas_fee
            if self._addr_balance < addr_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}]: "
                    f"need {addr_debit:,} MIST from addr balance, have {self._addr_balance:,}"
                )

        new_coins: list | None = None
        if resolved:
            new_coins = await self._split_and_transfer(resolved)

        if coin_debit:
            self._coin_balance -= coin_debit
        if addr_debit:
            self._addr_balance -= addr_debit

        return (True, new_coins)

    async def _split_and_transfer(self, amounts: list[int]) -> list:
        """Split fat coin and transfer new coins to self. Returns new coin objects.

        split_coin return type depends on amount count (pysui contract):
          1 amount  → single Argument; must be wrapped in list for transfer_objects
          2+ amounts → list[Argument]; passed directly to transfer_objects

        New coins are identified by pre/post snapshot delta: snapshot coin IDs
        before the PTB, then return only IDs that are new in the post-split
        inventory. This handles accounts with extra coins (e.g. test-leaked coins
        from a prior withdraw that weren't fully consumed) without relying solely
        on the 1-fat-coin invariant.
        """
        pre_result = await self._client.execute_for_all(command=cmd.GetGas(owner=self._address))
        if not pre_result.is_ok():
            raise RuntimeError(f"GetGas failed before bank split: {pre_result.result_string}")
        pre_ids = {c.object_id for c in (pre_result.result_data.objects or [])}

        txer = await self._client.transaction()

        if len(amounts) == 1:
            split_result = await txer.split_coin(coin=txer.gas, amounts=amounts)
            await txer.transfer_objects(transfers=[split_result], recipient=self._address)
        else:
            split_results = await txer.split_coin(coin=txer.gas, amounts=amounts)
            await txer.transfer_objects(transfers=split_results, recipient=self._address)

        txdict = await txer.build_and_sign()
        result = await self._client.execute(command=cmd.ExecuteTransaction(**txdict))
        if not result.is_ok():
            raise RuntimeError(f"Bank split PTB failed: {result.result_string}")

        await asyncio.sleep(SETTLE_SECS)

        post_result = await self._client.execute_for_all(command=cmd.GetGas(owner=self._address))
        if not post_result.is_ok():
            raise RuntimeError(f"GetGas failed after bank split: {post_result.result_string}")

        inventory = post_result.result_data.objects or []
        new_coins = [c for c in inventory if c.object_id not in pre_ids]

        if len(new_coins) != len(amounts):
            raise RuntimeError(
                f"Bank split produced {len(new_coins)} new coin(s), expected {len(amounts)}. "
                f"pre_ids={pre_ids}, "
                f"post_ids={[c.object_id for c in inventory]}"
            )

        return new_coins


# ---------------------------------------------------------------------------
# Bank helpers and session setup
# ---------------------------------------------------------------------------


async def _bank_faucet(faucet_url: str, address: str) -> list[str]:
    """Call faucet and return coin object IDs sent."""
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            faucet_url,
            headers={"Content-Type": "application/json"},
            json={"FixedAmountRequest": {"recipient": address}},
        )
    if resp.status_code == 429:
        raise RuntimeError(f"Faucet rate-limited (429): {resp.text}")
    resp.raise_for_status()
    data = resp.json()
    error = data.get("error") or (
        "status" in data and data["status"] != "Success" and data.get("status")
    )
    if error:
        raise RuntimeError(f"Faucet error: {resp.text}")
    await asyncio.sleep(SETTLE_SECS)
    return [entry["id"] for entry in data.get("coins_sent", [])]


async def _bank_audit(client: AsyncClientBase, address: str) -> tuple[int, int, list]:
    """Return (coin_balance, addr_balance, inventory_sorted_desc)."""
    bal_result = await client.execute(
        command=cmd.GetAddressCoinBalance(owner=address, coin_type="0x2::sui::SUI")
    )
    if not bal_result.is_ok():
        raise RuntimeError(f"GetAddressCoinBalance failed: {bal_result.result_string}")

    gas_result = await client.execute_for_all(command=cmd.GetGas(owner=address))
    if not gas_result.is_ok():
        raise RuntimeError(f"GetGas failed: {gas_result.result_string}")

    coin_balance: int = bal_result.result_data.balance.coin_balance or 0
    addr_balance: int = bal_result.result_data.balance.address_balance or 0
    inventory = sorted(
        gas_result.result_data.objects or [],
        key=lambda c: c.balance,
        reverse=True,
    )
    return coin_balance, addr_balance, inventory


async def _bank_exec(client: AsyncClientBase, build_fn) -> None:
    txer = await client.transaction()
    await build_fn(txer)
    txdict = await txer.build_and_sign()
    result = await client.execute(command=cmd.ExecuteTransaction(**txdict))
    if not result.is_ok():
        raise RuntimeError(f"Transaction failed: {result.result_string}")
    await asyncio.sleep(SETTLE_SECS)


async def bank_session_setup(client: AsyncClientBase, faucet_url: str) -> str:
    """Ensure the account is in the correct 1-fat-coin + funded state.

    Handles all 4 pre-condition scenarios (empty, fragmented, coin-low, addr-low).
    Returns the fat coin's object_id for identity tracking in withdraw().
    Raises RuntimeError if either balance cannot be brought to target.
    """
    address: str = str(client.config.active_address)

    coin_balance, addr_balance, inventory = await _bank_audit(client, address)

    if len(inventory) > 1:
        merge_ids = [c.object_id for c in inventory[1:]]

        async def _merge(txer, ids=merge_ids):
            await txer.merge_coins(merge_to=txer.gas, merge_from=ids)

        await _bank_exec(client, _merge)
        coin_balance, addr_balance, inventory = await _bank_audit(client, address)

    coin_deficit  = max(0, REQUIRED_COIN_BUDGET - coin_balance)
    addr_deficit  = max(0, REQUIRED_ADDR_BUDGET - addr_balance)
    total_deficit = coin_deficit + addr_deficit

    if total_deficit > 0:
        calls_needed = math.ceil(total_deficit / FAUCET_AMOUNT_MIST)
        faucet_coin_ids: list[str] = []
        for _ in range(calls_needed):
            ids = await _bank_faucet(faucet_url, address)
            faucet_coin_ids.extend(ids)

        merge_from_faucet = faucet_coin_ids if inventory else faucet_coin_ids[1:]
        if merge_from_faucet:
            async def _merge_faucet(txer, ids=merge_from_faucet):
                await txer.merge_coins(merge_to=txer.gas, merge_from=ids)

            await _bank_exec(client, _merge_faucet)

        coin_balance, addr_balance, _ = await _bank_audit(client, address)
        addr_deficit = max(0, REQUIRED_ADDR_BUDGET - addr_balance)

    if addr_deficit > 0:
        send_amount = addr_deficit

        async def _fund_addr(txer, amount=send_amount, addr=address):
            split_result = await txer.split_coin(coin=txer.gas, amounts=[amount])
            await txer.move_call(
                target="0x2::coin::send_funds",
                type_arguments=["0x2::sui::SUI"],
                arguments=[split_result, addr],
            )

        await _bank_exec(client, _fund_addr)

    coin_balance, addr_balance, final_inventory = await _bank_audit(client, address)

    if coin_balance < REQUIRED_COIN_BUDGET or addr_balance < REQUIRED_ADDR_BUDGET:
        raise RuntimeError(
            f"Bank setup failed: coinBalance={coin_balance:,}  addrBalance={addr_balance:,}"
        )

    if len(final_inventory) != 1:
        raise RuntimeError(
            f"Expected exactly 1 fat coin after setup, got {len(final_inventory)}: "
            f"{[c.object_id for c in final_inventory]}"
        )

    return final_inventory[0].object_id


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def central_bank(
    grpc_session_client: AsyncClientBase,
    grpc_cfg: PysuiConfiguration,
) -> AsyncGenerator[CentralBank, None]:
    """Session-scoped central bank. autouse=True — no parameter needed in tests
    that don't call withdraw(). Tests that call withdraw() declare
    central_bank: CentralBank as a fixture parameter to receive the instance.

    Rules 13-16:
      13 — autouse=True; 5 fixtures drop ensure_session_gas: None (no replacement)
      14 — grpc_session_client + grpc_cfg only (bank is strictly gRPC)
      15 — faucet URL from _faucet_url_for(grpc_cfg), never hardcoded
      16 — SETTLE_SECS used inside bank_session_setup and _split_and_transfer
    """
    faucet_url = _faucet_url_for(grpc_cfg)
    fat_coin_id = await bank_session_setup(grpc_session_client, faucet_url)
    yield CentralBank(client=grpc_session_client, fat_coin_id=fat_coin_id)


# ---------------------------------------------------------------------------
# Function-scoped clients — for simple per-test isolation
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def gql_client(
    gql_cfg: PysuiConfiguration,
) -> AsyncGenerator[AsyncClientBase, None]:
    """Per-test GQL client."""
    client = client_factory(gql_cfg)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def grpc_client(
    grpc_cfg: PysuiConfiguration,
) -> AsyncGenerator[AsyncClientBase, None]:
    """Per-test gRPC client.

    Created as an async fixture so GrpcProtocolClient (which captures the event loop
    via grpclib Channel at __init__ time) is created in the test's loop.
    """
    client = client_factory(grpc_cfg)
    yield client
    await client.close()


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
    grpc_session_client: AsyncClientBase,
    tmp_path_factory,
) -> str:
    """Copy tests/sui-test to a tmp dir, updating Move.toml devnet chain ID."""
    result = await grpc_session_client.execute(command=cmd.GetChainIdentifier())
    assert result.is_ok(), f"GetChainIdentifier failed: {result.result_string}"
    chain_id = result.result_data

    dst = tmp_path_factory.mktemp("sui-test-project")
    shutil.copytree(_SUI_TEST_SRC, str(dst), dirs_exist_ok=True)
    update_move_toml_chain_id(dst / "Move.toml", chain_id)
    return str(dst)


# ---------------------------------------------------------------------------
# Publish session fixtures — compile and publish sui-test once per session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def published_gql(
    gql_session_client: AsyncClientBase,
    gql_cfg: PysuiConfiguration,
    sui_test_project_path: str,
    central_bank: CentralBank,
) -> PublishedPackage:
    """Publish the sui-test contract once per session (GQL). Yields PublishedPackage.

    To skip publishing and use pre-published contract, set environment variables:
    - PYSUI_TEST_PKG_ID: package address
    - PYSUI_TEST_UPGRADE_CAP_ID: upgrade cap object ID
    - PYSUI_TEST_PARM_OBJECT_ID: parm object ID
    """
    pkg_id = os.getenv("PYSUI_TEST_PKG_ID")
    cap_id = os.getenv("PYSUI_TEST_UPGRADE_CAP_ID")
    parm_obj_id = os.getenv("PYSUI_TEST_PARM_OBJECT_ID")

    if pkg_id and cap_id and parm_obj_id:
        return PublishedPackage(pkg_addr=pkg_id, cap_id=cap_id, parm_obj_id=parm_obj_id)

    if not _sui_binary_available(gql_cfg):
        pytest.skip("sui CLI binary not configured — publish tests skipped")
    await asyncio.sleep(SETTLE_SECS)
    await central_bank.withdraw(
        pattern_id="publish_contract_gql",
        gas_source=GasBank.COIN,
        gas_fee=3_500_000,
        sui_coins=[],
        sui_draw=0,
    )
    txer = await gql_session_client.transaction()
    cap_result = await txer.publish(project_path=sui_test_project_path)
    await txer.transfer_objects(
        transfers=[cap_result],
        recipient=gql_session_client.config.active_address,
    )
    txdict = await txer.build_and_sign()
    result = await gql_session_client.execute(command=cmd.ExecuteTransaction(**txdict))
    assert result.is_ok(), f"GQL publish failed: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        "GQL publish on-chain execution failed"
    )
    await asyncio.sleep(SETTLE_SECS)
    return _extract_publish_result(result.result_data.transaction.effects.changed_objects)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def published_grpc(
    grpc_session_client: AsyncClientBase,
    grpc_cfg: PysuiConfiguration,
    sui_test_project_path: str,
    central_bank: CentralBank,
) -> PublishedPackage:
    """Publish the sui-test contract once per session (gRPC). Yields PublishedPackage.

    To skip publishing and use pre-published contract, set environment variables:
    - PYSUI_TEST_PKG_ID: package address
    - PYSUI_TEST_UPGRADE_CAP_ID: upgrade cap object ID
    - PYSUI_TEST_PARM_OBJECT_ID: parm object ID
    """
    pkg_id = os.getenv("PYSUI_TEST_PKG_ID")
    cap_id = os.getenv("PYSUI_TEST_UPGRADE_CAP_ID")
    parm_obj_id = os.getenv("PYSUI_TEST_PARM_OBJECT_ID")

    if pkg_id and cap_id and parm_obj_id:
        return PublishedPackage(pkg_addr=pkg_id, cap_id=cap_id, parm_obj_id=parm_obj_id)

    if not _sui_binary_available(grpc_cfg):
        pytest.skip("sui CLI binary not configured — publish tests skipped")
    await central_bank.withdraw(
        pattern_id="publish_contract_grpc",
        gas_source=GasBank.ACCOUNT,
        gas_fee=3_500_000,
        sui_coins=[],
        sui_draw=0,
    )
    txer = await grpc_session_client.transaction()
    cap_result = await txer.publish(project_path=sui_test_project_path)
    await txer.transfer_objects(
        transfers=[cap_result],
        recipient=grpc_session_client.config.active_address,
    )
    txdict = await txer.build_and_sign(use_account_for_gas=True)
    result = await grpc_session_client.execute(command=cmd.ExecuteTransaction(**txdict))
    assert result.is_ok(), f"gRPC publish failed: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        "gRPC publish on-chain execution failed"
    )
    await asyncio.sleep(SETTLE_SECS)
    return _extract_publish_result(result.result_data.transaction.effects.changed_objects)


# ---------------------------------------------------------------------------
# TxnDigests — one known-good digest per protocol for transaction query tests
# ---------------------------------------------------------------------------


class TxnDigests(NamedTuple):
    """A pair of on-chain transaction digests, one submitted per protocol."""

    digest1: str  # submitted via GQL ExecuteTransaction SuiCommand
    digest2: str  # submitted via gRPC ExecuteTransaction SuiCommand


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def txn_digests(
    gql_session_client: AsyncClientBase,
    grpc_session_client: AsyncClientBase,
    central_bank: CentralBank,
) -> TxnDigests:
    """Submit one trivial PTB per protocol and return both digests.

    Each PTB: split_coin(gas, [1_000]) + transfer_objects([result], active_address).
    Implicitly exercises ExecuteTransaction SuiCommand on both protocols.
    """
    # GQL PTB
    await central_bank.withdraw(
        pattern_id="split_gas_1k_transfer_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[],
        sui_draw=0,
    )
    gql_txer = await gql_session_client.transaction()
    gql_coin = await gql_txer.split_coin(coin=gql_txer.gas, amounts=[1_000])
    await gql_txer.transfer_objects(
        transfers=[gql_coin], recipient=gql_session_client.config.active_address
    )
    gql_result = await gql_session_client.execute(
        command=cmd.ExecuteTransaction(**await gql_txer.build_and_sign())
    )
    assert gql_result.is_ok(), f"GQL ExecuteTransaction failed: {gql_result.result_string}"
    digest1: str = gql_result.result_data.transaction.digest
    await asyncio.sleep(SETTLE_SECS)

    # gRPC PTB
    await central_bank.withdraw(
        pattern_id="split_gas_1k_transfer_self",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[],
        sui_draw=0,
    )
    grpc_txer = await grpc_session_client.transaction()
    grpc_coin = await grpc_txer.split_coin(coin=grpc_txer.gas, amounts=[1_000])
    await grpc_txer.transfer_objects(
        transfers=[grpc_coin], recipient=grpc_session_client.config.active_address
    )
    grpc_result = await grpc_session_client.execute(
        command=cmd.ExecuteTransaction(**await grpc_txer.build_and_sign())
    )
    assert grpc_result.is_ok(), f"gRPC ExecuteTransaction failed: {grpc_result.result_string}"
    digest2: str = grpc_result.result_data.transaction.digest
    await asyncio.sleep(SETTLE_SECS)

    return TxnDigests(digest1=digest1, digest2=digest2)
