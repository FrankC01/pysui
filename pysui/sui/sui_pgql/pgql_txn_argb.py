#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""Pysui Transaction argument builder that works with GraphQL connection."""

import itertools
from typing import Any, Optional, Union
from functools import partial
from dataclasses import dataclass, field
import canoser.int_type as cint
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type

import pysui.sui.sui_types as suit
from pysui.sui.sui_types import bcs
import pysui.sui.sui_txn.transaction_builder as tx_builder
from pysui.sui.sui_utils import serialize_uint32_as_uleb128

_SCALARS = {
    "u8": suit.SuiU8,
    "u16": suit.SuiU16,
    "u32": suit.SuiU32,
    "u64": suit.SuiU64,
    "u128": suit.SuiU128,
    "u256": suit.SuiU256,
}

_SCALARS_BCS = {
    "u8": bcs.U8,
    "u16": bcs.U16,
    "u32": bcs.U32,
    "u64": bcs.U64,
    "u128": bcs.U128,
    "u256": bcs.U256,
}


@dataclass
class _ArgSummary:
    """Summary of point-in-time internal processing."""

    # Orginal input arguments
    in_args: list[Any]
    # Matching length final args
    out_args: list[Any]
    # Argument types from meta function args
    func_args: list[Any]
    # Function arg set and convert
    convert_args: list[tuple[Any, Any]] = field(default_factory=list)


# TODO: This needs work
def _optional_processor(
    *,
    client: SuiGQLClient,
    arg: Any,
    expected_type: pgql_type.MoveObjectRefArg,
    construct: Optional[tuple[Any, Any]] = None,
) -> Any:
    """Process arguments wrapped in Move Optional."""
    if not arg:
        etr = bcs.OptionalTypeFactory.as_optional()
        return etr
    elif isinstance(arg, list) and arg[0] is None:
        etr = bcs.OptionalTypeFactory.as_optional()
        return etr

    if isinstance(construct, tuple):
        inner_fn, outer_fn = construct
        if inner_fn is _object_processor:
            inner_type = _object_processor(
                client=client,
                arg=arg,
                expected_type=expected_type.type_params[0],
            )
        else:
            inner_type = outer_fn(inner_fn(arg))
        etr = bcs.OptionalTypeFactory.as_optional(inner_type)
    elif isinstance(construct, list):
        for index, vconstruct in enumerate(construct):
            convert, encode = vconstruct
            inner_type = encode(convert(arg))
            etr = bcs.OptionalTypeFactory.as_optional(inner_type)
    elif construct:
        inner_type = construct(arg)
        etr = bcs.OptionalTypeFactory.as_optional(inner_type)
    etr.value = inner_type
    return etr


def _fetch_or_transpose_object(
    client: SuiGQLClient,
    arg: Union[str, pgql_type.ObjectReadGQL],
    expected_type: pgql_type.MoveObjectRefArg,
) -> bcs.ObjectArg:
    """Fetches and prepares an object reference to ObjectArg for BCS."""
    object_def: pgql_type.ObjectReadGQL = arg
    if isinstance(arg, str):
        result = client.execute_query_node(with_node=qn.GetObject(object_id=arg))
        if result.is_ok():
            object_def = result.result_data
            if isinstance(
                object_def, (pgql_type.NoopGQL, pgql_type.ObjectReadDeletedGQL)
            ):
                raise ValueError(f"{arg} object not found")

    if object_def.object_owner.obj_owner_kind in [
        "AddressOwner",
        "Immutable",
        "Parent",
    ]:
        if expected_type.is_receiving:
            b_obj_arg = bcs.ObjectArg(
                "Receiving",
                bcs.ObjectReference.from_gql_ref(object_def),
            )
        else:
            b_obj_arg = bcs.ObjectArg(
                "ImmOrOwnedObject",
                bcs.ObjectReference.from_gql_ref(object_def),
            )
        return b_obj_arg

    if object_def.object_owner.obj_owner_kind == "Shared":
        b_obj_arg = bcs.ObjectArg(
            "SharedObject",
            bcs.SharedObjectReference.from_gql_ref(
                object_def,
                expected_type.ref_type == pgql_type.RefType.MUT_REF,
            ),
        )
        return b_obj_arg
    raise ValueError(f"Unknown owner kind {object_def.object_owner.obj_owner_kind }")


def _object_processor(
    *,
    client: SuiGQLClient,
    arg: Any,
    expected_type: pgql_type.MoveObjectRefArg,
    _construct: Optional[tuple[Any, Any]] = None,
) -> bcs.ObjectArg:
    """Process an object reference."""
    if arg:
        return _fetch_or_transpose_object(client, arg, expected_type)
    raise ValueError("Missing argument")


def pass_through(arg: Any) -> Any:
    """Emulate 'identity'."""
    return arg


def _bytes_converter(
    scalar_class: cint.IntType, in_optional: bool, bytes_arg: bytes
) -> list[bytes]:
    """Convert bytes to vector of type driven by scalar class."""
    bcount = scalar_class.byte_lens
    bitr = iter(bytes_arg)
    silist: list[int] = []
    while ilist := list(itertools.islice(bitr, bcount)):
        silist.append(sum(ilist))
    return silist


def _canbt(
    arg: Any, expected_type: Any, in_optional: bool, in_vector
) -> tuple[Any, Any]:
    """."""
    match expected_type.scalar_type:
        case "address" | "signature" | "ID":
            if in_vector:
                return bcs.Address.from_str, pass_through
            return bcs.Address.from_str, tx_builder.PureInput.as_input
        case "digest":
            if in_vector:
                return bcs.Digest.from_str, pass_through
            return bcs.Digest.from_str, tx_builder.PureInput.as_input
        case "String":
            return (
                tx_builder.PureInput.pure,
                partial(bcs.Variable.bcs_var_length_field, bcs.U8),
            )
        case _:
            if isinstance(arg, str) and expected_type.scalar_type == "u8":
                return (
                    tx_builder.PureInput.pure,
                    partial(bcs.Variable.bcs_var_length_field, bcs.U8),
                )
            elif isinstance(arg, bool) and expected_type.scalar_type == "bool":
                return (
                    tx_builder.PureInput.pure,
                    partial(bcs.Variable.bcs_var_length_field, bcs.U8),
                )

            elif isinstance(arg, bytes):
                return (
                    partial(pass_through),
                    # tx_builder.PureInput.pure,
                    partial(
                        bcs.Variable.bcs_var_length_encoded_field,
                        _SCALARS_BCS.get(expected_type.scalar_type),
                        partial(
                            _bytes_converter,
                            _SCALARS_BCS.get(expected_type.scalar_type),
                            in_optional,
                        ),
                    ),
                )
                # if in_optional:
                #     return (
                #         partial(
                #             _bytes_converter,
                #             _SCALARS_BCS.get(expected_type.scalar_type),
                #             in_optional,
                #         ),
                #         partial(
                #             bcs.Variable.bcs_var_length_field,
                #             _SCALARS_BCS.get(expected_type.scalar_type),
                #         ),
                #     )
                # return (
                #     partial(
                #         _bytes_converter,
                #         _SCALARS_BCS.get(expected_type.scalar_type),
                #         in_optional,
                #     ),
                #     pass_through,
                # )

            return (
                _SCALARS.get(expected_type.scalar_type),
                tx_builder.PureInput.as_input,
            )


def _scalar_argument(
    expected_type, arg, in_optional: bool = False, in_vector: bool = False
) -> tuple[Any, Any]:
    """Prepares a scalar argument for the transaction."""

    # Validate arg matches expectation
    if arg:
        if _SCALARS.get(expected_type.scalar_type):
            if isinstance(arg, str) and expected_type.scalar_type == "u8":
                pass
            elif isinstance(arg, bytes):
                pass
            elif not isinstance(arg, int):
                raise ValueError(f"Expected int and found {arg.__class__}")
        elif isinstance(arg, bool):
            pass
        elif not isinstance(arg, str):
            raise ValueError(f"Expected str found {arg.__class__}")

    return _canbt(arg, expected_type, in_optional, in_vector)


def _object_argument(
    expected_type: pgql_type.MoveObjectRefArg,
    arg,
    in_optional: bool = False,
    in_vector: bool = False,
) -> tuple[Any, Any]:
    """Prepares an object argument for the transaction."""
    # If optional then get the inner type and validate
    if expected_type.is_optional:
        return _optional_processor, _argument_validate(
            expected_type.type_params[0], arg, True, in_vector
        )
    return _object_processor, None


def _argument_validate(
    expected_type: Any, arg: Any, in_optional: bool = False, in_vector: bool = False
) -> Union[None, tuple[Any, Any]]:
    """Argument validation and process dispatching function."""
    if isinstance(arg, bcs.Argument):
        return None
    if isinstance(expected_type, pgql_type.MoveScalarArg):
        # print("Scalar")
        return _scalar_argument(expected_type, arg, in_optional, in_vector)
    if isinstance(expected_type, pgql_type.MoveWitnessArg):
        # print("WitnessArg")
        return _object_argument(expected_type, arg, in_optional)
    elif isinstance(expected_type, pgql_type.MoveObjectRefArg):
        # print("ObjectRef")
        return _object_argument(expected_type, arg, in_optional)
    if isinstance(expected_type, (pgql_type.MoveVectorArg, pgql_type.MoveListArg)):
        # print("Vector or List")
        if in_optional and not arg:
            return arg
        elif not arg:
            raise ValueError("Excepted str, bytes or list")
        if isinstance(arg, (str, bytes)):
            pass
        elif not isinstance(arg, list):
            raise ValueError("Expected list type argument...")
        some_list = []
        inner_type = (
            expected_type.list_arg
            if isinstance(expected_type, pgql_type.MoveListArg)
            else expected_type.vec_arg
        )
        if isinstance(arg, (str, bytes)):
            some_list.append(_argument_validate(inner_type, arg, in_optional, True))
        else:
            for inner_arg in arg:
                if isinstance(inner_arg, bcs.Argument):
                    some_list.append(inner_arg)
                else:
                    some_list.append(
                        _argument_validate(inner_type, inner_arg, in_optional, True)
                    )
        return some_list

    raise ValueError(f"Unhhandled type {type(expected_type)}")


def _argument_builder(
    client: SuiGQLClient, arg, arg_meta, processor_fn, constructor_fn=None
) -> Any:
    """Convert user input argument to the BCS representation expected for transaction."""
    if processor_fn is _object_processor:
        return _object_processor(
            client=client,
            arg=arg,
            expected_type=arg_meta,
        )
    if processor_fn is _optional_processor:
        return _optional_processor(
            client=client,
            arg=arg,
            expected_type=arg_meta,
            construct=constructor_fn,
        )
    if constructor_fn:
        return constructor_fn(processor_fn(arg))
    return arg


def _list_arg_builder(
    client: SuiGQLClient, in_meta: any, convert_args: list, arg: list
) -> list:
    """."""
    res_list = []
    if isinstance(in_meta, pgql_type.MoveVectorArg):
        in_meta = in_meta.vec_arg
    elif isinstance(in_meta, pgql_type.MoveListArg):
        in_meta = in_meta.list_arg
    if isinstance(
        in_meta, (pgql_type.MoveVectorArg, pgql_type.MoveListArg)
    ) and isinstance(arg, list):
        res_list.append(_list_arg_builder(client, in_meta, convert_args[0], arg[0]))
    else:
        convert_args = convert_args[0]
        if isinstance(arg, bcs.Argument):
            res_list.append(arg)
        elif isinstance(arg, (str, bytes)):
            res_list.append(_argument_builder(client, arg, in_meta, *convert_args))
        else:
            res_list.append(_argument_builder(client, arg, in_meta, *convert_args))

    return res_list


def build_args(
    client: SuiGQLClient, in_args: list, meta_args: pgql_type.MoveArgSummary
) -> list:
    """build_args Validates and prepares arguments for transaction execution

    :param client: The Sui GraphQL client
    :type client: SuiGQLClient
    :param in_args: The list of pre-processed arguments
    :type in_args: list
    :param meta_args: The meta move function argument type list
    :type meta_args: pgql_type.MoveArgSummary
    :raises ValueError: If the provided arg count and expected don't match
    :return: The list of post processed arguments
    :rtype: list
    """
    alen = len(in_args)
    if alen == len(meta_args.arg_list):
        track = _ArgSummary(
            in_args=in_args,
            out_args=[None] * alen,
            func_args=meta_args.arg_list,
            convert_args=[None] * alen,
        )
        for aindex in range(alen):
            track.convert_args[aindex] = _argument_validate(
                track.func_args[aindex], track.in_args[aindex]
            )
        for aindex in range(alen):
            in_arg = track.in_args[aindex]
            in_meta = track.func_args[aindex]
            if not track.convert_args[aindex] and isinstance(
                track.in_args[aindex], bcs.Argument
            ):
                track.out_args[aindex] = track.in_args[aindex]
            elif isinstance(track.convert_args[aindex], list):
                res_list = []
                if isinstance(in_meta, pgql_type.MoveVectorArg):
                    in_meta = in_meta.vec_arg
                elif isinstance(in_meta, pgql_type.MoveListArg):
                    in_meta = in_meta.list_arg
                if isinstance(
                    in_meta, (pgql_type.MoveVectorArg, pgql_type.MoveListArg)
                ) and isinstance(in_arg, list):
                    res_list.append(
                        _list_arg_builder(
                            client,
                            in_meta,
                            track.convert_args[aindex][0],
                            in_arg[0],
                        )
                    )
                    track.out_args[aindex] = res_list
                else:
                    for ilindex, inner_list in enumerate(track.convert_args[aindex]):
                        if isinstance(inner_list, bcs.Argument):
                            res_list.append(inner_list)
                        elif isinstance(in_arg, (str, bytes)):
                            res_list = _argument_builder(
                                client, in_arg, in_meta, *inner_list
                            )
                            break
                        else:
                            res_list.append(
                                _argument_builder(
                                    client, in_arg[ilindex], in_meta, *inner_list
                                )
                            )
                    track.out_args[aindex] = res_list
            else:
                outer, inner = track.convert_args[aindex]
                track.out_args[aindex] = _argument_builder(
                    client, in_arg, in_meta, outer, inner
                )

        return track.out_args

    raise ValueError(
        f"Invalid arg count. Target:{len(meta_args.arg_list)} Source:{len(in_args)}"
    )
