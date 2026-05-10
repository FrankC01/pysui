#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Async cache mimmicing funtools @cache."""

import asyncio
import logging
from enum import IntEnum
from collections import OrderedDict
from typing import Any, Coroutine, Optional, cast


logger = logging.getLogger("async_funcs")
import pysui.sui.sui_bcs.bcs_txne as bcst
import pysui.sui.sui_common.sui_commands as cmd
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
            """Async wrapper that returns cached results when available."""
            key = KEY(args, kwargs)
            if key in self.lru and use_cache:
                return self.lru[key]
            else:
                self.lru[key] = await func(*args, **kwargs)
                return self.lru[key]

        wrapper.__name__ += func.__name__
        wrapper.__dict__["cache_clear"] = self.cache_clear

        return wrapper


class OperationStatus(IntEnum):
    """Result status for coin merge/splay operations."""

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
) -> Coroutine[Any, Any, tuple[OperationStatus, Any, str, Any]]:
    """Merge all Sui coins for a given address.

    :param client: Sui node client (GqlProtocolClient or GrpcProtocolClient)
    :type client: Any
    :param address: address of gas owner whose coins to merge
    :type address: str
    :param merge_only: restrict merge to these coin object IDs, defaults to None
    :type merge_only: Optional[list[str]], optional
    :param exclude: coin object IDs to exclude from merge, defaults to None
    :type exclude: Optional[list[str]], optional
    :param wait: wait for transaction finality, defaults to False
    :type wait: Optional[bool], optional
    :raises ValueError: address has no sui coins at all
    :raises ValueError: address has no mergeable coins
    :raises ValueError: transaction failure
    :return: (status, effects, gas_coin_id, exec_result)
    :rtype: Coroutine[Any, Any, tuple[OperationStatus, Any, str, Any]]
    """
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

    in_use: list[str] = exclude or []
    merge_only_ids: set[str] = set(merge_only or [])

    # Fetch all gas coins across all pages for both protocols
    gas_result = await client.execute_for_all(command=cmd.GetGas(owner=address))
    if not gas_result.is_ok():
        raise ValueError(f"GetGas failed for {address}: {gas_result.result_string}")
    response = gas_result.result_data
    # Both GQL and gRPC return ListOwnedObjectsResponse (.objects) with sui_prot.Object items
    raw_coins = list(getattr(response, "objects", None) or [])

    if not raw_coins:
        raise ValueError(f"Address {address} has no gas coins")
    logger.debug(f"{len(raw_coins)} found for {address}")

    # Normalize to (id, balance) for protocol-neutral filtering and sorting
    # Both SuiCoinObjectGQL (.object_id property) and sui_prot.Object (.object_id) work
    coin_data: list[tuple[str, int]] = [
        (c.object_id, int(c.balance or 0)) for c in raw_coins
    ]

    if in_use:
        coin_data = [(cid, bal) for cid, bal in coin_data if cid not in in_use]
    if merge_only_ids:
        coin_data = [(cid, bal) for cid, bal in coin_data if cid in merge_only_ids]

    if not coin_data:
        logger.debug(f"Address {address} has no mergeable coins")
        raise ValueError(f"Address {address} has no mergeable coins")

    if len(coin_data) == 1:
        ret_id = coin_data[0][0]
        logger.debug(f"Address {address} already has only 1 coin, returning {ret_id}")
        return (OperationStatus.ONE_COIN_NO_MERGE, None, ret_id, None)

    coin_data.sort(key=lambda x: x[1], reverse=True)
    use_as_gas_id = coin_data.pop(0)[0]
    merge_from_ids = [cid for cid, _ in coin_data]
    logger.debug(f"{len(merge_from_ids)} coins merging to {use_as_gas_id}")

    tx: AsyncSuiTransaction = await client.transaction()
    await tx.merge_coins(merge_to=tx.gas, merge_from=merge_from_ids)
    res = await client.execute(
        command=cmd.ExecuteTransaction(
            **await tx.build_and_sign(use_gas_objects=[use_as_gas_id])
        )
    )
    if res.is_err():
        logger.warning(f"merge_all_sui transaction failed {res.result_string}")
        raise ValueError(f"Failed smashing coins with {res.result_string}")

    # res.result_data is sui_prot.ExecutedTransaction for both GQL and gRPC
    etxn = res.result_data
    tx_effects = bcst.TransactionEffects.deserialize(
        etxn.effects.bcs.value  # bytes; decoded from base64 by GQL encode_fn or raw gRPC
    ).value

    if tx_effects.status.enum_name != "Success":
        logger.debug(f"Merge gas failed {tx_effects.status.to_json(indent=2)}")
        return (OperationStatus.OPS_FAIL, tx_effects, use_as_gas_id, None)

    if wait:
        wait_res: SuiRpcResult = await client.wait_for_transaction(digest=etxn.digest)
        if wait_res.is_err():
            raise ValueError(f"Merge transaction `{etxn.digest}` failed.")
        return (OperationStatus.MERGE, tx_effects, use_as_gas_id, wait_res.result_data)

    logger.debug(f"Merge gas returning {use_as_gas_id}")
    return (OperationStatus.MERGE, tx_effects, use_as_gas_id, None)


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
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction  # noqa: F401

    # Merge the gas available to address
    merge_tuple: Any = await asyncio.gather(
        merge_sui(
            client=client, address=address, merge_only=merge_only, exclude=exclude
        ),
        return_exceptions=True,
    )
    if isinstance(merge_tuple[0], tuple):
        merge_status, effects, mcoin_id, _mexec = cast(
            tuple[OperationStatus, Any, str, Any],
            merge_tuple,
        )
        # We have a mergable coin
        if merge_status == OperationStatus.ONE_COIN_NO_MERGE or (
            merge_status == OperationStatus.MERGE
            and effects.status.enum_name != "Success"
        ):
            logger.debug(f"Have coin to splay {mcoin_id}")

    else:
        raise merge_tuple[0]
