#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""gRPC transaction argument builder — uses new metadata-driven encoder."""

from typing import Any, Optional

import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txn_arg_encoder import (
    _BaseArgParser,
    OpenMoveDatatypeBodyGQL,
    grpc_to_raw_parameters,
)


class AsyncResolvingArgParser(_BaseArgParser):
    """gRPC argument parser that resolves objects via gRPC GetObject requests."""

    async def fetch_or_transpose_object(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Resolve or transpose an object reference to bcs.ObjectArg.

        Handles four input types:
        - bcs.ObjectArg: already wrapped, return as-is
        - bcs.ObjectReference: wrap in ObjectArg
        - bcs.SharedObjectReference: wrap in ObjectArg
        - sui_prot.Object (gRPC): convert via from_grpc_ref classmethods
        - str: fetch via gRPC, then convert
        """
        object_def: Optional[sui_prot.Object] = None

        # Dispatch on input type
        if isinstance(arg, bcs.ObjectArg):
            return arg

        if isinstance(arg, bcs.ObjectReference):
            if is_receiving:
                return bcs.ObjectArg("Receiving", arg)
            return bcs.ObjectArg("ImmOrOwnedObject", arg)

        if isinstance(arg, bcs.SharedObjectReference):
            return bcs.ObjectArg("SharedObject", arg)

        if isinstance(arg, sui_prot.Object):
            object_def = arg
        elif isinstance(arg, str):
            result = await self._client.execute(
                request=rn.GetObject(object_id=arg)
            )
            if result.is_ok():
                response = result.result_data
                object_def = response.object if hasattr(response, "object") else response
                if object_def is None:
                    raise ValueError(f"{arg} object not found")
            else:
                raise ValueError(f"Failed to fetch object {arg}")
        else:
            raise ValueError(f"Unsupported argument type: {type(arg)}")

        # Determine ownership and construct appropriate reference
        owner_kind = object_def.owner.kind if object_def.owner else None
        owner_type = owner_kind.name if owner_kind else "OWNER_KIND_UNKNOWN"

        if owner_type in ["ADDRESS", "IMMUTABLE", "OBJECT"]:
            obj_ref = bcs.ObjectReference.from_grpc_ref(object_def)
            if is_receiving:
                return bcs.ObjectArg("Receiving", obj_ref)
            return bcs.ObjectArg("ImmOrOwnedObject", obj_ref)

        if owner_type == "SHARED":
            obj_ref = bcs.SharedObjectReference.from_grpc_ref(object_def, is_mutable)
            return bcs.ObjectArg("SharedObject", obj_ref)

        raise ValueError(f"Unknown owner kind {owner_type}")


class UnResolvingArgParser(AsyncResolvingArgParser):
    """gRPC argument parser that defers object resolution."""

    async def fetch_or_transpose_object(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Generate unresolved object references for deferred resolution."""
        return bcs.UnresolvedObjectArg.from_object_ref_type(arg, expected_type)
