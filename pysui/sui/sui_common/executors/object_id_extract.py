#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Utility for extracting a canonical object ID string from any valid command argument type."""

from typing import Any

import pysui.sui.sui_bcs.bcs as bcs


def extract_object_id(arg: Any) -> str:
    """Return the canonical object ID string from any supported input type.

    Supported types:
    - str                        — returned as-is
    - bcs.ObjectReference        — ImmOrOwned / Receiving inner struct
    - bcs.SharedObjectReference  — Shared inner struct
    - bcs.ObjectArg              — RustEnum wrapping the above
    - Any object with object_id attr (GQL ObjectReadGQL, gRPC sui_prot.Object)

    :raises ValueError: for unsupported input types
    """
    if isinstance(arg, str):
        return arg

    if isinstance(arg, bcs.ObjectReference):
        return arg.ObjectID.to_address_str()

    if isinstance(arg, bcs.SharedObjectReference):
        return arg.ObjectID.to_address_str()

    if isinstance(arg, bcs.ObjectArg):
        return arg.value.ObjectID.to_address_str()

    # Duck-typed: GQL ObjectReadGQL and gRPC sui_prot.Object both expose object_id
    object_id = getattr(arg, "object_id", None)
    if isinstance(object_id, str):
        return object_id

    raise ValueError(
        f"extract_object_id: unsupported input type {type(arg).__name__!r}. "
        "Expected str, bcs.ObjectReference, bcs.SharedObjectReference, "
        "bcs.ObjectArg, or an object with an object_id attribute."
    )
