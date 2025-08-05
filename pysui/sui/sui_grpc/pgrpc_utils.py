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

P = ParamSpec("P")


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
    return objects


async def async_cursored_collector(
    pfn: Callable[P, list],
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
    result = await client.execute(request=pfn())  # type: ignore
    while True:
        if result.is_ok():
            collection.extend(
                active_types_only(result.result_data.objects)
                if only_active
                else result.result_data.objects
            )
            if (
                hasattr(result.result_data, "next_page_token")
                and result.result_data.next_page_token
            ):
                result = await client.execute(  # type: ignore
                    request=pfn(page_token=result.result_data.next_page_token)  # type: ignore
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
        partial(rn.GetGas, owner=owner), client, only_active  # type: ignore
    )


async def async_get_all_owned_objects(
    owner: str, client: PysuiClient, only_active: Optional[bool] = True
) -> list[sui_prot.Object]:
    """Asynchronous: Retrieves list of all object details for owner.

    Uses cursor to ensure all asked for are retrieved from node and
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
        partial(rn.GetObjectsOwnedByAddress, owner=owner),  # type: ignore
        client,
        only_active,
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
        partial(rn.GetMultipleObjects, object_ids=gas_ids), client, only_active  # type: ignore
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
        partial(rn.GetMultipleObjects, object_ids=object_ids), client, only_active  # type: ignore
    )


def _normalize_inner_arg(
    arg: sui_prot.OpenSignatureBody, in_optional: Optional[bool] = False
) -> Any | None:
    """."""
    result = None
    if arg.type == sui_prot.OpenSignatureBodyType.TYPE_PARAMETER:
        result = pgql_types.MoveParameterArg(arg.type_parameter)  # type: ignore
    elif arg.type.name in bcs.TypeTag._UCASE_SCALARS or arg.type in [  # type: ignore
        sui_prot.OpenSignatureBodyType.BOOL,
        sui_prot.OpenSignatureBodyType.ADDRESS,
    ]:
        result = pgql_types.MoveScalarArg(
            pgql_types.RefType.from_ref(""), arg.type.name.lower(), in_optional  # type: ignore
        )
    else:
        raise NotImplementedError(f"Inner Arg for {arg.to_json()}")
    return result


def _normalize_object_type(
    arg: sui_prot.OpenSignature, optional: bool, type_parms: Optional[Any] = None
) -> pgql_types.MoveObjectRefArg | pgql_types.MoveScalarArg:
    """."""
    receiving: bool = False
    package, package_module, package_struct = tv.TypeValidator.check_target_triplet(
        arg.body.type_name  # type: ignore
    )
    r_type = pgql_types.RefType.from_ref(
        arg.reference.name if arg.reference else pgql_types.RefType.NO_REF  # type: ignore
    )

    if package_module in ["object", "address", "string"] and package_struct in [
        "ID",
        "UID",
        "address",
        "String",
    ]:
        result = pgql_types.MoveScalarArg(r_type, package_struct, optional)
    else:
        assert arg.body is not None
        hastype = bool(arg.body.type_parameter)
        if package_module == "transfer" and package_struct == "Receiving":
            receiving = True
        result = pgql_types.MoveObjectRefArg(
            r_type,
            package,
            package_module,
            package_struct,
            type_parms if type_parms else arg.body.type_parameter_instantiation,
            optional,
            receiving,
            hastype,
        )

    return result


def _normalize_optional(
    arg: sui_prot.OpenSignature, in_optional: bool
) -> pgql_types.MoveObjectRefArg:
    """Return an MoveObjectRefArg."""
    assert arg.body is not None
    inner = _normalize_arg(
        sui_prot.OpenSignature(body=arg.body.type_parameter_instantiation[0]), True
    )
    return _normalize_object_type(arg, True, [inner])  # type: ignore


def _normalize_arg(
    arg: sui_prot.OpenSignature, in_optional: Optional[bool] = False
) -> Any | None:
    """."""
    result: Any = None
    # Handle scalar
    assert arg.body is not None
    assert arg.body.type is not None
    if arg.body.type.name in bcs.TypeTag._UCASE_SCALARS or arg.body.type.name in [
        "BOOL",
        "ADDRESS",
    ]:
        result = pgql_types.MoveScalarArg(
            pgql_types.RefType.from_ref(""), arg.body.type.name.lower(), in_optional
        )
    elif arg.body.type == sui_prot.OpenSignatureBodyType.TYPE_PARAMETER:
        result = _normalize_inner_arg(arg.body)
    # Otherwise, if not last arg
    elif not arg.body.type_name in [
        "0x2::tx_context::TxContext",
        "0x0000000000000000000000000000000000000000000000000000000000000002::tx_context::TxContext",
    ]:
        r_type = pgql_types.RefType.from_ref(
            arg.reference.name if arg.reference else pgql_types.RefType.NO_REF  # type: ignore
        )
        # Handle vector
        if arg.body.type == sui_prot.OpenSignatureBodyType.VECTOR:
            inner = arg.body.type_parameter_instantiation[0]
            if not isinstance(inner, sui_prot.OpenSignature):
                inner = sui_prot.OpenSignature(body=inner)
            result = pgql_types.MoveVectorArg(
                r_type,
                _normalize_arg(inner),  # type: ignore
            )
        # Else it's an object
        else:
            _, package_module, package_struct = tv.TypeValidator.check_target_triplet(
                arg.body.type_name  # type: ignore
            )
            if package_module in ["object", "address", "string"] and package_struct in [
                "ID",
                "UID",
                "address",
                "String",
            ]:
                result = pgql_types.MoveScalarArg(r_type, package_struct)
            else:
                if not in_optional:
                    if package_module == "option" and package_struct == "Option":
                        result = _normalize_optional(arg, False)
                    else:
                        result = _normalize_object_type(arg, False, None)
                else:
                    result = _normalize_object_type(arg, in_optional, None)

    return result


def _normalize_func(func: sui_prot.FunctionDescriptor) -> pgql_types.MoveArgSummary:
    """Function converter."""
    arg_list: list[
        pgql_types.MoveScalarArg
        | pgql_types.MoveObjectRefArg
        | pgql_types.MoveTypeArg
        | pgql_types.MoveVectorArg
        | pgql_types.MoveWitnessArg
        | pgql_types.MoveAnyArg
    ] = []
    for arg in func.parameters:
        if narg := _normalize_arg(arg):
            arg_list.append(narg)
    return pgql_types.MoveArgSummary(func.type_parameters, arg_list, len(func.returns))


def normalize_move_func(
    func: sui_prot.GetFunctionResponse,
) -> pgql_types.MoveArgSummary:
    """Convert gRPC function response to GraphQL MoveArgSummary

    :param func: Retrieved move function details
    :type func: sui_prot.GetFunctionResponse
    """
    assert func.function is not None
    return _normalize_func(func.function)


def normalize_funcs_from_module(
    module: sui_prot.Module,
) -> list[pgql_types.MoveArgSummary]:
    results: list[pgql_types.MoveArgSummary] = []
    for func in module.functions:
        results.append(_normalize_func(func))
    return results
