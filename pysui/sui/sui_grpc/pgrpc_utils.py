#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Collection of reusable functions."""

from typing import Any, Optional, Callable, ParamSpec
from functools import partial
from pysui.sui.sui_common.client import PysuiClient
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot
import pysui.sui.sui_grpc.pgrpc_requests as rn
import pysui.sui.sui_pgql.pgql_types as pgql_types
import pysui.sui.sui_pgql.pgql_validators as tv
import pysui.sui.sui_bcs.bcs as bcs

_P = ParamSpec("P")


def active_types_only(
    objects: list[sui_prot.Object],
) -> list[sui_prot.Object]:
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
                active_types_only(result.result_data.objects)
                if only_active
                else result.result_data.objects
            )
            if (
                hasattr(result.result_data, "page_token")
                and result.result_data.page_token
            ):
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
) -> list[sui_prot.Object]:
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
    :rtype: list[sui_prot.Object]
    """
    return await async_cursored_collector(
        partial(rn.GetGas, owner=owner), client, only_active
    )


async def async_get_all_owned_objects(
    owner: str, client: PysuiClient, only_active: Optional[bool] = True
) -> list[sui_prot.Object]:
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
    :rtype: list[sui_prot.Object]
    """
    return await async_cursored_collector(
        partial(rn.GetOwnedObjects, owner=owner), client, only_active
    )


async def async_get_gas_objects_by_ids(
    client: PysuiClient, gas_ids: list[str], only_active: Optional[bool] = True
) -> list[sui_prot.Object]:
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
    :rtype: list[sui_prot.Object]
    """
    # TODO: This call has no pagination, need to get max id constraint
    # and perform looped fetch
    # Also need to filter for coins only
    return await async_cursored_collector(
        partial(rn.GetMultipleObjects, object_ids=gas_ids), client, only_active
    )


async def async_get_objects_by_ids(
    client: PysuiClient, object_ids: list[str], only_active: Optional[bool] = True
) -> list[sui_prot.Object]:
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
    :rtype: list[sui_prot.Object]
    """
    # TODO: This call has no pagination, need to get max id constraint
    # and perform looped fetch
    return await async_cursored_collector(
        partial(rn.GetMultipleObjects, object_ids=object_ids), only_active
    )


def _normalize_inner_arg(
    arg: sui_prot.OpenSignatureBody, in_optional: Optional[bool] = False
) -> Any | None:
    """."""
    if arg.type.name in bcs.TypeTag._UCASE_SCALARS or arg.type.name in [
        "BOOL",
        "ADDRESS",
    ]:
        result = pgql_types.MoveScalarArg(
            pgql_types.RefType.from_ref(""), arg.type.name.lower(), in_optional
        )
    else:
        raise NotImplemented(f"Inner Arg for {arg.to_json()}")
    return result


def _normalize_arg(
    arg: sui_prot.OpenSignature, in_optional: Optional[bool] = False
) -> Any | None:
    """."""
    result: Any = None
    # Handle scalar
    if arg.body.type.name in bcs.TypeTag._UCASE_SCALARS or arg.body.type.name in [
        "BOOL",
        "ADDRESS",
    ]:
        result = pgql_types.MoveScalarArg(
            pgql_types.RefType.from_ref(""), arg.body.type.name.lower(), in_optional
        )
    # Otherwise, if not last arg
    elif arg.body.type_name != "0x2::tx_context::TxContext":
        r_type = pgql_types.RefType.from_ref(
            arg.reference.name if arg.reference else pgql_types.RefType.NO_REF
        )
        # Handle vector
        if arg.body.type == sui_prot.OpenSignatureBodyType.VECTOR:
            inner = arg.body.type_parameter_instantiation[0]
            if not isinstance(inner, sui_prot.OpenSignature):
                inner = sui_prot.OpenSignature(body=inner)
            result = pgql_types.MoveVectorArg(
                r_type,
                _normalize_arg(inner),
            )
        # Else it's an object
        # TODO: Optional and Receiving
        else:
            receiving: bool = False
            optional: bool = False
            package, package_module, package_struct = (
                tv.TypeValidator.check_target_triplet(arg.body.type_name)
            )
            if package_module in ["object", "address", "string"] and package_struct in [
                "ID",
                "UID",
                "address",
                "String",
            ]:
                result = pgql_types.MoveScalarArg(r_type, package_struct)
            else:
                if package_module == "transfer" and package_struct == "Receiving":
                    receiving = True
                if not in_optional:
                    if package_module == "option" and package_struct == "Option":
                        return _normalize_inner_arg(
                            arg.body.type_parameter_instantiation[0], True
                        )
                else:
                    optional = in_optional
                hastype = bool(arg.body.type_parameter)
                result = pgql_types.MoveObjectRefArg(
                    r_type,
                    package,
                    package_module,
                    package_struct,
                    arg.body.type_parameter_instantiation,
                    optional,
                    receiving,
                    hastype,
                )

    return result


def normalize_move_func(
    func: sui_prot.GetFunctionResponse,
) -> pgql_types.MoveArgSummary:
    """Convert gRPC function response to GraphQL MoveArgSummary

    :param func: Retrieved move function details
    :type func: sui_prot.GetFunctionResponse
    """
    arg_list: list[
        pgql_types.MoveScalarArg
        | pgql_types.MoveObjectRefArg
        | pgql_types.MoveTypeArg
        | pgql_types.MoveVectorArg
        | pgql_types.MoveWitnessArg
        | pgql_types.MoveAnyArg
    ] = []

    for arg in func.function.parameters:
        if narg := _normalize_arg(arg):
            arg_list.append(narg)
    return pgql_types.MoveArgSummary(
        func.function.type_parameters, arg_list, len(func.function.returns)
    )
