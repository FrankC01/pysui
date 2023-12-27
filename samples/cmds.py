#    Copyright Frank V. Castellucci
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
import sys
from typing import Union, Any
from pysui import (
    __version__,
    SyncClient,
    SuiRpcResult,
    handle_result,
    SuiAddress,
    ObjectID,
)
from pysui.sui.sui_txn import SyncTransaction
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR
from pysui.sui.sui_txresults.package_meta import (
    SuiMoveScalarArgument,
    SuiMoveVector,
    SuiParameterReference,
)
from pysui.sui.sui_types.event_filter import (
    AllFilter,
    MoveEventTypeQuery,
    MoveModuleEventQuery,
    SenderEventQuery,
    TimeRangeEventQuery,
    TransactionEventQuery,
)
from pysui.sui.sui_types.scalars import (
    SuiBoolean,
    SuiString,
    SuiU8,
    SuiU16,
    SuiU32,
    SuiU64,
    SuiU128,
    SuiU256,
)
from pysui.sui.sui_types.collections import SuiMap, EventID

from pysui.sui.sui_builders.get_builders import (
    GetCommittee,
    GetTotalTxCount,
    GetTx,
)

from pysui.sui.sui_excepts import (
    SuiMiisingBuildFolder,
    SuiPackageBuildFail,
    SuiMiisingModuleByteCode,
)
from pysui.sui.sui_txresults.single_tx import SuiCoinObjects


def sdk_version(_client: SyncClient, _args: argparse.Namespace) -> None:
    """Dispay version(s)."""
    print(f"pysui SDK version: {__version__} SUI RPC API version {_client.rpc_version}")


def sui_active_address(client: SyncClient, _args: argparse.Namespace) -> None:
    """Print active address."""
    print()
    print(f"Active address = {client.config.active_address.identifier}")


def sui_addresses(client: SyncClient, _args: argparse.Namespace) -> None:
    """Print all address."""
    print()
    print("Addresses")
    print("---------")
    for addy in client.config.addresses:
        if addy == client.config.active_address:
            print(f"{addy} <-- active")
        else:
            print(addy)


def sui_gas(client: SyncClient, args: argparse.Namespace) -> None:
    """Get gas for address."""

    def _detail_gas_objects(gas_objects: SuiCoinObjects) -> None:
        total = 0
        print()
        header_object_id = "Gas Object ID"
        header_mist = "Mist"
        header_sui = "SUI"
        header_str = format(
            f"{header_object_id:^72s}{header_mist:^12s}{header_sui:^15s}"
        )
        print(header_str)
        for _ in range(0, len(header_str)):
            print("-", end="")
        print()
        for gas_object in gas_objects.data:
            balance = int(gas_object.balance)
            total += balance
            print(
                f"{gas_object.coin_object_id:^66s} has {balance:12} -> {balance/SUI_COIN_DENOMINATOR:.8f}"
            )
        print(f"Total gas {total:12} -> {total/SUI_COIN_DENOMINATOR:.8f}")
        print()
        return total

    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    gas_result = client.get_gas(for_owner, True)
    if gas_result.is_ok():
        _detail_gas_objects(gas_result.result_data)
    else:
        print(f"Error: {gas_result.result_string}")


def sui_new_address(client: SyncClient, args: argparse.Namespace) -> None:
    """Generate a new SUI address."""
    if args.ed25519:
        mnen, address = client.config.create_new_keypair_and_address(
            scheme=SignatureScheme.ED25519, alias=args.alias
        )
    elif args.secp256k1:
        mnen, address = client.config.create_new_keypair_and_address(
            scheme=SignatureScheme.SECP256K1, alias=args.alias
        )
    elif args.secp256r1:
        mnen, address = client.config.create_new_keypair_and_address(
            scheme=SignatureScheme.SECP256R1, alias=args.alias
        )
    else:
        raise ValueError(f"Unknown keytype {args}")
    print(f"Keep this passphrase: '{mnen}'")
    print(f"For new address: {address}")
    if args.alias:
        print(f"Alias assigned {client.config.al4addr(address)}")
    else:
        print(f"Alias generated {client.config.al4addr(address)}")


def sui_package(client: SyncClient, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = client.get_package(args.id)
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
        print()
    else:
        print(f"{result.result_string}")


def sui_object(client: SyncClient, args: argparse.Namespace) -> None:
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
    header_str = format(
        f"{header_object_id:^70s}{header_version:^8s}{header_digest:^50s}{header_obj_type:^37}"
    )
    print(header_str)
    for _ in range(0, len(header_str)):
        print("-", end="")
    print()


def sui_objects(client: SyncClient, args: argparse.Namespace) -> None:
    """Show specific Sui object."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    result = client.get_objects(for_owner)
    if result.is_ok():
        if args.json:
            print(result.result_data.to_json(indent=2))
        else:
            _objects_header_print()
            for desc in result.result_data.data:
                print(
                    f"{desc.identifier} |  {desc.version:^8} | {desc.digest} | {desc.object_type}"
                )
    else:
        print(f"{result.result_string}")


def sui_api(client: SyncClient, args: argparse.Namespace) -> None:
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
                print(
                    f"    {parm.name:<20} => required: {parm.required} type: {parm.schema}"
                )
            print()
            print("Returns")
            print(f"    {namedef.result.name:<20} => type: {namedef.result.schema}")
        else:
            print(f"Sui RPC API does not contain {args.name}")

    else:
        for api_name in rpcapi.keys():
            print(api_name)


def transfer_object(client: SyncClient, args: argparse.Namespace) -> None:
    """transfer_object.

    :param client: _description_
    :type client: SyncClient
    :param args: _description_
    :type args: argparse.Namespace
    """
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    txn.transfer_objects(transfers=[args.transfer], recipient=args.recipient)

    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def transfer_sui(client: SyncClient, args: argparse.Namespace) -> None:
    """Transfer gas object."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    txn.transfer_sui(
        recipient=args.recipient,
        from_coin=args.takes,
        amount=int(args.mists),
    )
    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def merge_coin(client: SyncClient, args: argparse.Namespace) -> None:
    """Merge two coins together."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)
    # print(args)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    txn.merge_coins(merge_to=args.primary_coin, merge_from=[args.coin_to_merge])
    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def split_coin(client: SyncClient, args: argparse.Namespace) -> None:
    """Split coin into amounts."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    # print(args)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    coins = txn.split_coin(
        coin=args.coin_object_id, amounts=[int(x) for x in args.mists]
    )
    if not isinstance(coins, list):
        txn.transfer_objects(transfers=[coins], recipient=for_owner)
    else:
        txn.transfer_objects(transfers=coins, recipient=for_owner)
    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def split_coin_equally(client: SyncClient, args: argparse.Namespace) -> None:
    """Split coin equally across counts."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    # print(args)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    txn.split_coin_equal(coin=args.coin_object_id, split_count=int(args.split_count))
    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def publish(client: SyncClient, args: argparse.Namespace) -> None:
    """Publish a sui package."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)
    # print(args)
    try:
        txn = SyncTransaction(client=client, initial_sender=for_owner)
        upc = txn.publish(project_path=args.package)
        txn.transfer_objects(transfers=[upc], recipient=for_owner)
        print(
            handle_result(
                txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
            ).to_json(indent=2)
        )
    except (
        SuiMiisingBuildFolder,
        SuiPackageBuildFail,
        SuiMiisingModuleByteCode,
    ) as exc:
        print(exc.args, file=sys.stderr)


_INT_SCALAR_LOOKUP: dict[str, Any] = {
    "U8": SuiU8,
    "U16": SuiU16,
    "U32": SuiU32,
    "U64": SuiU64,
    "U128": SuiU128,
    "U1256": SuiU256,
}


def _recon_args(args: list[str], parms: list) -> list[Any]:
    """."""
    assert len(args) == len(parms)
    res_args: list[Any] = []
    for index, parm in enumerate(parms):
        if isinstance(parm, SuiParameterReference):
            res_args.append(ObjectID(args[index]))
        elif isinstance(parm, SuiMoveScalarArgument):
            if parm.scalar_type[0] == "U":
                res_args.append(_INT_SCALAR_LOOKUP[parm.scalar_type](int(args[index])))
            else:
                res_args.append(args[index])
        elif isinstance(parm, SuiMoveVector):
            raise NotImplementedError()
    return res_args


def move_call(client: SyncClient, args: argparse.Namespace) -> None:
    """Invoke a Sui move smart contract function."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    target = (
        args.package_object_id.value
        + "::"
        + args.module.value
        + "::"
        + args.function.value
    )
    if args.args:
        arguments = []
        for arg in args.args:
            if arg.value:
                arguments.append(arg.value)
    else:
        arguments = []
    if args.type_arguments:
        type_arguments = [x.value for x in args.type_arguments if x.value]
    else:
        type_arguments = []

    if arguments:
        txn = SyncTransaction(client=client, initial_sender=for_owner)
        (
            _target_id,
            _module_id,
            _function_id,
            parameters,
            _res_count,
        ) = txn._move_call_target_cache(target)

        arguments = _recon_args(arguments, parameters[:-1])
    res = txn.move_call(
        target=target, arguments=arguments, type_arguments=type_arguments
    )
    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def sui_pay(client: SyncClient, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    txn = SyncTransaction(client=client, initial_sender=for_owner)
    if len(args.input_coins) == len(args.mists) == len(args.recipients):
        for x in range(len(args.input_coins)):
            i_coin = txn.split_coin(
                coin=args.input_coins[x], amounts=[int(args.mists[x])]
            )
            txn.transfer_objects(transfers=i_coin, recipient=args.recipients[x])
    else:
        print("Lengths of --input-coins, --amounts and --recipients must be equal.")
        return

    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=args.gas)
        ).to_json(indent=2)
    )


def sui_pay_sui(client: SyncClient, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    t_gas = None
    if len(args.input_coins) == len(args.mists) == len(args.recipients):
        # Take the first as the gas coin
        t_gas = args.input_coins.pop(0)
        t_amt = args.mists.pop(0)
        t_rcp = args.recipients.pop(0)
        # Accumulate the amounts from the other inputs
        # and put in gas
        for x in range(len(args.input_coins)):
            i_coin = txn.split_coin(
                coin=args.input_coins[x], amounts=[int(args.mists[x])]
            )
            txn.merge_coins(merge_to=txn.gas, merge_from=[i_coin])
        # Send some gas to recipient[0]
        txn.transfer_sui(recipient=t_rcp, from_coin=txn.gas, amount=int(t_amt))
        for x in range(len(args.recipients)):
            txn.transfer_sui(
                recipient=args.recipients[x],
                from_coin=txn.gas,
                amount=int(args.amounts[x]),
            )
    else:
        print("Lengths of --input-coins, --amounts and --recipients must be equal.")
        return

    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=t_gas)
        ).to_json(indent=2)
    )


def sui_payall_sui(client: SyncClient, args: argparse.Namespace) -> None:
    """Payment of all of a one whole SUI coin to a recipient."""
    for_owner: SuiAddress = client.config.active_address
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)
    txn = SyncTransaction(client=client, initial_sender=for_owner)
    t_gas = None
    if len(args.input_coins) == 1:
        t_gas = args.input_coins[0]
    else:
        t_gas = args.input_coins.pop(0)
        txn.merge_coins(merge_to=txn.gas, merge_from=args.input_coins)

    txn.transfer_objects(transfers=[txn.gas], recipient=args.recipient)
    # print(txn.raw_kind().to_json(indent=2))
    print(
        handle_result(
            txn.execute(gas_budget=args.budget, use_gas_object=t_gas)
        ).to_json(indent=2)
    )


def committee(client: SyncClient, args: argparse.Namespace) -> None:
    """Committee info request handler."""
    result = client.execute(GetCommittee(args.epoch))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def _convert_event_query(
    var_args: argparse.Namespace, query: Union[SuiString, SuiMap]
) -> dict:
    """Convert arguments to SuiTypes."""
    var_args.pop("version")
    var_args["query"] = query
    if isinstance(var_args["cursor"], str):
        curser_event_id = var_args["cursor"].split(":")
        var_args["cursor"] = EventID(curser_event_id[0], curser_event_id[1])
    var_args["descending_order"] = SuiBoolean(var_args["descending_order"])
    return var_args


def events_all(client: SyncClient, args: argparse.Namespace) -> None:
    """Event info request handler for all events."""
    var_args = vars(args)
    result = client.get_events(**_convert_event_query(var_args, AllFilter(filters=[])))
    # result = client.get_events(query=AllFilter(filters=[]))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_module(client: SyncClient, args: argparse.Namespace) -> None:
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


def events_struct(client: SyncClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = MoveEventTypeQuery(args.struct_name)
    var_args.pop("struct_name")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_sender(client: SyncClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = SenderEventQuery(args.sender)
    var_args.pop("sender")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def events_time(client: SyncClient, args: argparse.Namespace) -> None:
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


def events_tx(client: SyncClient, args: argparse.Namespace) -> None:
    """Event info request handler."""
    var_args = vars(args)
    query = TransactionEventQuery(args.digest)
    var_args.pop("digest")
    result = client.get_events(**_convert_event_query(var_args, query))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def txn_count(client: SyncClient, _args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = client.execute(GetTotalTxCount())
    if result.is_ok():
        print(f"\nTotal count: {result.result_data}")
    else:
        print(f"Error: {result.result_string}")


def txn_txn(client: SyncClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = client.execute(GetTx(digest=args.digest))
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
    else:
        print(f"Error: {result.result_string}")


def sui_faucet(client: SyncClient, args: argparse.Namespace) -> None:
    """Get more gas from SUI faucet."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.addr4al(args.alias)

    result = client.get_gas_from_faucet(for_owner)
    if result.is_ok():
        print(f"Faucet Result: {result.result_data.to_json(indent=2)}.")
    else:
        print(f"Faucet Error: {result.result_string}")


def alias_list(client: SyncClient, args: argparse.Namespace) -> None:
    """List address aliases."""
    print()
    for alias in client.config.aliases:
        print(f"Alias:      {alias}")
        print(f"Address:    {client.config.addr4al(alias)}")
        print(f"PublicKey:  {client.config.pk4al(alias)}\n")


def alias_rename(client: SyncClient, args: argparse.Namespace) -> None:
    """List address aliases."""
    print()
    try:
        client.config.addr4al(args.existing)
    except ValueError as ve:
        print(ve.args)
        return
    try:
        client.config.rename_alias(old_alias=args.existing, new_alias=args.to)
        print(
            f"Renamed {args.existing} to {args.to} for Sui address {client.config.addr4al(args.to)}"
        )
    except ValueError as ve:
        print(ve.args)


SUI_CMD_DISPATCH = {
    "event-all": events_all,
    "event-module": events_module,
    "event-struct": events_struct,
    "event-sender": events_sender,
    "event-time": events_time,
    "event-tx": events_tx,
    "txn-count": txn_count,
    "txn-txn": txn_txn,
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
    "list-aliases": alias_list,
    "rename-aliases": alias_rename,
}
