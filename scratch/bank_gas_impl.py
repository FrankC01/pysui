"""Central bank implementation for conftest.py.

DO NOT RUN — write-only review artifact.
This file contains the exact code that will be inserted into conftest.py at Step 5.
It is isolated here so Frank and review agents can assess it before any test suite
file is touched. See scratch/README.md.

Q1 resolved (fat coin identity): Option A — bank_session_setup() returns the
fat coin's object_id after setup; passed to CentralBank at construction.
withdraw() filters new coins from GetGas by excluding that stable object_id.
"""

import asyncio
from enum import StrEnum
from math import ceil

import httpx
import pytest

from pysui import AsyncClientBase
from pysui.sui.sui_constants import DEVNET_FAUCET_URLV1, TESTNET_FAUCET_URLV1
import pysui.sui.sui_common.sui_commands as cmd

# ── Constants (already in conftest.py — not duplicated, shown for context) ────
#   SETTLE_SECS: float = 2.0                    (line 46, Rule 16)
#   _faucet_url_for(cfg) -> str | None          (lines 58-60, Rule 15)

REQUIRED_COIN_BUDGET: int = 1_000_000_000   # 1 SUI — fat coin reserve
REQUIRED_ADDR_BUDGET: int = 1_000_000_000   # 1 SUI — address balance reserve
FAUCET_AMOUNT_MIST: int   = 10_000_000_000  # 10 SUI per faucet call

BANK_SPLIT_FEE: int    = 1_988_000   # Tier B cost of the bank's own coin-split PTB
BANK_SPLIT_AMOUNT: int = 1_000       # Default MIST per coin when caller passes None


class GasBank(StrEnum):
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
        on the 1-fat-coin invariant. Cannot protect against coins deposited by
        an external process between the two GetGas calls, but that is an
        acknowledged limitation — no in-process solution covers true concurrency.
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


# ── Helpers (inserted into conftest.py alongside bank_session_setup) ──────────

_FAUCET_BY_PROFILE: dict[str, str] = {
    "devnet": DEVNET_FAUCET_URLV1,
    "testnet": TESTNET_FAUCET_URLV1,
}


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
    Returns the fat coin's object_id for Option A identity tracking in withdraw().
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
        calls_needed = ceil(total_deficit / FAUCET_AMOUNT_MIST)
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


# ── central_bank fixture (inserted into conftest.py at Step 5) ────────────────

@pytest.fixture(scope="session", autouse=True)
async def central_bank(grpc_session_client, grpc_cfg):
    """Session-scoped central bank. autouse=True — no parameter needed in tests
    that don't call withdraw(). Tests that call withdraw() declare
    central_bank: CentralBank as a parameter to receive the instance.

    Rules 13-16:
      13 — autouse=True; 5 fixtures drop ensure_session_gas: None (no replacement)
      14 — grpc_session_client + grpc_cfg only (bank is strictly gRPC)
      15 — faucet URL from _faucet_url_for(grpc_cfg), never hardcoded
      16 — SETTLE_SECS used inside bank_session_setup and _split_and_transfer
    """
    faucet_url = _faucet_url_for(grpc_cfg)
    fat_coin_id = await bank_session_setup(grpc_session_client, faucet_url)
    yield CentralBank(client=grpc_session_client, fat_coin_id=fat_coin_id)
