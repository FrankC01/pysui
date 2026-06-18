#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for Async Sui UCS (Uniform Command Set) for Pysui 1.0.0.

Demonstrates protocol-agnostic usage via SuiCommand and client_factory().
Set group_name in main() to SUI_GQL_RPC_GROUP or SUI_GRPC_GROUP — all
do_xx() functions work unchanged with either protocol.
"""

import asyncio
import base64

from pysui import PysuiConfiguration, SuiRpcResult, client_factory, AsyncClientBase
from pysui.sui.sui_common.async_txn import AsyncSuiTransaction
from pysui.sui.sui_common.txn_base import FundsSource

import pysui.sui.sui_common.sui_commands as cmd


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
                object_type="0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0588cff9a50e0eaf4cd50d337c1a36570bc1517793fd3303e1513e8ad4d2aa96::usdt::USDT>",
            )
        )
    )


async def do_gas(client: AsyncClientBase):
    """Fetch one page of 0x2::sui::SUI gas coins for owner.

    Returns a single page — the owner may have more coins than shown here.
    See do_all_gas() for full accumulation across all pages.
    """
    result = handle_result(
        await client.execute(command=cmd.GetGas(owner=client.config.active_address))
    )
    if result.is_ok():
        print(f"Coins this page: {len(result.result_data.objects)}")
        if result.result_data.next_page_token:
            print("  (more pages available — call do_all_gas() for full list)")


async def do_all_gas(client: AsyncClientBase):
    """Fetch ALL 0x2::sui::SUI gas coins for owner using manual page iteration.

    Demonstrates how a caller implements paging with execute() directly:
    hold the next_page_token from each result and pass it into a fresh command
    when requesting the next page. The result and command are fully decoupled —
    the token can be stored and used much later. See do_all_gas_alt() for the
    alternate way using the client to do the paging and return a full result.
    """
    owner = client.config.active_address
    all_coins = []
    next_page_token = None
    while True:
        result = await client.execute(
            command=cmd.GetGas(owner=owner, next_page_token=next_page_token)
        )
        if not result.is_ok():
            print(f"Error: {result.result_string}")
            break
        page = result.result_data
        all_coins.extend(page.objects)
        next_page_token = page.next_page_token
        if not next_page_token:
            break
    for coin in all_coins:
        print(coin.to_json(indent=2))
    print(f"Total coins: {len(all_coins)}")
    print(f"Total mists: {sum([int(x.balance) for x in all_coins])}")


async def do_all_gas_alt(client: AsyncClientBase):
    """Fetch ALL 0x2::sui::SUI gas coins for owner using execute_for_all().

    The client handles paging internally — accumulating all pages and returning
    a single result whose result_data contains the full coin list.
    """
    result = handle_result(
        await client.execute_for_all(
            command=cmd.GetGas(owner=client.config.active_address)
        )
    )
    if result.is_ok():
        print(f"Total coins: {len(result.result_data.objects)}")
        print(
            f"Total mists: {sum([int(x.balance) for x in result.result_data.objects])}"
        )


async def do_gas_ids(client: AsyncClientBase):
    """Fetch coins by the ids."""
    result = await client.execute_for_all(
        command=cmd.GetGas(owner=client.config.active_address)
    )
    if result.is_ok() and result.result_data.objects:
        cids = [x.object_id for x in result.result_data.objects]
        result = handle_result(
            await client.execute(command=cmd.GetMultipleObjects(object_ids=cids))
        )
    elif result.is_err():
        print(f"Error {result.result_string}")
    else:
        print(f"Data return from call is empty {result.result_data.objects}")


async def do_sysstate(client: AsyncClientBase):
    """Fetch the most current system state summary."""
    handle_result(await client.execute(command=cmd.GetLatestSuiSystemState()))


async def do_address_balance(client: AsyncClientBase):
    """Fetch coin balance for owner."""
    handle_result(
        await client.execute(
            command=cmd.GetAddressCoinBalance(
                owner=client.config.active_address, coin_type="0x2::sui::SUI"
            )
        )
    )


async def do_address_balances(client: AsyncClientBase):
    """Fetch all coin types and their total balances for owner.

    Demonstrates paging as well.
    """
    result = await client.execute(
        command=cmd.GetAddressCoinBalances(owner=client.config.active_address)
    )
    handle_result(result)
    if result.is_ok():
        while result.result_data.next_page_token:
            result = await client.execute(
                command=cmd.GetAddressCoinBalances(
                    owner=client.config.active_address,
                    next_page_token=result.result_data.next_page_token,
                )
            )
            handle_result(result)
        print("DONE")


async def do_object(client: AsyncClientBase):
    """Fetch specific object data."""
    handle_result(
        await client.execute(
            command=cmd.GetObject(
                object_id="0x3aab253af15cc6e116a4058f6caf0d87dc3df8fdf29c0704a4a86649237094a3"
            )
        )
    )


async def do_object_content(client: AsyncClientBase):
    """Fetch BCS content for a single object.

    Set 'object_id' to object address of choice.
    """
    handle_result(
        await client.execute(
            command=cmd.GetObjectContent(
                object_id="0x47f04c2327b45dfa6cb64d792ef53a5b7df8b0bf7ba3ef809a3de30f6fe26165"
            )
        )
    )


async def do_objects(client: AsyncClientBase):
    """Fetch all objects held by owner using execute_for_all()."""
    result = handle_result(
        await client.execute_for_all(
            command=cmd.GetObjectsOwnedByAddress(owner=client.config.active_address)
        )
    )
    if result.is_ok():
        for obj in result.result_data.objects:
            print(obj.to_json(indent=2))


async def do_past_object(client: AsyncClientBase):
    """Fetch a past object.
    To run, change the objectID str and version int.
    """
    handle_result(
        await client.execute(
            command=cmd.GetPastObject(
                object_id="0xdfa764b29d303acecc801828839108ea81a45e93c3b9ccbe05b0d9a697a2a9ed",
                version=17078252,
            )
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


async def do_multiple_object_versions(client: AsyncClientBase):
    """Fetch object details by version.
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
            command=cmd.GetMultiplePastObjects(for_versions=object_versions)
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
                    "0xb13248a6ed0cfe600fc9af1b4a12a7a22a44065070c57483e92e602c39c89b10",
                    "0xb9fc4cfbc77e594bee70c4014c545c38a654a2fc3fb7ac99759af2622cfec8d1",
                    "0xc299d0c17962366b46351bbe43d0178e306c8305d6a08168ce70a1b354cb3af4",
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
                object_id="0x73d05d62c18d9374e3ea529e8e0ed6161da1a141a94d3f76ae3fe4e99356db75"
            )
        )
    )


async def do_chain_id(client: AsyncClientBase):
    """Fetch the current environment chain_id."""
    handle_result(await client.execute(command=cmd.GetChainIdentifier()))


async def do_tx(client: AsyncClientBase):
    """Fetch specific transaction by its digest."""
    handle_result(
        await client.execute(
            command=cmd.GetTransaction(
                digest="8mP8YpKYPoS84sB4JGg5mrfahq55qwpMxa5KbaBF6nFT"
            )
        )
    )


async def do_txs(client: AsyncClientBase):
    """Fetch multiple transactions by digest list."""
    handle_result(
        await client.execute(
            command=cmd.GetTransactions(
                digests=[
                    "Du3fukucFwku6mKJfR3oor464w62LdSLG55Rf7HWpc2Q",
                    "7SbfCCV9nVSMJBkLYMVrNVKfBJoRPzZSjdcmNB41gcQ8",
                ]
            )
        )
    )


async def do_tx_kind(client: AsyncClientBase):
    """Fetch the ProgrammableTransaction kind from a transaction."""
    handle_result(
        await client.execute(
            command=cmd.GetTransactionKind(
                digest="4oZJ5bHgtmE6vHwALdQWVsQxor5tW2jWwUigKQvJNbBe"
            )
        )
    )


async def do_staked_sui(client: AsyncClientBase):
    """Fetch owner's staked coins."""
    handle_result(
        await client.execute(
            command=cmd.GetDelegatedStakes(owner=client.config.active_address)
        )
    )


async def do_latest_cp(client: AsyncClientBase):
    """Fetch the latest checkpoint."""
    handle_result(await client.execute(command=cmd.GetLatestCheckpoint()))


async def do_sequence_cp(client: AsyncClientBase):
    """Fetch checkpoint by sequence number, using the latest checkpoint's sequence."""
    result = await client.execute(command=cmd.GetLatestCheckpoint())
    if result.is_ok():
        handle_result(
            await client.execute(
                command=cmd.GetCheckpointBySequence(
                    sequence_number=result.result_data.checkpoint.sequence_number
                )
            )
        )
    else:
        print(result.result_string)


async def do_digest_cp(client: AsyncClientBase):
    """Fetch checkpoint by digest, using the latest checkpoint's digest."""
    result = await client.execute(command=cmd.GetLatestCheckpoint())
    if result.is_ok():
        handle_result(
            await client.execute(
                command=cmd.GetCheckpointByDigest(
                    digest=result.result_data.checkpoint.digest
                )
            )
        )
    else:
        print(result.result_string)


async def do_refgas(client: AsyncClientBase):
    """Fetch the current reference gas price."""
    result = await client.execute(command=cmd.GetBasicCurrentEpochInfo())
    if result.is_ok():
        print(f"Current reference gas price: {result.result_data.reference_gas_price}")
    else:
        print(result.result_string)


async def do_nameservice(client: AsyncClientBase):
    """Fetch name service address by name.

    Replace name argument with a valid name.
    """
    handle_result(await client.execute(command=cmd.GetNameServiceAddress(name="")))


async def do_owned_nameservice(client: AsyncClientBase):
    """Fetch owned name services by address."""
    handle_result(
        await client.execute(
            command=cmd.GetNameServiceNames(owner=client.config.active_address)
        )
    )


async def do_all_validators(client: AsyncClientBase):
    """Fetch all validators from current Epoch, accumulating all pages."""
    handle_result(await client.execute_for_all(command=cmd.GetCurrentValidators()))


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
    result = await client.execute_for_all(
        command=cmd.GetStructures(
            package="0x2",
            module_name="coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_func(client: AsyncClientBase):
    """Fetch a function by package::module::function_name.

    This is a testnet object!!!
    """
    result = await client.execute(
        command=cmd.GetFunction(
            package="0x3",
            module_name="sui_system",
            function_name="request_add_stake_mul_coin",
        )
    )
    if result.is_ok():
        print(result.result_data.to_json(indent=2))


async def do_funcs(client: AsyncClientBase):
    """Fetch functions by package::module.

    This is a testnet object!!!
    """
    result = await client.execute_for_all(
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
    """Fetch all modules from package.

    This is a testnet object!!!
    """
    result = await client.execute_for_all(
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
    await txer.transfer_objects(
        transfers=[scres], recipient=client.config.active_address
    )
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
                tx_kind=await txer.raw_kind(),
                tx_meta={"sender": txer.client.config.active_address},
            )
        )
    )


async def inspect_example(client: AsyncClientBase):
    """Execute a dryrun just on the TransactionKind of a transaction."""
    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[1000000000])
    await txer.transfer_objects(
        transfers=[scres], recipient=client.config.active_address
    )
    await do_dry_run_txkind(txer)


async def do_merge_to_one(client: AsyncClientBase):
    """If more than 1 Sui coin, merge to one.

    This takes the highest balanced coin and reserves it for gas, which
    is also the target to merge to.
    """
    result = await client.execute(
        command=cmd.GetCoins(owner=client.config.active_address)
    )
    if result.is_ok() and len(result.result_data.objects) > 1:
        d_coins = sorted(
            result.result_data.objects, key=lambda p: p.balance, reverse=True
        )
        txer: AsyncSuiTransaction = await client.transaction()
        await txer.merge_coins(merge_to=txer.gas, merge_from=d_coins[1:])
        handle_result(
            await client.execute(
                command=cmd.ExecuteTransaction(**await txer.build_and_sign())
            )
        )
    else:
        print("Only one coin exists for this address")


async def do_split_any_half(client: AsyncClientBase):
    """Split the 1st coin in wallet to another equal to 1/2 in wallet.

    This will only run if there is more than 1 coin in wallet.
    """
    result = await client.execute_for_all(
        command=cmd.GetGas(owner=client.config.active_address)
    )
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
                command=cmd.ExecuteTransaction(**await txer.build_and_sign())
            )
        )


async def do_execute(client: AsyncClientBase):
    """Splits an amount from active address account and sends to other account."""
    recipient: str = (
        "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28"
    )
    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[300_000_000])
    await txer.transfer_objects(transfers=[scres], recipient=recipient)
    handle_result(
        await client.execute(
            command=cmd.ExecuteTransaction(**await txer.build_and_sign())
        )
    )


async def do_verify_tx_sig(client: AsyncClientBase):
    """Build and sign a simple transaction, then verify the signature without executing."""
    recipient: str = (
        "0xa9fe7b9cab7ce187c768a9b16e95dbc5953a99ec461067a73a6b1c4288873e28"
    )
    txer: AsyncSuiTransaction = await client.transaction()
    scres = await txer.split_coin(coin=txer.gas, amounts=[300_000_000])
    await txer.transfer_objects(transfers=[scres], recipient=recipient)

    signed = await txer.build_and_sign()
    tx_bytes_b64: str = signed["tx_bytestr"]
    sig_b64: str = signed["sig_array"][0]
    author: str = str(client.config.active_address)

    # Happy path — valid signature
    handle_result(
        await client.execute(
            command=cmd.VerifyTransactionSignature(
                message=tx_bytes_b64,
                signature=sig_b64,
                author=author,
            )
        )
    )

    # Failure path — wrong author
    handle_result(
        await client.execute(
            command=cmd.VerifyTransactionSignature(
                message=tx_bytes_b64,
                signature=sig_b64,
                author=recipient,
            )
        )
    )


async def do_verify_pm_sig(client: AsyncClientBase):
    """Sign an arbitrary personal message and verify it; also show tampered-message failure."""
    pm_b64: str = base64.b64encode(b"Hello from pysui").decode()
    author: str = str(client.config.active_address)
    keypair = client.config.keypair_for_address(address=author)
    pm_sig_b64: str = keypair.sign_personal_message(pm_b64)

    # Happy path — valid signature
    handle_result(
        await client.execute(
            command=cmd.VerifyPersonalMessageSignature(
                message=pm_b64,
                signature=pm_sig_b64,
                author=author,
            )
        )
    )

    # Failure path — tampered message
    tampered_b64: str = base64.b64encode(b"Goodbye from pysui").decode()
    handle_result(
        await client.execute(
            command=cmd.VerifyPersonalMessageSignature(
                message=tampered_b64,
                signature=pm_sig_b64,
                author=author,
            )
        )
    )


async def do_stake(client: AsyncClientBase):
    """Stake some coinage.

    This uses a testnet validator (Blockscope.net). For different environment
    or different validator change the vaddress.
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
            command=cmd.SimulateTransactionKind(
                tx_kind=await txer.raw_kind(),
                tx_meta={"sender": client.config.active_address},
            )
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
    if result.is_ok() and result.result_data.objects:
        txer: AsyncSuiTransaction = await client.transaction()

        # Unstake the first staked coin
        await txer.unstake_coin(staked_coin=result.result_data.objects[0].object_id)
        # Uncomment to simulate (dry run)
        handle_result(
            await client.execute(
                command=cmd.SimulateTransactionKind(
                    tx_kind=await txer.raw_kind(),
                    tx_meta={"sender": client.config.active_address},
                )
            )
        )
        # Uncomment to execute the unstake
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
    await txer.fund_address_accumulator(
        funds=scres, recipient=client.config.active_address
    )
    # Uncomment to simulate (dry run)
    handle_result(
        await client.execute(
            command=cmd.SimulateTransactionKind(
                tx_kind=await txer.raw_kind(),
                tx_meta={"sender": client.config.active_address},
                gas_selection=True,
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
    set_balance: int = 1_000
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
        coin = await txer.coin_from_address_accumulator(
            source=FundsSource.SENDER, amount=set_balance
        )
        await txer.transfer_objects(
            transfers=[coin], recipient=client.config.active_address
        )
        # Uncomment to dry run — gas_selection=True estimates using address balance for gas
        handle_result(
            await client.execute(
                command=cmd.SimulateTransactionKind(
                    tx_kind=await txer.raw_kind(),
                    tx_meta={"sender": client.config.active_address},
                    gas_selection=True,
                )
            )
        )
        # Uncomment to Execute
        # txdict = await txer.build_and_sign(use_account_for_gas=True)
        # handle_result(await client.execute(command=cmd.ExecuteTransaction(**txdict)))


async def main():
    """Run example functions against a live Sui node.

    To switch protocols, change the group_name argument in the PysuiConfiguration
    constructor below:
      - PysuiConfiguration.SUI_GQL_RPC_GROUP  — use the GraphQL transport
      - PysuiConfiguration.SUI_GRPC_GROUP     — use the gRPC transport

    SUI_GQL_RPC_GROUP and SUI_GRPC_GROUP are the pysui default group names created
    during initial configuration. If you have defined your own custom group names,
    substitute them here in place of the defaults.

    All do_xx() functions in this module are protocol-agnostic — they work unchanged
    regardless of which group is active.
    """
    client_init: AsyncClientBase = None
    try:
        client_init = client_factory(
            PysuiConfiguration(
                # Uncomment one group:
                # group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
                group_name=PysuiConfiguration.SUI_GRPC_GROUP,
                # profile_name="devnet",
                profile_name="testnet",
                # profile_name="mainnet",
            )
        )
        print(f"Active address '{client_init.config.active_address}'")
        print()

        ## QueryNodes (fetch)
        # await do_coin_meta(client_init)
        # await do_coins_for_type(client_init)
        await do_gas(client_init)
        # await do_all_gas(client_init)
        # await do_all_gas_alt(client_init)
        # await do_gas_ids(client_init)
        # await do_sysstate(client_init)
        # await do_address_balance(client_init)
        # await do_address_balances(client_init)
        # await do_object(client_init)
        # await do_objects_for_type(client_init)
        # await do_object_content(client_init)
        # await do_objects(client_init)
        # await do_past_object(client_init)
        # await do_multiple_object_content(client_init)
        # await do_multiple_object_versions(client_init)
        # await do_objects_for(client_init)
        # await do_dynamics(client_init)
        # await do_tx(client_init)
        # await do_txs(client_init)
        # await do_tx_kind(client_init)
        # await do_staked_sui(client_init)
        # await do_latest_cp(client_init)
        # await do_sequence_cp(client_init)
        # await do_digest_cp(client_init)
        # await do_epoch(client_init)
        # await do_package_versions(client_init)
        # await do_owned_nameservice(client_init)
        # await do_all_validators(client_init)
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
        # await do_merge_to_one(client_init)
        # await do_split_any_half(client_init)
        # await do_execute(client_init)
        # await do_verify_tx_sig(client_init)
        # await do_verify_pm_sig(client_init)
        # await do_stake(client_init)
        # await do_unstake(client_init)
        # await do_sui_coin_to_account(client_init)
        # await do_account_to_sui_coin(client_init)
        ## Config
        # await do_chain_id(client_init)
        # await do_protcfg(client_init)
    except (ValueError, NotImplementedError) as ve:
        print(ve)
    finally:
        if client_init:
            await client_init.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, asyncio.CancelledError, Exception) as rte:
        print(rte)
