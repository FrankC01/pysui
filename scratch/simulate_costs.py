#!/usr/bin/env python3
"""Verify fee tier constants and compute bank reserve totals.

For ignore=false patterns: runs SimulateTransactionKind to get actual on-chain
gas cost. Updates fee_tiers[A/B/C] and cascades to fee_mist on affected patterns
so that temp_gas_management.py simulate stays in sync.

For ignore=true patterns: skips SimulateTransactionKind; uses fee_mist, sui_draw,
and sui_coins from the model directly. Both contribute to the same accumulators
so the final totals reflect all patterns — simulated and static-estimated alike.

Budget split:
  Fat coin  — fees for Form1/Form2/Form1+Form2 patterns; all sui_draw; all coin provisioning
  Addr bal  — fees for Form3/Form1+Form3 patterns only

Run from anywhere (sys.path is patched automatically):
    . env/bin/activate && python scratch/simulate_costs.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pysui import PysuiConfiguration, client_factory
import pysui.sui.sui_common.sui_commands as cmd

_COST_MODEL = Path(__file__).parent / "test_cost_model.json"
_BANK_COIN_AMOUNT = 1_000   # MIST for None elements in sui_coins

_FAT_FORMS = {"Form1", "Form2", "Form1+Form2"}
_ADDR_FORMS = {"Form3", "Form1+Form3"}


async def _sim(client, txer):
    """Simulate txer and return (fee_mist, error_str)."""
    result = await client.execute(
        command=cmd.SimulateTransactionKind(
            tx_kind=txer.raw_kind(),
            tx_meta={"sender": client.config.active_address},
            gas_selection=True,
        )
    )
    if not result.is_ok():
        return None, result.result_string
    gu = result.result_data.transaction.effects.gas_used
    return gu.computation_cost + gu.storage_cost, None


async def main():
    client = client_factory(
        PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
            profile_name="devnet",
        )
    )
    addr = client.config.active_address

    coins_res = await client.execute(command=cmd.GetGas(owner=addr))
    assert coins_res.is_ok(), f"GetGas failed: {coins_res.result_string}"
    coins = coins_res.result_data.objects
    assert len(coins) >= 1, f"Need >= 1 coin, got {len(coins)}"

    data = json.loads(_COST_MODEL.read_text())
    stored_tiers = data["fee_tiers"]

    print(f"Active address : {addr}")
    print(f"Coins available: {len(coins)}")
    print()

    simulated = {}

    # --- Tier A: split(txer.gas) + send_funds ---
    txer = await client.transaction()
    sc = await txer.split_coin(coin=txer.gas, amounts=[500_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[sc, addr],
    )
    fee, error = await _sim(client, txer)
    simulated["A"] = fee
    status = "OK" if fee == stored_tiers["A"] else "CHANGED"
    print(f"  Tier A [{status}]: simulated={fee:,}  stored={stored_tiers['A']:,}")

    # --- Tier B: split(txer.gas) + transfer_objects ---
    txer = await client.transaction()
    sc = await txer.split_coin(coin=txer.gas, amounts=[1_000])
    await txer.transfer_objects(transfers=[sc], recipient=addr)
    fee, error = await _sim(client, txer)
    simulated["B"] = fee
    status = "OK" if fee == stored_tiers["B"] else "CHANGED"
    print(f"  Tier B [{status}]: simulated={fee:,}  stored={stored_tiers['B']:,}")

    # --- Tier C: split(explicit_coin) + transfer_objects ---
    txer = await client.transaction()
    sc = await txer.split_coin(coin=coins[0].object_id, amounts=[1_000])
    await txer.transfer_objects(transfers=[sc], recipient=addr)
    fee, error = await _sim(client, txer)
    simulated["C"] = fee
    status = "OK" if fee == stored_tiers["C"] else "CHANGED"
    print(f"  Tier C [{status}]: simulated={fee:,}  stored={stored_tiers['C']:,}")

    # Update fee_tiers and cascade to fee_mist on non-ignored patterns
    changed = [t for t in ("A", "B", "C") if simulated[t] != stored_tiers[t]]
    if changed:
        for t in changed:
            data["fee_tiers"][t] = simulated[t]
        for p in data["patterns"]:
            if not p.get("ignore", False) and p.get("fee_tier") in changed:
                p["fee_mist"] = data["fee_tiers"][p["fee_tier"]]
        _COST_MODEL.write_text(json.dumps(data, indent=2))
        print(f"\nfee_tiers updated for: {', '.join(changed)}")
        print(f"fee_mist cascaded to all non-ignored patterns using changed tiers.")
    else:
        print("\nAll tiers match stored values — no update needed.")

    # --- Budget totals ---
    # ignore=false: fee from fee_tiers[tier] (authoritative, just updated above if changed)
    # ignore=true:  fee from fee_mist directly (static estimate)
    # sui_draw:     always debits fat coin (only meaningful for fat_form patterns)
    # sui_coins:    always debits fat coin (bank provisions coins from fat coin for all patterns)
    print()
    print("─" * 62)
    print("Budget totals (fee + draw + coin provisioning × N tests):")
    print("─" * 62)

    fat_fee = 0     # gas fees from fat coin (Form1/Form2/Form1+Form2 patterns)
    fat_draw = 0    # sui_draw outflows from fat coin
    fat_coins = 0   # explicit coin provisioning from fat coin (all patterns)
    addr_fee = 0    # gas fees from address balance (Form3/Form1+Form3 patterns)

    for p in data["patterns"]:
        n = len(p.get("tests", []))
        if n == 0:
            continue
        form = p["withdrawal_form"]
        ignored = p.get("ignore", False)

        if ignored:
            fee = p["fee_mist"]
        else:
            fee = data["fee_tiers"].get(p.get("fee_tier", ""), 0)

        draw = p.get("sui_draw", 0)
        resolved = [a if a is not None else _BANK_COIN_AMOUNT for a in p.get("sui_coins", [])]
        coins_total = sum(resolved)

        if form in _ADDR_FORMS:
            addr_fee += fee * n
        else:
            fat_fee += fee * n
            fat_draw += draw * n

        fat_coins += coins_total * n

    fat_total = fat_fee + fat_draw + fat_coins
    addr_total = addr_fee

    print(f"  Fat coin  fees  (gas, Form1/Form2 patterns) : {fat_fee:>14,} MIST")
    print(f"  Fat coin  draws (sui_draw outflows)         : {fat_draw:>14,} MIST")
    print(f"  Fat coin  coins (all sui_coins provisions)  : {fat_coins:>14,} MIST")
    print(f"  Fat coin  TOTAL                             : {fat_total:>14,} MIST")
    print()
    print(f"  Addr bal  fees  (gas, Form3 patterns)       : {addr_fee:>14,} MIST")
    print(f"  Addr bal  TOTAL                             : {addr_total:>14,} MIST")

    client.close()


asyncio.run(main())
