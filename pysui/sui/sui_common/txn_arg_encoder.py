#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Transaction argument encoder — metadata-driven, recursive, protocol-agnostic.

Encodes user-supplied Python values into BCS arguments for Sui PTB commands
by dispatching over OpenMoveBodyGQL variant instances from MoveFunctionGQL.

Replaces the brittle two-phase arg_summary() → Move*Arg → encoder pipeline.
"""

import logging
import warnings
from abc import ABC, abstractmethod
from functools import singledispatch
from typing import Any, Optional

from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_utils import serialize_uint32_as_uleb128
import pysui.sui.sui_types as suit

logger = logging.getLogger(__name__)

# Imported here to avoid a circular import; pgql_types imports nothing from sui_common
from pysui.sui.sui_pgql.pgql_types import (  # noqa: E402
    OpenMoveScalarBodyGQL,
    OpenMoveVectorBodyGQL,
    OpenMoveDatatypeBodyGQL,
    OpenMoveTypeParamBodyGQL,
    OpenMoveTypeGQL,
)

# ── Scalar lookup tables ────────────────────────────────────────────────────

_UINT_BCS: dict[str, type] = {
    "u8": bcs.U8,
    "u16": bcs.U16,
    "u32": bcs.U32,
    "u64": bcs.U64,
    "u128": bcs.U128,
    "u256": bcs.U256,
}

_UINT_SUI: dict[str, type] = {
    "u8": suit.SuiU8,
    "u16": suit.SuiU16,
    "u32": suit.SuiU32,
    "u64": suit.SuiU64,
    "u128": suit.SuiU128,
    "u256": suit.SuiU256,
}

# ── Helpers ─────────────────────────────────────────────────────────────────

def _is_pure_datatype(module: str, type_name: str) -> bool:
    """True if this well-known datatype encodes as pure BCS (not an object reference)."""
    return (module, type_name) in {
        ("string", "String"),
        ("option", "Option"),
        ("object", "ID"),
        ("object", "UID"),
        ("vec_map", "VecMap"),
        ("vec_set", "VecSet"),
    }


def _scalar_raw(value: Any, type_name: str) -> list[int]:
    """Encode a scalar value to raw BCS bytes."""
    if type_name in _UINT_BCS:
        return list(_UINT_BCS[type_name].encode(value))
    if type_name == "bool":
        return [1 if value else 0]
    if type_name in ("address", "ID", "UID"):
        return list(bcs.Address.from_str(value).serialize())
    if type_name == "String":
        utf8 = list(bytearray(value, encoding="utf-8"))
        return list(serialize_uint32_as_uleb128(len(utf8))) + utf8
    raise ValueError(f"Unknown scalar type: {type_name}")


# ── Raw (inner) encoders — return list[int] ──────────────────────────────────
# Used for nested encoding within vectors, options, and VecMap/VecSet.

@singledispatch
def _raw_value(body: Any, value: Any) -> list[int]:
    raise TypeError(f"Unhandled body type for raw encoding: {type(body)}")


@_raw_value.register(OpenMoveScalarBodyGQL)
def _raw_scalar(body: OpenMoveScalarBodyGQL, value: Any) -> list[int]:
    return _scalar_raw(value, body.scalar_type)


_SCALAR_CHUNK_BYTES: dict[str, int] = {
    "u16": 2, "u32": 4, "u64": 8, "u128": 16, "u256": 32
}


@_raw_value.register(OpenMoveVectorBodyGQL)
def _raw_vector(body: OpenMoveVectorBodyGQL, value: Any) -> list[int]:
    if isinstance(value, str):
        value = value.encode("utf-8")
    if isinstance(value, (bytes, bytearray)):
        inner = body.inner
        if isinstance(inner, OpenMoveScalarBodyGQL) and inner.scalar_type != "u8":
            chunk = _SCALAR_CHUNK_BYTES.get(inner.scalar_type, 1)
            chunks = [value[i:i + chunk] for i in range(0, len(value), chunk) if len(value[i:i + chunk]) == chunk]
            result = list(serialize_uint32_as_uleb128(len(chunks)))
            for c in chunks:
                result.extend(_scalar_raw(int.from_bytes(c, "little"), inner.scalar_type))
            return result
        elems = list(value)
        return list(serialize_uint32_as_uleb128(len(elems))) + elems
    if not isinstance(value, list):
        raise ValueError(f"Expected list for vector, got {type(value)}")
    encoded_elems: list[list[int]] = [_raw_value(body.inner, elem) for elem in value]
    result = list(serialize_uint32_as_uleb128(len(encoded_elems)))
    for enc in encoded_elems:
        result.extend(enc)
    return result


@_raw_value.register(OpenMoveDatatypeBodyGQL)
def _raw_datatype(body: OpenMoveDatatypeBodyGQL, value: Any) -> list[int]:
    type_name = body.type_name
    if type_name == "Option":
        return _option_raw(body.type_parameters, value)
    if type_name == "String":
        return _scalar_raw(value, "String")
    if type_name in ("ID", "UID"):
        return _scalar_raw(value, "address")
    if type_name == "VecMap":
        return _vecmap_raw(body.type_parameters, value)
    if type_name == "VecSet":
        inner = body.type_parameters[0] if body.type_parameters else None
        if inner is None:
            raise ValueError("VecSet missing type parameter")
        return _raw_vector_of(inner, value)
    raise ValueError(
        f"Cannot raw-encode object type {body.package}::{body.module}::{type_name}"
    )


def _option_raw(type_params: list, value: Any) -> list[int]:
    """Encode Option<T> to raw BCS bytes: 0x00=None, 0x01+T=Some."""
    if value is None or (isinstance(value, list) and len(value) == 1 and value[0] is None):
        return [0]
    inner = type_params[0] if type_params else None
    if inner is None:
        raise ValueError("Option missing type parameter")
    return [1] + _raw_value(inner, value)


def _vecmap_raw(type_params: list, value: Any) -> list[int]:
    """Encode VecMap<K,V> as ULEB128(len) + [(K,V), ...]."""
    if not isinstance(value, (list, dict)):
        raise ValueError("VecMap expects list of (k,v) tuples or a dict")
    pairs = list(value.items()) if isinstance(value, dict) else value
    k_body = type_params[0] if len(type_params) > 0 else None
    v_body = type_params[1] if len(type_params) > 1 else None
    if k_body is None or v_body is None:
        raise ValueError("VecMap missing type parameters")
    result = list(serialize_uint32_as_uleb128(len(pairs)))
    for k, v in pairs:
        result.extend(_raw_value(k_body, k))
        result.extend(_raw_value(v_body, v))
    return result


def _raw_vector_of(inner_body: Any, value: Any) -> list[int]:
    """Encode a sequence of elements using inner_body for each element."""
    if not isinstance(value, list):
        raise ValueError(f"Expected list, got {type(value)}")
    encoded_elems: list[list[int]] = [_raw_value(inner_body, elem) for elem in value]
    result = list(serialize_uint32_as_uleb128(len(encoded_elems)))
    for enc in encoded_elems:
        result.extend(enc)
    return result


# ── Top-level arg encoders — return BCS arg (PureInput or ObjectArg) ─────────
# encode_arg is only called at the top level in build_args.
# bcs.Argument pass-through is handled in build_args before dispatch.

@singledispatch
async def encode_arg(
    body: Any,
    value: Any,
    ref: Optional[str],
    parser: "_BaseArgParser",
) -> Any:
    raise TypeError(f"Unhandled body type for encode_arg: {type(body)}")


@encode_arg.register(OpenMoveScalarBodyGQL)
async def _encode_scalar(
    body: OpenMoveScalarBodyGQL,
    value: Any,
    ref: Optional[str],
    parser: "_BaseArgParser",
) -> Any:
    type_name = body.scalar_type
    if type_name in _UINT_SUI:
        return PureInput.as_input(_UINT_SUI[type_name](value))
    if type_name == "bool":
        return PureInput.as_input(value)
    if type_name in ("address",):
        return PureInput.as_input(bcs.Address.from_str(value))
    if type_name == "String":
        return PureInput.as_input(value)
    raise ValueError(f"Unknown scalar type: {type_name}")


@encode_arg.register(OpenMoveVectorBodyGQL)
async def _encode_vector(
    body: OpenMoveVectorBodyGQL,
    value: Any,
    ref: Optional[str],
    parser: "_BaseArgParser",
) -> Any:
    raw_bytes = _raw_value(body, value)
    return bcs.BuilderArg("Pure", raw_bytes)


@encode_arg.register(OpenMoveDatatypeBodyGQL)
async def _encode_datatype(
    body: OpenMoveDatatypeBodyGQL,
    value: Any,
    ref: Optional[str],
    parser: "_BaseArgParser",
) -> Any:
    type_name = body.type_name

    if type_name == "Option":
        return await _encode_option(body.type_parameters, value, ref, parser)

    if _is_pure_datatype(body.module, type_name):
        raw_bytes = _raw_value(body, value)
        return bcs.BuilderArg("Pure", raw_bytes)

    # Object reference — resolve via protocol-specific parser
    is_receiving = type_name == "Receiving"
    is_mutable = ref == "&mut"
    return await parser.fetch_or_transpose_object(value, is_receiving, is_mutable, body)


@encode_arg.register(OpenMoveTypeParamBodyGQL)
async def _encode_type_param(
    body: OpenMoveTypeParamBodyGQL,
    value: Any,
    ref: Optional[str],
    parser: "_BaseArgParser",
) -> Any:
    return await parser.fetch_or_transpose_object(value, False, ref == "&mut", None)


async def _encode_option(
    type_params: list,
    value: Any,
    ref: Optional[str],
    parser: "_BaseArgParser",
) -> Any:
    """Encode top-level Option<T>, handling optional object references."""
    if value is None or (isinstance(value, list) and value and value[0] is None):
        return bcs.OptionalTypeFactory.as_optional()

    inner = type_params[0] if type_params else None
    if inner is None:
        raise ValueError("Option missing type parameter")

    if isinstance(inner, OpenMoveDatatypeBodyGQL) and not _is_pure_datatype(
        inner.module, inner.type_name
    ):
        obj = await parser.fetch_or_transpose_object(
            value, inner.type_name == "Receiving", ref == "&mut", inner
        )
        return bcs.OptionalTypeFactory.as_unresolved_optional(obj)

    raw = _raw_value(inner, value)
    return bcs.OptionalTypeFactory.as_optional(bcs.BuilderArg("Pure", [1] + raw))


# ── gRPC normalization — Step 6: replace with OpenSignature → OpenMoveTypeGQL ──

def grpc_to_raw_parameters(func_response: Any) -> list["OpenMoveTypeGQL"]:
    """Convert gRPC GetFunctionResponse to list[OpenMoveTypeGQL].

    Deprecated shim — Step 6 will replace this with native conversion in
    pgrpc_txn_async_argb.py. TxContext is skipped here as in MoveFunctionGQL.from_query.
    """
    warnings.warn(
        "grpc_to_raw_parameters() is a temporary shim; replace in Step 6.",
        DeprecationWarning,
        stacklevel=2,
    )
    from pysui.sui.sui_pgql.pgql_types import OpenMoveTypeSignatureGQL

    result: list[OpenMoveTypeGQL] = []
    func = func_response.function
    assert func is not None
    for param in func.parameters:
        body = _grpc_body_to_variant(param.body)
        if body is None:
            continue  # TxContext
        ref: Optional[str] = None
        if param.reference:
            ref = "&mut" if param.reference.name == "MUTABLE" else "&"
        result.append(OpenMoveTypeGQL(
            signature=OpenMoveTypeSignatureGQL(ref=ref, body=body),
            repr="",
        ))
    return result


def _grpc_body_to_variant(
    open_sig_body: Any,
) -> Optional[OpenMoveScalarBodyGQL | OpenMoveVectorBodyGQL | OpenMoveDatatypeBodyGQL | OpenMoveTypeParamBodyGQL]:
    """Convert a gRPC OpenSignatureBody to an OpenMoveBodyGQL variant."""
    _GRPC_SCALAR_MAP: dict[str, str] = {
        "BOOL": "bool",
        "U8": "u8",
        "U16": "u16",
        "U32": "u32",
        "U64": "u64",
        "U128": "u128",
        "U256": "u256",
        "ADDRESS": "address",
    }
    type_name = open_sig_body.type.name

    if type_name in _GRPC_SCALAR_MAP:
        return OpenMoveScalarBodyGQL(scalar_type=_GRPC_SCALAR_MAP[type_name])

    if type_name == "TYPE_PARAMETER":
        return OpenMoveTypeParamBodyGQL(index=open_sig_body.type_parameter)

    if type_name == "VECTOR":
        import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
        inner_proto = open_sig_body.type_parameter_instantiation[0]
        if not isinstance(inner_proto, sui_prot.OpenSignature):
            inner_proto = sui_prot.OpenSignature(body=inner_proto)
        inner = _grpc_body_to_variant(inner_proto.body)
        if inner is None:
            return None
        return OpenMoveVectorBodyGQL(inner=inner)

    if type_name == "DATATYPE":
        type_fqn: str = open_sig_body.type_name
        if "tx_context::TxContext" in type_fqn:
            return None
        parts = type_fqn.split("::")
        package = parts[0] if len(parts) > 0 else ""
        module = parts[1] if len(parts) > 1 else ""
        type_ = parts[2] if len(parts) > 2 else ""
        type_params: list = []
        for tp in open_sig_body.type_parameter_instantiation:
            import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
            inner_proto = tp if isinstance(tp, sui_prot.OpenSignature) else sui_prot.OpenSignature(body=tp)
            converted = _grpc_body_to_variant(inner_proto.body)
            if converted is not None:
                type_params.append(converted)
        return OpenMoveDatatypeBodyGQL(
            package=package,
            module=module,
            type_name=type_,
            type_parameters=type_params,
        )

    raise ValueError(f"Unknown gRPC OpenSignatureBody type: {type_name}")


# ── Abstract base parser ─────────────────────────────────────────────────────

class _BaseArgParser(ABC):
    """Abstract base for transaction argument parsers.

    Concrete subclasses implement fetch_or_transpose_object for their protocol.
    build_args is shared — both GQL and gRPC parsers consume list[OpenMoveTypeGQL].
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    @abstractmethod
    async def fetch_or_transpose_object(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Resolve an object reference to a BCS ObjectArg.

        GQL: fetches via GetObject query.
        gRPC: fetches via gRPC GetObject request.
        UnResolvingArgParser: defers resolution.
        """
        ...

    async def build_args(
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
            encoded = await encode_arg(
                param.signature.body, value, param.signature.ref, self
            )
            result.append(encoded)
        return result
