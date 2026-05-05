import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from enum import Enum
from math import ceil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from pysui import PysuiConfiguration, client_factory, AsyncClientBase
from pysui.sui.sui_constants import DEVNET_FAUCET_URLV1, TESTNET_FAUCET_URLV1
import pysui.sui.sui_common.sui_commands as cmd

REQUIRED_COIN_BUDGET: int = 1_000_000_000   # 1 SUI — fat coin reserve (Form 1/2) [provisional]
REQUIRED_ADDR_BUDGET: int = 1_000_000_000   # 1 SUI — address balance reserve (Form 3) [provisional]
FAUCET_AMOUNT_MIST: int   = 10_000_000_000  # 10 SUI per faucet call
SETTLE_SECS: float         = 2.0

BANK_SPLIT_FEE: int    = 1_988_000  # Tier B — cost of bank's own coin-split PTB
BANK_SPLIT_AMOUNT: int = 1_000     # Default MIST per split coin when caller passes None

_MODEL_PATH = Path(__file__).parent / "test_cost_model.json"


class GasBank(Enum):
    COIN    = "coin"     # fat coin fund — gas paid from txer.gas
    ACCOUNT = "account"  # address balance fund — gas paid via use_account_for_gas


@dataclass
class SimCoin:
    """Simulated coin object returned by withdraw_trace — mirrors fields used from sui_prot.Object."""
    object_id: str
    balance: int


def _gas_source_from_form(form: str) -> GasBank:
    return GasBank.ACCOUNT if "Form3" in form else GasBank.COIN


class CentralBank:
    """Central bank for integration test gas management.

    Tracks two running balances (fat coin and address balance) and services
    per-test withdrawal requests. Simulation mode: pure math, no network calls.
    Live mode (Step 5+): real gRPC calls backed by the active devnet/testnet account.
    """

    def __init__(
        self,
        coin_balance: int = REQUIRED_COIN_BUDGET,
        addr_balance: int = REQUIRED_ADDR_BUDGET,
        fat_coin_id: str = "sim_fat_coin_0x0000",
    ) -> None:
        self._coin_balance: int = coin_balance
        self._addr_balance: int = addr_balance
        self._fat_coin_id: str = fat_coin_id

    def simulate_withdraw(
        self,
        pattern_id: str,
        test_name: str,
        gas_source: GasBank,
        gas_fee: int,
        sui_coins: list[int | None],
        sui_draw: int = 0,
    ) -> tuple[bool, list[str] | None]:
        """Simulate a single withdrawal and update cached balances.

        sui_coins — list of coin amounts the bank must produce:
            int  → coin of exactly that many MIST
            None → coin of BANK_SPLIT_AMOUNT (static default)
        sui_draw  — MIST the test's PTB draws from txer.gas (fat coin side only).
        """
        resolved = [a if a is not None else BANK_SPLIT_AMOUNT for a in sui_coins]
        coins_total = sum(resolved)
        bank_overhead = BANK_SPLIT_FEE if resolved else 0

        if gas_source == GasBank.COIN:
            # Form1, Form2, Form1+Form2: everything debits the fat coin
            coin_debit = gas_fee + sui_draw + bank_overhead + coins_total
            addr_debit = 0
            if self._coin_balance < coin_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {coin_debit:,} MIST from fat coin, have {self._coin_balance:,}"
                )
        elif resolved:
            # Form1+Form3: test gas from addr, bank split PTB + coin amounts from fat coin
            coin_debit = bank_overhead + coins_total
            addr_debit = gas_fee
            if self._coin_balance < coin_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {coin_debit:,} MIST from fat coin, have {self._coin_balance:,}"
                )
            if self._addr_balance < addr_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {addr_debit:,} MIST from addr balance, have {self._addr_balance:,}"
                )
        else:
            # Form3 only: everything debits the addr balance
            coin_debit = 0
            addr_debit = gas_fee
            if self._addr_balance < addr_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {addr_debit:,} MIST from addr balance, have {self._addr_balance:,}"
                )

        if coin_debit:
            self._coin_balance -= coin_debit
        if addr_debit:
            self._addr_balance -= addr_debit
        result_coins = [f"sim_coin_{i}" for i in range(len(resolved))] if resolved else None

        if gas_source == GasBank.COIN:
            print(f"    COIN  {test_name:<55}  -{coin_debit:>12,}  fat→{self._coin_balance:>15,}")
        elif resolved:
            print(f"    DUAL  {test_name:<55}  -{addr_debit:>12,}  addr→{self._addr_balance:>15,}  -{coin_debit:>12,}  fat→{self._coin_balance:>15,}")
        else:
            print(f"    ACCT  {test_name:<55}  -{addr_debit:>12,}  addr→{self._addr_balance:>15,}")

        return (True, result_coins)

    def withdraw_trace(
        self,
        pattern_id: str,
        test_name: str,
        gas_source: GasBank,
        gas_fee: int,
        sui_coins: list[int | None],
        sui_draw: int = 0,
    ) -> tuple[bool, list[SimCoin] | None]:
        """Trace what withdraw() WOULD do — no network calls, no balance effects until the end."""

        # 1. Resolve None → BANK_SPLIT_AMOUNT; validate all resolved values
        resolved = [a if a is not None else BANK_SPLIT_AMOUNT for a in sui_coins]
        for v in resolved:
            if not isinstance(v, int) or v <= 0:
                raise RuntimeError(
                    f"INVALID sui_coins [{pattern_id}::{test_name}]: "
                    f"all amounts must be positive int after resolution, got {sui_coins}"
                )

        coins_total = sum(resolved)
        bank_overhead = BANK_SPLIT_FEE if resolved else 0

        # 2. Coverage check — no debit yet
        if gas_source == GasBank.COIN:
            # Form1, Form2, Form1+Form2: everything debits the fat coin
            coin_debit = gas_fee + sui_draw + bank_overhead + coins_total
            addr_debit = 0
            if self._coin_balance < coin_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {coin_debit:,} MIST from fat coin, have {self._coin_balance:,}"
                )
        elif resolved:
            # Form1+Form3: test gas from addr, bank split PTB + coin amounts from fat coin
            coin_debit = bank_overhead + coins_total
            addr_debit = gas_fee
            if self._coin_balance < coin_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {coin_debit:,} MIST from fat coin, have {self._coin_balance:,}"
                )
            if self._addr_balance < addr_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {addr_debit:,} MIST from addr balance, have {self._addr_balance:,}"
                )
        else:
            # Form3 only: everything debits the addr balance
            coin_debit = 0
            addr_debit = gas_fee
            if self._addr_balance < addr_debit:
                raise RuntimeError(
                    f"COVERAGE FAIL [{pattern_id}::{test_name}]: "
                    f"need {addr_debit:,} MIST from addr balance, have {self._addr_balance:,}"
                )

        # 3. Simulate split path (if coins needed)
        result_coins: list[SimCoin] | None = None
        split_note = ""
        if resolved:
            result_coins = [
                SimCoin(object_id=f"sim_split_{i}", balance=v)
                for i, v in enumerate(resolved)
            ]
            expected_count = len(resolved) + 1
            split_note = (
                f"WOULD split_coin(txer.gas, amounts={resolved}) + transfer_objects → self | "
                f"WOULD GetGas → expect {expected_count} coins (fat + {len(resolved)} new) | "
                f"filter out {self._fat_coin_id} → return {len(resolved)} SimCoin(s)"
            )

        # 4. Debit LAST — all on-chain work would have succeeded
        if coin_debit:
            self._coin_balance -= coin_debit
        if addr_debit:
            self._addr_balance -= addr_debit

        if gas_source == GasBank.COIN:
            print(f"    COIN  {test_name:<55}  -{coin_debit:>12,}  fat→{self._coin_balance:>15,}")
        elif resolved:
            print(f"    DUAL  {test_name:<55}  -{addr_debit:>12,}  addr→{self._addr_balance:>15,}  -{coin_debit:>12,}  fat→{self._coin_balance:>15,}")
        else:
            print(f"    ACCT  {test_name:<55}  -{addr_debit:>12,}  addr→{self._addr_balance:>15,}")
        if split_note:
            print(f"          {split_note}")

        return (True, result_coins)


async def run_withdraw_trace(client: AsyncClientBase, faucet_url: str) -> None:
    """Confirm bank ready state, then trace all per-test withdrawals via withdraw_trace().

    Calls bank_session_setup() first — idempotent when both balances are already
    >= required constants (audit-only, no merges/faucet/fund-addr). After setup
    confirms the bank is ready, traces all withdrawal paths with no further network
    calls or balance effects on the active address.
    """
    await bank_session_setup(client, faucet_url)

    with open(_MODEL_PATH) as f:
        model = json.load(f)

    patterns: list[dict] = model["patterns"]
    bank = CentralBank()

    print(f"\n{'='*80}")
    print("WITHDRAW TRACE  (no network — path verification)")
    print(f"  Starting fat coin balance : {bank._coin_balance:>15,} MIST")
    print(f"  Starting addr balance     : {bank._addr_balance:>15,} MIST")
    print(f"  Fat coin ID (sim)         : {bank._fat_coin_id}")
    print(f"  BANK_SPLIT_AMOUNT         : {BANK_SPLIT_AMOUNT:>15,} MIST  (default per None element)")
    print(f"  BANK_SPLIT_FEE            : {BANK_SPLIT_FEE:>15,} MIST  (bank's own split PTB cost)")
    print(f"{'='*80}")

    total_calls = 0
    for pattern in patterns:
        pid: str = pattern["pattern_id"]
        form: str = pattern["withdrawal_form"]
        fee_tier: str | None = pattern.get("fee_tier")
        gas_fee: int = pattern["fee_mist"]
        sui_coins_spec: list[int | None] = pattern.get("sui_coins", [])
        sui_draw: int = pattern.get("sui_draw", 0)
        tests: list[str] = pattern.get("tests", [])

        gas_source = _gas_source_from_form(form)
        tier_note = f"Tier {fee_tier}" if fee_tier else "no tier"

        print(
            f"\n  [{pid}]\n"
            f"    form={form}  source={gas_source.value}  "
            f"fee_mist={gas_fee:,} ({tier_note})  coins={sui_coins_spec}  draw={sui_draw:,}"
        )

        for test_name in tests:
            bank.withdraw_trace(
                pattern_id=pid,
                test_name=test_name,
                gas_source=gas_source,
                gas_fee=gas_fee,
                sui_coins=sui_coins_spec,
                sui_draw=sui_draw,
            )
            total_calls += 1

    # Synthetic coverage case: COIN + non-empty sui_coins + sui_draw > 0
    # No real test pattern has both coins and a draw simultaneously; this exercises
    # the only code-path combination not covered by the 28 model patterns.
    print(
        f"\n  [SYNTHETIC — coverage only]\n"
        f"    form=Form1+Form2  source=coin  fee_mist=1,988,000 (Tier B)"
        f"  coins=[None]  draw=500,000"
    )
    bank.withdraw_trace(
        pattern_id="synthetic_coin_plus_draw",
        test_name="synthetic_coins_and_draw",
        gas_source=GasBank.COIN,
        gas_fee=1_988_000,
        sui_coins=[None],
        sui_draw=500_000,
    )
    total_calls += 1

    coin_used = REQUIRED_COIN_BUDGET - bank._coin_balance
    addr_used = REQUIRED_ADDR_BUDGET - bank._addr_balance

    print(f"\n{'='*80}")
    print(f"WITHDRAW TRACE COMPLETE — {total_calls} call(s)  ({total_calls - 1} model + 1 synthetic)")
    print(
        f"  Fat coin used    : {coin_used:>12,} MIST"
        f"  ({coin_used / REQUIRED_COIN_BUDGET * 100:.2f}% of {REQUIRED_COIN_BUDGET:,})"
    )
    print(f"  Fat coin remain  : {bank._coin_balance:>12,} MIST")
    print(
        f"  Addr balance used: {addr_used:>12,} MIST"
        f"  ({addr_used / REQUIRED_ADDR_BUDGET * 100:.2f}% of {REQUIRED_ADDR_BUDGET:,})"
    )
    print(f"  Addr balance rem : {bank._addr_balance:>12,} MIST")
    print(f"{'='*80}")


def run_withdrawal_simulation() -> None:
    """Load cost model and simulate all per-test withdrawal requests against starting balances.

    Reads fee_mist directly from each pattern — no fee_tier lookup. This keeps the
    simulation accurate for ignore=true patterns (Tier D = 0 in fee_tiers, but
    fee_mist holds the actual static cost estimate).
    """
    with open(_MODEL_PATH) as f:
        model = json.load(f)

    patterns: list[dict] = model["patterns"]

    bank = CentralBank()

    print(f"\n{'='*80}")
    print("WITHDRAWAL SIMULATION  (no network — math only)")
    print(f"  Starting fat coin balance : {bank._coin_balance:>15,} MIST")
    print(f"  Starting addr balance     : {bank._addr_balance:>15,} MIST")
    print(f"  BANK_SPLIT_FEE            : {BANK_SPLIT_FEE:>15,} MIST  (bank's own split PTB)")
    print(f"  BANK_SPLIT_AMOUNT         : {BANK_SPLIT_AMOUNT:>15,} MIST  (static coin default)")
    print(f"{'='*80}")

    total_calls = 0
    for pattern in patterns:
        pid: str = pattern["pattern_id"]
        form: str = pattern["withdrawal_form"]
        fee_tier: str | None = pattern.get("fee_tier")
        gas_fee: int = pattern["fee_mist"]
        sui_coins_spec: list[int | None] = pattern.get("sui_coins", [])
        sui_draw: int = pattern.get("sui_draw", 0)
        tests: list[str] = pattern.get("tests", [])

        gas_source = _gas_source_from_form(form)
        tier_note = f"Tier {fee_tier}" if fee_tier else "no tier"

        print(
            f"\n  [{pid}]\n"
            f"    form={form}  source={gas_source.value}  "
            f"fee_mist={gas_fee:,} ({tier_note})  coins={sui_coins_spec}  draw={sui_draw:,}"
        )

        for test_name in tests:
            bank.simulate_withdraw(
                pattern_id=pid,
                test_name=test_name,
                gas_source=gas_source,
                gas_fee=gas_fee,
                sui_coins=sui_coins_spec,
                sui_draw=sui_draw,
            )
            total_calls += 1

    coin_used = REQUIRED_COIN_BUDGET - bank._coin_balance
    addr_used = REQUIRED_ADDR_BUDGET - bank._addr_balance

    print(f"\n{'='*80}")
    print(f"SIMULATION COMPLETE — {total_calls} withdrawal call(s)")
    print(
        f"  Fat coin used    : {coin_used:>12,} MIST"
        f"  ({coin_used / REQUIRED_COIN_BUDGET * 100:.2f}% of {REQUIRED_COIN_BUDGET:,})"
    )
    print(
        f"  Fat coin remain  : {bank._coin_balance:>12,} MIST"
    )
    print(
        f"  Addr balance used: {addr_used:>12,} MIST"
        f"  ({addr_used / REQUIRED_ADDR_BUDGET * 100:.2f}% of {REQUIRED_ADDR_BUDGET:,})"
    )
    print(
        f"  Addr balance rem : {bank._addr_balance:>12,} MIST"
    )
    print(f"{'='*80}")

_FAUCET_BY_PROFILE: dict[str, str] = {
    "devnet": DEVNET_FAUCET_URLV1,
    "testnet": TESTNET_FAUCET_URLV1,
}


async def _faucet(faucet_url: str, address: str) -> list[str]:
    """Call faucet and return the list of coin object IDs that were sent."""
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            faucet_url,
            headers={"Content-Type": "application/json"},
            json={"FixedAmountRequest": {"recipient": address}},
        )
    if resp.status_code == 429:
        raise RuntimeError(f"Faucet rate-limited (429): {resp.text}")
    data = resp.json()
    error = data.get("error") or (
        "status" in data and data["status"] != "Success" and data.get("status")
    )
    if error:
        raise RuntimeError(f"Faucet error: {resp.text}")
    await asyncio.sleep(SETTLE_SECS)
    return [entry["id"] for entry in data.get("coins_sent", [])]


async def _audit(client: AsyncClientBase, address: str) -> tuple[int, int, list]:
    """Return (coin_balance, addr_balance, inventory_sorted_desc)."""
    bal_result = await client.execute(
        command=cmd.GetAddressCoinBalance(owner=address, coin_type="0x2::sui::SUI")
    )
    if not bal_result.is_ok():
        raise RuntimeError(f"GetAddressCoinBalance failed: {bal_result.result_string}")

    gas_result = await client.execute(command=cmd.GetGas(owner=address))
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


async def _execute_txn(client: AsyncClientBase, build_fn) -> None:
    txer = await client.transaction()
    await build_fn(txer)
    txdict = await txer.build_and_sign()
    result = await client.execute(command=cmd.ExecuteTransaction(**txdict))
    if not result.is_ok():
        raise RuntimeError(f"Transaction failed: {result.result_string}")
    await asyncio.sleep(SETTLE_SECS)


async def bank_session_setup(client: AsyncClientBase, faucet_url: str) -> None:
    address: str = str(client.config.active_address)

    print(f"\n{'='*60}")
    print(f"BANK SETUP")
    print(f"  address : {address}")
    print(f"{'='*60}")

    # --- Initial audit ---
    coin_balance, addr_balance, inventory = await _audit(client, address)
    print(f"\n  [INITIAL AUDIT]")
    print(f"    coinBalance : {coin_balance:>15,} MIST")
    print(f"    addrBalance : {addr_balance:>15,} MIST")
    print(f"    coin count  : {len(inventory)}")
    for i, c in enumerate(inventory):
        print(f"      [{i}] {c.object_id}  {c.balance:,} MIST")

    # --- Merge to one fat coin if fragmented ---
    if len(inventory) > 1:
        print(f"\n  [MERGE] {len(inventory)} coins → 1 fat coin")
        print(f"    merge_to  : txer.gas → {inventory[0].object_id} (largest)")
        merge_ids = [c.object_id for c in inventory[1:]]
        print(f"    merge_from: {merge_ids}")

        async def _merge_initial(txer, ids=merge_ids):
            await txer.merge_coins(merge_to=txer.gas, merge_from=ids)

        await _execute_txn(client, _merge_initial)
        coin_balance, addr_balance, inventory = await _audit(client, address)
        print(f"    post-merge coinBalance: {coin_balance:,} MIST")
    else:
        print(f"\n  [MERGE] skipped — {len(inventory)} coin(s)")

    # --- Compute deficits ---
    coin_deficit  = max(0, REQUIRED_COIN_BUDGET - coin_balance)
    addr_deficit  = max(0, REQUIRED_ADDR_BUDGET - addr_balance)
    total_deficit = coin_deficit + addr_deficit

    print(f"\n  [DEFICITS]")
    print(f"    coin_deficit : {coin_deficit:>15,} MIST")
    print(f"    addr_deficit : {addr_deficit:>15,} MIST")
    print(f"    total_deficit: {total_deficit:>15,} MIST")

    # --- Faucet if needed ---
    if total_deficit > 0:
        calls_needed = ceil(total_deficit / FAUCET_AMOUNT_MIST)
        print(f"\n  [FAUCET] {calls_needed} call(s) to cover {total_deficit:,} MIST deficit")
        faucet_coin_ids: list[str] = []
        for i in range(calls_needed):
            ids = await _faucet(faucet_url, address)
            faucet_coin_ids.extend(ids)
            print(f"    call {i + 1}: landed — coin(s): {ids}")

        # Determine merge_from without a re-fetch.
        # If a fat coin existed before faucet, all faucet coins go into merge_from so the
        # fat coin is the only candidate left for txer.gas auto-selection.
        # If the account was empty, the first faucet coin is left out of merge_from so it
        # becomes txer.gas and absorbs the rest.
        if inventory:
            merge_from_faucet = faucet_coin_ids
        else:
            merge_from_faucet = faucet_coin_ids[1:]

        if merge_from_faucet:
            print(f"\n  [MERGE faucet coins] txer.gas absorbs {len(merge_from_faucet)} coin(s)")
            print(f"    merge_from: {merge_from_faucet}")

            async def _merge_faucet(txer, ids=merge_from_faucet):
                await txer.merge_coins(merge_to=txer.gas, merge_from=ids)

            await _execute_txn(client, _merge_faucet)
        else:
            print(f"\n  [MERGE faucet coins] skipped — single faucet coin")

        coin_balance, addr_balance, _ = await _audit(client, address)
        addr_deficit = max(0, REQUIRED_ADDR_BUDGET - addr_balance)
        print(f"    post-faucet coinBalance: {coin_balance:,} MIST")
        print(f"    post-faucet addrBalance: {addr_balance:,} MIST")
    else:
        print(f"\n  [FAUCET] skipped — no deficit")

    # --- Fund addressBalance if needed ---
    if addr_deficit > 0:
        print(f"\n  [FUND addrBalance] {addr_deficit:,} MIST via split_coin + send_funds")
        send_amount = addr_deficit

        async def _fund_addr(txer, amount=send_amount, addr=address):
            split_result = await txer.split_coin(coin=txer.gas, amounts=[amount])
            await txer.move_call(
                target="0x2::coin::send_funds",
                type_arguments=["0x2::sui::SUI"],
                arguments=[split_result, addr],
            )

        await _execute_txn(client, _fund_addr)
        coin_balance, addr_balance, _ = await _audit(client, address)
        print(f"    coinBalance after : {coin_balance:,} MIST")
        print(f"    addrBalance after : {addr_balance:,} MIST")
    else:
        print(f"\n  [FUND addrBalance] skipped — no deficit")

    # --- Final verification ---
    coin_balance, addr_balance, _ = await _audit(client, address)
    coin_ok = coin_balance >= REQUIRED_COIN_BUDGET
    addr_ok = addr_balance >= REQUIRED_ADDR_BUDGET

    print(f"\n  [VERIFICATION]")
    print(
        f"    coinBalance : {coin_balance:>15,} MIST  >= {REQUIRED_COIN_BUDGET:,}?"
        f"  {'YES' if coin_ok else 'NO'}"
    )
    print(
        f"    addrBalance : {addr_balance:>15,} MIST  >= {REQUIRED_ADDR_BUDGET:,}?"
        f"  {'YES' if addr_ok else 'NO'}"
    )
    status = "OK" if coin_ok and addr_ok else "FAIL"
    print(f"\n  [BANK READY] {status}")

    if not (coin_ok and addr_ok):
        raise RuntimeError(f"Bank setup incomplete: coinOK={coin_ok}, addrOK={addr_ok}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        prog="temp_gas_management.py",
        description="Live-chain verification of CentralBank session setup logic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pre-conditions per scenario (arrange your devnet wallet before running):
  scenario1  Empty or near-empty account — no coins, zero balances
  scenario2  Fully funded but fragmented — 3+ coins, both balances >= target
  scenario3  Coin funded, addr low — coinBalance >= target, addrBalance < target
  scenario4  Addr funded, coin low — addrBalance >= target, coinBalance < target
        """,
    )
    parser.add_argument(
        "--profile",
        default="devnet",
        choices=["devnet", "testnet"],
        help="Sui network profile (default: devnet)",
    )
    subparsers = parser.add_subparsers(dest="scenario", required=True)
    subparsers.add_parser("scenario1", help="Empty account — full faucet + merge + fund path")
    subparsers.add_parser("scenario2", help="Fully funded, fragmented — merge only, no faucet")
    subparsers.add_parser("scenario3", help="Coin funded, addr low — faucet protects fat coin, then fund addr")
    subparsers.add_parser("scenario4", help="Addr funded, coin low — faucet + merge for coin side")
    subparsers.add_parser("simulate", help="Simulate all per-test withdrawal requests (no network)")
    subparsers.add_parser("withdraw_trace", help="Confirm bank ready state then trace withdraw() paths per cost model")
    args = parser.parse_args()

    # no-network subcommands — run immediately and exit
    if args.scenario == "simulate":
        try:
            run_withdrawal_simulation()
        except Exception as e:
            print(f"\nERROR: {e}", file=sys.stderr)
            sys.exit(1)
        return

    client: AsyncClientBase | None = None
    try:
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
            profile_name=args.profile,
        )
        client = client_factory(cfg)
        faucet_url = _FAUCET_BY_PROFILE.get(args.profile)
        if not faucet_url:
            raise RuntimeError(f"No faucet URL for profile '{args.profile}'")

        print(f"Profile  : {args.profile}")
        print(f"Scenario : {args.scenario}")
        print(f"Address  : {cfg.active_address}")

        if args.scenario == "withdraw_trace":
            await run_withdraw_trace(client, faucet_url)
        elif args.scenario == "scenario1":
            await bank_session_setup(client, faucet_url)
        elif args.scenario == "scenario2":
            await bank_session_setup(client, faucet_url)
        elif args.scenario == "scenario3":
            await bank_session_setup(client, faucet_url)
        elif args.scenario == "scenario4":
            await bank_session_setup(client, faucet_url)

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if client is not None:
            try:
                result = client.close()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
