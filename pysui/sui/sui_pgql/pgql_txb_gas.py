#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from typing import Optional, Union
from pysui.sui.sui_common.txb_signing import SignerBlock
from pysui.sui.sui_common.client import PysuiClient
from pysui.sui.sui_common.txb_gas import coins_for_budget, compute_gas_budget

import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn
from pysui.sui.sui_pgql.pgql_utils import (
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


