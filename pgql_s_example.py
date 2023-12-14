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

"""Sample module for incremental buildout of Sui GraphQL RPC for Pysui 1.0.0."""

from pysui.sui.sui_pgql.pgql_clients import (
    SuiGQLClient,
    SUI_GRAPHQL_MAINNET,
    SUI_GRAPHQL_TESTNET,
)
import pysui.sui.sui_pgql.pgql_query as qn
from pysui import SuiConfig


def do_coin_meta(client: SuiGQLClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    print(client.execute_query(with_query_node=qn.GetCoinMetaData()).to_json(indent=2))
    print(
        client.execute_query(
            with_query_node=qn.GetCoinMetaData(
                coin_type="0x3::staking_pool::StakedSui",
                # coin_type="0xbff8dc60d3f714f678cd4490ff08cabbea95d308c6de47a150c79cc875e0c7c6::sbox::SBOX",
            )
        ).to_json(indent=2)
    )


def do_coins_for_type(client: SuiGQLClient):
    """Fetch coins of specific type for owner."""
    qres = client.execute_query(
        # GetAllCoinsOfType requires a coin type
        with_query_node=qn.GetCoins(
            owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a",
            coin_type="0xbff8dc60d3f714f678cd4490ff08cabbea95d308c6de47a150c79cc875e0c7c6::sbox::SBOX",
        )
    )
    print(qres.to_json(indent=2))


def do_gas(client: SuiGQLClient):
    """Fetch 0x2::sui::SUI (default) for owner."""

    qres = client.execute_query(
        # GetAllCoins defaults to "0x2::sui::SUI"
        with_query_node=qn.GetCoins(
            owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
        )
    )
    print(qres.to_json(indent=2))


def do_sysstate(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    qres = client.execute_query(with_query_node=qn.GetLatestSuiSystemState())
    print(qres.to_json(indent=2))


def do_all_balances(client: SuiGQLClient):
    """Fetch all coin types and there total balances for owner.

    Demonstrates paging as well
    """
    coin_owner = "0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
    qres = client.execute_query(with_query_node=qn.GetAllCoinBalances(owner=coin_owner))
    if qres and not hasattr(qres, "errors"):
        print(qres.to_json(indent=2))
        while qres.next_cursor.hasNextPage:
            qres = client.execute_query(
                with_query_node=qn.GetAllCoinBalances(
                    owner=coin_owner, next_page=qres.next_cursor
                )
            )
            print(qres.to_json(indent=2))
        print("DONE")
    else:
        print(qres.errors)


def do_object(client: SuiGQLClient):
    """Fetch specific object data."""
    result = client.execute_query(
        with_query_node=qn.GetObject(
            # object_id="0xf0f919fac17bf50e82f32550290c359553fc3df6267cbeb4e4dbb75195375f4b"
            object_id="0x6"
        )
    )
    print(result.to_json(indent=2))


def do_objects(client: SuiGQLClient):
    """Fetch all objects help by owner."""
    result = client.execute_query(
        with_query_node=qn.GetObjectsOwnedByAddress(
            owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
        )
    )
    print(result.to_json(indent=2))


def do_objects_for(client: SuiGQLClient):
    """Fetch specific objects by their ids."""
    result = client.execute_query(
        with_query_node=qn.GetMultipleObjects(
            object_ids=[
                "0x52da4299641620148676cab1abdb17d6c4de7c0534a9c130a05887a0b8fcb2e2",
                "0x598a5a12cfedbe3ba2a0ce1162345e95ea926c6a7fb29062a152a85fbb29af07",
                "0xf889dd9c5f0f7459a01abf8fead765d4a529c3d492948d7df1ddb480cec83aeb",
            ]
        )
    )
    print(result.to_json(indent=2))


def do_event(client: SuiGQLClient):
    """."""
    result = client.execute_query(
        with_query_node=qn.GetEvents(event_filter={"sender": "0x0"})
    )
    print(result.to_json(indent=2))


def do_configs(client: SuiGQLClient):
    """Fetch the GraphQL, Protocol and System configurations."""
    print(client.rpc_config.to_json(indent=2))


def do_chain_id(client: SuiGQLClient):
    """Fetch the current environment chain_id.

    Demonstrates overriding serialization
    """

    print(client.chain_id)


def do_tx(client: SuiGQLClient):
    """Fetch specific transaction by it's digest."""

    print(
        client.execute_query(
            with_query_node=qn.GetTx(
                digest="CypToNgx6jN2V6vDZGtgpeEv1zSs4VGJcANJi85w9Ypm"
            )
        ).to_json(indent=2)
    )


def do_txs(client: SuiGQLClient):
    """Fetch transactions.

    We loop through 3 pages.
    """
    qres = client.execute_query(with_query_node=qn.GetMultipleTx())
    if qres and not hasattr(qres, "errors"):
        print(qres.to_json(indent=2))
        max_page = 3
        in_page = 0
        while True:
            in_page += 1
            if in_page < max_page and qres.next_cursor:
                qres = client.execute_query(
                    with_query_node=qn.GetMultipleTx(next_page=qres.next_cursor)
                )
                print(qres.to_json(indent=2))
            else:
                break
        print("DONE")
    else:
        print(qres.errors)


def do_staked_sui(client: SuiGQLClient):
    """."""
    owner = (
        # Main net
        "0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
        if client.url == SUI_GRAPHQL_MAINNET
        # Test net
        else "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4"
    )
    result = client.execute_query(with_query_node=qn.GetDelegatedStakes(owner=owner))
    print(result)


def do_latest_cp(client: SuiGQLClient):
    """."""
    qnode = qn.GetLatestCheckpointSequence()
    # print(qnode.query_as_string())
    result = client.execute_query(with_query_node=qnode)
    print(result.to_json(indent=2))


def do_sequence_cp(client: SuiGQLClient):
    """."""
    result = client.execute_query(
        with_query_node=qn.GetCheckpointBySequence(sequence_number=18888268)
    )
    print(result.to_json(indent=2))


def do_digest_cp(client: SuiGQLClient):
    """."""
    result = client.execute_query(
        with_query_node=qn.GetCheckpointByDigest(
            digest="8GonuNB363QrdTNMCx1u7mM73tVgnv7QiheSczktnN1R"
        )
    )
    print(result.to_json(indent=2))


def do_checkpoints(client: SuiGQLClient):
    """."""
    result = client.execute_query(with_query_node=qn.GetCheckpoints())
    print(result.to_json(indent=2))


def do_refgas(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    qres = client.execute_query(with_query_node=qn.GetReferenceGasPrice())
    print(qres.to_json(indent=2))


def do_nameservice(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    qres = client.execute_query(
        with_query_node=qn.GetNameServiceAddress(name="gql-frank")
    )
    print(qres)


def do_protcfg(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    qres = client.execute_query(with_query_node=qn.GetProtocolConfig(version=30))
    print(qres.to_json(indent=2))


if __name__ == "__main__":
    client_init = SuiGQLClient(
        gql_rpc_url=SUI_GRAPHQL_MAINNET,
        write_schema=True,
        config=SuiConfig.default_config(),
    )
    ## QueryNodes (fetch)
    # do_coin_meta(client_init)
    # do_coins_for_type(client_init)
    do_gas(client_init)
    # do_sysstate(client_init)
    # do_all_balances(client_init)
    # do_object(client_init)
    # do_objects(client_init)
    # do_objects_for(client_init)
    # do_event(client_init)
    # do_tx(client_init)
    # do_txs(client_init)
    # do_staked_sui(client_init)
    # do_latest_cp(client_init)
    # do_sequence_cp(client_init)
    # do_digest_cp(client_init)
    # do_checkpoints(client_init)
    # do_refgas(client_init)
    # do_nameservice(client_init)
    # do_protcfg(client_init)
    ## Config
    # do_chain_id(client_init)
    # do_configs(client_init)
    client_init.client.close_sync()
