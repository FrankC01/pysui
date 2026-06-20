#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""JSON interchange (serialize / from_json) for AsyncSuiTransaction — V2 schema."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from pysui.abstracts import AsyncClientBase
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
    from pysui.sui.sui_common.txn_signing import SigningMultiSig

from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 import OpenSignatureBody, OpenSignatureBodyType


# ── Constants ─────────────────────────────────────────────────────────────────

_SUI_FRAMEWORK = "0000000000000000000000000000000000000000000000000000000000000002"


class _UnresolvedPure:
    """Sentinel for an unresolved pure input parsed from JSON; resolved before builder insertion."""

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value


def _coerce_pure_value(value: Any, body: OpenSignatureBody) -> Any:
    """Recursively coerce a raw JSON pure value to the correct typed bcs value."""
    btype = body.type
    if btype == OpenSignatureBodyType.BOOL:
        return bool(value)
    if btype == OpenSignatureBodyType.U8:
        return bcs.SuiU8(int(value))
    if btype == OpenSignatureBodyType.U16:
        return bcs.SuiU16(int(value))
    if btype == OpenSignatureBodyType.U32:
        return bcs.SuiU32(int(value))
    if btype == OpenSignatureBodyType.U64:
        return bcs.SuiU64(int(value))
    if btype == OpenSignatureBodyType.U128:
        return bcs.SuiU128(int(value))
    if btype == OpenSignatureBodyType.U256:
        return bcs.SuiU256(int(value))
    if btype == OpenSignatureBodyType.ADDRESS:
        return bcs.Address.from_str(str(value))
    if btype == OpenSignatureBodyType.DATATYPE:
        return str(value)
    if btype == OpenSignatureBodyType.VECTOR:
        inner = body.type_parameter_instantiation[0]
        return [_coerce_pure_value(v, inner) for v in value]
    raise ValueError(f"Cannot resolve UnresolvedPure for parameter type {btype!r}")


# ── Argument ──────────────────────────────────────────────────────────────────


def _arg_to_json(arg: bcs.Argument) -> dict:
    name = arg.enum_name
    if name == "GasCoin":
        return {"GasCoin": True}
    if name == "Input":
        return {"Input": arg.value}
    if name == "Result":
        return {"Result": arg.value}
    if name == "NestedResult":
        return {"NestedResult": list(arg.value)}
    raise ValueError(f"Unknown Argument variant: {name!r}")


def _json_to_arg(obj: Any) -> bcs.Argument:
    if "GasCoin" in obj:
        return bcs.Argument("GasCoin", None)
    if "Input" in obj:
        return bcs.Argument("Input", int(obj["Input"]))
    if "Result" in obj:
        return bcs.Argument("Result", int(obj["Result"]))
    if "NestedResult" in obj:
        a, b = obj["NestedResult"]
        return bcs.Argument("NestedResult", (int(a), int(b)))
    raise ValueError(f"Unknown Argument shape: {obj!r}")


# ── ObjectReference ───────────────────────────────────────────────────────────


def _obj_ref_to_json(ref: bcs.ObjectReference) -> dict:
    return {
        "objectId": ref.ObjectID.to_address_str(),
        "version": str(ref.SequenceNumber),
        "digest": ref.ObjectDigest.to_digest_str(),
    }


def _json_to_obj_ref(obj: dict) -> bcs.ObjectReference:
    return bcs.ObjectReference(
        bcs.Address.from_str(obj["objectId"]),
        int(obj["version"]),
        bcs.Digest.from_str(obj["digest"]),
    )


# ── CallArg (inputs) ──────────────────────────────────────────────────────────


def _call_arg_to_json(ca: bcs.CallArg) -> dict:  # pylint: disable=too-many-return-statements
    name = ca.enum_name
    if name == "Pure":
        return {"Pure": {"bytes": base64.b64encode(bytes(ca.value)).decode()}}
    if name == "Object":
        obj_arg = ca.value
        on = obj_arg.enum_name
        if on == "ImmOrOwnedObject":
            return {"Object": {"ImmOrOwnedObject": _obj_ref_to_json(obj_arg.value)}}
        if on == "SharedObject":
            s = obj_arg.value
            return {"Object": {"SharedObject": {
                "objectId": s.ObjectID.to_address_str(),
                "initialSharedVersion": str(s.SequenceNumber),
                "mutable": s.Mutable,
            }}}
        if on == "Receiving":
            return {"Object": {"Receiving": _obj_ref_to_json(obj_arg.value)}}
        raise ValueError(f"Unknown ObjectArg variant: {on!r}")
    if name == "FundsWithdrawal":
        fw = ca.value
        amount = str(fw.Reservation.value)
        type_str = fw.Type_.value.type_tag_to_str()
        source_key = fw.Source.enum_name.title()
        return {"FundsWithdrawal": {
            "reservation": {"MaxAmountU64": amount},
            "typeArg": {"Balance": type_str},
            "withdrawFrom": {source_key: True},
        }}
    if name == "UnresolvedObject":
        unres = ca.value
        return {"UnresolvedObject": {"objectId": unres.ObjectStr}}
    raise ValueError(f"Unknown CallArg variant: {name!r}")


def _json_to_call_arg(inp: dict) -> bcs.CallArg:  # pylint: disable=too-many-return-statements
    if "Pure" in inp:
        raw = base64.b64decode(inp["Pure"]["bytes"])
        return bcs.CallArg("Pure", list(raw))
    if "Object" in inp:
        obj = inp["Object"]
        if "ImmOrOwnedObject" in obj:
            return bcs.CallArg(
                "Object",
                bcs.ObjectArg("ImmOrOwnedObject", _json_to_obj_ref(obj["ImmOrOwnedObject"])),
            )
        if "SharedObject" in obj:
            s = obj["SharedObject"]
            shared = bcs.SharedObjectReference(
                bcs.Address.from_str(s["objectId"]),
                int(s["initialSharedVersion"]),
                bool(s["mutable"]),
            )
            return bcs.CallArg("Object", bcs.ObjectArg("SharedObject", shared))
        if "Receiving" in obj:
            return bcs.CallArg(
                "Object",
                bcs.ObjectArg("Receiving", _json_to_obj_ref(obj["Receiving"])),
            )
        raise ValueError(f"Unknown Object sub-type: {obj!r}")
    if "FundsWithdrawal" in inp:
        fw_j = inp["FundsWithdrawal"]
        amount = int(fw_j["reservation"]["MaxAmountU64"])
        type_str = fw_j["typeArg"]["Balance"]
        source_key = next(iter(fw_j["withdrawFrom"])).upper()
        reservation = bcs.Reservation("Amount", amount)
        type_ = bcs.WithdrawalType("Balance", bcs.TypeTag.type_tag_from(type_str))
        source = bcs.WithdrawFrom(source_key, None)
        return bcs.CallArg("FundsWithdrawal", bcs.FundsWithdrawal(reservation, type_, source))
    if "UnresolvedObject" in inp:
        uo = inp["UnresolvedObject"]
        return bcs.CallArg(
            "UnresolvedObject",
            bcs.UnresolvedObjectArg(uo["objectId"], False, False, 0, ""),
        )
    if "UnresolvedPure" in inp:
        return _UnresolvedPure(inp["UnresolvedPure"]["value"])
    raise ValueError(f"Unknown CallArg shape: {inp!r}")


# ── Command serialization ─────────────────────────────────────────────────────


def _command_to_json(cmd: bcs.Command) -> dict:
    return _command_to_json_rewritten(cmd, _arg_to_json)


def _command_to_json_rewritten(  # pylint: disable=too-many-return-statements
    cmd: bcs.Command,
    arg_fn: Any,
) -> dict:
    name = cmd.enum_name
    val = cmd.value
    if name == "MoveCall":
        return {"MoveCall": {
            "package": val.Package.to_address_str(),
            "module": val.Module,
            "function": val.Function,
            "typeArguments": [ta.type_tag_to_str() for ta in val.Type_Arguments],
            "arguments": [arg_fn(a) for a in val.Arguments],
        }}
    if name == "TransferObjects":
        return {"TransferObjects": {
            "objects": [arg_fn(o) for o in val.Objects],
            "address": arg_fn(val.Address),
        }}
    if name == "SplitCoin":
        return {"SplitCoins": {
            "coin": arg_fn(val.FromCoin),
            "amounts": [arg_fn(a) for a in val.Amount],
        }}
    if name == "MergeCoins":
        return {"MergeCoins": {
            "destination": arg_fn(val.ToCoin),
            "sources": [arg_fn(c) for c in val.FromCoins],
        }}
    if name == "Publish":
        return {"Publish": {
            "modules": [base64.b64encode(bytes(m)).decode() for m in val.Modules],
            "dependencies": [d.to_address_str() for d in val.Dependents],
        }}
    if name == "MakeMoveVec":
        type_str = (
            val.TypeTag.value.type_tag_to_str()
            if (val.TypeTag and val.TypeTag.value)
            else None
        )
        return {"MakeMoveVec": {
            "type": type_str,
            "elements": [arg_fn(e) for e in val.Vector],
        }}
    if name == "Upgrade":
        return {"Upgrade": {
            "modules": [base64.b64encode(bytes(m)).decode() for m in val.Modules],
            "dependencies": [d.to_address_str() for d in val.Dependents],
            "package": val.Package.to_address_str(),
            "ticket": arg_fn(val.UpgradeTicket),
        }}
    raise ValueError(f"Unknown Command variant: {name!r}")


def _json_to_command(cmd_dict: dict) -> bcs.Command:  # pylint: disable=too-many-return-statements
    if len(cmd_dict) != 1:
        raise ValueError(f"Expected single-key command dict, got: {cmd_dict!r}")
    name, val = next(iter(cmd_dict.items()))
    if name == "MoveCall":
        pkg = bcs.Address.from_str(val["package"])
        type_args = [bcs.TypeTag.type_tag_from(ta) for ta in val.get("typeArguments", [])]
        args = [_json_to_arg(a) for a in val.get("arguments", [])]
        mc = bcs.ProgrammableMoveCall(pkg, val["module"], val["function"], type_args, args)
        return bcs.Command("MoveCall", mc)
    if name == "TransferObjects":
        return bcs.Command(
            "TransferObjects",
            bcs.TransferObjects(
                [_json_to_arg(o) for o in val["objects"]],
                _json_to_arg(val["address"]),
            ),
        )
    if name == "SplitCoins":
        return bcs.Command(
            "SplitCoin",
            bcs.SplitCoin(
                _json_to_arg(val["coin"]),
                [_json_to_arg(a) for a in val["amounts"]],
            ),
        )
    if name == "MergeCoins":
        return bcs.Command(
            "MergeCoins",
            bcs.MergeCoins(
                _json_to_arg(val["destination"]),
                [_json_to_arg(s) for s in val["sources"]],
            ),
        )
    if name == "Publish":
        modules = [list(base64.b64decode(m)) for m in val["modules"]]
        deps = [bcs.Address.from_str(d) for d in val["dependencies"]]
        return bcs.Command("Publish", bcs.Publish(modules, deps))
    if name == "MakeMoveVec":
        type_str = val.get("type")
        opt_tt = bcs.OptionalTypeTag(
            bcs.TypeTag.type_tag_from(type_str) if type_str else None
        )
        elems = [_json_to_arg(e) for e in val.get("elements", [])]
        return bcs.Command("MakeMoveVec", bcs.MakeMoveVec(opt_tt, elems))
    if name == "Upgrade":
        modules = [list(base64.b64decode(m)) for m in val["modules"]]
        deps = [bcs.Address.from_str(d) for d in val["dependencies"]]
        pkg = bcs.Address.from_str(val["package"])
        ticket = _json_to_arg(val["ticket"])
        return bcs.Command("Upgrade", bcs.Upgrade(modules, deps, pkg, ticket))
    raise ValueError(f"Unknown Command variant: {name!r}")


# ── Intent detection and processing (export) ──────────────────────────────────


def _normalize_address(addr_str: str) -> str:
    s = addr_str.lower()
    if s.startswith("0x"):
        s = s[2:]
    return s.zfill(64)


def _process_intents(
    input_list: list,
    command_list: list,
) -> tuple[list, list]:
    """Detect FundsWithdrawal inputs and emit $Intent commands.

    CoinWithBalance: FundsWithdrawal input referenced by MoveCall to
    0x2::coin/balance::redeem_funds -> replace MoveCall with $Intent.CoinWithBalance.

    FundsWithdrawal: FundsWithdrawal input not referenced by redeem_funds ->
    prepend $Intent.FundsWithdrawal command; rewrite Input(N)->Result(M).
    """
    fw_inputs: dict = {}
    for i, ca in enumerate(input_list):
        if ca.enum_name == "FundsWithdrawal":
            fw_inputs[i] = ca.value

    if not fw_inputs:
        return (
            [_call_arg_to_json(ca) for ca in input_list],
            [_command_to_json(cmd) for cmd in command_list],
        )

    # Classify: which FW inputs are referenced by 0x2::coin/balance::redeem_funds?
    # cwb_map: {input_idx: (cmd_idx, output_kind)}
    cwb_map: dict = {}
    for cmd_idx, cmd in enumerate(command_list):
        if cmd.enum_name != "MoveCall":
            continue
        mc = cmd.value
        if _normalize_address(mc.Package.to_address_str()) != _SUI_FRAMEWORK:
            continue
        if mc.Module == "coin" and mc.Function == "redeem_funds":
            output_kind = "coin"
        elif mc.Module == "balance" and mc.Function == "redeem_funds":
            output_kind = "balance"
        else:
            continue
        for arg in mc.Arguments:
            if arg.enum_name == "Input" and arg.value in fw_inputs:
                cwb_map[arg.value] = (cmd_idx, output_kind)
                break

    # FW inputs not in cwb_map -> FundsWithdrawal intent (prepended commands)
    fw_intent_inputs = {idx: val for idx, val in fw_inputs.items() if idx not in cwb_map}

    # Build new input list: remove all FW inputs; remap remaining indices
    new_inputs_json: list = []
    input_remap: dict = {}
    for i, ca in enumerate(input_list):
        if i not in fw_inputs:
            input_remap[i] = len(new_inputs_json)
            new_inputs_json.append(_call_arg_to_json(ca))

    # Assign Result indices to prepended FW intent commands
    fw_intent_result_map: dict = {}
    fw_intent_cmds_json: list = []
    for input_idx in sorted(fw_intent_inputs):
        fw_val = fw_intent_inputs[input_idx]
        fw_intent_result_map[input_idx] = len(fw_intent_cmds_json)
        fw_intent_cmds_json.append({
            "$Intent": {
                "name": "FundsWithdrawal",
                "inputs": {},
                "data": {
                    "amount": str(fw_val.Reservation.value),
                    "type": fw_val.Type_.value.type_tag_to_str(),
                    "source": fw_val.Source.enum_name,
                },
            }
        })

    n_prepended = len(fw_intent_cmds_json)

    # CWB reverse lookup: cmd_idx -> (input_idx, output_kind)
    cwb_by_cmd: dict = {
        cmd_idx: (inp_idx, ok) for inp_idx, (cmd_idx, ok) in cwb_map.items()
    }

    def _rewrite(arg: bcs.Argument) -> dict:
        aname = arg.enum_name
        if aname == "GasCoin":
            return {"GasCoin": True}
        if aname == "Input":
            idx = arg.value
            if idx in fw_intent_result_map:
                return {"Result": fw_intent_result_map[idx]}
            return {"Input": input_remap.get(idx, idx)}
        if aname == "Result":
            return {"Result": arg.value + n_prepended}
        if aname == "NestedResult":
            cmd_idx, res_idx = arg.value
            return {"NestedResult": [cmd_idx + n_prepended, res_idx]}
        raise ValueError(f"Unknown Argument variant: {aname!r}")

    # Build final command list: prepended FW intents + original commands (with replacements)
    final_cmds_json: list = list(fw_intent_cmds_json)
    for cmd_idx, cmd in enumerate(command_list):
        if cmd_idx in cwb_by_cmd:
            inp_idx, output_kind = cwb_by_cmd[cmd_idx]
            fw_val = fw_inputs[inp_idx]
            final_cmds_json.append({
                "$Intent": {
                    "name": "CoinWithBalance",
                    "inputs": {},
                    "data": {
                        "balance": str(fw_val.Reservation.value),
                        "type": fw_val.Type_.value.type_tag_to_str(),
                        "outputKind": output_kind,
                    },
                }
            })
        else:
            final_cmds_json.append(_command_to_json_rewritten(cmd, _rewrite))

    return new_inputs_json, final_cmds_json


# ── Helpers ───────────────────────────────────────────────────────────────────


def _signer_address_str(signer: Any) -> str:
    if isinstance(signer, str):
        return signer
    return signer.signing_address


# ── Public API ────────────────────────────────────────────────────────────────


def serialize_to_json(txn: AsyncSuiTransaction) -> str:
    """Serialize an AsyncSuiTransaction to V2 JSON interchange format.

    Works at any point: pre-build (gasData fields null) or post-build
    (gasData fully populated from the built TransactionData).
    FundsWithdrawal inputs are emitted as $Intent.FundsWithdrawal or
    $Intent.CoinWithBalance commands as appropriate.
    """
    sig_block = txn._sig_block
    sender = _signer_address_str(sig_block._sender)
    gas_owner = (
        _signer_address_str(sig_block._sponsor) if sig_block._sponsor else sender
    )

    if txn._built_transaction is not None:
        tdv1 = txn._built_transaction.value
        gas = tdv1.GasData
        expiry = tdv1.TransactionExpiration
        expiration: Any = (
            {"Epoch": str(expiry.value)} if expiry.enum_name == "Epoch" else None
        )
        gas_data: dict = {
            "budget": str(gas.Budget),
            "price": str(gas.Price),
            "owner": gas.Owner.to_address_str(),
            "payment": [_obj_ref_to_json(ref) for ref in gas.Payment],
        }
        ptb = tdv1.TransactionKind.value
        input_list = list(ptb.Inputs)
        command_list = list(ptb.Command)
    else:
        expiration = None
        gas_data = {
            "budget": None,
            "price": None,
            "owner": gas_owner,
            "payment": None,
        }
        input_list = list(txn.builder.inputs.values())
        command_list = list(txn.builder.commands)

    inputs_json, commands_json = _process_intents(input_list, command_list)

    doc: dict[str, Any] = {
        "version": 2,
        "sender": sender,
        "expiration": expiration,
        "gasData": gas_data,
        "inputs": inputs_json,
        "commands": commands_json,
    }
    if gas_owner != sender:
        doc["sponsor"] = gas_owner

    return json.dumps(doc, indent=2)


def _rewrite_result_refs(obj: Any, result_map: dict) -> Any:
    """Recursively rewrite Result/NestedResult references using result_map.

    result_map maps json_cmd_idx -> arg dict (e.g. {"Input": N} or {"Result": K}).
    Used during from_json to fix up Result indices when $Intent commands are present.
    """
    if isinstance(obj, dict):
        if len(obj) == 1 and "Result" in obj:
            ref_idx = int(obj["Result"])
            if ref_idx in result_map:
                return result_map[ref_idx]
        elif len(obj) == 1 and "NestedResult" in obj:
            cmd_idx, res_idx = obj["NestedResult"]
            cmd_idx = int(cmd_idx)
            if cmd_idx in result_map:
                mapped = result_map[cmd_idx]
                if "Result" in mapped:
                    return {"NestedResult": [int(mapped["Result"]), int(res_idx)]}
        return {k: _rewrite_result_refs(v, result_map) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rewrite_result_refs(item, result_map) for item in obj]
    return obj


def _parse_json_doc(json_str: str) -> tuple[dict, list[bcs.CallArg], list[dict]]:
    """Parse a V2 JSON interchange string into raw components."""
    doc = json.loads(json_str)
    version = doc.get("version")
    if version != 2:
        raise ValueError(
            f"Only V2 JSON interchange is supported, got version={version!r}"
        )
    inputs = [_json_to_call_arg(inp) for inp in doc.get("inputs", [])]
    raw_commands: list[dict] = list(doc.get("commands", []))
    return doc, inputs, raw_commands


async def from_json_data(
    *,
    json_str: str,
    client: AsyncClientBase,
    sender: Optional[Union[str, SigningMultiSig]] = None,
    sponsor: Optional[Union[str, SigningMultiSig]] = None,
) -> tuple[AsyncSuiTransaction, dict]:
    """Reconstruct an AsyncSuiTransaction from a V2 JSON interchange string.

    :param json_str: V2 JSON interchange string produced by ``export_json``.
    :type json_str: str
    :param client: Async client used to construct the transaction.
    :type client: AsyncClientBase
    :param sender: Optional override for the transaction sender. If omitted, the sender from the JSON is used.
    :type sender: Optional[Union[str, SigningMultiSig]]
    :param sponsor: Optional override for the transaction sponsor. If omitted, the sponsor from the JSON is used (or None if not present).
    :type sponsor: Optional[Union[str, SigningMultiSig]]
    :returns: A tuple of the reconstructed transaction and an info dict containing the JSON-sourced sender, sponsor, gas_budget, use_gas_objects, and txn_expires_after.
    :rtype: tuple[AsyncSuiTransaction, dict]
    """
    from pysui.sui.sui_common.txn_base import FundsSource

    doc, inputs, raw_commands = _parse_json_doc(json_str)

    unresolved: dict[int, Any] = {
        i: ca.value for i, ca in enumerate(inputs) if isinstance(ca, _UnresolvedPure)
    }
    if unresolved:
        from pysui.sui.sui_common.sui_commands import GetFunction as _GetFunction
        from pysui.sui.sui_common.txn_pure import PureInput

        pure_location: dict[int, tuple[str, str, str, int]] = {}
        for raw_cmd in raw_commands:
            if "$Intent" in raw_cmd or "MoveCall" not in raw_cmd:
                continue
            mc = raw_cmd["MoveCall"]
            pkg, mod, func = mc["package"], mc["module"], mc["function"]
            for param_pos, arg_j in enumerate(mc.get("arguments", [])):
                if "Input" in arg_j:
                    idx = int(arg_j["Input"])
                    if idx in unresolved and idx not in pure_location:
                        pure_location[idx] = (pkg, mod, func, param_pos)

        missing = set(unresolved) - set(pure_location)
        if missing:
            raise ValueError(
                f"UnresolvedPure input(s) at indices {sorted(missing)} not referenced by any MoveCall"
            )

        func_cache: dict[tuple[str, str, str], Any] = {}
        for idx, raw_value in unresolved.items():
            pkg, mod, func, param_pos = pure_location[idx]
            key = (pkg, mod, func)
            if key not in func_cache:
                res = await client.execute(
                    command=_GetFunction(package=pkg, module_name=mod, function_name=func)
                )
                if not res.is_ok():
                    raise ValueError(
                        f"GetFunction failed for {pkg}::{mod}::{func}: {res.result_string}"
                    )
                func_cache[key] = res.result_data.function
            body = func_cache[key].parameters[param_pos].body
            coerced = _coerce_pure_value(raw_value, body)
            inputs[idx] = bcs.CallArg("Pure", PureInput.pure(coerced))

    json_sender = doc.get("sender")
    gas_data = doc.get("gasData") or {}
    gas_owner = gas_data.get("owner")
    json_sponsor = gas_owner if (gas_owner and gas_owner != json_sender) else None

    txn = await client.transaction(
        initial_sender=sender if sender is not None else json_sender,
        initial_sponsor=sponsor if sponsor is not None else json_sponsor,
    )
    built_args: list[bcs.BuilderArg] = []
    for ca in inputs:
        if ca.enum_name == "Pure":
            barg = bcs.BuilderArg("Pure", ca.value)
        elif ca.enum_name == "Object":
            barg = bcs.BuilderArg("Object", ca.value.value.ObjectID)
        elif ca.enum_name == "UnresolvedObject":
            barg = bcs.BuilderArg("Unresolved", ca.value.ObjectStr)
        elif ca.enum_name == "FundsWithdrawal":
            barg = bcs.BuilderArg("Withdrawal", ca.value)
        else:
            raise ValueError(f"Unknown CallArg variant: {ca.enum_name!r}")
        txn.builder.inputs[barg] = ca
        built_args.append(barg)

    if len(txn.builder.inputs) != len(built_args):
        raise ValueError(
            f"Input reconstruction mismatch: expected {len(built_args)} inputs, "
            f"got {len(txn.builder.inputs)} in builder"
        )
    missing = [arg for arg in built_args if arg not in txn.builder.inputs]
    if missing:
        raise ValueError(
            f"Input reconstruction incomplete: {len(missing)} BuilderArg(s) not found in builder inputs"
        )

    result_map: dict = {}
    for json_cmd_idx, raw_cmd in enumerate(raw_commands):
        if "$Intent" in raw_cmd:
            intent = raw_cmd["$Intent"]
            name = intent["name"]
            data = intent.get("data", {})
            if name == "FundsWithdrawal":
                arg = await txn.withdrawal(
                    amount=int(data["amount"]),
                    coin_type=data.get("type"),
                    source=FundsSource[data.get("source", "SENDER")],
                )
                result_map[json_cmd_idx] = _arg_to_json(arg)
            elif name == "CoinWithBalance":
                output_kind = data.get("outputKind", "coin")
                coin_type = data.get("type")
                amount = int(data["balance"])
                if output_kind == "balance":
                    arg = await txn.create_balance(amount=amount, coin_type=coin_type)
                else:
                    arg = await txn.coin_from_address_accumulator(
                        amount=amount, coin_type=coin_type
                    )
                result_map[json_cmd_idx] = _arg_to_json(arg)
            else:
                raise ValueError(f"Unknown $Intent name: {name!r}")
        else:
            rewritten = _rewrite_result_refs(raw_cmd, result_map)
            txn.builder.commands.append(_json_to_command(rewritten))
            result_map[json_cmd_idx] = {"Result": len(txn.builder.commands) - 1}

    expiration = doc.get("expiration")
    txn_expires: Optional[int] = None
    if isinstance(expiration, dict) and "Epoch" in expiration:
        txn_expires = int(expiration["Epoch"])

    budget = gas_data.get("budget")
    payment = gas_data.get("payment")
    if budget is not None and payment is not None:
        gas_obj_ids = [p["objectId"] for p in payment]
        await txn.build(
            gas_budget=int(budget),
            use_gas_objects=gas_obj_ids,
            txn_expires_after=txn_expires,
        )
    info: dict = {
        "sender": json_sender,
        "sponsor": json_sponsor,
        "gas_budget": int(budget) if budget is not None else None,
        "use_gas_objects": payment if payment else None,
        "txn_expires_after": txn_expires,
    }
    return txn, info
