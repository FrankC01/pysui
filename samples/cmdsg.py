#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


"""Commands and dispath dict."""
import argparse
import json
from pathlib import Path
import pprint
import sys
from pysui import __version__, SuiRpcResult

from pysui.sui.sui_pgql.config.pysui_config import PysuiConfiguration
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR

from pysui.sui.sui_excepts import (
    SuiMiisingBuildFolder,
    SuiPackageBuildFail,
    SuiMiisingModuleByteCode,
)

_SUI_COIN_TYPE: str = (
    "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"
)

_SUI_UPGRADE_CAP: str = (
    "0x0000000000000000000000000000000000000000000000000000000000000002::package::UpgradeCap"
)


def handle_result(result: SuiRpcResult) -> SuiRpcResult:
    """."""
    if result.is_ok():
        if hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
            return result.result_data
        print(result.result_data)
    else:
        print(result.result_string)
        if result.result_data and hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    return result


def transaction_execute(
    *, txb: SuiTransaction, use_gas_objects: list[str] = None, gas_budget: str = None
):
    """Uses fully built and serialized TransactionData for ExecuteTransaction."""
    # Build and sign
    txdict = txb.build_and_sign(use_gas_objects=use_gas_objects, gas_budget=gas_budget)
    # Execute the transaction
    handle_result(
        txb.client.execute_query_node(with_node=qn.ExecuteTransaction(**txdict))
    )


def sdk_version(_client: SuiGQLClient, _args: argparse.Namespace) -> None:
    """Dispay version(s)."""
    print(
        f"pysui SDK version: {__version__} SUI GraphQL Schema version {_client.schema_version()}"
    )


def sui_active_address(client: SuiGQLClient, _args: argparse.Namespace) -> None:
    """Print active address."""
    print()
    print(f"Active address = {client.config.active_address}")


def sui_addresses(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Print all address."""
    print()
    addyt = "Addresses"
    pubkt = "Public Key (flag + key)"
    aliast = "Alias"
    space = " "
    active = "Def"

    if args.details:
        header_str = format(f"{space:^3s}{addyt:^73s}{pubkt:55}{aliast:34}")
    else:
        header_str = format(f"{space:^3s}{addyt:^72s}")
    print(header_str)
    for _ in range(0, len(header_str)):
        print("-", end="")
    print()
    for addy in client.config.active_group.address_list:
        addyl = addy
        if addy == client.config.active_address:
            addyl = f"{active:^3s}{addyl:^72s}"
        else:
            addyl = f"{space:^3s}{addyl:^72s}"
        if args.details:
            palias = client.config.alias_for_address(address=addy)
            addyl = addyl + f" {palias.public_key_base64:54s} {palias.alias}"
        print(addyl)


def sui_gas(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Get gas for address."""

    def _detail_gas_objects(gas_objects: list[ptypes.SuiCoinObjectGQL]) -> None:
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
        for gas_object in gas_objects:
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
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    all_gas = []
    gas_result = client.execute_query_node(with_node=qn.GetCoins(owner=for_owner))
    while gas_result.is_ok():
        all_gas.extend(gas_result.result_data.data)
        if gas_result.result_data.next_cursor.hasNextPage:
            gas_result = client.execute_query_node(
                with_node=qn.GetCoins(
                    owner=for_owner,
                    next_page=gas_result.result_data.next_cursor,
                )
            )
        else:
            break

    # gas_result = client.get_gas(for_owner, True)
    if gas_result.is_ok():
        _detail_gas_objects(all_gas)
    else:
        print(f"Error: {gas_result.result_string}")


def sui_new_address(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Generate a new SUI address."""
    _config: PysuiConfiguration = client.config
    if args.ed25519:
        mnen, address = _config.new_keypair(
            of_keytype=SignatureScheme.ED25519, alias=args.alias, persist=True
        )
    elif args.secp256k1:
        mnen, address = _config.new_keypair(
            of_keytype=SignatureScheme.SECP256K1, alias=args.alias, persist=True
        )
    elif args.secp256r1:
        mnen, address = _config.new_keypair(
            of_keytype=SignatureScheme.SECP256R1, alias=args.alias, persist=True
        )
    else:
        raise ValueError(f"Unknown keytype {args}")
    print(f"Keep this passphrase: '{mnen}'")
    print(f"For new address: {address}")
    if args.alias:
        print(f"Alias assigned {_config.alias_for_address(address=address)}")
    else:
        print(f"Alias generated {_config.alias_for_address(address=address)}")


def sui_package(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = client.execute_query_node(
        with_node=qn.GetPackage(
            package=args.id,
        )
    )

    if result.is_ok():
        print(result.result_data.to_json(indent=2))
        print()
    else:
        print(f"{result.result_string}")


def sui_object(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Show specific object."""
    if args.version:
        sobject = client.execute_query_node(
            with_node=qn.GetPastObject(
                object_id=args.id,
                version=args.version,
            )
        )
    else:
        sobject = client.execute_query_node(with_node=qn.GetObject(object_id=args.id))

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


def sui_objects(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Show specific Sui object."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    all_objects = []
    result = client.execute_query_node(
        with_node=qn.GetObjectsOwnedByAddress(owner=for_owner)
    )
    while result.is_ok():
        all_objects.extend(result.result_data.data)
        if result.result_data.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetObjectsOwnedByAddress(
                    owner=for_owner,
                    next_page=result.result_data.next_cursor,
                )
            )
        else:
            break

    # result = client.get_objects(for_owner)
    if result.is_ok():
        if args.json:
            print(result.result_data.to_json(indent=2))
        else:
            _objects_header_print()
            for desc in all_objects:
                if desc.object_type == _SUI_COIN_TYPE:
                    dobj_type = "Sui Coin"
                elif desc.object_type == _SUI_UPGRADE_CAP:
                    dobj_type = "Upgrade Cap"
                else:
                    dobj_type = desc.object_type
                print(
                    f"{desc.object_id} |  {desc.version:^8} | {desc.object_digest} | {dobj_type}"
                )
    else:
        print(f"{result.result_string}")


def transfer_object(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """transfer_object.

    :param client: _description_
    :type client: SyncClient
    :param args: _description_
    :type args: argparse.Namespace
    """
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn = SuiTransaction(client=client, initial_sender=for_owner)
    txn.transfer_objects(transfers=[args.transfer], recipient=args.recipient)

    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def transfer_sui(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Transfer gas object."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn = SuiTransaction(client=client, initial_sender=for_owner)
    txn.transfer_sui(
        recipient=args.recipient,
        from_coin=args.takes,
        amount=int(args.mists),
    )
    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def merge_coin(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Merge two coins together."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address
    # print(args)
    txn = SuiTransaction(client=client, initial_sender=for_owner)
    txn.merge_coins(merge_to=args.primary_coin, merge_from=[args.coin_to_merge])
    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def split_coin(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Split coin into amounts."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    # print(args)
    txn = SuiTransaction(client=client, initial_sender=for_owner)
    coins = txn.split_coin(
        coin=args.coin_object_id, amounts=[int(x) for x in args.mists]
    )
    if not isinstance(coins, list):
        txn.transfer_objects(transfers=[coins], recipient=for_owner)
    else:
        txn.transfer_objects(transfers=coins, recipient=for_owner)
    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def split_coin_equally(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Split coin equally across counts."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    # print(args)
    txn = SuiTransaction(client=client, initial_sender=for_owner)
    txn.split_coin_equal(coin=args.coin_object_id, split_count=int(args.split_count))
    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def publish(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Publish a sui package."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address
    # print(args)
    try:
        txn = SuiTransaction(client=client, initial_sender=for_owner)
        upc = txn.publish(project_path=args.package)
        txn.transfer_objects(transfers=[upc], recipient=for_owner)
        transaction_execute(
            txb=txn,
            gas_budget=args.budget,
            use_gas_objects=[args.gas] if args.gas else None,
        )
    except (
        SuiMiisingBuildFolder,
        SuiPackageBuildFail,
        SuiMiisingModuleByteCode,
    ) as exc:
        print(exc.args, file=sys.stderr)


def move_call(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Invoke a Sui move smart contract function."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    target = args.package_object_id + "::" + args.module + "::" + args.function
    if args.args:
        arguments = []
        for arg in args.args:
            if hasattr(arg, "value"):
                arguments.append(arg)
            else:
                arguments.append(arg)
    else:
        arguments = []
    if args.type_arguments:
        type_arguments = [x for x in args.type_arguments if x]
    else:
        type_arguments = []

    txn = SuiTransaction(client=client, initial_sender=for_owner)
    res = txn.move_call(
        target=target, arguments=arguments, type_arguments=type_arguments
    )
    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def sui_pay(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn = SuiTransaction(client=client, initial_sender=for_owner)
    if len(args.input_coins) == len(args.mists) == len(args.recipients):
        for x in range(len(args.input_coins)):
            i_coin = txn.split_coin(
                coin=args.input_coins[x], amounts=[int(args.mists[x])]
            )
            txn.transfer_objects(transfers=i_coin, recipient=args.recipients[x])
    else:
        print("Lengths of --input-coins, --amounts and --recipients must be equal.")
        return
    transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


def qgl_query(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Run a GQL Query."""
    target: Path = args.query_file
    try:
        result = client.execute_query_string(string=target.read_text(encoding="utf8"))
        if result.is_ok():
            if args.json:
                print(json.dumps(result.result_data, indent=2))
            elif args.pretty:
                # pprint.pprint(result.result_data, indent=2, compact=False)
                pprint.pprint(result.result_data)
            else:
                print(result.result_data)
        else:
            print(result.result_data)
    except Exception as exc:
        print(exc.args)


def dryrun_data(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Dry run a transaction block's bytes."""
    handle_result(
        client.execute_query_node(with_node=qn.DryRunTransaction(tx_bytestr=args.txb))
    )


def dryrun_kind(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Dry run a transaction block's kind bytes."""
    options = {
        "sender": args.sender,
        "sponsor": args.sponsor,
        "gasPrice": args.gas_price,
        "gasBudget": args.budget,
        "gasObjects": [x for x in args.gas_objects] if args.gas_objects else [],
    }
    handle_result(
        client.execute_query_node(
            with_node=qn.DryRunTransactionKind(tx_bytestr=args.txb, tx_meta=options)
        )
    )


def execute_txn(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Execute a transaction block."""
    handle_result(
        client.execute_query_node(
            with_node=qn.ExecuteTransaction(
                tx_bytestr=args.txb, sig_array=args.signatures
            )
        )
    )


def txn_count(client: SuiGQLClient, _args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = client.execute_query_node(with_node=qn.GetLatestCheckpointSequence())
    if result.is_ok():
        print(f"\nTotal count: {result.result_data.networkTotalTransactions}")
    else:
        print(f"Error: {result.result_string}")


def txn_txn(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = client.execute_query_node(with_node=qn.GetTx(digest=args.digest))
    handle_result(result)


def alias_list(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """List address aliases."""
    print()
    for alias_obj in client.config.active_group.alias_list:
        print(f"Alias:      {alias_obj.alias}")
        print(
            f"Address:    {client.config.address_for_alias(alias_name=alias_obj.alias)}"
        )
        print(f"PublicKey:  {alias_obj.public_key_base64}\n")


def alias_rename(client: SuiGQLClient, args: argparse.Namespace) -> None:
    """List address aliases."""
    print()
    try:
        client.config.address_for_alias(alias_name=args.existing)
    except ValueError as ve:
        print(ve.args)
        return
    try:

        assoc_addy = client.config.rename_alias(
            existing_alias=args.existing, new_alias=args.to, persist=True
        )
        print(f"Renamed {args.existing} to {args.to} for Sui address {assoc_addy}")
    except ValueError as ve:
        print(ve.args)


SUI_CMD_DISPATCH = {
    "txn-count": txn_count,
    "txn-txn": txn_txn,
    "active-address": sui_active_address,
    "addresses": sui_addresses,
    "gas": sui_gas,
    "new-address": sui_new_address,  # TODO: Fix
    "object": sui_object,
    "objects": sui_objects,
    "package": sui_package,
    "transfer-object": transfer_object,
    "transfer-sui": transfer_sui,
    "pay": sui_pay,
    "query": qgl_query,
    "dryrun-data": dryrun_data,
    "dryrun-kind": dryrun_kind,
    "execute-tx": execute_txn,
    "merge-coin": merge_coin,
    "split-coin": split_coin,
    "split-coin-equally": split_coin_equally,
    "call": move_call,
    "publish": publish,
    "version": sdk_version,
    "list-aliases": alias_list,
    "rename-aliases": alias_rename,
}
