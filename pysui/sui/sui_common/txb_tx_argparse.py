#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unified transaction argument parser — stateless w.r.t. mode between calls.

Replaces the four protocol-specific async arg parser classes
(GQL eager, GQL deferred, gRPC eager, gRPC deferred) with a single class.
Mode is per-call data passed by the transaction; the parser instance is
reusable across modes and contexts.
"""

from enum import Enum, auto
from typing import Any, Optional

import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.sui_commands as cmd
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txn_arg_encoder import (
    OpenMoveDatatypeBodyGQL,
    encode_arg,
)
from pysui.sui.sui_common.executors.cache import AsyncObjectCache, ObjectCacheEntry
from pysui.sui.sui_common.executors.object_id_extract import extract_object_id
from pysui.sui.sui_pgql.pgql_types import OpenMoveTypeGQL


class TxnArgMode(Enum):
    """Argument resolution mode for a transaction parse request."""

    EAGER = auto()
    DEFERRED = auto()


class _ModeContext:  # pylint: disable=too-few-public-methods
    """Per-call adapter that supplies fetch_or_transpose_object to encode_arg.

    Created fresh for each build_args / parse call so the parser itself
    carries no per-mode mutable state.
    """

    def __init__(
        self,
        client: Any,
        mode: TxnArgMode,
        object_cache: Optional[AsyncObjectCache],
    ) -> None:
        self._client = client
        self._mode = mode
        self._object_cache = object_cache

    async def fetch_or_transpose_object(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Resolve or defer object reference based on mode."""
        if isinstance(arg, bcs.ObjectArg):
            return arg
        if isinstance(arg, bcs.ObjectReference):
            return bcs.ObjectArg("Receiving" if is_receiving else "ImmOrOwnedObject", arg)
        if isinstance(arg, bcs.SharedObjectReference):
            return bcs.ObjectArg("SharedObject", arg)

        if self._mode == TxnArgMode.DEFERRED:
            return await self._deferred(arg, is_receiving, is_mutable, expected_type)
        return await self._eager(arg, is_receiving, is_mutable, expected_type)

    async def _deferred(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL],
    ) -> bcs.ObjectArg:
        """Return UnresolvedObjectArg, with object_cache lookup first."""
        oid = extract_object_id(arg)

        if self._object_cache is not None:
            entry: Optional[ObjectCacheEntry] = await self._object_cache.get_object(oid)
            if entry is not None:
                if entry.initialSharedVersion is not None:
                    shared_ref = bcs.SharedObjectReference(
                        bcs.Address.from_str(entry.objectId),
                        int(entry.initialSharedVersion),
                        is_mutable,
                    )
                    return bcs.ObjectArg("SharedObject", shared_ref)
                obj_ref = bcs.ObjectReference(
                    bcs.Address.from_str(entry.objectId),
                    int(entry.version),
                    bcs.Digest.from_str(entry.digest),
                )
                return bcs.ObjectArg("Receiving" if is_receiving else "ImmOrOwnedObject", obj_ref)

        ref_type = pgql_type.RefType.MUT_REF if is_mutable else pgql_type.RefType.NO_REF
        type_str = (
            f"{expected_type.package}::{expected_type.module}::{expected_type.type_name}"
            if expected_type is not None
            else ""
        )
        return bcs.UnresolvedObjectArg.from_flags(  # type: ignore[return-value]
            oid,
            is_optional=False,
            is_receiving=is_receiving,
            ref_type=ref_type,
            type_str=type_str,
        )

    async def _eager(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        _expected_type: Optional[OpenMoveDatatypeBodyGQL],
    ) -> bcs.ObjectArg:
        """Resolve object eagerly via on-chain fetch or direct type dispatch."""
        # GQL object types — use GQL reference constructors directly
        if isinstance(
            arg,
            (
                pgql_type.ObjectReadGQL,
                pgql_type.SuiCoinObjectGQL,
                pgql_type.SuiCoinObjectSummaryGQL,
                pgql_type.SuiStakedCoinGQL,
            ),
        ):
            owner_kind = arg.object_owner.obj_owner_kind
            if owner_kind in ("AddressOwner", "Immutable", "Parent"):
                obj_ref = bcs.ObjectReference.from_gql_ref(arg)
                return bcs.ObjectArg("Receiving" if is_receiving else "ImmOrOwnedObject", obj_ref)
            if owner_kind == "Shared":
                shared_ref = bcs.SharedObjectReference.from_gql_ref(arg, is_mutable)
                return bcs.ObjectArg("SharedObject", shared_ref)
            raise ValueError(f"Unknown GQL owner kind: {owner_kind}")

        # gRPC Object type — already canonical
        object_def: Optional[sui_prot.Object] = None
        if isinstance(arg, sui_prot.Object):
            object_def = arg
        elif isinstance(arg, str):
            # cmd.GetObject dispatches to the correct protocol and returns sui_prot.Object
            result = await self._client.execute(command=cmd.GetObject(object_id=arg))
            if result.is_ok():
                object_def = result.result_data
                if object_def is None:
                    raise ValueError(f"{arg} object not found")
            else:
                raise ValueError(f"Failed to fetch object {arg}: {result.result_string}")
        else:
            raise ValueError(f"Unsupported argument type: {type(arg)}")

        owner_kind_proto = object_def.owner.kind if object_def.owner else None
        owner_type = owner_kind_proto.name if owner_kind_proto else "OWNER_KIND_UNKNOWN"

        if owner_type in ("ADDRESS", "IMMUTABLE", "OBJECT"):
            obj_ref = bcs.ObjectReference.from_grpc_ref(object_def)
            return bcs.ObjectArg("Receiving" if is_receiving else "ImmOrOwnedObject", obj_ref)
        if owner_type == "SHARED":
            shared_ref = bcs.SharedObjectReference.from_grpc_ref(object_def, is_mutable)
            return bcs.ObjectArg("SharedObject", shared_ref)

        raise ValueError(f"Unknown gRPC owner kind: {owner_type}")


class TxnArgParse:
    """Unified stateless argument parser for all four async contexts.

    Replaces the four protocol-specific async arg parser classes (GQL eager,
    GQL deferred, gRPC eager, gRPC deferred). Mode and object_cache are
    per-call parameters; the parser instance is reusable across all modes.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def parse(  # pylint: disable=too-many-arguments
        self,
        argument: Any,
        *,
        mode: TxnArgMode,
        object_cache: Optional[AsyncObjectCache] = None,
        is_receiving: bool = False,
        is_mutable: bool = False,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Parse a single argument, resolving or deferring based on mode.

        Replaces direct calls to fetch_or_transpose_object in transaction classes.
        """
        ctx = _ModeContext(self._client, mode, object_cache)
        return await ctx.fetch_or_transpose_object(
            argument, is_receiving, is_mutable, expected_type
        )

    async def build_args(
        self,
        in_args: list[Any],
        func_params: list[OpenMoveTypeGQL],
        *,
        mode: TxnArgMode,
        object_cache: Optional[AsyncObjectCache] = None,
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
        ctx = _ModeContext(self._client, mode, object_cache)
        result: list[Any] = []
        for value, param in zip(in_args, func_params):
            if isinstance(value, bcs.Argument):
                result.append(value)
                continue
            encoded = await encode_arg(  # type: ignore[arg-type]
                param.signature.body, value, param.signature.ref, ctx
            )
            result.append(encoded)
        return result
