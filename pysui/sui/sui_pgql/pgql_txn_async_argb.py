#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""Pysui Transaction argument builder that works with GraphQL connection."""

import itertools
import inspect
from inspect import signature
from typing import Any, Optional, Union
from functools import partial, partialmethod
from dataclasses import dataclass, field
import canoser.int_type as cint
from pysui.sui.sui_common.txb_pure import PureInput
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type

import pysui.sui.sui_types as suit
from pysui.sui.sui_types import bcs
import pysui.sui.sui_txn.transaction_builder as tx_builder


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

_OPTIONAL_SCALARS_BCS = {
    "u8": bcs.OptionalU8,
    "u16": bcs.OptionalU16,
    "u32": bcs.OptionalU32,
    "u64": bcs.OptionalU64,
    "u128": bcs.OptionalU128,
    "u256": bcs.OptionalU256,
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


def _pass_through(arg: Any) -> Any:
    """Emulate 'identity'."""
    return arg


def _bytes_converter(
    scalar_class: cint.IntType,
    in_optional: bool,
    bytes_arg: bytes,
) -> list[bytes]:
    """Convert bytes to vector of type driven by scalar class."""
    bcount = scalar_class.byte_lens
    bitr = iter(bytes_arg)
    silist: list[int] = []
    while ilist := list(itertools.islice(bitr, bcount)):
        silist.append(sum(ilist))
    return silist


class AsyncResolvingArgParser:
    """Argument parser that does not resolves objects."""

    def __init__(self, client):
        self._client = client

    async def fetch_or_transpose_object(
        self,
        arg: Union[str, pgql_type.ObjectReadGQL],
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[Any] = None,
    ) -> bcs.ObjectArg:
        """Fetches and prepares an object reference to ObjectArg for BCS."""
        object_def: pgql_type.ObjectReadGQL = arg
        if isinstance(arg, str):
            result = await self._client.execute_query_node(
                with_node=qn.GetObject(object_id=arg)
            )
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
            if is_receiving:
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
                    is_mutable,
                ),
            )
            return b_obj_arg
        raise ValueError(
            f"Unknown owner kind {object_def.object_owner.obj_owner_kind }"
        )

    def _pure_generate(
        self,
        arg: Any,
        expected_type: Any,
        in_optional: bool,
        in_vector: bool,
    ) -> tuple[Any, Any]:
        """."""
        match expected_type.scalar_type:
            case "address" | "signature" | "ID":
                if in_vector:
                    return bcs.Address.from_str, _pass_through
                return bcs.Address.from_str, PureInput.as_input
            case "digest":
                if in_vector:
                    return bcs.Digest.from_str, _pass_through
                return bcs.Digest.from_str, PureInput.as_input
            case "String":
                return (
                    PureInput.pure,
                    partial(bcs.Variable.bcs_var_length_field, bcs.U8),
                )
            case _:
                if isinstance(arg, str) and expected_type.scalar_type == "u8":
                    return (
                        PureInput.pure,
                        partial(bcs.Variable.bcs_var_length_field, bcs.U8),
                    )
                elif isinstance(arg, bool) and expected_type.scalar_type == "bool":
                    return (
                        PureInput.pure,
                        partial(bcs.Variable.bcs_var_length_field, bcs.U8),
                    )

                elif isinstance(arg, bytes):
                    return (
                        partial(_pass_through),
                        # PureInput.pure,
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
                if in_optional:
                    return _OPTIONAL_SCALARS_BCS.get(expected_type.scalar_type)
                else:
                    return (
                        _SCALARS.get(expected_type.scalar_type),
                        PureInput.as_input,
                    )

    def _scalar_argument(
        self,
        expected_type,
        arg,
        in_optional: bool = False,
        in_vector: bool = False,
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

        return self._pure_generate(arg, expected_type, in_optional, in_vector)

    async def _object_processor(
        self,
        *,
        arg: Any,
        expected_type: pgql_type.MoveObjectRefArg,
        _construct: Optional[tuple[Any, Any]] = None,
    ) -> bcs.ObjectArg:
        """Process an object reference."""
        if arg:
            return await self.fetch_or_transpose_object(
                arg,
                expected_type.is_receiving,
                expected_type.ref_type == pgql_type.RefType.MUT_REF,
                expected_type,
            )
        raise ValueError("Missing argument")

    # TODO: This needs work
    async def _optional_processor(
        self,
        *,
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
            if inspect.iscoroutine(inner_fn):
                inner_type = await self._object_processor(
                    arg=arg,
                    expected_type=expected_type.type_params[0],
                )
            else:
                inner_type = outer_fn(inner_fn(arg))
            etr = bcs.OptionalTypeFactory.as_unresolved_optional(inner_type)
            # etr = bcs.OptionalTypeFactory.as_optional(inner_type)
        elif isinstance(construct, list):
            for index, vconstruct in enumerate(construct):
                convert, encode = vconstruct
                inner_type = encode(convert(arg))
                etr = bcs.OptionalTypeFactory.as_optional(inner_type)
        elif construct:
            inner_type = construct(arg)
            if construct in bcs.OPTIONAL_SCALARS:
                return inner_type
            etr = bcs.OptionalTypeFactory.as_optional(inner_type)
        etr.value = inner_type
        return etr

    async def _argument_builder(
        self, arg, arg_meta, processor_fn, constructor_fn=None
    ) -> Any:
        """Convert user input argument to the BCS representation expected for transaction."""
        if inspect.iscoroutinefunction(processor_fn):
            # if inspect.isawaitable(processor_fn):
            return await processor_fn(arg=arg, expected_type=arg_meta)
        if constructor_fn:
            return constructor_fn(processor_fn(arg))
        return arg

    async def _list_arg_builder(
        self, in_meta: any, convert_args: list, arg: list
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
            res_list.append(
                await self._list_arg_builder(in_meta, convert_args[0], arg[0])
            )
        else:
            convert_args = convert_args[0]
            if isinstance(arg, bcs.Argument):
                res_list.append(arg)
            elif isinstance(arg, (str, bytes)):
                res_list.append(
                    await self._argument_builder(arg, in_meta, *convert_args)
                )
            else:
                res_list.append(
                    await self._argument_builder(arg, in_meta, *convert_args)
                )

        return res_list

    async def _arg_builder(self, track: _ArgSummary, arglen: int):
        """."""
        for aindex in range(arglen):
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
                        await self._list_arg_builder(
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
                            res_list = await self._argument_builder(
                                self._client, in_arg, in_meta, *inner_list
                            )
                            break
                        else:
                            res_list.append(
                                await self._argument_builder(
                                    in_arg[ilindex],
                                    in_meta,
                                    *inner_list,
                                )
                            )
                    track.out_args[aindex] = res_list
            else:
                outer, inner = track.convert_args[aindex]
                track.out_args[aindex] = await self._argument_builder(
                    in_arg, in_meta, outer, inner
                )

    async def _object_argument(
        self,
        expected_type: pgql_type.MoveObjectRefArg,
        arg,
        in_optional: bool = False,
        in_vector: bool = False,
    ) -> tuple[Any, Any]:
        """Prepares an object argument for the transaction."""
        # If optional then get the inner type and validate
        if expected_type.is_optional:
            return self._optional_processor, await self._argument_validate(
                expected_type.type_params[0], arg, True, in_vector
            )

        return self._object_processor, None

    async def _argument_validate(
        self,
        expected_type: Any,
        arg: Any,
        in_optional: bool = False,
        in_vector: bool = False,
    ) -> Union[None, tuple[Any, Any]]:
        """Argument validation and process dispatching function."""
        if isinstance(arg, bcs.Argument):
            return None
        if isinstance(expected_type, pgql_type.MoveScalarArg):
            # print("Scalar")
            return self._scalar_argument(expected_type, arg, in_optional, in_vector)
        if isinstance(expected_type, pgql_type.MoveWitnessArg):
            # print("WitnessArg")
            return await self._object_argument(expected_type, arg, in_optional)
        elif isinstance(expected_type, pgql_type.MoveObjectRefArg):
            # print("ObjectRef")
            return await self._object_argument(expected_type, arg, in_optional)
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
                some_list.append(
                    await self._argument_validate(inner_type, arg, in_optional, True)
                )
            else:
                for inner_arg in arg:
                    if isinstance(inner_arg, bcs.Argument):
                        some_list.append(inner_arg)
                    else:
                        some_list.append(
                            await self._argument_validate(
                                inner_type, inner_arg, in_optional, True
                            )
                        )
            return some_list

        raise ValueError(f"Unhhandled type {type(expected_type)}")

    async def _gen_summary(self, in_args, meta_args, arglen) -> _ArgSummary:
        """."""
        track = _ArgSummary(
            in_args=in_args,
            out_args=[None] * arglen,
            func_args=meta_args.arg_list,
            convert_args=[None] * arglen,
        )
        for aindex in range(arglen):
            track.convert_args[aindex] = await self._argument_validate(
                track.func_args[aindex], track.in_args[aindex]
            )
        return track

    async def build_args(self, in_args, meta_args) -> list:
        """Async build arguments."""
        alen = len(in_args)
        if alen == len(meta_args.arg_list):
            track = await self._gen_summary(in_args, meta_args, alen)
            await self._arg_builder(track, alen)
            return track.out_args
        raise ValueError(
            f"Invalid arg count. Target:{len(meta_args.arg_list)} Source:{len(in_args)}"
        )


class UnResolvingArgParser(AsyncResolvingArgParser):
    """Argument parser that does not resolves objects."""

    def __init__(self, client):
        self._client = client

    async def fetch_or_transpose_object(
        self,
        arg: str,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[Any] = None,
    ) -> bcs.ObjectArg:
        """Generates unresolve object references for caching."""
        return bcs.UnresolvedObjectArg.from_object_ref_type(arg, expected_type)

    async def fetch_or_transpose_optional_object(
        self,
        arg: str,
        expected_type: pgql_type.MoveObjectRefArg,
        type_str: str,
    ) -> bcs.ObjectArg:
        """Generates unresolve object references for caching."""
        return bcs.UnresolvedObjectArg.from_optional_object_ref_type(
            arg, expected_type, type_str
        )
