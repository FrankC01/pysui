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
#
"""Sample module for incremental buildout of Async Sui GraphQL RPC for Pysui 1.0.0."""

import asyncio

from pysui.sui.sui_pgql.clients import (
    AsyncSuiGQLClient,
    SUI_GRAPHQL_MAINNET,
    SUI_GRAPHQL_TESTNET,
)
import pysui.sui.sui_pgql.pgql_query as qn


async def do_coin_meta(client: AsyncSuiGQLClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    res = await client.execute_query(with_query_node=qn.GetCoinMetaData())
    print(res.to_json(indent=2))
    res = await client.execute_query(
        with_query_node=qn.GetCoinMetaData(
            coin_type="0x3::staking_pool::StakedSui",
            # coin_type="0xbff8dc60d3f714f678cd4490ff08cabbea95d308c6de47a150c79cc875e0c7c6::sbox::SBOX",
        )
    )
    print(res.to_json(indent=2))


async def do_coins_for_type(client: AsyncSuiGQLClient):
    """Fetch coins of specific type for owner."""
    qres = await client.execute_query(
        # GetAllCoinsOfType requires a coin type
        with_query_node=qn.GetCoins(
            owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a",
            coin_type="0xbff8dc60d3f714f678cd4490ff08cabbea95d308c6de47a150c79cc875e0c7c6::sbox::SBOX",
        )
    )
    print(qres.to_json(indent=2))


async def do_gas(client: AsyncSuiGQLClient):
    """Fetch 0x2::sui::SUI (default) for owner."""

    qres = await client.execute_query(
        # GetAllCoins defaults to "0x2::sui::SUI"
        with_query_node=qn.GetCoins(
            owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
        )
    )
    print(qres.to_json(indent=2))


async def do_sysstate(client: AsyncSuiGQLClient):
    """Fetch the most current system state summary."""
    qres = await client.execute_query(with_query_node=qn.GetLatestSuiSystemState())
    print(qres.to_json(indent=2))


async def do_all_balances(client: AsyncSuiGQLClient):
    """Fetch all coin types and there total balances for owner.

    Demonstrates paging as well
    """
    coin_owner = "0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
    qres = await client.execute_query(
        with_query_node=qn.GetAllCoinBalances(owner=coin_owner)
    )
    if qres and not hasattr(qres, "errors"):
        print(qres.to_json(indent=2))
        while qres.next_cursor.hasNextPage:
            qres = await client.execute_query(
                with_query_node=qn.GetAllCoinBalances(
                    owner=coin_owner, next_page=qres.next_cursor
                )
            )
            print(qres.to_json(indent=2))
        print("DONE")
    else:
        print(qres.errors)


async def do_object(client: AsyncSuiGQLClient):
    """Fetch specific object data."""
    result = await client.execute_query(
        with_query_node=qn.GetObject(
            # object_id="0xf0f919fac17bf50e82f32550290c359553fc3df6267cbeb4e4dbb75195375f4b"
            object_id="0x6"
        )
    )
    print(result.to_json(indent=2))


async def do_objects(client: AsyncSuiGQLClient):
    """Fetch all objects help by owner."""
    result = await client.execute_query(
        with_query_node=qn.GetObjectsOwnedByAddress(
            owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
        )
    )
    print(result.to_json(indent=2))


async def do_objects_for(client: AsyncSuiGQLClient):
    """Fetch specific objects by their ids."""
    result = await client.execute_query(
        with_query_node=qn.GetMultipleObjects(
            object_ids=[
                "0x52da4299641620148676cab1abdb17d6c4de7c0534a9c130a05887a0b8fcb2e2",
                "0x598a5a12cfedbe3ba2a0ce1162345e95ea926c6a7fb29062a152a85fbb29af07",
                "0xf889dd9c5f0f7459a01abf8fead765d4a529c3d492948d7df1ddb480cec83aeb",
            ]
        )
    )
    print(result.to_json(indent=2))


async def do_event(client: AsyncSuiGQLClient):
    """."""
    result = await client.execute_query(
        with_query_node=qn.GetEvents(event_filter={"sender": "0x0"})
    )
    print(result.to_json(indent=2))


async def do_configs(client: AsyncSuiGQLClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config.to_json(indent=2))


async def do_chain_id(client: AsyncSuiGQLClient):
    """Fetch the current environment chain_id.

    Demonstrates overriding serialization
    """

    print(client.chain_id)


async def do_tx(client: AsyncSuiGQLClient):
    """Fetch specific transaction by it's digest."""
    res = await client.execute_query(
        with_query_node=qn.GetTx(digest="CypToNgx6jN2V6vDZGtgpeEv1zSs4VGJcANJi85w9Ypm")
    )
    print(res.to_json(indent=2))


async def do_txs(client: AsyncSuiGQLClient):
    """Fetch transactions.

    We loop through 3 pages.
    """
    qres = await client.execute_query(with_query_node=qn.GetMultipleTx())
    if qres and not hasattr(qres, "errors"):
        print(qres.to_json(indent=2))
        max_page = 3
        in_page = 0
        while True:
            in_page += 1
            if in_page < max_page and qres.next_cursor:
                qres = await client.execute_query(
                    with_query_node=qn.GetMultipleTx(next_page=qres.next_cursor)
                )
                print(qres.to_json(indent=2))
            else:
                break
        print("DONE")
    else:
        print(qres.errors)


async def do_staked_sui(client: AsyncSuiGQLClient):
    """."""
    owner = (
        # Main net
        "0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
        if client.url == SUI_GRAPHQL_MAINNET
        # Test net
        else "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4"
    )
    result = await client.execute_query(
        with_query_node=qn.GetDelegatedStakes(owner=owner)
    )
    print(result)


async def do_latest_cp(client: AsyncSuiGQLClient):
    """."""
    qnode = qn.GetLatestCheckpointSequence()
    # print(qnode.query_as_string())
    result = await client.execute_query(with_query_node=qnode)
    print(result.to_json(indent=2))


async def do_sequence_cp(client: AsyncSuiGQLClient):
    """."""
    result = await client.execute_query(
        with_query_node=qn.GetCheckpointBySequence(sequence_number=18888268)
    )
    print(result.to_json(indent=2))


async def do_digest_cp(client: AsyncSuiGQLClient):
    """."""
    result = await client.execute_query(
        with_query_node=qn.GetCheckpointByDigest(
            digest="8GonuNB363QrdTNMCx1u7mM73tVgnv7QiheSczktnN1R"
        )
    )
    print(result.to_json(indent=2))


async def do_checkpoints(client: AsyncSuiGQLClient):
    """."""
    result = await client.execute_query(with_query_node=qn.GetCheckpoints())
    print(result.to_json(indent=2))


async def do_refgas(client: AsyncSuiGQLClient):
    """Fetch the most current system state summary."""
    qres = await client.execute_query(with_query_node=qn.GetReferenceGasPrice())
    print(qres.to_json(indent=2))


async def do_nameservice(client: AsyncSuiGQLClient):
    """Fetch the most current system state summary."""
    qres = await client.execute_query(
        with_query_node=qn.GetNameServiceAddress(name="gql-frank")
    )
    print(qres)


async def do_protcfg(client: AsyncSuiGQLClient):
    """Fetch the most current system state summary."""
    qres = await client.execute_query(with_query_node=qn.GetProtocolConfig(version=30))
    print(qres.to_json(indent=2))


async def main():
    """."""
    client_init = AsyncSuiGQLClient(gql_rpc_url=SUI_GRAPHQL_MAINNET, write_schema=True)
    ## QueryNodes (fetch)
    # await do_coin_meta(client_init)
    # await do_coins_for_type(client_init)
    # await do_gas(client_init)
    # await do_sysstate(client_init)
    # await do_all_balances(client_init)
    # await do_object(client_init)
    await do_objects(client_init)
    # await do_objects_for(client_init)
    # await do_event(client_init)
    # await do_tx(client_init)
    # await do_txs(client_init)
    # await do_staked_sui(client_init)
    # await do_latest_cp(client_init)
    # await do_sequence_cp(client_init)
    # await do_digest_cp(client_init)
    # await do_checkpoints(client_init)
    # await do_refgas(client_init)
    # await do_nameservice(client_init)
    # await do_protcfg(client_init)
    ## Config
    # await do_chain_id(client_init)
    # await do_configs(client_init)
    # await do_protcfg(client_init)


if __name__ == "__main__":
    asyncio.run(main())
