#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Collection of reusable functions."""

from typing import Optional, Callable, ParamSpec
from functools import partial
from pysui.sui.sui_pgql.pgql_clients import BaseSuiGQLClient
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn

_P = ParamSpec("P")


def active_types_only(
    objects: list[pgql_type.PGQL_Type],
) -> list[pgql_type.PGQL_Type]:
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


def sync_cursored_collector(
    pfn: Callable[_P, list],
    client: BaseSuiGQLClient,
    only_active: Optional[bool] = True,
) -> list:
    """Synchronous: Handles paging for any query type that return a 'data' list and cursor.

    :param pfn: Partial function that takes keyword argument of `next_page` and returns a list
    :type pfn: Callable[_P, list]
    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: A list of results
    :rtype: list
    """
    collection = list = []
    result = client.execute_query_node(with_node=pfn())
    while True:
        if result.is_ok():
            collection.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = client.execute_query_node(
                    with_node=pfn(next_page=result.result_data.next_cursor)
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")

    return collection


async def async_cursored_collector(
    pfn: Callable[_P, list],
    client: BaseSuiGQLClient,
    only_active: Optional[bool] = True,
) -> list:
    """Handles paging for any query type that return a 'data' list and cursor.

    :param pfn: Partial function that takes keyword argument of `next_page` and returns a list
    :type pfn: Callable[_P, list]
    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: A list of results
    :rtype: list
    """
    collection = list = []
    result = await client.execute_query_node(with_node=pfn())
    while True:
        if result.is_ok():
            collection.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = await client.execute_query_node(
                    with_node=pfn(next_page=result.result_data.next_cursor)
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")

    return collection


def get_all_owned_gas_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Synchronous: Retrieves list of all gas objects details for owner.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param owner: The owner address id
    :type owner: str
    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: List of active SuiCoin objects
    :rtype: list[pgql_type.SuiCoinObjectGQL]
    """
    return sync_cursored_collector(
        partial(qn.GetCoins, owner=owner), client, only_active
    )


def get_all_owned_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.ObjectReadGQL]:
    """Synchronous: Retrieves list of all object details for owner.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param owner: The owner address id
    :type owner: str
    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: List of address owned objects
    :rtype: list[pgql_type.ObjectReadGQL]
    """
    return sync_cursored_collector(
        partial(qn.GetObjectsOwnedByAddress, owner=owner), client, only_active
    )


def get_gas_objects_by_ids(
    client: BaseSuiGQLClient, gas_ids: list[str], only_active: Optional[bool] = True
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Synchronous: Retrieves list of all gas objects details from object id strs.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param gas_ids: List of well formed object ids
    :type gas_ids: list[str]
    :param only_active: Flag indicating return only active coins
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active SuiCoin objects
    :rtype: list[pgql_type.SuiCoinObjectGQL]
    """
    return sync_cursored_collector(
        partial(qn.GetMultipleGasObjects, coin_object_ids=gas_ids), client, only_active
    )


def get_objects_by_ids(
    client: BaseSuiGQLClient, object_ids: list[str], only_active: Optional[bool] = True
) -> list[pgql_type.ObjectReadGQL]:
    """Synchronous: Retrieves list of all objects details from object id strs.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param object_ids: List of well formed object ids
    :type object_ids: list[str]
    :param only_active: Flag indicating return only active objects
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active objects
    :rtype: list[pgql_type.ObjectReadGQL]
    """
    return sync_cursored_collector(
        partial(qn.GetMultipleObjects, object_ids=object_ids), only_active
    )


async def async_get_all_owned_gas_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Asynchronous: Retrieves list of all gas objects details for owner.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param owner: The owner address id
    :type owner: str
    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param only_active: Flag indicating return only active coins
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active SuiCoin objects
    :rtype: list[pgql_type.SuiCoinObjectGQL]
    """
    return await async_cursored_collector(
        partial(qn.GetCoins, owner=owner), client, only_active
    )


async def async_get_all_owned_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.ObjectReadGQL]:
    """Asynchronous: Retrieves list of all object details for owner.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param owner: The owner address id
    :type owner: str
    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param only_active: Flag indicating return only active, defaults to True
    :type only_active: Optional[bool], optional
    :raises ValueError: If the query fails
    :return: List of address owned objects
    :rtype: list[pgql_type.ObjectReadGQL]
    """
    return await async_cursored_collector(
        partial(qn.GetObjectsOwnedByAddress, owner=owner), client, only_active
    )


async def async_get_gas_objects_by_ids(
    client: BaseSuiGQLClient, gas_ids: list[str], only_active: Optional[bool] = True
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Asynchronous: Retrieves list of all gas objects details from object id strs.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param gas_ids: List of well formed object ids
    :type gas_ids: list[str]
    :param only_active: Flag indicating return only active coins
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active SuiCoin objects
    :rtype: list[pgql_type.SuiCoinObjectGQL]
    """
    return await async_cursored_collector(
        partial(qn.GetMultipleGasObjects, coin_object_ids=gas_ids), client, only_active
    )


async def async_get_objects_by_ids(
    client: BaseSuiGQLClient, object_ids: list[str], only_active: Optional[bool] = True
) -> list[pgql_type.ObjectReadGQL]:
    """Asynchronous: Retrieves list of all objects details from object id strs.

    Uses cursor to ensure all asked for are retrieved from graph node and
    only returns those that are not deleted or pruned.

    :param client: The GraphQL client
    :type client: BaseSuiGQLClient
    :param object_ids: List of well formed object ids
    :type object_ids: list[str]
    :param only_active: Flag indicating return only active objects
    :type only_active: bool, optional defaults to True
    :raises ValueError: If the query fails
    :return: List of active objects
    :rtype: list[pgql_type.ObjectReadGQL]
    """
    return await async_cursored_collector(
        partial(qn.GetMultipleObjects, object_ids=object_ids), only_active
    )
