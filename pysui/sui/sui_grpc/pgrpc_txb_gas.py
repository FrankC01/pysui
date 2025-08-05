#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


from typing import Optional, Union
from pysui.sui.sui_common.txb_signing import SignerBlock
from pysui.sui.sui_common.client import PysuiClient

# TODO: Fixup cursors for gRPC in utils
from pysui.sui.sui_grpc.pgrpc_utils import (
    async_get_all_owned_gas_objects,
    async_get_gas_objects_by_ids,
)
from pysui.sui.sui_bcs import bcs
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot
import pysui.sui.sui_grpc.pgrpc_requests as rn


def _coins_for_budget(
    coins: list[sui_prot.Object],
    budget: int,
) -> list[bcs.ObjectReference]:
    """."""
    coins.sort(key=lambda x: x.balance, reverse=True)  # type: ignore
    _coin_fit = [x for x in coins if x.balance > budget]  # type: ignore
    if _coin_fit:
        _coin_fit = [_coin_fit[0]]
    else:
        _accum: int = 0
        _accum_coin: list = []
        for _coin in coins:
            assert _coin.balance is not None
            if _accum >= budget:
                break
            else:
                _accum_coin.append(_coin)
                _accum += _coin.balance
        if _accum < budget:
            raise ValueError(
                f"Total gas available {_accum}, transaction requires {budget}"
            )
        _coin_fit = _accum_coin
    return [bcs.ObjectReference.from_grpc_ref(x) for x in _coin_fit]


async def _async_dry_run_for_budget(
    client: PysuiClient,
    sender: str,
    tx_kind: bcs.TransactionKind,
) -> int:
    """Perform a dry run when no budget specified."""
    result = await client.execute(
        request=rn.SimulateTransactionLKind(sender=sender, transaction=tx_kind)
    )
    if result.is_ok():
        return result.result_data.transaction.transaction.gas_payment.budget
    else:
        raise ValueError(f"Error running SimulateTransaction: {result.result_string}")


async def async_get_gas_data(
    *,
    signing: SignerBlock,
    client: PysuiClient,
    budget: Optional[int] = None,
    use_coins: Optional[list[Union[str, sui_prot.Object]]] = None,
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
    :type use_coins: Optional[list[Union[str, sui_prot.Object]]], optional
    :raises ValueError: If use_coins are not either strings or SuiCoinObjectGQL objects
    :raises ValueError: If not gas coins provided and none found
    :return: _description_
    :rtype: bcs.GasData
    """
    # Get available coins
    if use_coins:
        if all(isinstance(x, str) for x in use_coins):
            use_coins = await async_get_gas_objects_by_ids(client, use_coins)
        elif not all(isinstance(x, (sui_prot.Object)) for x in use_coins):
            raise ValueError("use_gas_objects must use same type.")
    else:
        use_coins = await async_get_all_owned_gas_objects(signing.payer_address, client)
    # TODO: Remove budget default when equivalent of DryRun/Simulate support TransactionKind
    # budget = budget or 1_000
    if not budget:
        budget = await _async_dry_run_for_budget(client, signing.payer_address, tx_kind)
    # Remove conflicts with objects in use
    use_coins = [x for x in use_coins if x.object_id not in objects_in_use]
    # Make sure something left to pay for
    if use_coins:
        # Return constructs for createing bcs.GasData
        return bcs.GasData(
            _coins_for_budget(use_coins, budget),
            bcs.Address.from_str(signing.payer_address),
            active_gas_price,
            budget,
        )
    raise ValueError("No coin objects found to fund transaction.")
