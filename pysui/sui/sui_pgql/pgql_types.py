#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui data classes for GraphQL results."""

from abc import ABC, abstractmethod

import base64
import dataclasses
from enum import IntEnum
from typing import Any, Optional, Union, Callable
import dataclasses_json
import json
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented


@sync_instrumented("pysui.sui.sui_pgql.pgql_types._fast_flat")
def _fast_flat(in_dict: dict, out_dict: dict):
    """Flattens a nested dictionary."""

    for i_key, i_value in in_dict.items():
        if isinstance(i_value, dict):
            _fast_flat(i_value, out_dict)
        else:
            out_dict[i_key] = i_value


class PGQL_Type(ABC):
    """Base GraphQL to pysui data representation class."""

    @classmethod
    @abstractmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.PGQL_Type.from_query")
    def from_query(cls, in_data: Any = None) -> "PGQL_Type":
        """Converts raw GraphQL result to dataclass type.

        :return: Object instance of implementing class
        :rtype: PGQL_Type
        """


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PagingCursor:
    """Static cursor controls used for paging results."""

    hasNextPage: bool = dataclasses.field(default=False)
    endCursor: Optional[str] = dataclasses.field(default_factory=str)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class NoopGQL(PGQL_Type):
    """Returned when no data received from GraphQL."""

    next_cursor: PagingCursor
    data: list

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.NoopGQL.from_query")
    def from_query(self) -> "NoopGQL":  # type: ignore[override]
        """Deserialize from GraphQL query result dict."""
        return NoopGQL(PagingCursor(), [])


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ErrorGQL(PGQL_Type):
    """."""

    next_cursor: PagingCursor
    data: list
    errors: Any

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.ErrorGQL.from_query")
    def from_query(self, errors: Any) -> "ErrorGQL":  # type: ignore[override]
        """Deserialize from GraphQL query result dict."""
        return ErrorGQL(PagingCursor(), [], errors)


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class KeyValue:
    """Generic map element."""

    key: str
    value: Union[bool, str, None]


from pysui.sui.sui_common.types import TransactionConstraints


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ProtocolConfigGQL:
    """Sui ProtocolConfig representation."""

    protocolVersion: int
    configs: list[KeyValue]
    featureFlags: list[KeyValue]
    transaction_constraints: Optional[TransactionConstraints] = dataclasses.field(
        default_factory=TransactionConstraints
    )

    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.ProtocolConfigGQL._value_to_type")
    def _value_to_type(self, v: Any) -> Any:
        """."""
        if v:
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                if v == "true" or v == "false":
                    return v
                if v.count("."):
                    return float(v)
                return int(v, base=0)
        return None

    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.ProtocolConfigGQL.__post_init__")
    def __post_init__(self):
        """."""
        # Convert configs key/val to dict of key/int
        cfg_dict: dict = {}
        cnst_dict: dict = self.transaction_constraints.to_dict()
        # Turn to key addressable dict
        for ckv in self.configs:
            cfg_dict[ckv.key] = self._value_to_type(ckv.value)

        # Fetch the constraint and replace self.constraints
        for cnst_key in cnst_dict.keys():
            if cnst_key in cfg_dict:
                cnst_dict[cnst_key] = cfg_dict[cnst_key]
        self.transaction_constraints = TransactionConstraints.from_dict(cnst_dict)  # type: ignore[attr-defined]
        self.transaction_constraints.protocol_version = self.protocolVersion

        # Set appropriate features
        feat_dict: dict = {k.key: k.value for k in self.featureFlags}
        # Receive objects
        self.transaction_constraints.receive_objects = feat_dict.get(
            "receive_objects", False
        )
        # Use account balance for gas payments
        self.transaction_constraints.enable_address_balance_gas_payments = (
            feat_dict.get("enable_address_balance_gas_payments", False)
        )

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.ProtocolConfigGQL.from_query")
    def from_query(clz, in_data: dict) -> "ProtocolConfigGQL":  # type: ignore[override]
        """Deserialize from GraphQL query result dict."""
        return ProtocolConfigGQL.from_dict(in_data.pop("protocolConfigs"))  # type: ignore[attr-defined]


# ── OpenMoveType dataclasses — schema-faithful representation ─────────────────


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveScalarBodyGQL:
    """A primitive scalar type body: 'u8', 'bool', 'address', etc."""

    scalar_type: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveVectorBodyGQL:
    """A vector type body: { vector: body }."""

    inner: Union[
        OpenMoveScalarBodyGQL,
        "OpenMoveVectorBodyGQL",
        "OpenMoveDatatypeBodyGQL",
        "OpenMoveTypeParamBodyGQL",
    ]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveDatatypeBodyGQL:
    """A named datatype body: { datatype: { package, module, type, typeParameters } }."""

    package: str
    module: str
    type_name: str
    type_parameters: list[
        Union[
            OpenMoveScalarBodyGQL,
            OpenMoveVectorBodyGQL,
            "OpenMoveDatatypeBodyGQL",
            "OpenMoveTypeParamBodyGQL",
        ]
    ]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveTypeParamBodyGQL:
    """A generic type parameter reference: { typeParameter: N }."""

    index: int


@sync_instrumented("pysui.sui.sui_pgql.pgql_types._body_from_dict")
def _body_from_dict(
    raw: Any,
) -> Union[
    OpenMoveScalarBodyGQL,
    OpenMoveVectorBodyGQL,
    OpenMoveDatatypeBodyGQL,
    OpenMoveTypeParamBodyGQL,
]:
    """Recursively deserialize an OpenMoveTypeSignatureBody from raw JSON."""
    if isinstance(raw, str):
        return OpenMoveScalarBodyGQL(scalar_type=raw)
    if "vector" in raw:
        return OpenMoveVectorBodyGQL(inner=_body_from_dict(raw["vector"]))
    if "datatype" in raw:
        dt = raw["datatype"]
        return OpenMoveDatatypeBodyGQL(
            package=dt["package"],
            module=dt["module"],
            type_name=dt["type"],
            type_parameters=[_body_from_dict(p) for p in dt.get("typeParameters", [])],
        )
    if "typeParameter" in raw:
        return OpenMoveTypeParamBodyGQL(index=raw["typeParameter"])
    raise ValueError(f"Unrecognised OpenMoveTypeSignatureBody: {raw}")


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveTypeSignatureGQL:
    """Decoded OpenMoveTypeSignature scalar: { ref, body }."""

    ref: Optional[str]
    body: Union[
        OpenMoveScalarBodyGQL,
        OpenMoveVectorBodyGQL,
        OpenMoveDatatypeBodyGQL,
        OpenMoveTypeParamBodyGQL,
    ]

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.OpenMoveTypeSignatureGQL.from_query")
    def from_query(cls, raw: dict) -> "OpenMoveTypeSignatureGQL":
        """Deserialize an OpenMoveTypeSignature scalar dict.

        :param raw: dict with optional ``ref`` ("&" or "&mut") and required ``body``
            (an OpenMoveTypeSignatureBody — scalar string, vector dict, datatype dict,
            or typeParameter dict).
        :returns: Fully constructed ``OpenMoveTypeSignatureGQL`` with decoded body variant.
        :raises KeyError: if ``body`` is absent.
        :raises ValueError: if ``body`` shape is not recognised.
        """
        return cls(ref=raw.get("ref"), body=_body_from_dict(raw["body"]))


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveTypeGQL:
    """OpenMoveType: a type with its recursive signature and display repr."""

    signature: OpenMoveTypeSignatureGQL
    repr: str

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.OpenMoveTypeGQL.from_query")
    def from_query(cls, raw: dict) -> "OpenMoveTypeGQL":
        """Deserialize an OpenMoveType wire dict.

        :param raw: dict with keys ``signature`` (OpenMoveTypeSignature scalar dict)
            and ``repr`` (human-readable type string).
        :returns: Fully constructed ``OpenMoveTypeGQL`` with decoded signature and body.
        :raises KeyError: if ``signature`` is absent.
        :raises ValueError: if the signature body shape is not recognised.
        """
        return cls(
            signature=OpenMoveTypeSignatureGQL.from_query(raw["signature"]),
            repr=raw.get("repr", ""),
        )


class RefType(IntEnum):
    """."""

    NO_REF = 0
    REF = 1
    MUT_REF = 2

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.RefType.from_ref")
    def from_ref(cls, rstr: str) -> "RefType":
        """."""
        reftype = RefType.NO_REF
        if rstr:
            if rstr in ["&mut", "MUTABLE"]:
                reftype = RefType.MUT_REF
            elif rstr in ["&", "IMMUTABLE"]:
                reftype = RefType.REF
        return reftype


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveScalarArg:
    """."""

    ref: RefType
    scalar_type: str
    optional: Optional[bool] = False

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.MoveScalarArg.from_str")
    def from_str(cls, in_ref: str, in_type: str) -> "MoveScalarArg":
        """ "."""
        return cls(RefType.from_ref(in_ref), in_type)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveAnyArg:
    """."""

    ref: RefType


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveObjectRefArg:
    """."""

    ref_type: RefType
    type_package: str
    type_module: str
    type_struct: str
    type_params: list
    is_optional: bool
    is_receiving: bool
    has_type: bool

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.MoveObjectRefArg.from_body")
    def from_body(
        cls, in_ref: Union[str, "RefType", None], in_type: dict
    ) -> "MoveObjectRefArg":
        """."""
        ref_type: RefType = (
            in_ref if isinstance(in_ref, RefType) else RefType.from_ref(in_ref)  # type: ignore[arg-type]
        )
        if in_type["type"] == "String" or in_type["type"] == "ID":
            return MoveScalarArg.from_str(in_ref, in_type["type"])  # type: ignore[return-value, arg-type]
        inner_type = in_type.get("typeParameters")
        has_type = bool(inner_type)
        inner_list: list[Any] = []

        if has_type:
            inner_list = []
            for inner_t in inner_type:  # type: ignore[union-attr]
                if isinstance(inner_t, dict):
                    if "typeParameter" in inner_t:
                        inner_list.append(inner_t["typeParameter"])
                    else:
                        if "vector" in inner_t:
                            inner_list.append(
                                MoveVectorArg.from_body(ref_type, inner_t)
                            )
                        else:
                            inner_list.append(
                                MoveObjectRefArg.from_body(
                                    ref_type, inner_t["datatype"]
                                )
                            )
                else:
                    inner_list.append(MoveScalarArg.from_str("", inner_t))

        return cls(
            ref_type,
            in_type["package"],
            in_type["module"],
            in_type["type"],
            inner_list,
            in_type["type"] == "Option",
            in_type["type"] == "Receiving",
            has_type,
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveVectorArg:
    """."""

    ref: RefType
    vec_arg: Union["MoveVectorArg", MoveScalarArg, MoveObjectRefArg, MoveAnyArg]

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.MoveVectorArg.from_body")
    def from_body(
        cls, in_ref: Union[str, "RefType", None], in_type: dict
    ) -> "MoveVectorArg":
        """ "."""
        from_vec: dict = in_type["vector"]
        if not isinstance(from_vec, str):
            if ivec := from_vec.get("vector"):
                if isinstance(ivec, dict) and ivec.get("vector"):
                    return cls(
                        RefType.from_ref(in_ref), cls.from_body(in_ref, from_vec)  # type: ignore[arg-type]
                    )
                else:
                    from_vec = ivec
            else:
                key, value = next(iter(from_vec.items()))
                if key == "datatype":
                    return cls(
                        RefType.from_ref(in_ref),  # type: ignore[arg-type]
                        MoveObjectRefArg.from_body(None, value),
                    )
                elif (
                    len(from_vec) == 1
                    and key == "typeParameter"
                    and isinstance(value, int)
                ):
                    return cls(
                        RefType.from_ref(in_ref),  # type: ignore[arg-type]
                        MoveAnyArg(RefType.from_ref("")),
                    )
                else:
                    raise ValueError(f"Can't resolve {from_vec}")
        return cls(
            RefType.from_ref(in_ref),  # type: ignore[arg-type]
            (
                MoveScalarArg.from_str("", from_vec)
                if isinstance(from_vec, str)
                else MoveObjectRefArg.from_body("", from_vec["datatype"])
            ),
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionGQL:
    """Sui MoveFunction representation."""

    function_name: str
    is_entry: bool
    visibility: str
    type_parameters: list
    parameters: list[OpenMoveTypeGQL]
    returns: list[OpenMoveTypeGQL] = dataclasses.field(default_factory=list)

    @classmethod
    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.MoveFunctionGQL.from_query")
    def from_query(clz, in_data: dict) -> "Union[MoveFunctionGQL, NoopGQL]":  # type: ignore[override]
        """Deserialize from GraphQL query result dict."""
        if (
            in_data.get("object")
            or in_data.get("function_name")
            or in_data.get("functionName")
        ):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            params = [
                OpenMoveTypeGQL.from_query(p) for p in fdict.get("parameters", [])
            ]
            # Skip TxContext parameters at any position
            filtered_params = [
                p
                for p in params
                if not (
                    isinstance(p.signature.body, OpenMoveDatatypeBodyGQL)
                    and p.signature.body.type_name == "TxContext"
                )
            ]
            returns = [OpenMoveTypeGQL.from_query(r) for r in fdict.get("returns", [])]
            return MoveFunctionGQL(
                function_name=fdict.get("functionName", ""),
                is_entry=fdict.get("isEntry", False),
                visibility=fdict.get("visibility", ""),
                type_parameters=fdict.get("typeParameters", []),
                parameters=filtered_params,
                returns=returns,
            )
        return NoopGQL.from_query()

    @sync_instrumented("pysui.sui.sui_pgql.pgql_types.MoveFunctionGQL.arg_summary")
    def arg_summary(self) -> list["OpenMoveTypeGQL"]:
        """Deprecated — use parameters directly."""
        import warnings

        warnings.warn(
            "arg_summary() is deprecated; use parameters (list[OpenMoveTypeGQL]) directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.parameters
