#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui DeSertializtion from Sui Wallet JSON standard to pysui GraphQL SuiTransaction."""

from typing import Any, Optional
import functools as ft

from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as tn
import pysui.sui.sui_pgql.pgql_wallet_deser as deser


def _is_unresolved(clup: tuple, item: Any) -> Any:
    """Filter function for Unresolved types.

    :param clup: A tuple of classes of unresolved types
    :type clup: tuple
    :param item: An object to test if in any of the clup classes
    :type item: Any
    :return: The item if true, else None
    :rtype: Any
    """
    if isinstance(item, clup):
        return item
    return None


def _resolve_inputs(client: SuiGQLClient, unresolved: list[tuple[int, Any]]) -> list:
    """Resolves unresolved types from wallet standard.

    :param client: HTTP client
    :type client: SuiGQLClient
    :param unresolved: list of unresolved types
    :type unresolved: list
    :raises ValueError: If unresolved types inlclude UnresolvedPure types (not handled yet)
    :return: List of resolved UnresolvedObjects (i.e. wallet Object)
    :rtype: list
    """
    unrlen = len(unresolved)
    unracc = []
    unoids = [x[1].object_id for x in unresolved]
    # Fetch all unresolved
    result = client.execute_query_node(
        with_node=qn.GetMultipleObjects(object_ids=unoids)
    )
    while result.is_ok():
        unracc.extend(result.result_data.data)
        if result.result_data.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetMultipleObjects(
                    object_ids=unoids, next_page=result.result_data.next_cursor
                )
            )
            if result.is_err():
                raise ValueError(f"Error retrieving objects {result.result_string}")
        else:
            break
    # Lengths must match
    if len(unracc) != unrlen:
        raise ValueError(
            f"Object fetch failure for {unoids} found {[x.object_id for x in unracc]}"
        )
    # Convert to resolve SuiObject in wallet standard
    resobjs: list[tuple[int, deser.SuiObjectCallArg]] = []
    for idx, item in enumerate(unracc):
        if item.object_id != unresolved[idx][1].object_id:
            raise ValueError("Misalignment")
        objcarg = {"object_id": item.object_id}
        if isinstance(item.object_owner, tn.SuiObjectOwnedAddress):
            objcarg["ref_type"] = "Imm"
            objcarg["digest"] = item.object_digest
            objcarg["version"] = item.version
        elif isinstance(item.object_owner, tn.SuiObjectOwnedShared):
            objcarg["ref_type"] = "Shared"
            objcarg["initial_shared_version"] = item.initial_version
            objcarg["mutable"] = True
        else:
            raise ValueError(f"Object owner not recognized {item.object_owner}")
        resobjs.append((unresolved[idx][0], deser.SuiObjectCallArg.from_dict(objcarg)))

    return resobjs


def _resolve_unresolved(client, inputs: list) -> list:
    """."""
    if unp := list(
        filter(ft.partial(_is_unresolved, (deser.SuiUnresolvedPureCallArg)), inputs)
    ):
        raise ValueError(f"pysui does not support Unresolved pures. Found {unp}")

    unresobj: list[tuple[int, deser.SuiUnresolvedObjectCallArg]] = []
    for idx, item in enumerate(inputs):
        if isinstance(item, deser.SuiUnresolvedObjectCallArg):
            unresobj.append((idx, item))
    if unresobj:
        result: list[deser.SuiObjectCallArg] = _resolve_inputs(client, unresobj)
        for inidx, replacement in result:
            inputs[inidx] = replacement

    return inputs


def deserialize_to_transaction(
    *, wallet_json: str, substitutions: Optional[dict] = None, **kwargs
) -> tuple[int, SuiTransaction]:
    """Deserialize from the Sui Wallet Transaction Standard to pysui GraphQL SuiTransaction."""
    wallet: deser.SuiBuilder = deser.SuiBuilder.from_json(wallet_json)
    client: SuiGQLClient = kwargs["client"]

    # Manage Unresolved
    [print(x.to_json(indent=2)) for x in wallet.inputs]
    wallet.inputs = _resolve_unresolved(client, wallet.inputs)
    [print(x.to_json(indent=2)) for x in wallet.inputs]
    # Manage substitutes
    # Manage Addresses
    # Manage $Intents
    # sui_txn = SuiTransaction(**kwargs)

    return wallet.expiration, None
