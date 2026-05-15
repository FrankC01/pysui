#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared gas management utilities for serial and parallel executors."""

import logging

from pysui.sui.sui_common.executors.exec_types import ExecutorContext
from pysui.sui.sui_common.validators import valid_sui_address
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.sui_commands as cmd

logger = logging.getLogger(__name__)

_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"
_SEND_FUNDS_GAS_OVERHEAD = 3_000_000


async def acquire_coins(client, sender: str, initial_coins: list, threshold: int) -> list:
    """Fetch, filter (SUI only), sort descending, and select coins meeting threshold.

    :returns: list of selected coin objects meeting the cumulative threshold.
    :raises ValueError: if no coins found or total is below threshold.
    """
    if initial_coins:
        coins = initial_coins
        if isinstance(coins[0], str):
            if not all(valid_sui_address(c) for c in coins):
                raise ValueError("initial_coins: one or more entries are not valid object IDs")
            result = await client.execute(command=cmd.GetMultipleObjects(object_ids=coins))
            if not result.is_ok():
                raise ValueError(f"Failed to fetch initial coins: {result.result_string}")
            obj_list = [o for o in result.result_data if o.object_type == _SUI_COIN_TYPE]
        else:
            obj_list = [o for o in coins if o.object_type == _SUI_COIN_TYPE]
    else:
        result = await client.execute_for_all(command=cmd.GetGas(owner=sender))
        if not result.is_ok():
            raise ValueError(f"Failed to fetch gas coins: {result.result_string}")
        obj_list = result.result_data.objects

    if not obj_list:
        raise ValueError(f"No SUI coins found for sender {sender}")

    sorted_coins = sorted(obj_list, key=lambda o: o.balance or 0, reverse=True)
    selected = []
    running = 0
    for o in sorted_coins:
        selected.append(o)
        running += o.balance or 0
        if running >= threshold:
            break
    if running < threshold:
        raise ValueError(f"Insufficient balance {running} < min_threshold_balance {threshold}")
    return selected


async def _build_and_sign_with_gas(send_tx, gas_coin_obj) -> dict:
    """Build and sign send_tx using gas_coin_obj as the gas object."""
    gas_obj = sui_prot.Object(
        object_id=gas_coin_obj.object_id,
        version=gas_coin_obj.version,
        digest=gas_coin_obj.digest,
        balance=gas_coin_obj.balance or 0,
    )
    return await send_tx.build_and_sign(use_gas_objects=[gas_obj])


async def send_funds_to_account(
    client,
    sender: str,
    candidates: list,
    existing_balance: int,
    min_threshold_balance: int,
    new_transaction_fn,
) -> "sui_prot.ExecutedTransaction":
    """ADDRESS_BALANCE mode: send primary coin to account balance via send_funds PTB.

    Option A: use non-primary coin as gas.
    Option B: primary has surplus — split and send, primary pays gas.
    Fallback: fetch another coin from chain.

    :returns: ExecutedTransaction — caller updates tracked balance from accumulator.
    :raises ValueError: on fetch or execution failure.
    """
    sorted_candidates = sorted(candidates, key=lambda o: o.balance or 0, reverse=True)
    primary = sorted_candidates[0]
    not_primary = sorted_candidates[1:]

    send_tx = await new_transaction_fn()

    if not_primary:
        gas_coin_obj = not_primary[0]
        await send_tx.move_call(
            target="0x2::coin::send_funds",
            type_arguments=["0x2::sui::SUI"],
            arguments=[primary, sender],
        )
        build_dict = await _build_and_sign_with_gas(send_tx, gas_coin_obj)

    elif primary.balance > (min_threshold_balance - existing_balance) + _SEND_FUNDS_GAS_OVERHEAD:
        amount_to_send = min_threshold_balance - existing_balance
        what_we_send = await send_tx.split_coin(coin=send_tx.gas, amounts=[amount_to_send])
        await send_tx.move_call(
            target="0x2::coin::send_funds",
            type_arguments=["0x2::sui::SUI"],
            arguments=[what_we_send, sender],
        )
        build_dict = await _build_and_sign_with_gas(send_tx, primary)

    else:
        result = await client.execute_for_all(command=cmd.GetGas(owner=sender))
        if not result.is_ok():
            raise ValueError(f"send_funds: failed to fetch gas coins: {result.result_string}")
        other_coins = [o for o in result.result_data.objects if o.object_id != primary.object_id]
        if not other_coins:
            raise ValueError("send_funds: no gas coin available — hard stop")
        gas_coin_obj = other_coins[0]
        await send_tx.move_call(
            target="0x2::coin::send_funds",
            type_arguments=["0x2::sui::SUI"],
            arguments=[primary, sender],
        )
        build_dict = await _build_and_sign_with_gas(send_tx, gas_coin_obj)

    result = await client.execute(command=cmd.ExecuteTransaction(**build_dict))
    if not result.is_ok():
        raise ValueError(f"send_funds: transaction failed: {result.result_string}")
    return result.result_data


def update_tracked_balance(effects, tracked_balance: int) -> int:
    """Deduct net gas cost from tracked_balance. Returns updated balance."""
    gas = effects.gas_used
    if gas is None:
        return tracked_balance
    net_gas = (gas.computation_cost or 0) + (gas.storage_cost or 0) - (gas.storage_rebate or 0)
    return max(0, tracked_balance - net_gas)


def update_tracked_balance_from_accumulator(executed_tx, tracked_balance: int) -> int:
    """ADDRESS_BALANCE mode: apply MERGE/SPLIT accumulator write. Returns updated balance."""
    if executed_tx is None or executed_tx.effects is None:
        return tracked_balance
    for changed_obj in executed_tx.effects.changed_objects:
        if "ACCUMULATOR" in str(changed_obj.output_state):
            acc = changed_obj.accumulator_write
            if acc is not None:
                op_name = getattr(acc.operation, "name", str(acc.operation))
                if op_name == "MERGE":
                    return tracked_balance + acc.value
                elif op_name == "SPLIT":
                    return max(0, tracked_balance - acc.value)
            break
    return tracked_balance


async def run_replenishment(
    on_balance_low,
    sender: str,
    tracked_balance: int,
    min_threshold_balance: int,
    client,
    add_funds_fn,
    label: str = "Executor",
) -> bool:
    """Invoke on_balance_low callback and pass returned coins to add_funds_fn.

    :returns: True if replenishment succeeded, False if caller should hard stop.
    """
    if on_balance_low is None:
        logger.warning("%s: balance low but no on_balance_low callback — hard stop", label)
        return False
    ctx = ExecutorContext(
        sender=sender,
        tracked_balance=tracked_balance,
        min_threshold_balance=min_threshold_balance,
        client=client,
    )
    coins = await on_balance_low(ctx)
    if not coins:
        logger.warning("%s: on_balance_low returned None/[] — hard stop", label)
        return False
    try:
        await add_funds_fn(coins)
    except Exception as exc:
        logger.warning("%s: add_funds failed: %s — hard stop", label, exc)
        return False
    return True
