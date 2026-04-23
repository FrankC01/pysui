#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""GraphQL transaction argument builder — uses new metadata-driven encoder."""

from typing import Any, Optional, Union

import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_query as qn
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txn_arg_encoder import _BaseArgParser, OpenMoveDatatypeBodyGQL


class AsyncResolvingArgParser(_BaseArgParser):
    """GQL argument parser that resolves objects via GetObject queries."""

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
        - ObjectReadGQL: convert via from_gql_ref classmethods
        - str: fetch via GetObject, then convert
        """
        object_def: Optional[pgql_type.ObjectReadGQL] = None

        # Dispatch on input type
        if isinstance(arg, bcs.ObjectArg):
            return arg

        if isinstance(arg, bcs.ObjectReference):
            if is_receiving:
                return bcs.ObjectArg("Receiving", arg)
            return bcs.ObjectArg("ImmOrOwnedObject", arg)

        if isinstance(arg, bcs.SharedObjectReference):
            return bcs.ObjectArg("SharedObject", arg)

        if isinstance(arg, (
            pgql_type.ObjectReadGQL,
            pgql_type.SuiCoinObjectGQL,
            pgql_type.SuiStakedCoinGQL,
            pgql_type.SuiCoinObjectSummaryGQL,
        )):
            object_def = arg
        elif isinstance(arg, str):
            result = await self._client.execute_query_node(
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

        # Determine ownership and construct appropriate reference
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


class UnResolvingArgParser(AsyncResolvingArgParser):
    """GQL argument parser that defers object resolution."""

    async def fetch_or_transpose_object(
        self,
        arg: Any,
        is_receiving: bool,
        is_mutable: bool,
        expected_type: Optional[OpenMoveDatatypeBodyGQL] = None,
    ) -> bcs.ObjectArg:
        """Generate unresolved object references for deferred resolution."""
        return bcs.UnresolvedObjectArg.from_object_ref_type(arg, expected_type)
