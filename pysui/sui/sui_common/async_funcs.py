#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Async cache mimmicing funtools @cache."""

import asyncio
import base64
import logging
from enum import IntEnum
from collections import OrderedDict
from typing import Any, Coroutine, Optional, cast

logger = logging.getLogger("async_funcs")

import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_types.bcs_txne as bcst
from pysui import SuiRpcResult


class KEY:
    """Key class management for LRU"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        kwargs.pop("use_cache", None)

    def __eq__(self, obj):
        return hash(self) == hash(obj)

    def __hash__(self):
        def _hash(param: Any):
            if isinstance(param, tuple):
                return tuple(map(_hash, param))
            if isinstance(param, dict):
                return tuple(map(_hash, param.items()))
            elif hasattr(param, "__dict__"):
                return str(vars(param))
            else:
                return str(param)

        return hash(_hash(self.args) + _hash(self.kwargs))


class LRU(OrderedDict):
    """Cache repository management."""

    def __init__(self, maxsize, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.maxsize and len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


class AsyncLRU:
    """Decorator."""

    def __init__(self, maxsize=128):
        """
        :param maxsize: Use maxsize as None for unlimited size cache
        """
        self.lru = LRU(maxsize=maxsize)

    def cache_clear(self):
        """
        Clears the LRU cache.

        This method empties the cache, removing all stored
        entries and effectively resetting the cache.

        :return: None
        """
        self.lru.clear()

    def __call__(self, func):
        async def wrapper(*args, use_cache=True, **kwargs):
            key = KEY(args, kwargs)
            if key in self.lru and use_cache:
                return self.lru[key]
            else:
                self.lru[key] = await func(*args, **kwargs)
                return self.lru[key]

        wrapper.__name__ += func.__name__
        wrapper.__dict__["cache_clear"] = self.cache_clear

        return wrapper


async def get_all_sui(
    *,
    client: Any,
    gas_owner: str,
) -> Coroutine[Any, Any, list[pgql_type.SuiCoinObjectGQL]]:
    """Fetch owner Sui coins

    :raises ValueError: If fetch error
    :return: list of ptypes.SuiCoinObjectGQL
    :rtype: Coroutine[Any, Any, list[pgql_type.SuiCoinObjectGQL]]]
    """

    all_coins: list[pgql_type.SuiCoinObjectGQL] = []

    result = await client.execute_query_node(with_node=qn.GetCoins(owner=gas_owner))
    while result.is_ok():
        all_coins.extend(result.result_data.data)
        if result.result_data.next_cursor.hasNextPage:
            result = await client.execute_query_node(
                with_node=qn.GetCoins(
                    owner=gas_owner,
                    next_page=result.result_data.next_cursor,
                )
            )
        else:
            break
    logger.debug(f"fetching all coins result {len(all_coins)}")
    return all_coins


class OperationStatus(IntEnum):
    OPS_FAIL = 0
    ONE_COIN_NO_MERGE = 1
    MERGE = 2
    MERGE_AND_SPLAY = 3


async def merge_sui(
    *,
    client: Any,
    address: str,
    merge_only: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    wait: Optional[bool] = False,
) -> Coroutine[
    Any,
    Any,
    tuple[
        OperationStatus,
        bcst.TransactionEffects,
        pgql_type.SuiCoinObjectGQL,
        pgql_type.TransactionResultGQL,
    ],
]:
    """merge_all Sui coins for a given address.

    :param client: Sui node client
    :type client: AsyncSuiGQLClient
    :param address: address of gas owner whose coins to merge
    :type address: str
    :param exclude: list of sui coin object ids to exclude from merge, defaults to None
    :type exclude: Optional[list[str]], optional
    :raises ValueError: address has no sui coins at all
    :raises ValueError: address has no mergeable coins
    :raises ValueError: transaction failure
    :return: The uncommitted transaction effects and Sui coin merged into
    :rtype: Coroutine[Any, Any, tuple[OperationStatus,bcst.TransactionEffects, pgql_type.SuiCoinObjectGQL]]
    """
    from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction

    # Get object references
    in_use: list[str] = exclude or []
    merge_only: list[str] = merge_only or []

    # Get all gas
    coin_list: list[pgql_type.SuiCoinObjectGQL] = await get_all_sui(
        client=client, gas_owner=address
    )
    if not coin_list:
        raise ValueError(f"Address {address} has no gas coins")
    else:
        logger.debug(f"{len(coin_list)} found for {address}")
    # Eliminate in use if provided
    if in_use:
        coin_list[:] = [coin for coin in coin_list if coin.coin_object_id not in in_use]
    # Use explicit list of coin ids if provided
    if merge_only:
        coin_list[:] = [coin for coin in coin_list if coin.coin_object_id in merge_only]

    # If noting available, throw exception
    if not coin_list:
        logger.debug(f"Address {address} has no mergeable coins")
        raise ValueError(f"Address {address} has no mergeable coins")
    # If one return it
    if len(coin_list) == 1:
        ret_coin = coin_list[0]
        logger.debug(
            f"Address {address} already has only 1 coin, returning {ret_coin.coin_object_id}"
        )
        return (OperationStatus.ONE_COIN_NO_MERGE, None, ret_coin, None)
    # Otherwise smash lowest to highesst and return it
    coin_list.sort(key=lambda x: int(x.balance), reverse=True)

    tx = AsyncSuiTransaction(client=client)

    use_as_gas = coin_list.pop(0)
    logger.debug(f"{len(coin_list)} coins merging to {use_as_gas.coin_object_id}")
    await tx.merge_coins(merge_to=tx.gas, merge_from=coin_list)
    res = await client.execute_query_node(
        with_node=qn.ExecuteTransaction(
            **await tx.build_and_sign(use_gas_objects=[use_as_gas])
        )
    )
    if res.is_err():
        logger.warn(f"merge_all_sui transaction failed {res.result_string}")
        raise ValueError(f"Failed smashing coins with {res.result_string}")

    # Deserialize tx effects and get updated gas coin information
    tx_effects = bcst.TransactionEffects.deserialize(
        base64.b64decode(res.result_data.bcs)
    ).value
    # If failed, stop ops
    if tx_effects.status.enum_name != "Success":
        logger.debug(f"Merge gas failed {tx_effects.ExecutionStatus.to_json(indent=2)}")
        return (OperationStatus.OPS_FAIL, tx_effects, use_as_gas, None)

    if wait:
        res: SuiRpcResult = await client.wait_for_transaction(
            digest=tx_effects.transactionDigest.to_digest_str()
        )
        if res.is_err():
            raise ValueError(f"Merge transaction `{res.result_data.digest}` failed.")
        return (OperationStatus.MERGE, tx_effects, use_as_gas, res.result_data)

    logger.debug(f"Merge gas returning {use_as_gas.coin_object_id}")
    return (OperationStatus.MERGE, tx_effects, use_as_gas, None)


async def split_to_distribution(
    *,
    client: Any,
    address: str,
    send_to: list[str],
    merge_only: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    wait: Optional[bool] = False,
):
    """."""
    from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction

    # Merge the gas available to address
    merge_tuple: pgql_type.SuiCoinObjectGQL = await asyncio.gather(
        merge_sui(
            client=client, address=address, merge_only=merge_only, exclude=exclude
        ),
        return_exceptions=True,
    )
    if isinstance(merge_tuple[0], tuple):
        merge_status, effects, mcoin, _mexec = cast(
            tuple[
                OperationStatus,
                bcst.TransactionEffects,
                pgql_type.SuiCoinObjectGQL,
                pgql_type.TransactionResultGQL,
            ],
            merge_tuple,
        )
        # We have a mergable coin
        if merge_status == OperationStatus.ONE_COIN_NO_MERGE or (
            merge_status == OperationStatus.MERGE
            and effects.status.enum_name != "Success"
        ):
            logger.debug(f"Have coin to splay{mcoin.coin_object_id}")
            tx = AsyncSuiTransaction(client=client)

    else:
        raise merge_tuple[0]
