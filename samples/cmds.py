#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-


"""Commands and dispath dict."""
import argparse
import json
import sys
from typing import Union
from pysui import __version__
from pysui.sui.sui_builders import (
    MoveEventQuery,
    MoveModuleEventQuery,
    ObjectEventQuery,
    RecipientEventQuery,
    SenderEventQuery,
    TransactionEventQuery,
    TimeRangeEventQuery,
    GetTxsFromAddress,
    GetTxsToAddress,
    GetTxsInputObject,
    GetTxsMutateObject,
    GetTxsMoveFunction,
)
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR
from pysui.sui.sui_types import SuiBoolean, SuiMap, SuiString, EventID
from pysui.abstracts import SignatureScheme
from pysui.sui.sui_rpc import SuiRpcResult
from pysui.sui.sui_utils import build_b64_modules
from pysui.sui.sui_excepts import SuiMiisingBuildFolder, SuiPackageBuildFail, SuiMiisingModuleByteCode
from .faux_wallet import SuiWallet


def sdk_version(_wallet: SuiWallet, _args: argparse.Namespace) -> None:
    """Dispay version."""
    print(f"pysui SDK version: {__version__}")


def sui_active_address(wallet: SuiWallet, _args: argparse.Namespace) -> None:
    """Print active address."""
    print()
    print(f"Active address = {wallet.current_address.identifier}")


def sui_addresses(wallet: SuiWallet, _args: argparse.Namespace) -> None:
    """Print all address."""
    print()
    print("Addresses")
    print("---------")
    for addy in wallet.addresses:
        if addy == wallet.current_address:
            print(f"{addy} <-- active")
        else:
            print(addy)


def sui_gas(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Print gas information."""

    def _detail_gas(gas_objects: SuiRpcResult):
        if gas_objects.is_ok():
            for gasobj in gas_objects.result_data:
                print(
                    f"{gasobj.identifier} | MISTS: {gasobj.balance:12} SUI: {gasobj.balance / SUI_COIN_DENOMINATOR:.9f}"
                )
            mists = wallet.total_gas(gas_objects.result_data)
            sui = mists / SUI_COIN_DENOMINATOR
            print(f"Total Gas = MISTS: {mists:12} SUI: {sui:.9f}")
        else:
            print(f"Sui RPC Error: {gas_objects.result_string} -> {gas_objects.result_data}")

    _detail_gas(wallet.gas_objects(args.address))


def sui_new_address(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Generate a new SUI address."""
    if args.ed25519:
        print(wallet.create_new_keypair_and_address(SignatureScheme.ED25519))
    else:
        print(wallet.create_new_keypair_and_address(SignatureScheme.SECP256K1))


def sui_package(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = wallet.get_package(args.id)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
        print()
    else:
        print(f"{result.result_string}")


def sui_object(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Show specific object."""
    sobject = wallet.get_object(args.id)
    if sobject.is_ok():
        print("Object")
        if isinstance(sobject.result_data, list):
            for item in sobject.result_data:
                print(item.to_json(indent=2))
        else:
            print(sobject.result_data.to_json(indent=2))
    else:
        print(f"{sobject.result_string}")


def _objects_header_print() -> None:
    """Print non-json object header."""
    # TODO: Clean this up with formatted strings
    print("        Object ID                          ", end=" ")
    print("  Version  ", end=" ")
    print("                    Digest                    ", end=" ")
    print("    Object Type")
    print("--------------------------------------------", end="")
    print("------------", end="")
    print("-------------------------------------------------------------------------")


def sui_objects(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Show specific object."""

    def _object_type(args: argparse.Namespace) -> SuiRpcResult:
        """Get objects of type from Namespace."""
        if args.data:
            return wallet.data_objects(args.address)
        return wallet.get_objects(args.address)

    result = _object_type(args)
    if result.is_ok():
        if args.json:
            for desc in result.result_data:
                print(desc.to_json(indent=2))
        else:
            _objects_header_print()
            for desc in result.result_data:
                print(f"{desc.identifier} |      {desc.version}    | {desc.digest} | {desc.type_signature}")
    else:
        print(f"{result.result_string}")


def sui_api(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Display information about Sui RPC API."""
    rpcapi = wallet.get_rpc_api()

    if args.name:
        if rpcapi.get(args.name, None):
            namedef = rpcapi[args.name]
            print()
            print(f"{namedef.name} - {namedef.description}")
            print("Parameters")
            for parm in namedef.params:
                print(f"    {parm.name:<20} => required: {parm.required} type: {parm.schema}")
            print()
            print("Returns")
            print(f"    {namedef.result.name:<20} => type: {namedef.result.schema}")
        else:
            print(f"Sui RPC API does not contain {args.name}")

    else:
        for api_name in rpcapi:
            print(api_name)


def transfer_object(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """transfer_object.

    :param wallet: _description_
    :type wallet: SuiWallet
    :param args: _description_
    :type args: argparse.Namespace
    """
    args.signer = args.signer if args.signer else wallet.current_address
    var_args = vars(args)
    var_args.pop("version")
    # print(f"transfer_object args {var_args}")
    result = wallet.transfer_object(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def transfer_sui(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transfer gas object."""
    args.signer = args.signer if args.signer else wallet.current_address
    var_args = vars(args)
    var_args.pop("version")
    # print(f"transfer_sui args {var_args}")
    result = wallet.transfer_sui(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def merge_coin(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Merge two coins together."""
    args.signer = args.signer if args.signer else wallet.current_address
    # print(args)
    var_args = vars(args)
    var_args.pop("version")
    result = wallet.merge_coin(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def split_coin(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Merge two coins together."""
    args.signer = args.signer if args.signer else wallet.current_address
    # print(args)
    var_args = vars(args)
    var_args.pop("version")
    result = wallet.split_coin(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_pay(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    args.signer = args.signer if args.signer else wallet.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = wallet.pay_transfer(**var_args)

    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_pay_sui(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    args.signer = args.signer if args.signer else wallet.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = wallet.pay_sui_transfer(**var_args)

    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_payall_sui(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Payment of all of a one whole SUI coin to a recipient."""
    args.signer = args.signer if args.signer else wallet.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = wallet.pay_all_sui_transfer(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def move_call(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Invoke a Sui move smart contract function."""
    args.signer = args.signer if args.signer else wallet.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = wallet.move_call(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def publish(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Publish a sui package."""
    # print(args)
    args.sender = args.sender if args.sender else wallet.current_address
    try:
        args.compiled_modules = build_b64_modules(args.compiled_modules)
        var_args = vars(args)
        var_args.pop("version")
        result = wallet.publish_package(**var_args)
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(f"Error: {result.result_string}")
    except (SuiMiisingBuildFolder, SuiPackageBuildFail, SuiMiisingModuleByteCode) as exc:
        print(exc.args, file=sys.stderr)


def committee(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Committee info request handler."""
    result = wallet.get_committee_info(args.epoch)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def _convert_event_query(var_args: argparse.Namespace, query: Union[SuiString, SuiMap]) -> dict:
    """Convert arguments to SuiTypes."""
    var_args.pop("version")
    var_args["query"] = query
    curser_event_id = var_args["cursor"].split(":")
    var_args["cursor"] = EventID(int(curser_event_id[0]), int(curser_event_id[1]))
    var_args["descending_order"] = SuiBoolean(var_args["descending_order"])
    return var_args


def events_all(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler for all events."""
    var_args = vars(args)
    result = wallet.get_events(**_convert_event_query(var_args, SuiString("All")))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_module(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler for module events."""
    var_args = vars(args)
    query = MoveModuleEventQuery(args.module, args.package.value)
    var_args.pop("package")
    var_args.pop("module")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_struct(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = MoveEventQuery(args.struct_name)
    var_args.pop("struct_name")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_object(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = ObjectEventQuery(args.object)
    var_args.pop("object")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_recipient(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = RecipientEventQuery(args.recipient)
    var_args.pop("recipient")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_sender(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = SenderEventQuery(args.sender)
    var_args.pop("sender")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_time(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = TimeRangeEventQuery(args.start_time, args.end_time)
    var_args.pop("start_time")
    var_args.pop("end_time")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_tx(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = TransactionEventQuery(args.digest)
    var_args.pop("digest")
    result = wallet.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txn_count(wallet: SuiWallet, _args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = wallet.get_total_tx_count()
    if result.is_ok():
        print(result.result_data)
    else:
        print(f"Error: {result.result_string}")


def txn_txn(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = wallet.get_transaction(args.digest)
    if result.is_ok():
        print(json.dumps(result.result_data, indent=2))
    else:
        print(f"Error: {result.result_string}")


def _convert_txns_query(var_args: argparse.Namespace, query: Union[SuiString, SuiMap]) -> dict:
    """Convert arguments to GetTxns."""
    var_args.pop("version")
    var_args["query"] = query
    var_args["cursor"] = SuiString(var_args["digest"])
    var_args.pop("digest")
    var_args["descending_order"] = SuiBoolean(var_args["descending_order"])
    return var_args


def txns_all(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    result = wallet.get_txns(**_convert_txns_query(var_args, SuiString("All")))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_movefunc(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsMoveFunction(args.package.value, args.function, args.module)
    var_args.pop("package")
    var_args.pop("function")
    var_args.pop("module")
    result = wallet.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")
    #


def txns_input(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsInputObject(var_args["input"].value)
    var_args.pop("input")
    result = wallet.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_mutate(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsMutateObject(var_args["mutated"].value)
    var_args.pop("mutated")
    result = wallet.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_from(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsFromAddress(args.froms.value.value)
    var_args.pop("froms")
    result = wallet.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_to(wallet: SuiWallet, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsToAddress(args.to.value.value)
    var_args.pop("to")
    result = wallet.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


SUI_CMD_DISPATCH = {
    "event-all": events_all,
    "event-module": events_module,
    "event-struct": events_struct,
    "event-object": events_object,
    "event-recipient": events_recipient,
    "event-sender": events_sender,
    "event-time": events_time,
    "event-tx": events_tx,
    "txn-count": txn_count,
    "txn-txn": txn_txn,
    "txnsq-all": txns_all,
    "txnsq-movefunc": txns_movefunc,
    "txnsq-input": txns_input,
    "txnsq-mutate": txns_mutate,
    "txnsq-from": txns_from,
    "txnsq-to": txns_to,
    "active-address": sui_active_address,
    "addresses": sui_addresses,
    "gas": sui_gas,
    "new-address": sui_new_address,
    "object": sui_object,
    "objects": sui_objects,
    "package": sui_package,
    "rpcapi": sui_api,
    "transfer-object": transfer_object,
    "transfer-sui": transfer_sui,
    "pay": sui_pay,
    "paysui": sui_pay_sui,
    "payallsui": sui_payall_sui,
    "merge-coin": merge_coin,
    "split-coin": split_coin,
    "call": move_call,
    "publish": publish,
    "committee": committee,
    "version": sdk_version,
}
