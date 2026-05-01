#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Protocol-agnostic gas selection and budget utilities shared across GQL and gRPC paths."""

import asyncio
from typing import Callable, Optional, TypeVar, Union

from pysui.sui.sui_bcs import bcs

# Per Mysten TS SDK: GAS_SAFE_OVERHEAD applied to every budget estimate.
_GAS_SAFE_OVERHEAD: int = 1000  # gas units (not MIST)

# Sui protocol hard limit on gas payment objects.
_MAX_GAS_PAYMENT_OBJECTS: int = 256

T = TypeVar("T")


def compute_gas_budget(
    computation_cost: int,
    storage_cost: int,
    gas_price: int,
) -> int:
    """Compute the transaction gas budget.

    Computes ``max(computationCost + overhead, computationCost + overhead + storageCost)``
    where ``overhead = GAS_SAFE_OVERHEAD * gasPrice``.

    :param computation_cost: Computation cost from simulation, in MIST
    :type computation_cost: int
    :param storage_cost: Storage cost from simulation, in MIST
    :type storage_cost: int
    :param gas_price: Current reference gas price
    :type gas_price: int
    :return: Gas budget in MIST
    :rtype: int
    """
    overhead = _GAS_SAFE_OVERHEAD * gas_price
    return max(
        computation_cost + overhead,
        computation_cost + overhead + storage_cost,
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


async def async_get_gas_data(
    *,
    signing,
    client,
    budget: Optional[int] = None,
    use_coins: Optional[list] = None,
    objects_in_use: set,
    active_gas_price: int,
    tx_kind: bcs.TransactionKind,
    merge_gas: bool = False,
    gas_source_draw: int = 0,
) -> bcs.GasData:
    """Protocol-agnostic gas selection and budget computation.

    When both use_coins and budget are None, coin fetch and simulation run in parallel.
    Dispatches via SuiCommand so the same code path runs for both GQL and gRPC clients.

    :param signing: The SignerBlock carrying sender/payer/sponsor addresses
    :param client: The protocol client (GQL or gRPC)
    :param budget: Budget override in MIST; simulated if not provided, defaults to None
    :type budget: Optional[int], optional
    :param use_coins: Gas coins to use; by-ID strings or pre-fetched Objects; fetched if None, defaults to None
    :type use_coins: Optional[list], optional
    :param objects_in_use: Coin IDs already referenced in the transaction
    :type objects_in_use: set
    :param active_gas_price: Current reference gas price
    :type active_gas_price: int
    :param tx_kind: The TransactionKind BCS
    :type tx_kind: bcs.TransactionKind
    :param merge_gas: Allow multi-coin gas payment (gas smashing), defaults to False
    :type merge_gas: bool, optional
    :param gas_source_draw: Extra MIST drawn from gas source by PTB commands, defaults to 0
    :type gas_source_draw: int, optional
    :raises ValueError: If gas coin fetch or simulation fails
    :raises ValueError: If no gas coins remain after conflict filtering
    :return: GasData BCS structure
    :rtype: bcs.GasData
    """
    from pysui.sui.sui_common import sui_commands as cmd

    async def _fetch_gas() -> list:
        """Fetch all gas coins for the payer via GetGas (auto-paged for GQL, looped for gRPC)."""
        all_objects: list = []
        gas_cmd = cmd.GetGas(owner=signing.payer_address)
        while True:
            result = await client.execute(command=gas_cmd)
            if not result.is_ok():
                raise ValueError(f"Failed to fetch gas coins: {result.result_string}")
            response = result.result_data
            all_objects.extend(response.objects)
            if response.next_page_token:
                gas_cmd = cmd.GetGas(
                    owner=signing.payer_address,
                    grpc_page_token=response.next_page_token,
                )
            else:
                break
        return all_objects

    async def _simulate_budget() -> int:
        """Simulate the transaction to determine gas budget."""
        tx_meta: dict = {"sender": signing.sender_str, "gasPrice": active_gas_price}
        if signing.sponsor_str:
            tx_meta["gasSponsor"] = signing.sponsor_str
        result = await client.execute(
            command=cmd.SimulateTransactionKind(
                tx_kind=tx_kind,
                tx_meta=tx_meta,
            )
        )
        if not result.is_ok():
            raise ValueError(f"Error running SimulateTransactionKind: {result.result_string}")
        gas_used = result.result_data.transaction.effects.gas_used
        return compute_gas_budget(
            gas_used.computation_cost or 0,
            gas_used.storage_cost or 0,
            active_gas_price,
        )

    # Resolve coin list and budget — parallel when both are unspecified.
    if use_coins is None and budget is None:
        use_coins, budget = await asyncio.gather(_fetch_gas(), _simulate_budget())
    elif use_coins is None:
        use_coins = await _fetch_gas()
    elif budget is None:
        if use_coins and all(isinstance(x, str) for x in use_coins):
            # String IDs: fetch all gas coins then filter to the requested subset.
            all_gas = await _fetch_gas()
            requested = set(use_coins)
            use_coins = [x for x in all_gas if x.object_id in requested]
        budget = await _simulate_budget()
    else:
        if use_coins and all(isinstance(x, str) for x in use_coins):
            all_gas = await _fetch_gas()
            requested = set(use_coins)
            use_coins = [x for x in all_gas if x.object_id in requested]

    required = budget + gas_source_draw

    use_coins = [x for x in use_coins if x.object_id not in objects_in_use]
    if not use_coins:
        raise ValueError("No coin objects found to fund transaction.")

    return bcs.GasData(
        coins_for_budget(
            use_coins,
            required,
            balance_fn=lambda x: x.balance or 0,
            ref_fn=bcs.ObjectReference.from_grpc_ref,
            merge=merge_gas,
        ),
        bcs.Address.from_str(signing.payer_address),
        active_gas_price,
        required,
    )
