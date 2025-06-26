#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Collection of reusable functions."""

from typing import Optional, Callable, ParamSpec
from functools import partial
from pysui.sui.sui_common.client import PysuiClient
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta as v2base
import pysui.sui.sui_grpc.pgrpc_requests as rn

_P = ParamSpec("P")


def active_types_only(
    objects: list[v2base.Object],
) -> list[v2base.Object]:
    """Attempts to Filter out objects that have been pruned or deleted.

    :param objects: Homogenous list of objects
    :type objects: list[pgql_type.PGQL_Type]
    :return: List of objects
    :rtype: list[pgql_type.PGQL_Type]
    """
    if objects:
        if x := next(filter(lambda x: x is not None, objects), False):
            if hasattr(x, "previous_transaction"):
                return [x for x in objects if x and x.previous_transaction]
            elif hasattr(x, "previous_transaction_digest"):
                return [x for x in objects if x and x.previous_transaction_digest]
    return objects


async def async_cursored_collector(
    pfn: Callable[_P, list],
    client: PysuiClient,
    only_active: Optional[bool] = True,
) -> list:
    """Handles paging for any query type that return a 'data' list and cursor.

    :param pfn: Partial function that takes keyword argument of `page_token` and returns a list
    :type pfn: Callable[_P, list]
    :param client: The gRPC client
    :type client: PysuiClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: A list of results
    :rtype: list
    """
    collection = list = []
    result = await client.execute(request=pfn())
    while True:
        if result.is_ok():
            collection.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.page_token:
                result = await client.execute_query_node(
                    with_node=pfn(page_token=result.result_data.page_token)
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")

    return collection


async def async_get_all_owned_gas_objects(
    owner: str, client: PysuiClient, only_active: Optional[bool] = True
) -> list[v2base.Object]:
    """Asynchronous: Retrieves list of all gas objects details for owner.

    Uses cursor to ensure all asked for are retrieved from gRPC node and
    only returns those that are not deleted or pruned.

    :param owner: The owner address id
    :type owner: str
    :param client: The gRPC client
    :type client: PysuiClient
    :param only_active: Flag indicating return only active coins
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active SuiCoin objects
    :rtype: list[v2base.Object]
    """
    return await async_cursored_collector(
        partial(rn.GetGas, owner=owner), client, only_active
    )


async def async_get_all_owned_objects(
    owner: str, client: PysuiClient, only_active: Optional[bool] = True
) -> list[v2base.Object]:
    """Asynchronous: Retrieves list of all object details for owner.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param owner: The owner address id
    :type owner: str
    :param client: The gRPC client
    :type client: PysuiClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: List of address owned objects
    :rtype: list[v2base.Object]
    """
    return await async_cursored_collector(
        partial(rn.GetOwnedObjects, owner=owner), client, only_active
    )


async def async_get_gas_objects_by_ids(
    client: PysuiClient, gas_ids: list[str], only_active: Optional[bool] = True
) -> list[v2base.Object]:
    """Asynchronous: Retrieves list of all gas objects details from object id strs.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param client: The gRPC client
    :type client: PysuiClient
    :param gas_ids: List of well formed object ids
    :type gas_ids: list[str]
    :param only_active: Flag indicating return only active coins
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active SuiCoin objects
    :rtype: list[v2base.Object]
    """
    # TODO: This call has no pagination, need to get max id constraint
    # and perform looped fetch
    # Also need to filter for coins only
    return await async_cursored_collector(
        partial(rn.GetMultipleObjects, object_ids=gas_ids), client, only_active
    )


async def async_get_objects_by_ids(
    client: PysuiClient, object_ids: list[str], only_active: Optional[bool] = True
) -> list[v2base.Object]:
    """Asynchronous: Retrieves list of all objects details from object id strs.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param client: The gRPC client
    :type client: PysuiClient
    :param object_ids: List of well formed object ids
    :type object_ids: list[str]
    :param only_active: Flag indicating return only active objects
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active objects
    :rtype: list[v2base.Object]
    """
    # TODO: This call has no pagination, need to get max id constraint
    # and perform looped fetch
    return await async_cursored_collector(
        partial(rn.GetMultipleObjects, object_ids=object_ids), only_active
    )
