#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui DeSertializtion from Sui Wallet JSON standard to pysui GraphQL SuiTransaction."""

import base64
from typing import Any, Optional, Union
import functools as ft

from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
from pysui.sui.sui_txn.transaction_builder import ProgrammableTransactionBuilder
import pysui.sui.sui_types.bcs as bcs
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as tn
import pysui.sui.sui_pgql.pgql_wallet_deser as deser


def _is_unresolved(clup: tuple, item: Any) -> Any:
    """Filter function for Unresolved types.

    :param clup: A tuple of classes of unresolved types
    :type clup: tuple
    :param item: An object to test if in any of the clup classes
    :type item: Any
    :return: The item if true, else None
    :rtype: Any
    """
    if isinstance(item, clup):
        return item
    return None


def _resolve_inputs(client: SuiGQLClient, unresolved: list[tuple[int, Any]]) -> list:
    """Resolves unresolved types from wallet standard.

    :param client: HTTP client
    :type client: SuiGQLClient
    :param unresolved: list of unresolved types
    :type unresolved: list
    :raises ValueError: If unresolved types inlclude UnresolvedPure types (not handled yet)
    :return: List of resolved UnresolvedObjects (i.e. wallet Object)
    :rtype: list
    """
    unrlen = len(unresolved)
    unracc = []
    unoids = [x[1].object_id for x in unresolved]
    # Fetch all unresolved
    result = client.execute_query_node(
        with_node=qn.GetMultipleObjects(object_ids=unoids)
    )
    while result.is_ok():
        unracc.extend(result.result_data.data)
        if result.result_data.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetMultipleObjects(
                    object_ids=unoids, next_page=result.result_data.next_cursor
                )
            )
            if result.is_err():
                raise ValueError(f"Error retrieving objects {result.result_string}")
        else:
            break
    # Lengths must match
    if len(unracc) != unrlen:
        raise ValueError(
            f"Object fetch failure for {unoids} found {[x.object_id for x in unracc]}"
        )
    # Convert to resolve SuiObject in wallet standard
    resobjs: list[tuple[int, deser.SuiObjectCallArg]] = []
    for idx, item in enumerate(unracc):
        if item.object_id != unresolved[idx][1].object_id:
            raise ValueError("Misalignment")
        objcarg = {"object_id": item.object_id}
        if isinstance(item.object_owner, tn.SuiObjectOwnedAddress):
            objcarg["ref_type"] = "ImmOrOwnedObject"
            objcarg["digest"] = item.object_digest
            objcarg["version"] = item.version
        elif isinstance(item.object_owner, tn.SuiObjectOwnedShared):
            objcarg["ref_type"] = "Shared"
            objcarg["initial_shared_version"] = item.object_owner.initial_version
            objcarg["mutable"] = True
        else:
            raise ValueError(f"Object owner not recognized {item.object_owner}")
        resobjs.append((unresolved[idx][0], deser.SuiObjectCallArg.from_dict(objcarg)))

    return resobjs


def _resolve_unresolved(client: SuiGQLClient, wallet: deser.SuiBuilder) -> None:
    """."""
    if unp := list(
        filter(
            ft.partial(_is_unresolved, (deser.SuiUnresolvedPureCallArg)), wallet.inputs
        )
    ):
        raise ValueError(f"pysui does not support Unresolved pures. Found {unp}")

    unresobj: list[tuple[int, deser.SuiUnresolvedObjectCallArg]] = []
    for idx, item in enumerate(wallet.inputs):
        if isinstance(item, deser.SuiUnresolvedObjectCallArg):
            unresobj.append((idx, item))
    if unresobj:
        result: list[deser.SuiObjectCallArg] = _resolve_inputs(client, unresobj)
        for inidx, replacement in result:
            wallet.inputs[inidx] = replacement


def _resolve_object_check(txer: SuiTransaction, wallet: deser.SuiBuilder) -> None:
    """Pre-process that checks for Receiving or Optional object argument.

    If one is found, take the index of the argument and adjust the input type

    :param txer: The transaction being built
    :type txer: SuiTransaction
    :param wallet: The Sui Wallet construct
    :type wallet: deser.SuiBuilder
    """
    for cmd in wallet.commands:
        if isinstance(cmd, deser.SuiMoveCall):
            target = cmd.package + "::" + cmd.module + "::" + cmd.function
            _, _, _, _, arguments = txer.target_function_summary(target)
            # Check for Receiving object argument type
            receiving_input_index: list[int] = []
            optional_input_index: list[int] = []
            argsgql: tn.MoveArgSummary = arguments
            for idx, arg in enumerate(argsgql.arg_list):
                if isinstance(arg, tn.MoveObjectRefArg):
                    if arg.is_receiving:
                        receiving_input_index.append(idx)
                    elif arg.is_optional:
                        optional_input_index.append(idx)
            # Adjust the inputs offset to Receiving
            for arg_indx in receiving_input_index:
                input_type = cmd.arguments[arg_indx]
                if isinstance(input_type, deser.SuiCallArgIndex) and isinstance(
                    wallet.inputs[input_type.index], deser.SuiObjectCallArg
                ):
                    wallet.inputs[input_type.index.index]["ref_type"] = "Receiving"
            # Adjust the inputs offset to Optional
            for arg_indx in optional_input_index:
                input_type = cmd.arguments[arg_indx]
                if isinstance(input_type, deser.SuiCallArgIndex) and isinstance(
                    wallet.inputs[input_type.index], deser.SuiObjectCallArg
                ):
                    wallet.inputs[input_type.index.index]["ref_type"] = "Optional"


def _build_inputs(txer: SuiTransaction, wallet: deser.SuiBuilder) -> list[bcs.Argument]:
    """."""
    txbuilder: ProgrammableTransactionBuilder = txer.builder
    argrefs: list[bcs.Argument] = []
    for input in wallet.inputs:
        if isinstance(input, deser.SuiPureCallArg):
            argrefs.append(
                txbuilder.input_pure(
                    bcs.BuilderArg("Pure", list(base64.b64decode(input.pure_bytes)))
                )
            )

        elif isinstance(input, deser.SuiObjectCallArg):
            addy = bcs.Address.from_str(input.object_id)
            match input.ref_type:
                case "ImmOrOwnedObject" | "Receiving":
                    objarg = bcs.ObjectArg(
                        input.ref_type,
                        bcs.ObjectReference(
                            addy,
                            int(input.version),
                            bcs.Digest.from_str(input.digest),
                        ),
                    )
                    barg = bcs.BuilderArg("Object", addy)
                    argrefs.append(txbuilder.input_obj(barg, objarg))
                case "Shared":
                    objarg = bcs.ObjectArg(
                        "SharedObject",
                        bcs.SharedObjectReference(
                            addy, int(input.initial_shared_version), input.mutable
                        ),
                    )
                    barg = bcs.BuilderArg("Object", addy)
                    argrefs.append(txbuilder.input_obj(barg, objarg))
                case _:
                    raise ValueError(f"Unhandled Object Type {input}")
        else:
            raise ValueError(f"Unknown input type {input}")
    return argrefs


def _arg_for_input(
    ref: Any, txer: SuiTransaction, arg: list[bcs.Argument], crefs: list[bcs.Argument]
) -> bcs.Argument:
    """."""
    result: bcs.Argument = None
    if isinstance(ref, deser.SuiCallArgIndex):
        result = arg[ref.index]
    elif isinstance(ref, deser.SuiCmdResultIndex):
        result = crefs[ref.result]
    elif isinstance(ref, deser.SuiCmdNestedResultIndex):
        result = bcs.Argument("NestedResult", tuple(ref.nested_result))
    elif isinstance(ref, deser.SuiGasCoinArg):
        result = txer.gas
    return result


def _build_commands(
    txer: SuiTransaction, wallet: deser.SuiBuilder, args: list[bcs.Argument]
) -> None:
    """."""
    cmdrefs: list = []
    txbuilder: ProgrammableTransactionBuilder = txer.builder
    for cmd in wallet.commands:
        if isinstance(cmd, deser.SuiMoveCall):
            cmdrefs.append(
                txbuilder.move_call(
                    target=bcs.Address.from_str(cmd.package),
                    module=cmd.module,
                    function=cmd.function,
                    arguments=[
                        _arg_for_input(x, txer, args, cmdrefs) for x in cmd.arguments
                    ],
                    type_arguments=[
                        bcs.TypeTag.type_tag_from(x) for x in cmd.type_arguments
                    ],
                )
            )
        elif isinstance(cmd, deser.SuiSplitCoins):
            cmdrefs.append(
                txbuilder.split_coin(
                    from_coin=_arg_for_input(cmd.coin, txer, args, cmdrefs),
                    amounts=[
                        _arg_for_input(x, txer, args, cmdrefs) for x in cmd.amounts
                    ],
                )
            )

        elif isinstance(cmd, deser.SuiTransferObjects):
            cmdrefs.append(
                txbuilder.transfer_objects(
                    recipient=_arg_for_input(cmd.address, txer, args, cmdrefs),
                    object_ref=[
                        _arg_for_input(x, txer, args, cmdrefs) for x in cmd.objects
                    ],
                )
            )
            # txbuilder.transfer_objects()
        elif isinstance(cmd, deser.SuiMergeCoins):
            cmdrefs.append(
                txbuilder.merge_coins(
                    to_coin=_arg_for_input(cmd.destination, txer, args, cmdrefs),
                    from_coins=[
                        _arg_for_input(x, txer, args, cmdrefs) for x in cmd.sources
                    ],
                )
            )
        elif isinstance(cmd, deser.SuiMakeMoveVec):
            vtag = bcs.OptionalTypeTag()
            if cmd.vec_type:
                vtag = bcs.OptionalTypeTag(bcs.TypeTag.type_tag_from(cmd.vec_type[0]))
            cmdrefs.append(
                txbuilder.make_move_vector(
                    items=[
                        _arg_for_input(x, txer, args, cmdrefs) for x in cmd.elements
                    ],
                    vtype=vtag,
                )
            )
        elif isinstance(cmd, deser.SuiPublish):
            cmdrefs.append(
                txbuilder.publish(
                    [list(base64.b64decode(x)) for x in cmd.modules],
                    [bcs.Address.from_str(x) for x in cmd.dependencies],
                )
            )
        elif isinstance(cmd, deser.SuiUpgrade):
            cmdrefs.append(
                txbuilder.publish_upgrade(
                    [list(base64.b64decode(x)) for x in cmd.modules],
                    [bcs.Address.from_str(x) for x in cmd.dependencies],
                    bcs.Address.from_str(cmd.package),
                    _arg_for_input(cmd.ticket, txer, args, cmdrefs),
                )
            )


def deserialize_to_transaction(
    *, wallet_json: str, **kwargs
) -> tuple[int, SuiTransaction, Union[deser.SuiGasData, None]]:
    """Deserializes a Sui Transaction to a pysui SuiTransaction (GraphQL).

    Notes:

    1. If there are UnresolvedPure this will fail.
    2. $Intents are ignored.
    3. If the 'sender' or 'gas owner' are not resolvable this will fail.

    :param wallet_json: _description_
    :type wallet_json: str
    :param \**kwargs: The keywords passed to instantiating SuiTranaaction
    :type \**kwargs: dict
    :return: A tuple of expiration epoch (if any), the SuiTransaction and optional Sponsor dataclass
    :rtype: tuple[int, SuiTransaction, Union[deser.SuiGasData, None]]
    """
    wallet: deser.SuiBuilder = deser.SuiBuilder.from_json(wallet_json)
    client: SuiGQLClient = kwargs["client"]
    sui_txn = SuiTransaction(**kwargs)
    sponsor: deser.SuiGasData = None

    try:
        # Manage Unresolved
        _resolve_unresolved(client, wallet)
        # Hydrate objects and Receiving adjustments
        _resolve_object_check(sui_txn, wallet)
        # Commands
        _build_commands(sui_txn, wallet, _build_inputs(sui_txn, wallet))
        # Validate sender and sponsors
        # Use config key resolutions
        if wallet.sender:
            _ = client.config.kp4add(wallet.sender)
        if wallet.gas_data:
            sponsor = wallet.gas_data
            if sponsor.owner:
                _ = client.config.kp4add(sponsor.owner)
    except ValueError as ve:
        sui_txn = None
        raise ve

    return wallet.expiration, sui_txn, sponsor
