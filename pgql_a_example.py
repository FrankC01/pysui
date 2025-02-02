#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for incremental buildout of Async Sui GraphQL RPC for Pysui 1.0.0."""

import asyncio

from pysui import PysuiConfiguration, SuiRpcResult, AsyncGqlClient, SyncGqlClient
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction

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


async def do_coin_meta(client: AsyncGqlClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    handle_result(await client.execute_query_node(with_node=qn.GetCoinMetaData()))


async def do_coins_for_type(client: AsyncGqlClient):
    """Fetch coins of specific type for owner."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetCoins(
                owner=client.config.active_address,
                coin_type="0x2::sui::SUI",
            )
        )
    )


async def do_gas(client: AsyncGqlClient):
    """Fetch 0x2::sui::SUI (default) for owner."""
    result = handle_result(
        await client.execute_query_node(
            with_node=qn.GetCoins(owner=client.config.active_address)
        )
    )
    if result.is_ok():
        print(
            f"Total coins in page: {len(result.result_data.data)} has more: {result.result_data.next_cursor.hasNextPage}"
        )


async def do_all_gas(client: AsyncGqlClient):
    """Fetch all coins for owner."""
    result = handle_result(
        await client.execute_query_node(
            with_node=qn.GetCoins(owner=client.config.active_address)
        )
    )
    tcoins = 0
    tbalance = 0
    while result.is_ok():
        coins: ptypes.SuiCoinObjectsGQL = result.result_data
        tcoins += len(coins.data)
        tbalance += sum([int(x.balance) for x in coins.data])
        if result.result_data.next_cursor.hasNextPage:
            result = handle_result(
                await client.execute_query_node(
                    with_node=qn.GetCoins(
                        owner=client.config.active_address,
                        next_page=result.result_data.next_cursor,
                    )
                )
            )
        else:
            break
    print(f"Total coins: {tcoins}")
    print(f"Total mists: {tbalance}")


async def do_gas_ids(client: AsyncGqlClient):
    """Fetch coins by the ids."""

    # Use coins found for active address to use to validate
    # fetching by coin ids
    result = await client.execute_query_node(
        with_node=qn.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and result.result_data.data:
        cids = [x.coin_object_id for x in result.result_data.data]
        result = handle_result(
            await client.execute_query_node(
                with_node=qn.GetMultipleGasObjects(coin_object_ids=cids)
            )
        )
    elif result.is_err():
        print(f"Error calling GraphQL {result.result_string}")
    else:
        print(f"Data return from call is empty {result.result_data.data}")


async def do_sysstate(client: AsyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(
        await client.execute_query_node(with_node=qn.GetLatestSuiSystemState())
    )


async def do_all_balances(client: AsyncGqlClient):
    """Fetch all coin types and there total balances for owner.

    Demonstrates paging as well
    """
    result = await client.execute_query_node(
        with_node=qn.GetAllCoinBalances(owner=client.config.active_address)
    )
    handle_result(result)
    if result.is_ok():
        while result.result_data.next_cursor.hasNextPage:
            result = await client.execute_query_node(
                with_node=qn.GetAllCoinBalances(
                    owner=client.config.active_address,
                    next_page=result.result_data.next_cursor,
                )
            )
            handle_result(result)
        print("DONE")


async def do_object(client: AsyncGqlClient):
    """Fetch specific object data."""
    handle_result(
        await client.execute_query_node(with_node=qn.GetObject(object_id="0x6"))
    )


async def do_objects(client: AsyncGqlClient):
    """Fetch all objects held by owner."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetObjectsOwnedByAddress(owner=client.config.active_address)
        )
    )


async def do_past_object(client: AsyncGqlClient):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetPastObject(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed",
                version=17078252,
            )
        )
    )


async def do_multiple_object_versions(client: AsyncGqlClient):
    """Fetchs object details by version.
    To run, change the objectID str and version int.
    """
    object_versions = [
        {
            "objectId": "0x0c11bba3ea02576c30c9e627683277264a6c775bb65dbc9a6f818d91f93c6d82",
            "version": 43,
        }
    ]
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetMultipleVersionedObjects(for_versions=object_versions)
        )
    )


async def do_objects_for(client: AsyncGqlClient):
    """Fetch specific objects by their ids.

    These are test IDs, replace to run.
    """
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetMultipleObjects(
                object_ids=[
                    "0x0847e1e02965e3f6a8b237152877a829755fd2f7cfb7da5a859f203a8d4316f0",
                    "0x68e961e3af906b160e1ff21137304537fa6b31f5a4591ef3acf9664eb6e3cd2b",
                    "0x77851d73e7c1227c048fc7cbf21ff9053faa872950dd33f5d0cb5b40a79d9d99",
                ]
            )
        )
    )


async def do_dynamics(client: AsyncGqlClient):
    """Get objects dynamic field and dynamic object fields.

    This is test ID, replace to run.
    """
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetDynamicFields(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed"
            )
        )
    )


async def do_event(client: AsyncGqlClient):
    """."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetEvents(event_filter={"sender": "0x0"})
        )
    )


async def do_configs(client: AsyncGqlClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config.to_json(indent=2))


async def do_service_config(client: AsyncGqlClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config.serviceConfig.to_json(indent=2))


async def do_chain_id(client: AsyncGqlClient):
    """Fetch the current environment chain_id.

    Demonstrates overriding serialization
    """
    print(client.chain_id)


async def do_tx(client: AsyncGqlClient):
    """Fetch specific transaction by it's digest."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetTx(digest="A8kCT1n8dmCWchz5WnKPsQ8x7U49ExgMEWJ13nRULpiz")
        )
    )


async def do_txs(client: AsyncGqlClient):
    """Fetch transactions.

    We loop through 3 pages.
    """
    result = await client.execute_query_node(with_node=qn.GetMultipleTx())
    handle_result(result)
    if result.is_ok():
        max_page = 3
        in_page = 0
        while True:
            in_page += 1
            if in_page < max_page and result.result_data.next_cursor:
                result = await client.execute_query_node(
                    with_node=qn.GetMultipleTx(next_page=result.result_data.next_cursor)
                )
                handle_result(result)
            else:
                break
        print("DONE")


async def do_filter_txs(client: AsyncGqlClient):
    """Fetch all transactions matching filter.

    See Sui GraphQL schema for TransactionBlockFilter options.
    """
    obj_filter = {"changedObject": "ENTER OBJECT_ID HERE"}
    result = await client.execute_query_node(
        with_node=qn.GetFilteredTx(tx_filter=obj_filter)
    )
    while result.is_ok():
        txs: ptypes.TransactionSummariesGQL = result.result_data
        for tx in txs.data:
            print(f"Digest: {tx.digest} timestamp: {tx.timestamp}")
        if txs.next_cursor.hasNextPage:
            result = await client.execute_query_node(
                with_node=qn.GetFilteredTx(
                    tx_filter=obj_filter,
                    next_page=txs.next_cursor,
                )
            )
        else:
            break


async def do_tx_kind(client: AsyncGqlClient):
    """Fetch the PTB details from transaction."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetTxKind(digest="ENTER TRANSACTION DIGESST HERE")
        )
    )


async def do_staked_sui(client: AsyncGqlClient):
    """."""
    owner = client.config.active_address
    handle_result(
        await client.execute_query_node(with_node=qn.GetDelegatedStakes(owner=owner))
    )


async def do_latest_cp(client: AsyncGqlClient):
    """."""
    qnode = qn.GetLatestCheckpointSequence()
    # print(qnode.query_as_string())
    handle_result(await client.execute_query_node(with_node=qnode))


async def do_sequence_cp(client: AsyncGqlClient):
    """."""
    result = await client.execute_query_node(with_node=qn.GetLatestCheckpointSequence())
    if result.is_ok():
        cp: ptypes.CheckpointGQL = result.result_data
        handle_result(
            await client.execute_query_node(
                with_node=qn.GetCheckpointBySequence(sequence_number=cp.sequence_number)
            )
        )
    else:
        print(result.result_string)


async def do_digest_cp(client: AsyncGqlClient):
    """."""
    result = await client.execute_query_node(with_node=qn.GetLatestCheckpointSequence())
    if result.is_ok():
        cp: ptypes.CheckpointGQL = result.result_data
        handle_result(
            await client.execute_query_node(
                with_node=qn.GetCheckpointByDigest(digest=cp.digest)
            )
        )
    else:
        print(result.result_string)


async def do_checkpoints(client: AsyncGqlClient):
    """."""
    handle_result(await client.execute_query_node(with_node=qn.GetCheckpoints()))


async def do_refgas(client: AsyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(await client.execute_query_node(with_node=qn.GetReferenceGasPrice()))


async def do_nameservice(client: AsyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetNameServiceAddress(name="gql-frank")
        )
    )


async def do_owned_nameservice(client: AsyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetNameServiceNames(owner=client.config.active_address)
        )
    )


async def do_validators_apy(client: AsyncGqlClient):
    """Fetch the most current validators apy and identity."""
    handle_result(await client.execute_query_node(with_node=qn.GetValidatorsApy()))


async def do_validators(client: AsyncGqlClient):
    """Fetch the most current validator detail."""
    handle_result(await client.execute_query_node(with_node=qn.GetCurrentValidators()))


async def do_all_validators(client: AsyncGqlClient):
    """Fetch all validators and show name and data."""
    all_vals: list[ptypes.ValidatorFullGQL] = []
    valres = await client.execute_query_node(with_node=qn.GetCurrentValidators())
    while valres.is_ok():
        all_vals.extend(valres.result_data.validators)
        if valres.result_data.next_cursor.hasNextPage:
            valres = await client.execute_query_node(
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


async def do_protcfg(client: AsyncGqlClient):
    """Fetch the most current system state summary."""
    handle_result(
        await client.execute_query_node(with_node=qn.GetProtocolConfig(version=30))
    )


async def do_struct(client: AsyncGqlClient):
    """Fetch structure by package::module::struct_name.

    This is a testnet object!!!
    """
    result = await client.execute_query_node(
        with_node=qn.GetStructure(
            package="0x2",
            module_name="coin",
            structure_name="CoinMetadata",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_structs(client: AsyncGqlClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute_query_node(
        with_node=qn.GetStructures(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_func(client: AsyncGqlClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute_query_node(
        with_node=qn.GetFunction(
            package="0x2",
            module_name="coin",
            function_name="join",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_funcs(client: AsyncGqlClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute_query_node(
        with_node=qn.GetFunctions(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_module(client: AsyncGqlClient):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = await client.execute_query_node(
        with_node=qn.GetModule(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_package(client: AsyncGqlClient):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = await client.execute_query_node(
        with_node=qn.GetPackage(
            package="0x2",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_dry_run(client: AsyncGqlClient):
    """Execute a dry run."""

    # Use synchronous transaction builder
    txer: AsyncSuiTransaction = AsyncSuiTransaction(client=client)
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

    handle_result(
        await client.execute_query_node(
            with_node=qn.DryRunTransaction(tx_bytestr=await txer.build())
        )
    )


async def do_split_any_half(client: AsyncGqlClient):
    """Split the 1st coin in wallet to another another equal to 1/2 in wallet.

    This will only run if there is more than 1 coin in wallet.
    """

    result = await client.execute_query_node(
        with_node=qn.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and len(result.result_data.data) > 1:
        amount = int(int(result.result_data.data[0].balance) / 2)
        txer: AsyncSuiTransaction = AsyncSuiTransaction(client=client)
        scres = await txer.split_coin(coin=result.result_data.data[0], amounts=[amount])
        await txer.transfer_objects(
            transfers=scres, recipient=client.config.active_address
        )
        handle_result(
            await client.execute_query_node(
                with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
            )
        )


async def do_execute(client: AsyncGqlClient):
    """Execute a transaction."""
    txer: AsyncSuiTransaction = AsyncSuiTransaction(client=client)
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    handle_result(
        await client.execute_query_node(
            with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
        )
    )


async def do_stake(client: AsyncGqlClient):
    """Stake some coinage.

    This uses a testnet validator (Blockscope.net). For different environment
    or different validator change the vaddress
    """
    vaddress = "0x44b1b319e23495995fc837dafd28fc6af8b645edddff0fc1467f1ad631362c23"
    txer: AsyncSuiTransaction = AsyncSuiTransaction(client=client)

    # Take 1 Sui from gas
    stake_coin_split = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    # Stake the coin
    await txer.stake_coin(
        coins=[stake_coin_split],
        validator_address=vaddress,
    )
    # Uncomment to dry run
    handle_result(
        await client.execute_query_node(
            with_node=qn.DryRunTransaction(tx_bytestr=await txer.build())
        )
    )
    # Uncomment to execute the stake
    # handle_result(
    #     await client.execute_query_node(
    #         with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    #     )
    # )


async def do_unstake(client: AsyncGqlClient):
    """Unstake first Staked Sui if address has any."""

    owner = client.config.active_address
    result = await client.execute_query_node(
        with_node=qn.GetDelegatedStakes(owner=owner)
    )
    if result.is_ok() and result.result_data.staked_coins:
        txer: AsyncSuiTransaction = AsyncSuiTransaction(client=client)

        # Unstake the first staked coin
        await txer.unstake_coin(
            staked_coin=result.result_data.staked_coins[0].object_id
        )
        # Uncomment to dry run
        handle_result(
            await client.execute_query_node(
                with_node=qn.DryRunTransaction(tx_bytestr=await txer.build())
            )
        )

        # Uncomment to execute the stake
        # handle_result(
        #     await client.execute_query_node(
        #         with_node=qn.ExecuteTransaction(**txer.build_and_sign())
        #     )
        # )

    else:
        print(f"No staked Sui for {owner}")


async def main():
    """."""
    try:
        client_init = AsyncGqlClient(
            write_schema=False,
            pysui_config=PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
                # profile_name="devnet",
                # profile_name="testnet",
                # profile_name="mainnet",
            ),
        )
        print(f"Active chain profile   '{client_init.chain_environment}'")
        print(f"Default schema base version '{client_init.base_schema_version}'")
        print(f"Default schema build version '{client_init.schema_version()}'")
        print()

        ## QueryNodes (fetch)
        # await do_coin_meta(client_init)
        # await do_coins_for_type(client_init)
        await do_gas(client_init)
        # await do_all_gas(client_init)
        # await do_gas_ids(client_init)
        # await do_sysstate(client_init)
        # await do_all_balances(client_init)
        # await do_object(client_init)
        # await do_objects(client_init)
        # await do_past_object(client_init)
        # await do_multiple_object_versions(client_init)
        # await do_objects_for(client_init)
        # await do_dynamics(client_init)
        # await do_event(client_init)
        # await do_tx(client_init)
        # await do_txs(client_init)
        # await do_filter_txs(client_init)
        # await do_tx_kind(client_init)
        # await do_staked_sui(client_init)
        # await do_latest_cp(client_init)
        # await do_sequence_cp(client_init)
        # await do_digest_cp(client_init)
        # await do_checkpoints(client_init)
        # await do_owned_nameservice(client_init)
        # await do_validators_apy(client_init)
        # await do_validators(client_init)
        # await do_all_validators(client_init)
        # await do_nameservice(client_init)
        # await do_refgas(client_init)
        # await do_struct(client_init)
        # await do_structs(client_init)
        # await do_func(client_init)
        # await do_funcs(client_init)
        # await do_module(client_init)
        # await do_package(client_init)
        # await do_dry_run(client_init)
        # await do_split_any_half(client_init)
        # await do_execute(client_init)
        # await do_stake(client_init)
        # await do_unstake(client_init)
        ## Config
        # await do_chain_id(client_init)
        # await do_configs(client_init)
        # await do_service_config(client_init)
        # await do_protcfg(client_init)
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    asyncio.run(main())
