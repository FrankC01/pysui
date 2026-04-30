#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for incremental buildout of Async Sui GraphQL RPC for Pysui 1.0.0."""

import asyncio

# import logging

# logging.basicConfig(level=logging.DEBUG)

from pysui import PysuiConfiguration, SuiRpcResult, client_factory, AsyncClientBase
from pysui.sui.sui_common.client import PysuiClient
from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
from pysui.sui.sui_common.trxn_base import FundsSource
from pysui.sui.sui_pgql.pgql_async_txn import AsyncSuiTransaction

import pysui.sui.sui_pgql.pgql_query as qn  # protocol-level access: queries without a SuiCommand
import pysui.sui.sui_pgql.pgql_types as ptypes
import pysui.sui.sui_common.sui_commands as cmd
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_gas_objects,
    async_get_all_owned_objects,
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


async def do_coin_meta(client: AsyncClientBase):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    handle_result(await client.execute(command=cmd.GetCoinMetaData()))


async def do_coins_for_type(client: AsyncClientBase):
    """Fetch coins of specific type for owner."""
    handle_result(
        await client.execute(
            command=cmd.GetCoins(
                owner=client.config.active_address,
                coin_type="0x2::coin::Coin<0x2::sui::SUI>",
            )
        )
    )


async def do_objects_for_type(client: AsyncClientBase):
    """Fetch objects of specific type owned by an address."""
    handle_result(
        await client.execute(
            command=cmd.GetObjectsForType(
                owner=client.config.active_address,
                object_type="0x2::coin::Coin<0x2::sui::SUI>",
            )
        )
    )


async def do_gas(client: AsyncClientBase):
    """Fetch 0x2::sui::SUI (default) for owner."""
    result = handle_result(
        await client.execute(command=cmd.GetGas(owner=client.config.active_address))
    )
    if result.is_ok():
        print(f"Total coins in page: {len(result.result_data.objects)}")


async def do_all_gas(client: AsyncSuiGQLClient):
    """Fetch all coins for owner.
    protocol-level access: async_get_all_owned_gas_objects is GraphQL-specific.
    """
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


async def do_gas_ids(client: AsyncSuiGQLClient):
    """Fetch coins by the ids.
    protocol-level access: GetMultipleGasObjects has no SuiCommand equivalent.
    """

    # Use coins found for active address to validate fetching by coin ids
    result = await client.execute(
        command=cmd.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and result.result_data.data:
        cids = [x.coin_object_id for x in result.result_data.data]
        result = handle_result(
            await client.execute_query_node(  # protocol-level access: GetMultipleGasObjects
                with_node=qn.GetMultipleGasObjects(coin_object_ids=cids)
            )
        )
    elif result.is_err():
        print(f"Error calling GraphQL {result.result_string}")
    else:
        print(f"Data return from call is empty {result.result_data.data}")


async def do_sysstate(client: AsyncSuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(await client.execute(command=cmd.GetLatestSuiSystemState()))


async def do_address_balance(client: AsyncClientBase):
    """."""
    handle_result(
        await client.execute(
            command=cmd.GetAddressCoinBalance(owner=client.config.active_address)
        )
    )


async def do_address_balances(client: AsyncClientBase):
    """Fetch all coin types and there total balances for owner.

    Demonstrates paging as well
    """
    result = await client.execute(
        command=cmd.GetAddressCoinBalances(owner=client.config.active_address)
    )
    handle_result(result)
    if result.is_ok():
        while result.result_data.next_cursor.hasNextPage:
            result = await client.execute(
                command=cmd.GetAddressCoinBalances(
                    owner=client.config.active_address,
                    next_page=result.result_data.next_cursor,
                )
            )
            handle_result(result)
        print("DONE")


async def do_object(client: AsyncClientBase):
    """Fetch specific object data."""
    handle_result(await client.execute(command=cmd.GetObject(object_id="0x6")))


async def do_object_content(client: AsyncClientBase):
    """Fetch BCS content for a single object.

    Set 'object_id' to object address of choice.
    """
    handle_result(
        await client.execute(
            command=cmd.GetObjectContent(
                object_id="0x7658a888e3f2c9c4e80b6ded17f07b4f2a6621195cdd74743a815e1f526969de"
            )
        )
    )


async def do_objects(client: AsyncSuiGQLClient):
    """Fetch all objects held by owner.
    protocol-level access: async_get_all_owned_objects is GraphQL-specific.
    """
    try:
        objects: list = await async_get_all_owned_objects(
            client.config.active_address, client
        )
        for object in objects:
            print(object.to_json(indent=2))
    except ValueError as ve:
        raise ve


async def do_past_object(client: AsyncClientBase):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    handle_result(
        await client.execute(
            command=cmd.GetPastObject(
                object_id="0x2803dd7600c24b4e26e9478e8f32424985c57a7e3fcdd3db7fa063cdf5d4c396",
                version=3,
            )
        )
    )


async def do_multiple_object_versions(client: AsyncSuiGQLClient):
    """Fetchs object details by version.
    protocol-level access: GetMultipleVersionedObjects has no SuiCommand equivalent.
    To run, change the objectID str and version int.
    """
    object_versions = [
        {
            "address": "0x0c11bba3ea02576c30c9e627683277264a6c775bb65dbc9a6f818d91f93c6d82",
            "version": 43,
        }
    ]
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetMultipleVersionedObjects(for_versions=object_versions)
        )
    )


async def do_multiple_object_content(client: AsyncClientBase):
    """Fetch BCS content for multiple objects."""
    handle_result(
        await client.execute(
            command=cmd.GetMultipleObjectContent(
                object_ids=[
                    "0x7658a888e3f2c9c4e80b6ded17f07b4f2a6621195cdd74743a815e1f526969de"
                ]
            )
        )
    )


async def do_objects_for(client: AsyncClientBase):
    """Fetch specific objects by their ids.

    These are test IDs, replace to run.
    """
    handle_result(
        await client.execute(
            command=cmd.GetMultipleObjects(
                object_ids=[
                    "0x2803dd7600c24b4e26e9478e8f32424985c57a7e3fcdd3db7fa063cdf5d4c396",
                    "0x285c48a3bc7440f08ad91caf6955f8b9b8c2db69e4b4c5071aa94c2468689d93",
                ]
            )
        )
    )


async def do_dynamics(client: AsyncClientBase):
    """Get objects dynamic field and dynamic object fields.

    This is test ID, replace to run.
    """
    handle_result(
        await client.execute(
            command=cmd.GetDynamicFields(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed"
            )
        )
    )


async def do_event(client: AsyncSuiGQLClient):
    """Fetch events matching a filter.
    protocol-level access: GetEvents SuiCommand removed; use legacy GQL query directly.
    """
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetEvents(event_filter={"sender": "0x0"})
        )
    )


async def do_configs(client: AsyncSuiGQLClient):
    """Fetch the GraphQL, Protocol and System configurations.
    protocol-level access: rpc_config is a GraphQL-specific property.
    """
    print(client.rpc_config.to_json(indent=2))


async def do_service_config(client: AsyncSuiGQLClient):
    """Fetch the GraphQL service configuration.
    protocol-level access: rpc_config is a GraphQL-specific property.
    """
    print(client.rpc_config().serviceConfig.to_json(indent=2))


async def do_chain_id(client: AsyncClientBase):
    """Fetch the current environment chain_id."""
    handle_result(await client.execute(command=cmd.GetChainIdentifier()))


async def do_tx(client: AsyncSuiGQLClient):
    """Fetch specific transaction by it's digest.
    protocol-level access: GetTx SuiCommand removed; use legacy GQL query directly.
    """
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetTx(digest="A8kCT1n8dmCWchz5WnKPsQ8x7U49ExgMEWJ13nRULpiz")
        )
    )


async def do_txs(client: AsyncSuiGQLClient):
    """Fetch transactions.
    protocol-level access: GetMultipleTx (batch by digest) is not supported by GraphQL via SuiCommand.
    Use GetFilteredTx for filtered queries over GraphQL.

    We loop through 3 pages.
    """
    result = await client.execute_query_node(  # protocol-level access: gql_class=None for GetMultipleTx
        with_node=qn.GetMultipleTx()
    )
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


async def do_filter_txs(client: AsyncSuiGQLClient):
    """Fetch all transactions matching filter.
    protocol-level access: GetFilteredTx SuiCommand removed; use legacy GQL query directly.

    See Sui GraphQL schema for TransactionFilter options.
    """
    obj_filter = {"affectedObject": "ENTER OBJECT_ID HERE"}
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


async def do_tx_kind(client: AsyncSuiGQLClient):
    """Fetch the PTB details from transaction.
    protocol-level access: GetTxKind SuiCommand removed; use legacy GQL query directly.
    """
    handle_result(
        await client.execute_query_node(
            with_node=qn.GetTxKind(digest="ENTER TRANSACTION DIGEST HERE")
        )
    )


async def do_staked_sui(client: AsyncClientBase):
    """."""
    owner = client.config.active_address
    handle_result(await client.execute(command=cmd.GetDelegatedStakes(owner=owner)))


async def do_latest_cp(client: AsyncClientBase):
    """."""
    handle_result(await client.execute(command=cmd.GetLatestCheckpoint()))


async def do_sequence_cp(client: AsyncClientBase):
    """."""
    result = await client.execute(command=cmd.GetLatestCheckpoint())
    if result.is_ok():
        cp: ptypes.CheckpointGQL = result.result_data
        handle_result(
            await client.execute(
                command=cmd.GetCheckpointBySequence(sequence_number=cp.sequence_number)
            )
        )
    else:
        print(result.result_string)


async def do_checkpoints(client: AsyncSuiGQLClient):
    """Fetch checkpoint list.
    protocol-level access: GetCheckpoints has no SuiCommand equivalent.
    """
    handle_result(await client.execute_query_node(with_node=qn.GetCheckpoints()))


async def do_refgas(client: AsyncSuiGQLClient):
    """Fetch the current reference gas price.
    protocol-level access: GetReferenceGasPrice has no SuiCommand equivalent.
    """
    handle_result(await client.execute_query_node(with_node=qn.GetReferenceGasPrice()))


async def do_nameservice(client: AsyncClientBase):
    """Fetch the most current system state summary."""
    handle_result(
        await client.execute(command=cmd.GetNameServiceAddress(name="gql-frank"))
    )


async def do_owned_nameservice(client: AsyncClientBase):
    """Fetch the most current system state summary."""
    handle_result(
        await client.execute(
            command=cmd.GetNameServiceNames(owner=client.config.active_address)
        )
    )


async def do_all_validators(client: AsyncSuiGQLClient):
    """Fetch all validators from current Epoch (GQL paging handled internally)."""
    handle_result(await client.execute(command=cmd.GetCurrentValidators()))


async def do_validators(client: AsyncSuiGQLClient):
    """Fetch the most current validator detail."""
    handle_result(await client.execute(command=cmd.GetCurrentValidators()))


async def do_validator_xchange_rates(client: AsyncSuiGQLClient):
    """Get exchange rate table entries.

    Uses the protocol-level GQL query to retrieve the exchange rate address
    from ValidatorSetsGQL (GetValidatorExchangeRates has no SuiCommand equivalent).
    """

    # Get list of validators via legacy protocol-level query to access exchangeRateTableAddress
    result = await client.execute_query_node(with_node=qn.GetCurrentValidators())
    if result.is_ok():
        # Extract the first validator's exchange rate object
        v_set: ptypes.ValidatorSetsGQL = result.result_data
        if v_set.validators:
            vexr_addy = v_set.validators[0].exchangeRateTableAddress
            er_results = await client.execute_query_node(
                with_node=qn.GetValidatorExchangeRates(
                    validator_exchange_address=vexr_addy, epoch_ids=[0, 1, 2]
                )
            )
            if er_results.is_ok():
                print(er_results.result_data.to_json(indent=2))


async def do_protcfg(client: AsyncClientBase):
    """Fetch the most current protocol configuration.

    By default, the current protocol version is used. You
    can set an `int` value otherwise to get past protocol states.
    """
    handle_result(await client.execute(command=cmd.GetProtocolConfig()))


async def do_struct(client: AsyncClientBase):
    """Fetch structure by package::module::struct_name.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetStructure(
            package="0x2",
            module_name="coin",
            structure_name="CoinMetadata",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_structs(client: AsyncClientBase):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetStructures(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_func(client: AsyncClientBase):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetFunction(
            package="0x2",
            module_name="coin",
            function_name="join",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_funcs(client: AsyncClientBase):
    """Fetch structures by package::module.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetFunctions(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_module(client: AsyncClientBase):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetModule(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_package(client: AsyncClientBase):
    """Fetch a module from package.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetPackage(
            package="0x2",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_epoch(client: AsyncClientBase):
    """Fetch current epoch info (omit epoch_id for current, or pass an int for a specific epoch)."""
    handle_result(await client.execute(command=cmd.GetEpoch()))


async def do_package_versions(client: AsyncClientBase):
    """Fetch all versions of a Move package.

    Change package_address to the storage address of any version of the target package.
    """
    handle_result(
        await client.execute(command=cmd.GetPackageVersions(package_address="0x2"))
    )


async def do_dry_run(client: AsyncClientBase):
    """Execute a simulate (dry run)."""

    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    tx_data = await txer.transaction_data()

    handle_result(
        await client.execute(
            command=cmd.SimulateTransaction(tx_bytestr=tx_data.serialize())
        )
    )


async def do_dry_run_txkind(txer: AsyncSuiTransaction):
    """Execute a simulate (dry run) with just the TransactionKind."""
    handle_result(
        await txer.client.execute(
            command=cmd.SimulateTransactionKind(
                tx_kind=txer.raw_kind(),
                tx_meta={"sender": txer.client.config.active_address},
            )
        )
    )


async def inspect_example(client: AsyncClientBase):
    """Execute a dryrun just on the TransactionKind of a transaction."""

    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    await do_dry_run_txkind(txer)


async def do_split_any_half(client: AsyncClientBase):
    """Split the 1st coin in wallet to another another equal to 1/2 in wallet.

    This will only run if there is more than 1 coin in wallet.
    """

    result = await client.execute(
        command=cmd.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and len(result.result_data.data) > 1:
        amount = int(int(result.result_data.data[0].balance) / 2)
        txer: AsyncSuiTransaction = await client.transaction()
        scres = await txer.split_coin(coin=result.result_data.data[0], amounts=[amount])
        await txer.transfer_objects(
            transfers=[scres], recipient=client.config.active_address
        )
        handle_result(
            await client.execute(
                command=cmd.ExecuteTransaction(**await txer.build_and_sign())
            )
        )


async def do_execute(client: AsyncClientBase):
    """Execute a transaction."""
    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(transfers=scres, recipient=client.config.active_address)
    handle_result(
        await client.execute(
            command=cmd.ExecuteTransaction(**await txer.build_and_sign())
        )
    )


async def do_stake(client: AsyncClientBase):
    """Stake some coinage.

    This uses a testnet validator (Blockscope.net). For different environment
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
    # Uncomment to simulate (dry run)
    handle_result(
        await client.execute(
            command=cmd.SimulateTransaction(tx_bytestr=await txer.build())
        )
    )
    # Uncomment to execute the stake
    # handle_result(
    #     await client.execute(
    #         command=cmd.ExecuteTransaction(**await txer.build_and_sign())
    #     )
    # )


async def do_unstake(client: AsyncClientBase):
    """Unstake first Staked Sui if address has any."""

    owner = client.config.active_address
    result = await client.execute(command=cmd.GetDelegatedStakes(owner=owner))
    if result.is_ok() and result.result_data.staked_coins:
        txer: AsyncSuiTransaction = await client.transaction()

        # Unstake the first staked coin
        await txer.unstake_coin(
            staked_coin=result.result_data.staked_coins[0].object_id
        )
        # Uncomment to simulate (dry run)
        handle_result(
            await client.execute(
                command=cmd.SimulateTransaction(tx_bytestr=await txer.build())
            )
        )

        # Uncomment to execute the stake
        # handle_result(
        #     await client.execute(
        #         command=cmd.ExecuteTransaction(**await txer.build_and_sign())
        #     )
        # )

    else:
        print(f"No staked Sui for {owner}")


async def do_sui_coin_to_account(client: AsyncClientBase):
    """Moves Sui mists to an account."""
    # Print before
    print("Before Sui coin balances")
    await do_address_balance(client)
    txer: AsyncSuiTransaction = await client.transaction()
    # Pull amount from transaction Gas
    scres = await txer.split_coin(coin=txer.gas, amounts=[1_000_000_000])
    await txer.move_call(
        target="0x2::coin::send_funds",
        type_arguments=["0x2::sui::SUI"],
        arguments=[scres, client.config.active_address],
    )
    # Uncomment to simulate (dry run)
    handle_result(
        await client.execute(
            command=cmd.SimulateTransactionKind(
                tx_kind=txer.raw_kind(),
                tx_meta={"sender": client.config.active_address},
            )
        )
    )
    # Uncomment to Execute
    # txdict = await txer.build_and_sign()
    # handle_result(await client.execute(command=cmd.ExecuteTransaction(**txdict)))


async def do_account_to_sui_coin(client: AsyncClientBase):
    """Moves account balance to Sui coin and transfer to current address.

    Execution, vs. DryRun, also demonstrates funding the transaction with sender account balance vs. gas coins.
    """
    # If set_balance is None, will use the total account balance
    set_balance: int = 1000000
    # Get the current balance
    curr_balance_res = await client.execute(
        command=cmd.GetAddressCoinBalance(owner=client.config.active_address)
    )
    # Validate existing funds exist.
    if curr_balance_res.is_ok():
        if curr_balance_res.result_data.balance.address_balance is None:
            raise ValueError(f"{client.config.active_address} Has no account balance")
        if not set_balance:
            set_balance = curr_balance_res.result_data.balance.address_balance
        else:
            if set_balance > curr_balance_res.result_data.balance.address_balance:
                raise ValueError(
                    f"{set_balance} exceeds existing address balance of {curr_balance_res.result_data.balance.address_balance}"
                )
        # Enable the transaction to use account for gas payments.
        txer: AsyncSuiTransaction = await client.transaction()
        coin = await txer.balance_from(source=FundsSource.SENDER, amount=set_balance)
        await txer.transfer_objects(
            transfers=[coin], recipient=client.config.active_address
        )

        # Uncomment to dry run
        # As we are using the address balance to pay for transaction
        # we want to get an estimate that reflects that, so setting `gas_selection=True` does
        # that.

        handle_result(
            await client.execute(
                command=cmd.SimulateTransactionKind(
                    tx_kind=txer.raw_kind(),
                    tx_meta={"sender": client.config.active_address},
                    gas_selection=True,
                )
            )
        )

        # Uncomment to Execute
        # Using the new build and signing method

        # txdict = await txer.build_and_sign(use_account_for_gas=True)
        # handle_result(
        #     await client.execute(command=cmd.ExecuteTransaction(**txdict))
        # )


async def main():
    """."""
    try:
        client_init: PysuiClient = client_factory(
            PysuiConfiguration(
                group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
                profile_name="devnet",
                # profile_name="testnet",
                # profile_name="mainnet",
                # persist=True,
            )
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
        # await do_address_balance(client_init)
        # await do_address_balances(client_init)
        # await do_object(client_init)
        # await do_objects_for_type(client_init)
        # await do_object_content(client_init)
        # await do_objects(client_init)
        # await do_past_object(client_init)
        # await do_multiple_object_versions(client_init)
        # await do_multiple_object_content(client_init)
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

        # await do_checkpoints(client_init)
        # await do_epoch(client_init)
        # await do_package_versions(client_init)
        # await do_owned_nameservice(client_init)
        # await do_all_validators(client_init)
        # await do_validators(client_init)
        # await do_validator_xchange_rates(client_init)
        # await do_nameservice(client_init)
        # await do_refgas(client_init)
        # await do_struct(client_init)
        # await do_structs(client_init)
        # await do_func(client_init)
        # await do_funcs(client_init)
        # await do_module(client_init)
        # await do_package(client_init)
        # await inspect_example(client_init)
        # await do_dry_run(client_init)
        # await do_split_any_half(client_init)
        # await do_execute(client_init)
        # await do_stake(client_init)
        # await do_unstake(client_init)
        # await do_sui_coin_to_account(client_init)
        # await do_account_to_sui_coin(client_init)
        ## Config
        # await do_chain_id(client_init)
        # await do_configs(client_init)
        # await do_service_config(client_init)
        # await do_protcfg(client_init)
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    asyncio.run(main())
