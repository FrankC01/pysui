#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for incremental buildout of Sui GraphQL RPC for Pysui 1.0.0."""

import base64

# import logging

# logging.basicConfig(level=logging.DEBUG)

from pysui import PysuiConfiguration, SuiRpcResult, SyncGqlClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes
from pysui.sui.sui_pgql.pgql_utils import (
    get_all_owned_gas_objects,
    get_all_owned_objects,
)


def handle_result(result: SuiRpcResult) -> SuiRpcResult:
    """."""
    if result.is_ok():
        if hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    else:
        print(result.result_string)
        if result.result_data and hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    return result


def do_coin_meta(client: SyncGqlClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    handle_result(client.execute_query_node(with_node=qn.GetCoinMetaData()))


def do_coins_for_type(client: SyncGqlClient):
    """Fetch coins of specific type for owner."""
    handle_result(
        client.execute_query_node(
            with_node=qn.GetCoins(
                owner=client.config.active_address,
                coin_type="0x2::coin::Coin<0x2::sui::SUI>",
            )
        )
    )


def do_gas(client: SyncGqlClient):
    """Fetch 0x2::sui::SUI (default) for owner."""
    # Returns the first 'page' of coins only
    coins_node = qn.GetCoins(owner=client.config.active_address)
    result = handle_result(client.execute_query_node(with_node=coins_node))
    if result.is_ok():
        print(
            f"Total coins in page: {len(result.result_data.data)} \nhas more: {result.result_data.next_cursor.hasNextPage}"
        )


def do_all_gas(client: SyncGqlClient):
    """Fetch all coins for owner."""
    try:
        # This will include all coins whether active, pruned or deleted.
        # Change only_active to True for only active coins
        all_coins = get_all_owned_gas_objects(
            owner=client.config.active_address, client=client, only_active=False
        )
        for coin in all_coins:
            print(coin.to_json(indent=2))
        print(f"Total coins: {len(all_coins)}")
        print(f"Total mists: {sum([int(x.balance) for x in all_coins])}")

    except ValueError as ve:
        raise ve


def do_gas_ids(client: SyncGqlClient):
    """Fetch coins by the ids."""

    # Use coins found for active address to use to validate
    # fetching by coin ids
    result = client.execute_query_node(
        with_node=qn.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and result.result_data.data:
        cids = [x.coin_object_id for x in result.result_data.data]
        result = handle_result(
            client.execute_query_node(
                with_node=qn.GetMultipleGasObjects(coin_object_ids=cids)
            )
        )
    elif result.is_err():
        print(f"Error calling GraphQL {result.result_string}")
    else:
        print(f"Data return from call is empty {result.result_data.data}")


def do_sysstate(client: SyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query_node(with_node=qn.GetLatestSuiSystemState()))


def do_all_balances(client: SyncGqlClient):
    """Fetch all coin types for active address and total balances.

    Demonstrates paging as well
    """
    result = client.execute_query_node(
        with_node=qn.GetAllCoinBalances(owner=client.config.active_address)
    )
    handle_result(result)
    if result.is_ok():
        while result.result_data.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetAllCoinBalances(
                    owner=client.config.active_address,
                    next_page=result.result_data.next_cursor,
                )
            )
            handle_result(result)
        print("DONE")


def do_object(client: SyncGqlClient):
    """Fetch specific object data.

    To run, replace object_id with object you are interested in.
    """
    gobj = qn.GetObject(object_id="0x6")
    # print(client.query_node_to_string(query_node=gobj))
    handle_result(client.execute_query_node(with_node=gobj))


def do_object_content(client: SyncGqlClient):
    """Fetch minimal object content, basically just reference information.

    Set 'obect_id' to object address of choice.
    """
    gobj = qn.GetObjectContent(
        object_id="0x7658a888e3f2c9c4e80b6ded17f07b4f2a6621195cdd74743a815e1f526969de"
    )
    # print(client.query_node_to_string(query_node=gobj))
    handle_result(client.execute_query_node(with_node=gobj))


def do_past_object(client: SyncGqlClient):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    handle_result(
        client.execute_query_node(
            with_node=qn.GetPastObject(
                object_id="0x2803dd7600c24b4e26e9478e8f32424985c57a7e3fcdd3db7fa063cdf5d4c396",
                version=3,
            )
        )
    )


def do_multiple_object_versions(client: SyncGqlClient):
    """Fetch a past object.
    To run, change the objectID str and version int and add more dicts to the list.
    """
    object_versions = [
        {
            "address": "0x2803dd7600c24b4e26e9478e8f32424985c57a7e3fcdd3db7fa063cdf5d4c396",
            "version": 3,
        }
    ]
    handle_result(
        client.execute_query_node(
            with_node=qn.GetMultipleVersionedObjects(for_versions=object_versions)
        )
    )


def do_multiple_object_content(client: SyncGqlClient):
    """Fetch minimal object content, basically just reference information."""
    gobj = qn.GetMultipleObjectContent(
        object_ids=[
            "0x7658a888e3f2c9c4e80b6ded17f07b4f2a6621195cdd74743a815e1f526969de"
        ]
    )
    # print(client.query_node_to_string(query_node=gobj))
    handle_result(client.execute_query_node(with_node=gobj))


def do_objects(client: SyncGqlClient):
    """Fetch all objects held by owner."""
    try:
        objects: list = get_all_owned_objects(client.config.active_address, client)
        for object in objects:
            print(object.to_json(indent=2))
    except ValueError as ve:
        raise ve


def do_objects_for(client: SyncGqlClient):
    """Fetch specific objects by their ids.

    These are test IDs, replace to run.
    """
    handle_result(
        client.execute_query_node(
            with_node=qn.GetMultipleObjects(
                object_ids=[
                    "0x2803dd7600c24b4e26e9478e8f32424985c57a7e3fcdd3db7fa063cdf5d4c396",
                    "0x285c48a3bc7440f08ad91caf6955f8b9b8c2db69e4b4c5071aa94c2468689d93",
                ]
            )
        )
    )


def do_dynamics(client: SyncGqlClient):
    """Get objects dynamic field and dynamic object fields.

    This is test ID, replace to run.
    """
    handle_result(
        client.execute_query_node(
            with_node=qn.GetDynamicFields(
                object_id="0xb0e372e6abc2dfa87b19e8e4a29b74be7f68b21d8a6a7e005c256d02ef19911d"
            )
        )
    )


def do_event(client: SyncGqlClient):
    """."""
    res = client.execute_query_node(
        with_node=qn.GetEvents(
            event_filter={"type": "0x3::validator::StakingRequestEvent"}
        )
    )
    if res.is_ok():
        handle_result(res)
        max_page = 3
        in_page = 0
        while True:
            in_page += 1
            if in_page < max_page and res.result_data.next_cursor:
                res = client.execute_query_node(
                    with_node=qn.GetEvents(
                        event_filter={"sender": "0x0"},
                        next_page=res.result_data.next_cursor,
                    )
                )
                handle_result(res)
            else:
                break
        print("DONE")


def do_configs(client: SyncGqlClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config().to_json(indent=2))


def do_service_config(client: SyncGqlClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config().serviceConfig.to_json(indent=2))


def do_chain_id(client: SyncGqlClient):
    """Fetch the current environment chain_id.

    Demonstrates overriding serialization
    """
    print(f"Chain Identifier: {client.chain_id()}")


def do_tx(client: SyncGqlClient):
    """Fetch specific transaction by it's digest.

    To run, replace digest value with a valid one for network you are working with
    """

    handle_result(
        client.execute_query_node(
            with_node=qn.GetTx(digest="HUBRYJeTCmcXTSW4Q5peCSDBXzvX8JDhw7uf7gVrYibw")
        )
    )


def do_txs(client: SyncGqlClient):
    """Fetch transactions.

    We loop through 3 pages.
    """
    result = client.execute_query_node(with_node=qn.GetMultipleTx())
    handle_result(result)
    if result.is_ok():
        max_page = 3
        in_page = 0
        while True:
            in_page += 1
            if in_page < max_page and result.result_data.next_cursor:
                result = client.execute_query_node(
                    with_node=qn.GetMultipleTx(next_page=result.result_data.next_cursor)
                )
                handle_result(result)
            else:
                break
        print("DONE")


def do_filter_txs(client: SyncGqlClient):
    """Fetch all transactions matching filter.

    See Sui GraphQL schema for TransactionFilter options.
    """
    obj_filter = {
        "affectedObject": "0x065f4c3414e14b74215f9fa585b7f0880228f37f2b0fb962282f752ada3c1ceb"
    }
    result = client.execute_query_node(with_node=qn.GetFilteredTx(tx_filter=obj_filter))
    while result.is_ok():
        txs: ptypes.TransactionSummariesGQL = result.result_data
        for tx in txs.data:
            print(f"Kind: {tx.tx_kind} Digest: {tx.digest} timestamp: {tx.timestamp}")
        if txs.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetFilteredTx(
                    tx_filter=obj_filter,
                    next_page=txs.next_cursor,
                )
            )
        else:
            break


def do_tx_kind(client: SyncGqlClient):
    """Fetch the PTB details from transaction.

    Substitute a valid transaction digest from operating environment.
    """
    qnode = qn.GetTxKind(
        digest="6UfWSAfUArkkKc24DeRDje2mtQdZar8H2J21ZsMgTexK"
    )  # split and transfer
    handle_result(client.execute_query_node(with_node=qnode))


def do_staked_sui(client: SyncGqlClient):
    """Retreive Staked Coins."""
    owner = client.config.active_address

    handle_result(
        client.execute_query_node(with_node=qn.GetDelegatedStakes(owner=owner))
    )


def do_latest_cp(client: SyncGqlClient):
    """."""
    qnode = qn.GetLatestCheckpointSequence()
    handle_result(client.execute_query_node(with_node=qnode))


def do_sequence_cp(client: SyncGqlClient):
    """Fetch a checkpoint by checkpoint sequence number.

    Uses the most recent checkpoint's sequence id (inefficient for example only)
    """
    result = client.execute_query_node(with_node=qn.GetLatestCheckpointSequence())
    if result.is_ok():
        cp: ptypes.CheckpointGQL = result.result_data
        handle_result(
            client.execute_query_node(
                with_node=qn.GetCheckpointBySequence(sequence_number=cp.sequence_number)
            )
        )
    else:
        print(result.result_string)


def do_checkpoints(client: SyncGqlClient):
    """Get a batch of checkpoints."""
    handle_result(client.execute_query_node(with_node=qn.GetCheckpoints()))


def do_refgas(client: SyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query_node(with_node=qn.GetReferenceGasPrice()))


def do_nameservice(client: SyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query_node(
            with_node=qn.GetNameServiceAddress(name="example.sui")
        )
    )


def do_owned_nameservice(client: SyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query_node(
            with_node=qn.GetNameServiceNames(owner=client.config.active_address)
        )
    )


def do_validators(client: SyncGqlClient):
    """Fetch the most current validator detail."""
    handle_result(client.execute_query_node(with_node=qn.GetCurrentValidators()))


def do_all_validators(client: SyncGqlClient):
    """Fetch all validators and show name and data."""
    all_vals: list[ptypes.ValidatorFullGQL] = []
    valres = client.execute_query_node(with_node=qn.GetCurrentValidators())
    while valres.is_ok():
        all_vals.extend(valres.result_data.validators)
        if valres.result_data.next_cursor.hasNextPage:
            valres = client.execute_query_node(
                with_node=qn.GetCurrentValidators(
                    next_page=valres.result_data.next_cursor,
                )
            )
        else:
            break
    print(f"Total validators {len(all_vals)}")
    for val in all_vals:
        print(
            f"Address: {val.validator_address} Apy: {val.apy} Name: {val.validator_name}"
        )


def do_protcfg(client: SyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query_node(with_node=qn.GetProtocolConfig(version=96)))


def do_struct(client: SyncGqlClient):
    """Fetch structure by package::module::struct_name.

    This is a testnet object!!!
    """
    result = client.execute_query_node(
        with_node=qn.GetStructure(
            package="0x2",
            module_name="coin",
            structure_name="CoinMetadata",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_structs(client: SyncGqlClient):
    """Fetch structures by package::module."""
    result = client.execute_query_node(
        with_node=qn.GetStructures(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_func(client: SyncGqlClient):
    """Fetch structures by package::module.

    You will need to change the package,module and functions here for a well known one
    depending on the environment (devnet, testnet, mainnet) you are running this.
    """
    result = client.execute_query_node(
        with_node=qn.GetFunction(
            package="0x2",
            module_name="coin",
            function_name="balance",
        )
    )
    if result.is_ok():
        mv_fn: ptypes.MoveFunctionGQL = result.result_data
        print(mv_fn.to_json(indent=2))
        print(mv_fn.arg_summary().to_json(indent=2))


def do_funcs(client: SyncGqlClient):
    """Fetch structures by package::module."""
    result = client.execute_query_node(
        with_node=qn.GetFunctions(
            package="0x1",
            module_name="ascii",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_module(client: SyncGqlClient):
    """Fetch a module from package."""
    result = client.execute_query_node(
        with_node=qn.GetModule(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_package(client: SyncGqlClient):
    """Fetch a module from package.

    The cursor, if used, applies to the modules listing
    """
    result = client.execute_query_node(
        with_node=qn.GetPackage(
            package="0x2",
        )
    )
    while result.is_ok():
        sui_package: ptypes.MovePackageGQL = handle_result(result).result_data
        if sui_package.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetPackage(
                    package=sui_package.package_id, next_page=sui_package.next_cursor
                )
            )
        else:
            break


def do_dry_run_kind_new(client: SyncGqlClient):
    """Execute a dry run with TransactionKind where meta data is set by caller.

    This uses the new SuiTransaction (GraphQL RPC based)
    """

    txer = SuiTransaction(client=client)
    scres = txer.split_coin(coin=txer.gas, amounts=[1000000, 1000000])
    txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    handle_result(
        client.execute_query_node(
            with_node=qn.DryRunTransactionKind(tx_bytestr=txer.build_for_dryrun())
        )
    )


def do_dry_run_new(client: SyncGqlClient):
    """Execute a dry run with TransactionData where gas and budget set by txer.

    This uses the new SuiTransaction (GraphQL RPC based)
    """
    txer = SuiTransaction(client=client)
    scres = txer.split_coin(coin=txer.gas, amounts=[1000000000])
    txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

    tx_b64 = base64.b64encode(txer.transaction_data().serialize()).decode()
    print(tx_b64)
    handle_result(
        client.execute_query_node(with_node=qn.DryRunTransaction(tx_bytestr=tx_b64))
    )


def do_execute_new(client: SyncGqlClient):
    """Execute a transaction.

    The result contains the digest of the transaction which can then be queried
    for details

    This uses the new SuiTransaction (GraphQL RPC based)
    """
    txer: SuiTransaction = client.transaction()
    scres = txer.split_coin(coin=txer.gas, amounts=[1000000])
    txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    txdict = txer.build_and_sign()
    print(txdict)
    handle_result(client.execute_query_node(with_node=qn.ExecuteTransaction(**txdict)))


def merge_some(client: SyncGqlClient):
    """Merge some coins in wallet.

    To merge all coins, ensure to use paging to gather all coins first and
    combine them into a single list, then perform the merge.
    """

    result = client.execute_query_node(
        with_node=qn.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and len(result.result_data.data) > 1:
        txer: SuiTransaction = client.transaction()
        txer.merge_coins(merge_to=txer.gas, merge_from=result.result_data.data[1:])
        txdict = txer.build_and_sign()
        handle_result(
            client.execute_query_node(with_node=qn.ExecuteTransaction(**txdict))
        )


def split_1_half(client: SyncGqlClient):
    """Split the 1 coin into 2 (or more) in wallet.

    If there is more than 1 coin for the address, this transaction won't be
    submitted.
    """

    result = client.execute_query_node(
        with_node=qn.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and len(result.result_data.data) == 1:
        amount = int(int(result.result_data.data[0].balance) / 2)
        txer: SuiTransaction = client.transaction()
        scres = txer.split_coin(coin=txer.gas, amounts=[amount])
        txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
        txdict = txer.build_and_sign()
        result = handle_result(
            client.execute_query_node(with_node=qn.ExecuteTransaction(**txdict))
        )


def split_any_half(client: SyncGqlClient):
    """Split the 1st coin in wallet to another another equal to 1/2 in wallet.

    This will only run if there is more than 1 coin in wallet.
    """

    result = client.execute_query_node(
        with_node=qn.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and len(result.result_data.data) > 1:
        amount = int(int(result.result_data.data[0].balance) / 2)
        txer: SuiTransaction = client.transaction()
        scres = txer.split_coin(coin=result.result_data.data[0], amounts=[amount])
        txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
        txdict = txer.build_and_sign(
            use_gas_objects=[result.result_data.data[1]], gas_budget="4000000"
        )
        result = handle_result(
            client.execute_query_node(with_node=qn.ExecuteTransaction(**txdict))
        )


def do_stake(client: SyncGqlClient):
    """Stake some coinage.

    This uses a testnet validator (Blockscope.net). For different environment
    or different validator change the vaddress
    """
    vaddress = "0xdfed72a46fa7899fd80edf960bb4e05d6852f74a628d55b8dba69064f0ca07d4"
    txer: SuiTransaction = client.transaction()
    # Take 1 Sui from gas
    stake_coin_split = txer.split_coin(coin=txer.gas, amounts=[1000000000])
    # Stake the coin
    txer.stake_coin(
        coins=[stake_coin_split],
        validator_address=vaddress,
    )
    # Uncomment to dry run
    handle_result(
        client.execute_query_node(
            with_node=qn.DryRunTransaction(tx_bytestr=txer.build())
        )
    )
    # Uncomment to Execute the unstake
    # txdict = txer.build_and_sign()
    # handle_result(
    #     client.execute_query_node(
    #         with_node=qn.ExecuteTransaction(**txdict)
    #     )
    # )


def do_unstake(client: SyncGqlClient):
    """Unstake first Staked Sui if address has any."""

    owner = client.config.active_address
    result = client.execute_query_node(with_node=qn.GetDelegatedStakes(owner=owner))
    if result.is_ok() and result.result_data.staked_coins:
        txer: SuiTransaction = client.transaction()
        # Unstake the first staked coin
        txer.unstake_coin(staked_coin=result.result_data.staked_coins[0])
        # Uncomment to dry run
        handle_result(
            client.execute_query_node(
                with_node=qn.DryRunTransaction(tx_bytestr=txer.build())
            )
        )
        # Uncomment to Execute the unstake
        # txdict = txer.build_and_sign()
        # handle_result(
        #     client.execute_query_node(
        #         with_node=qn.ExecuteTransaction(**txdict)
        #     )
        # )
    else:
        print(f"No staked Sui for {owner}")


if __name__ == "__main__":

    client_init: SyncGqlClient = None
    try:
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
            profile_name="devnet-beta",
            # profile_name="testnet",
            # profile_name="mainnet",
            # persist=True,
        )
        client_init = SyncGqlClient(write_schema=False, pysui_config=cfg)
        print(f"Active chain profile   '{client_init.chain_environment}'")
        print(f"Default schema base version '{client_init.base_schema_version}'")
        print(f"Default schema build version '{client_init.schema_version()}'")
        print()
        # for pname in cfg.profile_names():
        #     print(pname)
        ## QueryNodes (fetch)
        # do_coin_meta(client_init)
        # do_coins_for_type(client_init)
        # do_gas(client_init)
        # do_all_gas(client_init)
        # do_gas_ids(client_init)
        # do_sysstate(client_init) # TODO: Needs update from Mysten, missing active validators
        # do_all_balances(client_init)
        # do_object(client_init)
        # do_object_content(client_init)
        # do_objects(client_init)
        # do_past_object(client_init)
        # do_multiple_object_versions(client_init)
        # do_multiple_object_content(client_init)
        # do_objects_for(client_init)
        do_dynamics(client_init)
        # do_event(client_init)
        # do_tx(client_init)
        # do_txs(client_init)
        # do_filter_txs(client_init)
        # do_tx_kind(client_init)
        # do_staked_sui(client_init)
        # do_latest_cp(client_init)
        # do_sequence_cp(client_init)
        # do_checkpoints(client_init)
        # do_nameservice(client_init) # TODO: Only get name from address? No reverse Address from Name?
        # do_owned_nameservice(client_init) # TODO: Address only carries 1 defaultSuinsName?
        # do_validators(client_init)  # TODO: missing active validators
        # do_all_validators(client_init) # TODO: missing active validators
        # do_refgas(client_init)
        # do_struct(client_init)
        # do_structs(client_init)
        # do_func(client_init)
        # do_funcs(client_init)
        # do_module(client_init)
        # do_package(client_init)
        # do_dry_run_new(client_init)  # TODO: Needs rework
        # do_dry_run_kind_new(client_init) # TODO: Needs Mysten implementation
        # do_execute_new(client_init) # TODO: Requires dry run
        # merge_some(client_init) # TODO: Requires dry run
        # split_any_half(client_init)  # TODO: Requires dry run
        # split_1_half(client_init) # TODO: Requires dry run
        # do_stake(client_init) # TODO: Requires dry run
        # do_unstake(client_init) # TODO: Requires dry run
        ## Config
        # do_chain_id(client_init)
        # do_configs(client_init)
        # do_service_config(client_init)
        # do_protcfg(client_init)
    except Exception as ex:
        print(ex.args)
    if client_init:
        client_init.client().close_sync()
