#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for incremental buildout of Async Sui gRPC for Pysui 1.0.0."""

import asyncio

from pysui import PysuiConfiguration, SuiRpcResult, SuiGrpcClient
from pysui.sui.sui_grpc.pgrpc_async_txn import AsyncSuiTransaction

import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui.sui.sui_grpc.pgrpc_utils import (
    async_get_all_owned_gas_objects,
    async_get_all_owned_objects,
)
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2beta2 as sui_prot


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


async def do_coin_meta(client: SuiGrpcClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    handle_result(await client.execute(request=rn.GetCoinMetaData()))


async def do_coins_for_type(client: SuiGrpcClient):
    """Fetch coins of specific type for owner."""
    handle_result(
        await client.execute(
            request=rn.GetCoins(
                owner=client.config.active_address,
                coin_type="0x2::coin::Coin<0x2::sui::SUI>",
            )
        )
    )


async def do_gas(client: SuiGrpcClient):
    """Fetch 0x2::sui::SUI (default) for owner."""
    result = handle_result(
        await client.execute(request=rn.GetGas(owner=client.config.active_address))
    )
    if result.is_ok():
        print(
            f"Total coins in page: {len(result.result_data.objects)} has more: {result.result_data.next_page_token}"
        )


async def do_all_gas(client: SuiGrpcClient):
    """Fetch all coins for owner."""
    try:
        # This will include all coins whether active, pruned or deleted.
        # Change only_active to True for only active coins
        all_coins = await async_get_all_owned_gas_objects(
            owner=client.config.active_address, client=client, only_active=False
        )
        for coin in all_coins:
            print(coin.to_json(indent=2))
        print(f"Total coins: {len(all_coins)}")
        print(f"Total mists: {sum([int(x.balance) for x in all_coins])}")

    except ValueError as ve:
        raise ve


async def do_gas_ids(client: SuiGrpcClient):
    """Fetch coins by the ids."""

    # Use gas found for active address to use to validate
    # fetching by coin ids
    result = await client.execute(request=rn.GetGas(owner=client.config.active_address))
    if result.is_ok() and result.result_data.objects:
        cids = [x.object_id for x in result.result_data.objects]
        result = handle_result(
            await client.execute(request=rn.GetMultipleObjects(object_ids=cids))
        )
    elif result.is_err():
        print(f"Error calling gRPC {result.result_string}")
    else:
        print(f"Data return from call is empty {result.result_data.objects}")


async def do_sysstate(client: SuiGrpcClient):
    """Fetch the most current system state summary."""
    handle_result(await client.execute(request=rn.GetLatestSuiSystemState()))


async def do_all_balances(client: SuiGrpcClient):
    """Fetch all coin types and there total balances for owner."""
    handle_result(
        await client.execute(
            request=rn.GetBalance(
                owner=client.config.active_address, coin_type="0x2::sui::SUI"
            )
        )
    )


async def do_object(client: SuiGrpcClient):
    """Fetch specific object data."""
    handle_result(await client.execute(request=rn.GetObject(object_id="0x6")))


async def do_objects(client: SuiGrpcClient):
    """Fetch all objects held by owner."""
    try:
        objects: list = await async_get_all_owned_objects(
            client.config.active_address, client
        )
        for object in objects:
            print(object.to_json(indent=2))
    except ValueError as ve:
        raise ve


async def do_past_object(client: SuiGrpcClient):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    handle_result(
        await client.execute(
            request=rn.GetPastObject(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed",
                version=17078252,
            )
        )
    )


async def do_multiple_object_versions(client: SuiGrpcClient):
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
        await client.execute(
            request=rn.GetMultiplePastObjects(for_versions=object_versions)
        )
    )


async def do_objects_for(client: SuiGrpcClient):
    """Fetch specific objects by their ids.

    These are test IDs, replace to run.
    """
    handle_result(
        await client.execute(
            request=rn.GetMultipleObjects(
                object_ids=[
                    "0x0847e1e02965e3f6a8b237152877a829755fd2f7cfb7da5a859f203a8d4316f0",
                    "0x68e961e3af906b160e1ff21137304537fa6b31f5a4591ef3acf9664eb6e3cd2b",
                    "0x77851d73e7c1227c048fc7cbf21ff9053faa872950dd33f5d0cb5b40a79d9d99",
                ]
            )
        )
    )


async def do_dynamics(client: SuiGrpcClient):
    """Get objects dynamic field and dynamic object fields.

    This is test ID, replace to run.
    """
    handle_result(
        await client.execute(
            request=rn.GetDynamicFields(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed"
            )
        )
    )


async def do_event(_client: SuiGrpcClient):
    """."""
    raise NotImplementedError(f"Mysten has not implemented query events in gRPC.")


async def do_service_config(client: SuiGrpcClient):
    """Fetch the gRPC, Protocol and System configurations."""
    handle_result(await client.execute(request=rn.GetServiceInfo()))


async def do_chain_id(client: SuiGrpcClient):
    """Fetch the current environment chain_id.

    Demonstrates overriding serialization
    """
    result = await client.execute(request=rn.GetServiceInfo())
    if result.is_ok():
        print(f"Chain ID: {result.result_data.chain_id}")


async def do_tx(client: SuiGrpcClient):
    """Fetch specific transaction by it's digest."""
    handle_result(
        await client.execute(
            # Also can use rn.GetTx alias
            request=rn.GetTransaction(
                digest="4oZJ5bHgtmE6vHwALdQWVsQxor5tW2jWwUigKQvJNbBe"
            )
        )
    )


async def do_txs(client: SuiGrpcClient):
    """Fetch transactions.

    We loop through 3 pages.
    """
    handle_result(
        await client.execute(
            # Also can use rn.GetMulipleTx alias
            request=rn.GetTransactions(
                transactions=["4oZJ5bHgtmE6vHwALdQWVsQxor5tW2jWwUigKQvJNbBe"]
            )
        )
    )


async def do_filter_txs(client: SuiGrpcClient):
    """Fetch all transactions matching filter."""
    raise NotImplementedError(
        f"Mysten has not implemented filtering transactions in gRPC."
    )


async def do_tx_kind(client: SuiGrpcClient):
    """Fetch the PTB details from transaction."""
    handle_result(
        await client.execute(
            request=rn.GetTxKind(digest="4oZJ5bHgtmE6vHwALdQWVsQxor5tW2jWwUigKQvJNbBe")
        )
    )


async def do_staked_sui(client: SuiGrpcClient):
    """Fetch owner's staked coins."""
    handle_result(
        await client.execute(
            # Alias for GetStaked
            request=rn.GetDelegatedStakes(owner=client.config.active_address)
        )
    )


async def do_latest_cp(client: SuiGrpcClient):
    """."""
    handle_result(await client.execute(request=rn.GetLatestCheckpoint()))


async def do_sequence_cp(client: SuiGrpcClient):
    """."""
    result = await client.execute(request=rn.GetLatestCheckpoint())
    if result.is_ok():
        cp: sui_prot.GetCheckpointResponse = result.result_data
        handle_result(
            await client.execute(
                request=rn.GetCheckpointBySequence(
                    sequence_number=cp.checkpoint.sequence_number
                )
            )
        )
    else:
        print(result.result_string)


async def do_digest_cp(client: SuiGrpcClient):
    """."""
    result = await client.execute(request=rn.GetLatestCheckpoint())
    if result.is_ok():
        cp: sui_prot.GetCheckpointResponse = result.result_data
        handle_result(
            await client.execute(
                request=rn.GetCheckpointByDigest(digest=cp.checkpoint.digest)
            )
        )
    else:
        print(result.result_string)


async def do_checkpoints(client: SuiGrpcClient):
    """Uses subscriptions for checkpoints."""
    fields = ["sequenceNumber", "digest", "summary.timestamp"]
    gobj = rn.SubscribeCheckpoint(field_mask=fields)
    so_res = await client.execute(request=gobj)

    # List maximum of 3
    max_try = 3
    in_try = 0
    async for cpoint in so_res.result_data:
        print(cpoint.to_json(indent=2))
        in_try += 1
        if in_try == max_try:
            break


async def do_refgas(client: SuiGrpcClient):
    """Fetch the most current system state summary."""
    print(f"Current reference gas price: {await client.current_gas_price}")


async def do_nameservice(client: SuiGrpcClient):
    """Fetch name service by name.

    Replace name argument in request to valid name.

    """
    handle_result(await client.execute(request=rn.NameLookup(name="")))


async def do_owned_nameservice(client: SuiGrpcClient):
    """Fetch owned named services by address.

    Replace address argument in request to valid Sui address string.

    """
    handle_result(await client.execute(request=rn.ReverseNameLookup(address="")))


async def do_validators_apy(client: SuiGrpcClient):
    """Fetch the most current validators apy and identity."""
    results = await client.execute(request=rn.GetValidatorsApy())
    if results.is_ok():
        for val in results.result_data:
            print(val)


async def do_validators(client: SuiGrpcClient):
    """Fetch the most current validator detail."""
    handle_result(await client.execute(request=rn.GetCurrentValidators()))


async def do_all_validators(client: SuiGrpcClient):
    """Fetch all validators and show name and data."""
    await do_validators(client)


async def do_protcfg(client: SuiGrpcClient):
    """Fetch the most current system state summary."""
    prtcl_cfg = await client.protocol()
    print(prtcl_cfg.to_json(indent=2))


async def do_struct(client: SuiGrpcClient):
    """Fetch structure by package::module::struct_name.

    This is a testnet object!!!
    """
    result = await client.execute(
        # Alias for GetDataType
        request=rn.GetStructure(
            package="0x2",
            module_name="coin",
            structure_name="CoinMetadata",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_structs(client: SuiGrpcClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute(
        request=rn.GetStructures(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_func(client: SuiGrpcClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute(
        request=rn.GetFunction(
            package="0x3",
            module_name="sui_system",
            function_name="request_add_stake_mul_coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_funcs(client: SuiGrpcClient):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute(
        request=rn.GetFunctions(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_module(client: SuiGrpcClient):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = await client.execute(
        request=rn.GetModule(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_package(client: SuiGrpcClient):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = await client.execute(
        request=rn.GetPackage(
            package="0x2",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_dry_run(client: SuiGrpcClient):
    """Execute a dry run."""

    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)

    handle_result(
        await client.execute(
            request=rn.SimulateTransactionLKind(
                transaction=txer.raw_kind(), sender=client.config.active_address
            )
        )
    )


async def do_split_any_half(client: SuiGrpcClient):
    """Split the 1st coin in wallet to another another equal to 1/2 in wallet.

    This will only run if there is more than 1 coin in wallet.
    """

    result = await client.execute(request=rn.GetGas(owner=client.config.active_address))
    if result.is_ok() and len(result.result_data.objects) > 1:
        amount = int(int(result.result_data.objects[0].balance) / 2)
        txer: AsyncSuiTransaction = await client.transaction()
        scres = await txer.split_coin(
            coin=result.result_data.objects[0], amounts=[amount]
        )
        await txer.transfer_objects(
            transfers=[scres], recipient=client.config.active_address
        )
        handle_result(
            await client.execute(
                request=rn.ExecuteTransaction(**await txer.build_and_sign())
            )
        )


async def do_execute(client: SuiGrpcClient):
    """Execute a split/transfer transaction."""
    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    bdict = await txer.build_and_sign()
    # Demonstrate verifying signature
    handle_result(
        await client.execute(
            request=rn.VerifySignature(
                address=client.config.active_address,
                message_type="Transaction",
                message=bdict["tx_bytestr"],
                signature=bdict["sig_array"][0],
            )
        )
    )
    handle_result(await client.execute(request=rn.ExecuteTransaction(**bdict)))


async def do_stake(client: SuiGrpcClient):
    """Stake some coinage.

    This uses a random validator (Blockscope.net on testnet). For different environment
    or different validator change the vaddress
    """
    vaddress = "0x44b1b319e23495995fc837dafd28fc6af8b645edddff0fc1467f1ad631362c23"
    txer: AsyncSuiTransaction = await client.transaction()

    # Take 1 Sui from gas
    stake_coin_split = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    # Stake the coin
    await txer.stake_coin(
        coins=[stake_coin_split],
        validator_address=vaddress,
    )
    # Uncomment to dry run
    handle_result(
        await client.execute(
            request=rn.SimulateTransactionLKind(
                transaction=txer.raw_kind(), sender=client.config.active_address
            )
        )
    )
    # Uncomment to execute the stake
    # handle_result(
    #     await client.execute(
    #         request=rn.ExecuteTransaction(**await txer.build_and_sign())
    #     )
    # )


async def do_unstake(client: SuiGrpcClient):
    """Unstake first Staked Sui if address has any."""

    owner = client.config.active_address
    result = await client.execute(request=rn.GetDelegatedStakes(owner=owner))
    if result.is_ok() and result.result_data.staked_coins:
        txer: AsyncSuiTransaction = await client.transaction()

        # Unstake the first staked coin
        await txer.unstake_coin(
            staked_coin=result.result_data.staked_coins[0].object_id
        )
        # Uncomment to dry run
        handle_result(
            await client.execute(
                request=rn.SimulateTransactionLKind(
                    transaction=txer.raw_kind(), sender=client.config.active_address
                )
            )
        )

        # Uncomment to execute the stake
        # handle_result(
        #     await client.execute(
        #         request=rn.ExecuteTransaction(**await txer.build_and_sign())
        #     )
        # )

    else:
        print(f"No staked Sui for {owner}")


async def main():
    """Example main."""
    client_init: SuiGrpcClient = None
    try:
        client_init = SuiGrpcClient(
            pysui_config=PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GRPC_GROUP,  # Default gRPC group
                profile_name="devnet",
                # profile_name="testnet",
                # profile_name="mainnet",
                # profile_name="test-arch",
                # profile_name="main-arch",
            ),
        )
        print(f"Active chain profile   '{client_init.config.active_profile}'")
        print(f"Active Address '{client_init.config.active_address}'")
        print()

        ## QueryNodes (fetch)
        # await do_coin_meta(client_init)
        # await do_coins_for_type(client_init)
        # await do_gas(client_init)
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
        await do_dry_run(client_init)
        # await do_split_any_half(client_init)
        # await do_execute(client_init)
        # await do_stake(client_init)
        # await do_unstake(client_init)
        ## Config
        # await do_chain_id(client_init)
        # await do_service_config(client_init)
        # await do_protcfg(client_init)
    except (ValueError, NotImplementedError) as ve:
        print(ve)
    finally:
        if client_init:
            client_init.close()


if __name__ == "__main__":
    asyncio.run(main())
