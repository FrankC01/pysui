#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for incremental buildout of Sui GraphQL RPC for Pysui 1.0.0."""

import base64
from pysui import SuiConfig, SuiRpcResult, SyncClient
from pysui.sui.sui_txn import SyncTransaction
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes


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


def do_coin_meta(client: SuiGQLClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    handle_result(client.execute_query_node(with_node=qn.GetCoinMetaData()))


def do_coins_for_type(client: SuiGQLClient):
    """Fetch coins of specific type for owner."""
    handle_result(
        client.execute_query_node(
            with_node=qn.GetCoins(
                owner=client.config.active_address.address,
                coin_type="0x2::sui::SUI",
            )
        )
    )


def do_gas(client: SuiGQLClient):
    """Fetch 0x2::sui::SUI (default) for owner."""
    result = handle_result(
        client.execute_query_node(
            with_node=qn.GetCoins(
                # owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
                owner=client.config.active_address.address
            )
        )
    )
    if result.is_ok():
        print(
            f"Total coins in page: {len(result.result_data.data)} has more: {result.result_data.next_cursor.hasNextPage}"
        )


def do_all_gas(client: SuiGQLClient):
    """Fetch all coins for owner."""
    result = handle_result(
        client.execute_query_node(
            with_node=qn.GetCoins(
                # owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
                owner=client.config.active_address.address
            )
        )
    )
    while result.is_ok() and result.result_data.next_cursor.hasNextPage:
        result = handle_result(
            client.execute_query_node(
                with_node=qn.GetCoins(
                    owner=client.config.active_address.address,
                    next_page=result.result_data.next_cursor,
                )
            )
        )


def do_gas_ids(client: SuiGQLClient):
    """Fetch coins by the ids."""
    result = handle_result(
        client.execute_query_node(
            with_node=qn.GetMultipleGasObjects(
                coin_object_ids=[
                    "0x0847e1e02965e3f6a8b237152877a829755fd2f7cfb7da5a859f203a8d4316f0",
                    "0x18de17501278b65f469d12c031180bd0175291f8381820111a577531b70ea6fc",
                ]
            )
        )
    )


def do_sysstate(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query_node(with_node=qn.GetLatestSuiSystemState()))


def do_all_balances(client: SuiGQLClient):
    """Fetch all coin types for active address and total balances.

    Demonstrates paging as well
    """
    result = client.execute_query_node(
        with_node=qn.GetAllCoinBalances(owner=client.config.active_address.address)
    )
    handle_result(result)
    if result.is_ok():
        while result.result_data.next_cursor.hasNextPage:
            result = client.execute_query_node(
                with_node=qn.GetAllCoinBalances(
                    owner=client.config.active_address.address,
                    next_page=result.next_cursor,
                )
            )
            handle_result(result)
        print("DONE")


def do_object(client: SuiGQLClient):
    """Fetch specific object data."""
    # handle_result(client.execute_query(with_query_node=qn.GetObject(object_id="0x6")))
    handle_result(
        client.execute_query_node(
            with_node=qn.GetObject(
                object_id="0x18de17501278b65f469d12c031180bd0175291f8381820111a577531b70ea6fc"
            )
        )
    )


def do_past_object(client: SuiGQLClient):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    handle_result(
        client.execute_query_node(
            with_node=qn.GetPastObject(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed",
                version=17078252,
            )
        )
    )


def do_multiple_past_object(client: SuiGQLClient):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    past_objects = [
        {
            "objectId": "0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed",
            "version": 17078252,
        }
    ]
    handle_result(
        client.execute_query_node(
            with_node=qn.GetMultiplePastObjects(for_versions=past_objects)
        )
    )


def do_objects(client: SuiGQLClient):
    """Fetch all objects help by owner."""
    handle_result(
        client.execute_query_node(
            with_node=qn.GetObjectsOwnedByAddress(
                owner=client.config.active_address.address
            )
        )
    )


def do_objects_for(client: SuiGQLClient):
    """Fetch specific objects by their ids.

    These are test IDs, replace to run.
    """
    handle_result(
        client.execute_query_node(
            with_node=qn.GetMultipleObjects(
                object_ids=[
                    "0x0847e1e02965e3f6a8b237152877a829755fd2f7cfb7da5a859f203a8d4316f0",
                    "0x68e961e3af906b160e1ff21137304537fa6b31f5a4591ef3acf9664eb6e3cd2b",
                    "0x77851d73e7c1227c048fc7cbf21ff9053faa872950dd33f5d0cb5b40a79d9d99",
                ]
            )
        )
    )


def do_dynamics(client: SuiGQLClient):
    """Get objects dynamic field and dynamic object fields.

    This is test ID, replace to run.
    """
    handle_result(
        client.execute_query_node(
            with_node=qn.GetDynamicFields(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed"
            )
        )
    )


def do_event(client: SuiGQLClient):
    """."""
    res = client.execute_query_node(
        with_node=qn.GetEvents(event_filter={"sender": "0x0"})
    )
    if res.is_ok():
        handle_result(res)
        max_page = 2
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


def do_configs(client: SuiGQLClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config.to_json(indent=2))


def do_chain_id(client: SuiGQLClient):
    """Fetch the current environment chain_id.

    Demonstrates overriding serialization
    """
    print(client.chain_id)


def do_tx(client: SuiGQLClient):
    """Fetch specific transaction by it's digest.

    Digest is testnet specific
    """

    handle_result(
        client.execute_query_node(
            with_node=qn.GetTx(digest="CMyUnPRqz9ECAtBeL19aWDG9CdsEd5K2p5NMHTyvaoa7")
        )
    )


def do_txs(client: SuiGQLClient):
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


def do_staked_sui(client: SuiGQLClient):
    """."""
    owner = client.config.active_address.address

    handle_result(
        client.execute_query_node(with_node=qn.GetDelegatedStakes(owner=owner))
    )


def do_latest_cp(client: SuiGQLClient):
    """."""
    qnode = qn.GetLatestCheckpointSequence()
    # print(qnode.query_as_string())
    handle_result(client.execute_query_node(with_node=qnode))


def do_sequence_cp(client: SuiGQLClient):
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


def do_digest_cp(client: SuiGQLClient):
    """Fetch a checkpoint by checkpoint digest.

    Uses the most recent checkpoint's digest (inefficient for example only)
    """
    result = client.execute_query_node(with_node=qn.GetLatestCheckpointSequence())
    if result.is_ok():
        cp: ptypes.CheckpointGQL = result.result_data
        handle_result(
            client.execute_query_node(
                with_node=qn.GetCheckpointByDigest(digest=cp.digest)
            )
        )
    else:
        print(result.result_string)


def do_checkpoints(client: SuiGQLClient):
    """Get a batch of checkpoints."""
    handle_result(client.execute_query_node(with_node=qn.GetCheckpoints()))


def do_refgas(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query_node(with_node=qn.GetReferenceGasPrice()))


def do_nameservice(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query_node(with_node=qn.GetNameServiceAddress(name="gql-frank"))
    )


def do_owned_nameservice(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query_node(
            with_node=qn.GetNameServiceNames(owner=client.config.active_address.address)
        )
    )


def do_validators_apy(client: SuiGQLClient):
    """Fetch the most current validators apy and identity."""
    handle_result(client.execute_query_node(with_node=qn.GetValidatorsApy()))


def do_validators(client: SuiGQLClient):
    """Fetch the most current validator detail."""
    handle_result(client.execute_query_node(with_node=qn.GetCurrentValidators()))


def do_protcfg(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query_node(with_node=qn.GetProtocolConfig(version=30)))


def do_struct(client: SuiGQLClient):
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


def do_structs(client: SuiGQLClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = client.execute_query_node(
        with_node=qn.GetStructures(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_func(client: SuiGQLClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = client.execute_query_node(
        with_node=qn.GetFunction(
            package="0x2",
            module_name="clock",
            function_name="timestamp_ms",
        )
    )
    if result.is_ok():
        mv_fn: ptypes.MoveFunctionGQL = result.result_data
        print(mv_fn.to_json(indent=2))
        print(mv_fn.arg_summary().to_json(indent=2))


def do_funcs(client: SuiGQLClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = client.execute_query_node(
        with_node=qn.GetFunctions(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_module(client: SuiGQLClient):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = client.execute_query_node(
        with_node=qn.GetModule(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_package(client: SuiGQLClient):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = client.execute_query_node(
        with_node=qn.GetPackage(
            package="0x2",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


def do_dry_run_kind(client: SuiGQLClient):
    """Execute a dry run with TransactionKind where meta data is set by caller.

    This uses the legacy SyncTransaction (JSON RPC based)
    """
    if client.chain_environment == "testnet":
        txer = SyncTransaction(client=SyncClient(client.config))
        scres = txer.split_coin(coin=txer.gas, amounts=[1000000000])
        txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

        tx_b64 = base64.b64encode(txer.raw_kind().serialize()).decode()
        handle_result(
            client.execute_query_node(
                with_node=qn.DryRunTransactionKind(tx_bytestr=tx_b64)
            )
        )


def do_dry_run(client: SuiGQLClient):
    """Execute a dry run with TransactionData where gas and budget set by txer.

    This uses the legacy SyncTransaction (JSON RPC based)
    """
    if client.chain_environment == "testnet":
        txer = SyncTransaction(client=SyncClient(client.config))
        scres = txer.split_coin(coin=txer.gas, amounts=[1000000000])
        txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

        tx_b64 = base64.b64encode(txer.get_transaction_data().serialize()).decode()
        handle_result(
            client.execute_query_node(with_node=qn.DryRunTransaction(tx_bytestr=tx_b64))
        )


def do_execute(client: SuiGQLClient):
    """Execute a transaction.

    The result contains the digest of the transaction which can then be queried
    for details

    This uses the legacy SyncTransaction (JSON RPC based)
    """
    if client.chain_environment == "testnet":
        rpc_client = SyncClient(client.config)
        txer = SyncTransaction(client=rpc_client)
        scres = txer.split_coin(coin=txer.gas, amounts=[1000000000])
        txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
        tx_b64 = txer.deferred_execution(run_verification=True)
        sig_array = txer.signer_block.get_signatures(client=rpc_client, tx_bytes=tx_b64)
        rsig_array = [x.value for x in sig_array.array]
        handle_result(
            client.execute_query_node(
                with_node=qn.ExecuteTransaction(tx_bytestr=tx_b64, sig_array=rsig_array)
            )
        )


if __name__ == "__main__":
    client_init = SuiGQLClient(
        write_schema=False,
        config=SuiConfig.default_config(),
    )
    print(f"Schema version {client_init.schema_version}")
    ## QueryNodes (fetch)
    # do_coin_meta(client_init)
    # do_coins_for_type(client_init)
    # do_gas(client_init)
    # do_all_gas(client_init)
    do_gas_ids(client_init)
    # do_sysstate(client_init)
    # do_all_balances(client_init)
    # do_object(client_init)
    # do_objects(client_init)
    # do_past_object(client_init)
    # do_multiple_past_object(client_init)
    # do_objects_for(client_init)
    # do_dynamics(client_init)
    # do_event(client_init)
    # do_tx(client_init)
    # do_txs(client_init)
    # do_staked_sui(client_init)
    # do_latest_cp(client_init)
    # do_sequence_cp(client_init)
    # do_digest_cp(client_init)
    # do_checkpoints(client_init)
    # do_nameservice(client_init)
    # do_owned_nameservice(client_init)
    # do_validators_apy(client_init)
    # do_validators(client_init)
    # do_refgas(client_init)
    # do_struct(client_init)
    # do_structs(client_init)
    # do_func(client_init)
    # do_funcs(client_init)
    # do_module(client_init)
    # do_package(client_init)
    # do_dry_run(client_init)
    # do_dry_run_kind(client_init)
    # do_execute(client_init)

    ## Config
    # do_chain_id(client_init)
    # do_configs(client_init)
    # do_protcfg(client_init)
    client_init.client.close_sync()
