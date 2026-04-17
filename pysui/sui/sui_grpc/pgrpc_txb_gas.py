#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


import asyncio
from typing import Optional, Union
from pysui.sui.sui_common.txb_signing import SignerBlock
from pysui.sui.sui_common.client import PysuiClient
from pysui.sui.sui_common.txb_gas import coins_for_budget, compute_gas_budget

from pysui.sui.sui_grpc.pgrpc_utils import (
    async_get_all_owned_gas_objects,
    async_get_gas_objects_by_ids,
)
from pysui.sui.sui_bcs import bcs

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_grpc.pgrpc_requests as rn


async def _async_dry_run_for_budget(
    client: PysuiClient,
    sender: str,
    tx_kind: bcs.TransactionKind,
    active_gas_price: int,
) -> int:
    """Simulate the transaction to determine the gas budget."""
    result = await client.execute(
        request=rn.SimulateTransactionKind(sender=sender, transaction=tx_kind)
    )
    if result.is_ok():
        gas_used = result.result_data.transaction.effects.gas_used
        return compute_gas_budget(
            gas_used.computation_cost or 0,
            gas_used.storage_cost or 0,
            gas_used.storage_rebate or 0,
            active_gas_price,
        )
    raise ValueError(f"Error running SimulateTransactionKind: {result.result_string}")


async def async_get_gas_data(
    *,
    signing: SignerBlock,
    client: PysuiClient,
    budget: Optional[int] = None,
    use_coins: Optional[list[Union[str, sui_prot.Object]]] = None,
    objects_in_use: set[str],
    active_gas_price: int,
    tx_kind: bcs.TransactionKind,
    merge_gas: bool = False,
    gas_source_draw: int = 0,
) -> bcs.GasData:
    """async_get_gas_data Builds the GasData BCS structure for the transaction data.

    When both use_coins and budget are None, coin fetch and simulation run in parallel.

    :param signing: The gRPC SigningBlock
    :type signing: SignerBlock
    :param client: The gRPC Client
    :type client: PysuiClient
    :param objects_in_use: Coin IDs already in use in the transaction (pre-filtered before calling)
    :type objects_in_use: set[str]
    :param active_gas_price: Current reference gas price
    :type active_gas_price: int
    :param tx_kind: The TransactionKind BCS
    :type tx_kind: bcs.TransactionKind
    :param budget: Budget override; simulated if not provided, defaults to None
    :type budget: Optional[int], optional
    :param use_coins: Gas coins to use; fetched from payer if not provided, defaults to None
    :type use_coins: Optional[list[Union[str, sui_prot.Object]]], optional
    :param merge_gas: Allow multi-coin gas payment (gas smashing), defaults to False
    :type merge_gas: bool, optional
    :param gas_source_draw: Extra MIST drawn from gas source by PTB commands, defaults to 0
    :type gas_source_draw: int, optional
    :raises ValueError: If use_coins contains mixed types
    :raises ValueError: If no gas coins remain after conflict filtering
    :return: GasData BCS structure
    :rtype: bcs.GasData
    """
    # Resolve coin list and budget — parallel when both are unspecified (UC1/UC5)
    if use_coins is None and budget is None:
        use_coins, budget = await asyncio.gather(
            async_get_all_owned_gas_objects(signing.payer_address, client),
            _async_dry_run_for_budget(client, signing.payer_address, tx_kind, active_gas_price),
        )
    elif use_coins is None:
        use_coins = await async_get_all_owned_gas_objects(signing.payer_address, client)
    elif budget is None:
        if all(isinstance(x, str) for x in use_coins):
            use_coins = await async_get_gas_objects_by_ids(client, use_coins)
        elif not all(isinstance(x, sui_prot.Object) for x in use_coins):
            raise ValueError("use_gas_objects must use same type.")
        budget = await _async_dry_run_for_budget(
            client, signing.payer_address, tx_kind, active_gas_price
        )
    else:
        if all(isinstance(x, str) for x in use_coins):
            use_coins = await async_get_gas_objects_by_ids(client, use_coins)
        elif not all(isinstance(x, sui_prot.Object) for x in use_coins):
            raise ValueError("use_gas_objects must use same type.")

    # Total required = budget + any amounts drawn from gas source by PTB commands (UC12)
    required = budget + gas_source_draw

    # Filter out coins already used in the transaction
    use_coins = [x for x in use_coins if x.object_id not in objects_in_use]

    if not use_coins:
        raise ValueError("No coin objects found to fund transaction.")

    return bcs.GasData(
        coins_for_budget(
            use_coins,
            required,
            balance_fn=lambda x: x.balance,
            ref_fn=bcs.ObjectReference.from_grpc_ref,
            merge=merge_gas,
        ),
        bcs.Address.from_str(signing.payer_address),
        active_gas_price,
        required,
    )
