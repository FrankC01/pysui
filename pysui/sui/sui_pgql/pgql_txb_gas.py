#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

import asyncio
import base64
from typing import Optional, Union
from pysui.sui.sui_common.txb_signing import SignerBlock
from pysui.sui.sui_common.client import PysuiClient
from pysui.sui.sui_common.txb_gas import coins_for_budget, compute_gas_budget

import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_gas_objects,
    async_get_gas_objects_by_ids,
    get_all_owned_gas_objects,
    get_gas_objects_by_ids,
)
from pysui.sui.sui_bcs import bcs


def _dry_run_for_budget(
    signing: SignerBlock,
    client: PysuiClient,
    tx_bytes: bcs.TransactionKind,
    active_gas_price: int,
) -> int:
    """Perform a dry run when no budget specified."""
    query = qn.DryRunTransactionKind(
        tx_kind=tx_bytes,
        tx_meta={
            "sender": signing.sender_str,
            "gasPrice": active_gas_price,
            "gasSponsor": signing.sponsor_str,
        },
        skip_checks=False,
    )
    # print(client.query_node_to_string(query_node=query))
    result = client.execute_query_node(with_node=query)

    if result.is_ok():
        c_cost: int = int(
            result.result_data.transaction_block.gas_effects["gasSummary"][
                "computationCost"
            ]
        )
        s_cost: int = int(
            result.result_data.transaction_block.gas_effects["gasSummary"][
                "storageCost"
            ]
        )
        return c_cost + s_cost
    else:
        raise ValueError(f"Error running DryRunTransactionKind: {result.result_string}")




def get_gas_data(
    *,
    signing: SignerBlock,
    client: PysuiClient,
    budget: Optional[int] = None,
    use_coins: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
    objects_in_use: set[str],
    active_gas_price: int,
    tx_kind: bcs.TransactionKind,
) -> bcs.GasData:
    """get_gas_data Builds the GasData BCS structure for the transaction data.

    :param signing: The GraphQL SigningBlock
    :type signing: SignerBlock
    :param client: The GraphQL Client
    :type client: BaseSuiGQLClient
    :param objects_in_use: Objects already identified as 'in-use' in the builder
    :type objects_in_use: set[str]
    :param active_gas_price: Current Gas Price
    :type active_gas_price: int
    :param tx_kind: The TransactionKind BCS
    :type tx_kind: bcs.TransactionKind
    :param budget: Option budget to set for transaction, defaults to None
    :type budget: Optional[int], optional
    :param use_coins: Gas coins to use for paying transactions, defaults to None
    :type use_coins: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
    :raises ValueError: If use_coins are not either strings or SuiCoinObjectGQL objects
    :raises ValueError: If not gas coins provided and none found
    :return: _description_
    :rtype: bcs.GasData
    """
    # Get available coins
    if use_coins:
        if all(isinstance(x, str) for x in use_coins):
            use_coins = get_gas_objects_by_ids(client, use_coins)
        elif not all(isinstance(x, pgql_type.SuiCoinObjectGQL) for x in use_coins):
            raise ValueError("use_gas_objects must use same type.")
    else:
        use_coins = get_all_owned_gas_objects(signing.payer_address, client)
    if not budget:
        budget = _dry_run_for_budget(
            signing,
            client,
            tx_kind,
            # base64.b64encode(tx_kind.serialize()).decode(),
            active_gas_price,
        )
    # Remove conflicts with objects in use
    use_coins = [x for x in use_coins if x.coin_object_id not in objects_in_use]
    # Make sure something left to pay for
    if use_coins:
        # Return constructs for createing bcs.GasData
        return bcs.GasData(
            coins_for_budget(
                use_coins,
                budget,
                balance_fn=lambda x: int(x.balance),
                ref_fn=bcs.ObjectReference.from_gql_ref,
            ),
            bcs.Address.from_str(signing.payer_address),
            active_gas_price,
            budget,
        )
    raise ValueError("No coin objects found to fund transaction.")


async def _async_dry_run_for_budget(
    signing: SignerBlock,
    client: PysuiClient,
    tx_bytes: bcs.TransactionKind,
    active_gas_price: int,
) -> int:
    """Simulate the transaction to determine the gas budget."""
    result = await client.execute_query_node(
        with_node=qn.SimulateTransactionKind(
            tx_kind=tx_bytes,
            tx_meta={
                "sender": signing.sender_str,
                "gasPrice": active_gas_price,
                "gasSponsor": signing.sponsor_str,
            },
        )
    )
    if result.is_ok():
        summary = result.result_data.transaction_block.gas_effects["gasSummary"]
        return compute_gas_budget(
            int(summary["computationCost"]),
            int(summary["storageCost"]),
            int(summary.get("storageRebate", 0)),
            active_gas_price,
        )
    raise ValueError(f"Error running SimulateTransactionKind: {result.result_string}")


async def async_get_gas_data(
    *,
    signing: SignerBlock,
    client: PysuiClient,
    budget: Optional[int] = None,
    use_coins: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]] = None,
    objects_in_use: set[str],
    active_gas_price: int,
    tx_kind: bcs.TransactionKind,
    merge_gas: bool = False,
    gas_source_draw: int = 0,
) -> bcs.GasData:
    """async_get_gas_data Builds the GasData BCS structure for the transaction data.

    When both use_coins and budget are None, coin fetch and simulation run in parallel.

    :param signing: The GraphQL SigningBlock
    :type signing: SignerBlock
    :param client: The GraphQL Client
    :type client: BaseSuiGQLClient
    :param objects_in_use: Coin IDs already in use in the transaction (pre-filtered before calling)
    :type objects_in_use: set[str]
    :param active_gas_price: Current reference gas price
    :type active_gas_price: int
    :param tx_kind: The TransactionKind BCS
    :type tx_kind: bcs.TransactionKind
    :param budget: Budget override; simulated if not provided, defaults to None
    :type budget: Optional[int], optional
    :param use_coins: Gas coins to use; fetched from payer if not provided, defaults to None
    :type use_coins: Optional[list[Union[str, pgql_type.SuiCoinObjectGQL]]], optional
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
            _async_dry_run_for_budget(signing, client, tx_kind, active_gas_price),
        )
    elif use_coins is None:
        use_coins = await async_get_all_owned_gas_objects(signing.payer_address, client)
    elif budget is None:
        if all(isinstance(x, str) for x in use_coins):
            use_coins = await async_get_gas_objects_by_ids(client, use_coins)
        elif not all(
            isinstance(
                x, (pgql_type.SuiCoinObjectGQL, pgql_type.SuiCoinObjectSummaryGQL)
            )
            for x in use_coins
        ):
            raise ValueError("use_gas_objects must use same type.")
        budget = await _async_dry_run_for_budget(signing, client, tx_kind, active_gas_price)
    else:
        if all(isinstance(x, str) for x in use_coins):
            use_coins = await async_get_gas_objects_by_ids(client, use_coins)
        elif not all(
            isinstance(
                x, (pgql_type.SuiCoinObjectGQL, pgql_type.SuiCoinObjectSummaryGQL)
            )
            for x in use_coins
        ):
            raise ValueError("use_gas_objects must use same type.")

    # Total required = budget + any amounts drawn from gas source by PTB commands (UC12)
    required = budget + gas_source_draw

    # Filter out coins already used in the transaction (callers' pre-condition; filter again as safety)
    use_coins = [x for x in use_coins if x.coin_object_id not in objects_in_use]

    if not use_coins:
        raise ValueError("No coin objects found to fund transaction.")

    return bcs.GasData(
        coins_for_budget(
            use_coins,
            required,
            balance_fn=lambda x: int(x.balance),
            ref_fn=bcs.ObjectReference.from_gql_ref,
            merge=merge_gas,
        ),
        bcs.Address.from_str(signing.payer_address),
        active_gas_price,
        required,
    )
