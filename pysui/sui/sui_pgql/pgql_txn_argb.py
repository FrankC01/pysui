#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""Pysui synchronous transaction argument builder — uses new metadata-driven encoder."""

from typing import Any, Optional, Union

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_pgql.pgql_types import (
    OpenMoveScalarBodyGQL,
    OpenMoveVectorBodyGQL,
    OpenMoveDatatypeBodyGQL,
    OpenMoveTypeParamBodyGQL,
    OpenMoveTypeGQL,
)
from pysui.sui.sui_common.txn_arg_encoder import (
    _raw_value,
    _is_pure_datatype,
    _UINT_SUI,
)
from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_bcs import bcs


class ResolvingArgParser:
    """Synchronous GQL argument parser using the metadata-driven encoder."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def fetch_or_transpose_object(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Resolve or transpose an object reference to bcs.ObjectArg."""
        if isinstance(arg, bcs.ObjectArg):
            return arg

        if isinstance(arg, bcs.ObjectReference):
            if is_receiving:
                return bcs.ObjectArg("Receiving", arg)
            return bcs.ObjectArg("ImmOrOwnedObject", arg)

        if isinstance(arg, bcs.SharedObjectReference):
            return bcs.ObjectArg("SharedObject", arg)

        object_def: Optional[pgql_type.ObjectReadGQL] = None
        if isinstance(arg, (
            pgql_type.ObjectReadGQL,
            pgql_type.SuiCoinObjectGQL,
            pgql_type.SuiStakedCoinGQL,
            pgql_type.SuiCoinObjectSummaryGQL,
        )):
            object_def = arg
        elif isinstance(arg, str):
            result = self._client.execute_query_node(
                with_node=qn.GetObject(object_id=arg)
            )
            if result.is_ok():
                object_def = result.result_data
                if isinstance(
                    object_def, (pgql_type.NoopGQL, pgql_type.ObjectReadDeletedGQL)
                ):
                    raise ValueError(f"{arg} object not found")
            else:
                raise ValueError(f"Failed to fetch object {arg}")
        else:
            raise ValueError(f"Unsupported argument type: {type(arg)}")

        if object_def.object_owner.obj_owner_kind in [
            "AddressOwner",
            "Immutable",
            "Parent",
        ]:
            obj_ref = bcs.ObjectReference.from_gql_ref(object_def)
            if is_receiving:
                return bcs.ObjectArg("Receiving", obj_ref)
            return bcs.ObjectArg("ImmOrOwnedObject", obj_ref)

        if object_def.object_owner.obj_owner_kind == "Shared":
            obj_ref = bcs.SharedObjectReference.from_gql_ref(object_def, is_mutable)
            return bcs.ObjectArg("SharedObject", obj_ref)

        raise ValueError(
            f"Unknown owner kind {object_def.object_owner.obj_owner_kind}"
        )

    def _encode_option(
        self,
        type_params: list,
        value: Any,
        ref: Optional[str],
    ) -> Any:
        """Encode top-level Option<T>."""
        if value is None or (isinstance(value, list) and value and value[0] is None):
            return bcs.OptionalTypeFactory.as_optional()
        inner = type_params[0] if type_params else None
        if inner is None:
            raise ValueError("Option missing type parameter")
        if isinstance(inner, OpenMoveDatatypeBodyGQL) and not _is_pure_datatype(
            inner.module, inner.type_name
        ):
            obj = self.fetch_or_transpose_object(
                value, inner.type_name == "Receiving", ref == "&mut", inner
            )
            return bcs.OptionalTypeFactory.as_unresolved_optional(obj)
        raw = _raw_value(inner, value)
        return bcs.OptionalTypeFactory.as_optional(bcs.BuilderArg("Pure", [1] + raw))

    def _encode_arg(
        self,
        body: Any,
        value: Any,
        ref: Optional[str],
    ) -> Any:
        """Encode a single argument value against its OpenMoveBodyGQL descriptor."""
        if isinstance(body, OpenMoveScalarBodyGQL):
            type_name = body.scalar_type
            if type_name in _UINT_SUI:
                return PureInput.as_input(_UINT_SUI[type_name](value))
            if type_name == "bool":
                return PureInput.as_input(value)
            if type_name == "address":
                return PureInput.as_input(bcs.Address.from_str(value))
            if type_name == "String":
                return PureInput.as_input(value)
            raise ValueError(f"Unknown scalar type: {type_name}")

        if isinstance(body, OpenMoveVectorBodyGQL):
            return bcs.BuilderArg("Pure", _raw_value(body, value))

        if isinstance(body, OpenMoveDatatypeBodyGQL):
            type_name = body.type_name
            if type_name == "Option":
                return self._encode_option(body.type_parameters, value, ref)
            if _is_pure_datatype(body.module, type_name):
                return bcs.BuilderArg("Pure", _raw_value(body, value))
            is_receiving = type_name == "Receiving"
            is_mutable = ref == "&mut"
            return self.fetch_or_transpose_object(value, is_receiving, is_mutable, body)

        if isinstance(body, OpenMoveTypeParamBodyGQL):
            return self.fetch_or_transpose_object(value, False, ref == "&mut", None)

        raise TypeError(f"Unhandled body type for encoding: {type(body)}")

    def build_args(
        self,
        in_args: list[Any],
        func_params: list[OpenMoveTypeGQL],
    ) -> list[Any]:
        """Encode user-supplied args against OpenMoveTypeGQL parameter list.

        TxContext is already filtered from func_params by MoveFunctionGQL.from_query.
        bcs.Argument values are passed through without encoding.
        Raises ValueError on arg count mismatch.
        """
        if len(in_args) != len(func_params):
            raise ValueError(
                f"Argument count mismatch: expected {len(func_params)}, got {len(in_args)}"
            )
        result: list[Any] = []
        for value, param in zip(in_args, func_params):
            if isinstance(value, bcs.Argument):
                result.append(value)
                continue
            encoded = self._encode_arg(
                param.signature.body, value, param.signature.ref
            )
            result.append(encoded)
        return result
