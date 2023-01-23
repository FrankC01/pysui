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
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR
from pysui.sui.sui_types.scalars import SuiBoolean, SuiString
from pysui.sui.sui_types.collections import SuiMap, EventID

from pysui.sui.sui_builders.get_builders import (
    GetCommittee,
    GetTotalTxCount,
    GetTx,
    GetTxsFromAddress,
    GetTxsToAddress,
    GetTxsInputObject,
    GetTxsMutateObject,
    GetTxsMoveFunction,
    MoveEventQuery,
    MoveModuleEventQuery,
    ObjectEventQuery,
    RecipientEventQuery,
    SenderEventQuery,
    TransactionEventQuery,
    TimeRangeEventQuery,
)

from pysui.sui.sui_utils import build_b64_modules
from pysui.sui.sui_excepts import SuiMiisingBuildFolder, SuiPackageBuildFail, SuiMiisingModuleByteCode
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_txresults.single_tx import MoveDataDescriptor, SuiCoinObjects


def sdk_version(_client: SuiClient, _args: argparse.Namespace) -> None:
    """Dispay version(s)."""
    print(f"pysui SDK version: {__version__} SUI RPC API version {_client.rpc_version}")


def sui_active_address(client: SuiClient, _args: argparse.Namespace) -> None:
    """Print active address."""
    print()
    print(f"Active address = {client.config.active_address.identifier}")


def sui_addresses(client: SuiClient, _args: argparse.Namespace) -> None:
    """Print all address."""
    print()
    print("Addresses")
    print("---------")
    for addy in client.config.addresses:
        if addy == client.config.active_address:
            print(f"{addy} <-- active")
        else:
            print(addy)


def sui_gas(client: SuiClient, args: argparse.Namespace) -> None:
    """Get gas for address."""

    def _detail_gas_objects(gas_objects: SuiCoinObjects) -> None:
        total = 0
        print()
        header_object_id = "Gas Object ID"
        header_mist = "Mist"
        header_sui = "SUI"
        header_str = format(f"{header_object_id:^50s}{header_mist:^12s}{header_sui:^15s}")
        print(header_str)
        for _ in range(0, len(header_str)):
            print("-", end="")
        print()
        for gas_object in gas_objects.data:
            balance = gas_object.balance
            total += balance
            print(f"{gas_object.coin_object_id:^45s} has {balance:12} -> {balance/SUI_COIN_DENOMINATOR:.8f}")
        print(f"Total gas {total:12} -> {total/SUI_COIN_DENOMINATOR:.8f}")
        print()
        return total

    gas_result = client.get_gas(args.address)
    if gas_result.is_ok():
        _detail_gas_objects(gas_result.result_data)
    else:
        print(f"Error: {gas_result.result_string}")


def sui_new_address(client: SuiClient, args: argparse.Namespace) -> None:
    """Generate a new SUI address."""
    if args.ed25519:
        mnen, address = client.config.create_new_keypair_and_address(SignatureScheme.ED25519)
    elif args.secp256k1:
        mnen, address = client.config.create_new_keypair_and_address(SignatureScheme.SECP256K1)
    elif args.secp256r1:
        mnen, address = client.config.create_new_keypair_and_address(SignatureScheme.SECP256R1)
    else:
        raise ValueError(f"Unknown keytype {args}")
    print(f"Keep this passphrase '{mnen}'")
    print(f"For new address {address}")


def sui_package(client: SuiClient, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = client.get_package(args.id)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
        print()
    else:
        print(f"{result.result_string}")


def sui_object(client: SuiClient, args: argparse.Namespace) -> None:
    """Show specific object."""
    # if args.version:
    #     sobject = client.execute(GetPastObject(args.id, args.version))
    # else:
    sobject = client.get_object(args.id, args.version)
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
    print()
    header_object_id = "Object ID"
    header_version = "Version"
    header_digest = "Digest"
    header_obj_type = "Object Type"
    header_str = format(f"{header_object_id:^45s}{header_version:^11s}{header_digest:^50s}{header_obj_type:^40}")
    print(header_str)
    for _ in range(0, len(header_str)):
        print("-", end="")
    print()


def sui_objects(client: SuiClient, args: argparse.Namespace) -> None:
    """Show specific object."""

    def _object_type(args: argparse.Namespace) -> SuiRpcResult:
        """Get objects of type from Namespace."""
        if args.data:
            descriptor_result = client.get_address_object_descriptors(MoveDataDescriptor, args.address)
        else:
            descriptor_result = client.get_address_object_descriptors(None, args.address)
        identities = [ids.identifier for ids in descriptor_result.result_data]
        return client.get_objects_for(identities)

    result = _object_type(args)
    if result.is_ok():
        if args.json:
            for desc in result.result_data:
                print(desc.to_json(indent=2))
        else:
            _objects_header_print()
            for desc in result.result_data:
                print(f"{desc.identifier} |  {desc.version:^11} | {desc.digest} | {desc.type_signature}")
    else:
        print(f"{result.result_string}")


def sui_api(client: SuiClient, args: argparse.Namespace) -> None:
    """Display information about Sui RPC API."""
    rpcapi = client.rpc_api

    print(f"RPC API Version: {client.rpc_version}")

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
        for api_name in rpcapi.keys():
            print(api_name)


def transfer_object(client: SuiClient, args: argparse.Namespace) -> None:
    """transfer_object.

    :param client: _description_
    :type client: SuiClient
    :param args: _description_
    :type args: argparse.Namespace
    """
    args.signer = args.signer if args.signer else client.current_address
    var_args = vars(args)
    var_args.pop("version")
    # print(f"transfer_object args {var_args}")
    result = client.transfer_object_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def transfer_sui(client: SuiClient, args: argparse.Namespace) -> None:
    """Transfer gas object."""
    args.signer = args.signer if args.signer else client.current_address
    var_args = vars(args)
    var_args.pop("version")
    # print(f"transfer_sui args {var_args}")
    result = client.transfer_sui_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def merge_coin(client: SuiClient, args: argparse.Namespace) -> None:
    """Merge two coins together."""
    args.signer = args.signer if args.signer else client.current_address
    # print(args)
    var_args = vars(args)
    var_args.pop("version")
    result = client.merge_coin_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def split_coin(client: SuiClient, args: argparse.Namespace) -> None:
    """Split coin into amounts."""
    args.signer = args.signer if args.signer else client.current_address
    # print(args)
    var_args = vars(args)
    var_args.pop("version")
    result = client.split_coin_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def split_coin_equally(client: SuiClient, args: argparse.Namespace) -> None:
    """Split coin equally across counts."""
    args.signer = args.signer if args.signer else client.current_address
    # print(args)
    var_args = vars(args)
    var_args.pop("version")
    result = client.split_coin_equally_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_pay(client: SuiClient, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    args.signer = args.signer if args.signer else client.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = client.pay_txn(**var_args)

    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_pay_sui(client: SuiClient, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    args.signer = args.signer if args.signer else client.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = client.pay_sui_txn(**var_args)

    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_payall_sui(client: SuiClient, args: argparse.Namespace) -> None:
    """Payment of all of a one whole SUI coin to a recipient."""
    args.signer = args.signer if args.signer else client.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = client.pay_allsui_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def move_call(client: SuiClient, args: argparse.Namespace) -> None:
    """Invoke a Sui move smart contract function."""
    args.signer = args.signer if args.signer else client.current_address
    var_args = vars(args)
    var_args.pop("version")
    result = client.move_call_txn(**var_args)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def publish(client: SuiClient, args: argparse.Namespace) -> None:
    """Publish a sui package."""
    # print(args)
    args.sender = args.sender if args.sender else client.config.active_address
    try:
        args.compiled_modules = build_b64_modules(args.compiled_modules)
        var_args = vars(args)
        var_args.pop("version")
        result = client.publish_package_txn(**var_args)
        if result.is_ok():
            print(result.result_data.to_json(indent=2))
        else:
            print(f"Error: {result.result_string}")
    except (SuiMiisingBuildFolder, SuiPackageBuildFail, SuiMiisingModuleByteCode) as exc:
        print(exc.args, file=sys.stderr)


def committee(client: SuiClient, args: argparse.Namespace) -> None:
    """Committee info request handler."""
    result = client.execute(GetCommittee(args.epoch))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def _convert_event_query(var_args: argparse.Namespace, query: Union[SuiString, SuiMap]) -> dict:
    """Convert arguments to SuiTypes."""
    var_args.pop("version")
    var_args["query"] = query
    if isinstance(var_args["cursor"], str):
        curser_event_id = var_args["cursor"].split(":")
        var_args["cursor"] = EventID(int(curser_event_id[0]), int(curser_event_id[1]))
    var_args["descending_order"] = SuiBoolean(var_args["descending_order"])
    return var_args


def events_all(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler for all events."""
    var_args = vars(args)
    result = client.get_events(**_convert_event_query(var_args, SuiString("All")))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_module(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler for module events."""
    var_args = vars(args)
    query = MoveModuleEventQuery(args.module, args.package.value)
    var_args.pop("package")
    var_args.pop("module")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_struct(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = MoveEventQuery(args.struct_name)
    var_args.pop("struct_name")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_object(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = ObjectEventQuery(args.object)
    var_args.pop("object")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_recipient(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = RecipientEventQuery(args.recipient)
    var_args.pop("recipient")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_sender(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = SenderEventQuery(args.sender)
    var_args.pop("sender")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_time(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = TimeRangeEventQuery(args.start_time, args.end_time)
    var_args.pop("start_time")
    var_args.pop("end_time")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_tx(client: SuiClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = TransactionEventQuery(args.digest)
    var_args.pop("digest")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txn_count(client: SuiClient, _args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = client.execute(GetTotalTxCount())
    if result.is_ok():
        print(result.result_data)
    else:
        print(f"Error: {result.result_string}")


def txn_txn(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = client.execute(GetTx(args.digest))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
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


def txns_all(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    result = client.get_txns(**_convert_txns_query(var_args, SuiString("All")))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_movefunc(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsMoveFunction(args.package.value, args.function, args.module)
    var_args.pop("package")
    var_args.pop("function")
    var_args.pop("module")
    result = client.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")
    #


def txns_input(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsInputObject(var_args["input"].value)
    var_args.pop("input")
    result = client.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_mutate(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsMutateObject(var_args["mutated"].value)
    var_args.pop("mutated")
    result = client.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_from(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsFromAddress(args.froms.value.value)
    var_args.pop("froms")
    result = client.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txns_to(client: SuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    var_args = vars(args)
    query = GetTxsToAddress(args.to.value.value)
    var_args.pop("to")
    result = client.get_txns(**_convert_txns_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_faucet(client: SuiClient, args: argparse.Namespace) -> None:
    """Get more gas from SUI faucet."""
    result = client.get_gas_from_faucet(args.address)
    if result.is_ok():
        print(f"Faucet Result: {result.result_data.to_json(indent=2)}.")
    else:
        print(f"Faucet Error: {result.result_string}")


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
    "split-coin-equally": split_coin_equally,
    "call": move_call,
    "publish": publish,
    "committee": committee,
    "version": sdk_version,
    "faucet": sui_faucet,
}
