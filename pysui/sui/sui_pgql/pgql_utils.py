#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Collection of reusable functions."""

from typing import Optional
from pysui.sui.sui_pgql.pgql_clients import BaseSuiGQLClient
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn


def active_types_only(
    objects: list[pgql_type.SuiCoinObjectGQL] | list[pgql_type.ObjectReadGQL],
) -> list[pgql_type.SuiCoinObjectGQL] | list[pgql_type.ObjectReadGQL]:
    """Filters out any objects that are pruned or deleted.

    :param coins: List of coins or generic objects
    :type coins: list[pgql_type.SuiCoinObjectGQL]
    :return: List of active coins or genertic objects
    :rtype: llist[pgql_type.SuiCoinObjectGQL] | list[pgql_type.ObjectReadGQL]
    """
    if objects:
        if isinstance(objects[0], pgql_type.SuiCoinObjectGQL):
            return [x for x in objects if x.previous_tractions]
        elif isinstance(objects[0], pgql_type.ObjectReadGQL):
            return [x for x in objects if x.previous_transaction_digest]
        else:
            raise ValueError(
                "active_types list contains neither SuiCoinObjectGQL or ObjectReadGQL"
            )
    return []


def get_all_owned_gas_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Syncrhnous: Retrieves list of all gas objects details for owner.

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
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
    result = client.execute_query_node(with_node=qn.GetCoins(owner=owner))
    while True:
        if result.is_ok():
            coin_list.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = client.execute_query_node(
                    with_node=qn.GetCoins(
                        owner=owner, next_page=result.result_data.next_cursor
                    )
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")
    return coin_list


def get_all_owned_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.ObjectReadGQL]:
    """Syncrhnous: Retrieves list of all object details for owner.

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

    object_list: list[pgql_type.ObjectReadGQL] = []
    result = client.execute_query_node(
        with_node=qn.GetObjectsOwnedByAddress(owner=owner)
    )
    while True:
        if result.is_ok():
            object_list.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = client.execute_query_node(
                    with_node=qn.GetObjectsOwnedByAddress(
                        owner=owner, next_page=result.result_data.next_cursor
                    )
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")
    return object_list


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
    result = client.execute_query_node(
        with_node=qn.GetMultipleGasObjects(coin_object_ids=gas_ids)
    )
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
    while True:
        if result.is_ok():
            coin_list.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = client.execute_query_node(
                    with_node=qn.GetMultipleGasObjects(
                        coin_object_ids=gas_ids, ext_page=result.result_data.next_cursor
                    )
                )
            else:
                break

        else:
            raise ValueError(f"Error retrieving coins by id {result.result_string}")
    return coin_list


async def async_get_all_owned_gas_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.SuiCoinObjectGQL]:
    """Asyncrhnous: Retrieves list of all gas objects details for owner.

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
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
    result = await client.execute_query_node(with_node=qn.GetCoins(owner=owner))
    while True:
        if result.is_ok():
            coin_list.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = await client.execute_query_node(
                    with_node=qn.GetCoins(
                        owner=owner, next_page=result.result_data.next_cursor
                    )
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")
    return coin_list


async def async_get_all_owned_objects(
    owner: str, client: BaseSuiGQLClient, only_active: Optional[bool] = True
) -> list[pgql_type.ObjectReadGQL]:
    """Asyncrhnous: Retrieves list of all object details for owner.

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

    object_list: list[pgql_type.ObjectReadGQL] = []
    result = await client.execute_query_node(
        with_node=qn.GetObjectsOwnedByAddress(owner=owner)
    )
    while True:
        if result.is_ok():
            object_list.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = await client.execute_query_node(
                    with_node=qn.GetObjectsOwnedByAddress(
                        owner=owner, next_page=result.result_data.next_cursor
                    )
                )
            else:
                break
        else:
            raise ValueError(f"Execute query error: {result.result_string}")
    return object_list


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
    result = await client.execute_query_node(
        with_node=qn.GetMultipleGasObjects(coin_object_ids=gas_ids)
    )
    coin_list: list[pgql_type.SuiCoinObjectGQL] = []
    while True:
        if result.is_ok():
            coin_list.extend(
                active_types_only(result.result_data.data)
                if only_active
                else result.result_data.data
            )
            if result.result_data.next_cursor.hasNextPage:
                result = await client.execute_query_node(
                    with_node=qn.GetMultipleGasObjects(
                        coin_object_ids=gas_ids, ext_page=result.result_data.next_cursor
                    )
                )
            else:
                break

        else:
            raise ValueError(f"Error retrieving coins by id {result.result_string}")
    return coin_list
