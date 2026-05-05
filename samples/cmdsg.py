#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


"""Commands and dispatch dict."""
import argparse
import asyncio
import json
from pathlib import Path
import pprint
import sys
from pysui import __version__, SuiRpcResult

from pysui import PysuiConfiguration, PysuiClient
from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes
import pysui.sui.sui_common.sui_commands as cmd

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_constants import SUI_COIN_DENOMINATOR

from pysui.sui.sui_excepts import (
    SuiMiisingBuildFolder,
    SuiPackageBuildFail,
    SuiMiisingModuleByteCode,
)
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_gas_objects,
    async_get_all_owned_objects,
    async_get_all_address_balances,
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


async def transaction_execute(
    *, txb: AsyncSuiTransaction, use_gas_objects: list[str] = None, gas_budget: str = None
):
    """Uses fully built and serialized TransactionData for ExecuteTransaction."""
    txdict = await txb.build_and_sign(use_gas_objects=use_gas_objects, gas_budget=gas_budget)
    handle_result(
        await txb.client.execute_query_node(with_node=qn.ExecuteTransaction(**txdict))
    )


async def sdk_version(client: PysuiClient, _args: argparse.Namespace) -> None:
    """Display version(s)."""
    print(f"pysui SDK version: {__version__} SUI GraphQL Schema version {client.schema_version()}")


async def sui_active_address(client: PysuiClient, _args: argparse.Namespace) -> None:
    """Print active address."""
    print()
    print(f"Active address = {client.config.active_address}")


async def sui_addresses(client: PysuiClient, args: argparse.Namespace) -> None:
    """Print all addresses."""
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


async def sui_gas(client: PysuiClient, args: argparse.Namespace) -> None:
    """Get gas for address."""

    def _detail_gas_objects(gas_objects: list[ptypes.SuiCoinObjectGQL]) -> None:
        print()
        header_object_id = "Gas Object ID"
        header_mist = "Mist"
        header_sui = "SUI"
        header_status = "Status"
        header_str = format(
            f"{header_object_id:^72s}{header_mist:^12s}{header_sui:^15s}{header_status}"
        )
        print(header_str)
        for _ in range(0, len(header_str)):
            print("-", end="")
        print()
        for gas_object in gas_objects:
            if gas_object.previous_transaction:
                status = "Active"
            else:
                status = "Pruned"
            balance = int(gas_object.balance)
            print(
                f"{gas_object.coin_object_id:^66s} has {balance:12} -> {balance/SUI_COIN_DENOMINATOR:>8.4f}    {status}"
            )
        return None

    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    try:
        all_gas = await async_get_all_owned_gas_objects(for_owner, client, not args.include_pruned)
        abal_res = await client.execute_query_node(
            with_node=qn.GetAddressCoinBalance(owner=client.config.active_address)
        )
        if abal_res.is_ok():
            _detail_gas_objects(all_gas)
            balances = abal_res.result_data.balance
            print(
                f"\nCoin-All gas: {balances.coin_balance:12} -> {balances.coin_balance/SUI_COIN_DENOMINATOR:>8.4f}"
            )
            print(
                f"Addr-All gas: {balances.address_balance:12} -> {balances.address_balance/SUI_COIN_DENOMINATOR:>8.4f}"
            )
            print(
                f"   Total gas: {balances.total_balance:12} -> {balances.total_balance/SUI_COIN_DENOMINATOR:>8.4f}\n"
            )
        else:
            print(f"Error retrieving address balance {abal_res.result_string}")
    except ValueError as ve:
        raise ve


async def address_coins(client: PysuiClient, args: argparse.Namespace) -> None:
    """Fetch all balance summaries by coin type."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address
    balances = await async_get_all_address_balances(for_owner, client)
    for bal in balances:
        print(bal.to_json(indent=2))


async def sui_new_address(client: PysuiClient, args: argparse.Namespace) -> None:
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


async def sui_package(client: PysuiClient, args: argparse.Namespace) -> None:
    """Get a package object."""
    result: SuiRpcResult = await client.execute_query_node(
        with_node=qn.GetPackage(package=args.id)
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))
        print()
    else:
        print(f"{result.result_string}")


async def sui_object(client: PysuiClient, args: argparse.Namespace) -> None:
    """Show specific object."""
    if args.version:
        sobject = await client.execute_query_node(
            with_node=qn.GetPastObject(object_id=args.id, version=args.version)
        )
    else:
        sobject = await client.execute_query_node(with_node=qn.GetObject(object_id=args.id))

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


async def sui_objects(client: PysuiClient, args: argparse.Namespace) -> None:
    """Show specific Sui objects."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    all_objects: list = await async_get_all_owned_objects(
        for_owner, client, not args.include_pruned
    )

    if args.json:
        for desc in all_objects:
            print(desc.to_json(indent=2))
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


async def transfer_object(client: PysuiClient, args: argparse.Namespace) -> None:
    """Transfer an object."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    await txn.transfer_objects(transfers=[args.transfer], recipient=args.recipient)
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


async def transfer_sui(client: PysuiClient, args: argparse.Namespace) -> None:
    """Transfer gas object."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    await txn.transfer_sui(
        recipient=args.recipient,
        from_coin=args.takes,
        amount=int(args.mists),
    )
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


async def merge_coin(client: PysuiClient, args: argparse.Namespace) -> None:
    """Merge two coins together."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    await txn.merge_coins(merge_to=args.primary_coin, merge_from=[args.coin_to_merge])
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


async def split_coin(client: PysuiClient, args: argparse.Namespace) -> None:
    """Split coin into amounts."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    use_gas_coin = None
    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    if args.coin_object_id:
        target_coin = args.coin_object_id
        use_gas_coin = [args.gas]
    else:
        if args.gas:
            print("Specifying '-g' option while defaulting '-c' is invalid")
            return
        total_mist = 0
        for mist in args.mists:
            total_mist += int(mist)
        assets = await async_get_all_owned_gas_objects(owner=for_owner, client=client)
        if assets:
            target_coin = txn.gas
            if len(assets) == 1:
                pass
            else:
                use_gas_coin = []
                assets.sort(key=lambda x: int(x.balance), reverse=True)
                running_total = 0
                for asset in assets:
                    if running_total <= total_mist:
                        use_gas_coin.append(asset)
                        running_total += int(asset.balance)
                    else:
                        break
        else:
            raise ValueError(f"{for_owner} has no Sui coins")

    coins = await txn.split_coin(coin=target_coin, amounts=[int(x) for x in args.mists])
    if not isinstance(coins, list):
        await txn.transfer_objects(transfers=[coins], recipient=for_owner)
    else:
        await txn.transfer_objects(transfers=coins, recipient=for_owner)
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=use_gas_coin,
    )


async def split_coin_equally(client: PysuiClient, args: argparse.Namespace) -> None:
    """Split coin equally across counts."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    await txn.split_coin_equal(coin=args.coin_object_id, split_count=int(args.split_count))
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


async def publish(client: PysuiClient, args: argparse.Namespace) -> None:
    """Publish a sui package."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address
    try:
        txn = await client.transaction(initial_sender=for_owner)
        upc = await txn.publish(project_path=args.package)
        await txn.transfer_objects(transfers=[upc], recipient=for_owner)
        await transaction_execute(
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


async def move_call(client: PysuiClient, args: argparse.Namespace) -> None:
    """Invoke a Sui move smart contract function."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    target = args.package_object_id + "::" + args.module + "::" + args.function
    arguments = [arg for arg in args.args] if args.args else []
    type_arguments = [x for x in args.type_arguments if x] if args.type_arguments else []

    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    await txn.move_call(target=target, arguments=arguments, type_arguments=type_arguments)
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


async def sui_pay(client: PysuiClient, args: argparse.Namespace) -> None:
    """Payments for one or more recipients from one or more coins for one or more amounts."""
    for_owner: str = None
    if args.owner:
        for_owner = args.owner
    elif args.alias:
        for_owner = client.config.address_for_alias(alias_name=args.alias)
    else:
        for_owner = client.config.active_address

    txn: AsyncSuiTransaction = await client.transaction(initial_sender=for_owner)
    if len(args.input_coins) == len(args.mists) == len(args.recipients):
        for x in range(len(args.input_coins)):
            i_coin = await txn.split_coin(
                coin=args.input_coins[x], amounts=[int(args.mists[x])]
            )
            await txn.transfer_objects(transfers=i_coin, recipient=args.recipients[x])
    else:
        print("Lengths of --input-coins, --amounts and --recipients must be equal.")
        return
    await transaction_execute(
        txb=txn,
        gas_budget=args.budget,
        use_gas_objects=[args.gas] if args.gas else None,
    )


async def qgl_query(client: PysuiClient, args: argparse.Namespace) -> None:
    """Run a GQL Query."""
    target: Path = args.query_file
    try:
        result = await client.execute_query_string(string=target.read_text(encoding="utf8"))
        if result.is_ok():
            if args.json:
                print(json.dumps(result.result_data, indent=2))
            elif args.pretty:
                pprint.pprint(result.result_data)
            else:
                print(result.result_data)
        else:
            print(result.result_data)
    except Exception as exc:
        print(exc.args)


async def dryrun_data(client: PysuiClient, args: argparse.Namespace) -> None:
    """Dry run a transaction block's bytes."""
    handle_result(
        await client.execute_query_node(with_node=qn.DryRunTransaction(tx_bytestr=args.txb))
    )


async def dryrun_kind(client: PysuiClient, args: argparse.Namespace) -> None:
    """Dry run a transaction block's kind bytes."""
    options = {
        "sender": args.sender,
        "sponsor": args.sponsor,
        "gasPrice": args.gas_price,
        "gasBudget": args.budget,
        "gasObjects": [x for x in args.gas_objects] if args.gas_objects else [],
    }
    handle_result(
        await client.execute_query_node(
            with_node=qn.DryRunTransactionKind(tx_kind=args.txb, tx_meta=options)
        )
    )


async def execute_txn(client: PysuiClient, args: argparse.Namespace) -> None:
    """Execute a transaction block."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.ExecuteTransaction(tx_bytestr=args.txb, sig_array=args.signatures)
        )
    )


async def txn_count(client: PysuiClient, _args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = await client.execute_query_node(with_node=qn.GetLatestCheckpointSequence())
    if result.is_ok():
        print(f"\nTotal count: {result.result_data.networkTotalTransactions}")
    else:
        print(f"Error: {result.result_string}")


async def txn_txn(client: PysuiClient, args: argparse.Namespace) -> None:
    """Transaction information request handler."""
    result = await client.execute(command=cmd.GetTransaction(digest=args.digest))
    handle_result(result)


async def alias_list(client: PysuiClient, args: argparse.Namespace) -> None:
    """List address aliases."""
    print()
    for alias_obj in client.config.active_group.alias_list:
        print(f"Alias:      {alias_obj.alias}")
        print(
            f"Address:    {client.config.address_for_alias(alias_name=alias_obj.alias)}"
        )
        print(f"PublicKey:  {alias_obj.public_key_base64}\n")


async def alias_rename(client: PysuiClient, args: argparse.Namespace) -> None:
    """Rename an address alias."""
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
    "coins": address_coins,
    "new-address": sui_new_address,
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
