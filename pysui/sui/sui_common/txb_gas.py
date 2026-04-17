#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Protocol-agnostic gas selection and budget utilities shared across GQL and gRPC paths."""

from typing import Callable, TypeVar

from pysui.sui.sui_bcs import bcs

# Per Mysten TS SDK: GAS_SAFE_OVERHEAD applied to every budget estimate.
_GAS_SAFE_OVERHEAD: int = 1000  # gas units (not MIST)

# Sui protocol hard limit on gas payment objects.
_MAX_GAS_PAYMENT_OBJECTS: int = 256

T = TypeVar("T")


def compute_gas_budget(
    computation_cost: int,
    storage_cost: int,
    storage_rebate: int,
    gas_price: int,
) -> int:
    """Compute the transaction gas budget using the TS SDK formula.

    budget = max(
        computationCost + overhead,
        computationCost + overhead + storageCost - storageRebate,
    )
    where overhead = GAS_SAFE_OVERHEAD * gasPrice.

    :param computation_cost: Computation cost from simulation, in MIST
    :type computation_cost: int
    :param storage_cost: Storage cost from simulation, in MIST
    :type storage_cost: int
    :param storage_rebate: Storage rebate from simulation, in MIST
    :type storage_rebate: int
    :param gas_price: Current reference gas price
    :type gas_price: int
    :return: Gas budget in MIST
    :rtype: int
    """
    overhead = _GAS_SAFE_OVERHEAD * gas_price
    return max(
        computation_cost + overhead,
        computation_cost + overhead + storage_cost - storage_rebate,
    )


def coins_for_budget(
    coins: list[T],
    budget: int,
    balance_fn: Callable[[T], int],
    ref_fn: Callable[[T], bcs.ObjectReference],
    merge: bool = False,
) -> list[bcs.ObjectReference]:
    """Select gas coins sufficient to cover the given budget.

    Coins are sorted descending by balance and capped at 256 (protocol limit)
    before selection begins. Callers must filter out coins already present in
    the transaction's objects_in_use before calling this function.

    If a single coin covers the budget it is returned alone. If no single coin
    suffices and merge=False, raises ValueError. If merge=True, coins are
    accumulated in descending balance order until the budget is covered.

    :param coins: Available candidate gas coins (pre-filtered for conflicts)
    :type coins: list[T]
    :param budget: Required budget in MIST
    :type budget: int
    :param balance_fn: Returns the balance of a coin as int
    :type balance_fn: Callable[[T], int]
    :param ref_fn: Returns the bcs.ObjectReference for a coin
    :type ref_fn: Callable[[T], bcs.ObjectReference]
    :param merge: Allow multi-coin gas payment (gas smashing), defaults to False
    :type merge: bool
    :raises ValueError: If no single coin covers the budget and merge=False
    :raises ValueError: If total available balance is insufficient for the budget
    :return: List of ObjectReferences to use as gas payment
    :rtype: list[bcs.ObjectReference]
    """
    # Sort descending and cap at protocol limit before any selection.
    coins = sorted(coins, key=balance_fn, reverse=True)[:_MAX_GAS_PAYMENT_OBJECTS]

    single_fit = [c for c in coins if balance_fn(c) > budget]
    if single_fit:
        return [ref_fn(single_fit[0])]

    if not merge:
        raise ValueError(
            f"No single gas coin covers budget of {budget}. "
            "Set merge_gas_budget=True to allow multi-coin gas payment."
        )

    accum, selected = 0, []
    for coin in coins:
        if accum >= budget:
            break
        selected.append(coin)
        accum += balance_fn(coin)

    if accum < budget:
        raise ValueError(
            f"Total gas available {accum}, transaction requires {budget}."
        )

    return [ref_fn(c) for c in selected]
