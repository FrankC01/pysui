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

from pysui import SuiConfig, SuiRpcResult
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
import pysui.sui.sui_pgql.pgql_query as qn


def handle_result(result: SuiRpcResult) -> SuiRpcResult:
    """."""
    if result.is_ok():
        if hasattr(result.result_data, "to_json"):
            print(result.result_data.to_json(indent=2))
        else:
            print(result.result_data)
    else:
        print(result.result_string)
        print(result.result_data.to_json(indent=2))
    return result


def do_coin_meta(client: SuiGQLClient):
    """Fetch meta data about coins, includes supply."""
    # Defaults to 0x2::sui::SUI
    handle_result(client.execute_query(with_query_node=qn.GetCoinMetaData()))
    # Check stakes as well
    handle_result(
        client.execute_query(
            with_query_node=qn.GetCoinMetaData(
                coin_type="0x3::staking_pool::StakedSui",
            )
        )
    )


def do_coins_for_type(client: SuiGQLClient):
    """Fetch coins of specific type for owner."""
    handle_result(
        client.execute_query(
            # GetAllCoinsOfType requires a coin type
            with_query_node=qn.GetCoins(
                owner=client.config.active_address.address,
                coin_type="0x2::sui::SUI",
            )
        )
    )


def do_gas(client: SuiGQLClient):
    """Fetch 0x2::sui::SUI (default) for owner."""
    result = handle_result(
        client.execute_query(
            # GetAllCoins defaults to "0x2::sui::SUI"
            with_query_node=qn.GetCoins(
                owner="0x00878369f475a454939af7b84cdd981515b1329f159a1aeb9bf0f8899e00083a"
            )
        )
    )
    if result.is_ok():
        print(
            f"Total coins in page: {len(result.result_data.data)} has more: {result.result_data.next_cursor.hasNextPage}"
        )


def do_sysstate(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query(with_query_node=qn.GetLatestSuiSystemState()))


def do_all_balances(client: SuiGQLClient):
    """Fetch all coin types for active address and total balances.

    Demonstrates paging as well
    """
    result = client.execute_query(
        with_query_node=qn.GetAllCoinBalances(
            owner=client.config.active_address.address
        )
    )
    handle_result(result)
    if result.is_ok():
        while result.result_data.next_cursor.hasNextPage:
            result = client.execute_query(
                with_query_node=qn.GetAllCoinBalances(
                    owner=client.config.active_address.address,
                    next_page=result.next_cursor,
                )
            )
            handle_result(result)
        print("DONE")


def do_object(client: SuiGQLClient):
    """Fetch specific object data."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetObject(
                # object_id="0xf0f919fac17bf50e82f32550290c359553fc3df6267cbeb4e4dbb75195375f4b"
                object_id="0x0847e1e02965e3f6a8b237152877a829755fd2f7cfb7da5a859f203a8d4316f0"
            )
        )
    )


def do_objects(client: SuiGQLClient):
    """Fetch all objects help by owner."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetObjectsOwnedByAddress(
                owner=client.config.active_address.address
            )
        )
    )


def do_objects_for(client: SuiGQLClient):
    """Fetch specific objects by their ids."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetMultipleObjects(
                object_ids=[
                    "0x0847e1e02965e3f6a8b237152877a829755fd2f7cfb7da5a859f203a8d4316f0",
                    "0x68e961e3af906b160e1ff21137304537fa6b31f5a4591ef3acf9664eb6e3cd2b",
                    "0x77851d73e7c1227c048fc7cbf21ff9053faa872950dd33f5d0cb5b40a79d9d99",
                ]
            )
        )
    )


def do_event(client: SuiGQLClient):
    """."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetEvents(event_filter={"sender": "0x0"})
        )
    )


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

    handle_result(
        client.execute_query(
            with_query_node=qn.GetTx(
                digest="A8kCT1n8dmCWchz5WnKPsQ8x7U49ExgMEWJ13nRULpiz"
            )
        )
    )


def do_txs(client: SuiGQLClient):
    """Fetch transactions.

    We loop through 3 pages.
    """
    result = client.execute_query(with_query_node=qn.GetMultipleTx())
    handle_result(result)
    if result.is_ok():
        max_page = 3
        in_page = 0
        while True:
            in_page += 1
            if in_page < max_page and result.result_data.next_cursor:
                result = client.execute_query(
                    with_query_node=qn.GetMultipleTx(
                        next_page=result.result_data.next_cursor
                    )
                )
                handle_result(result)
            else:
                break
        print("DONE")


def do_staked_sui(client: SuiGQLClient):
    """."""
    owner = client.config.active_address.address

    handle_result(
        client.execute_query(with_query_node=qn.GetDelegatedStakes(owner=owner))
    )


def do_latest_cp(client: SuiGQLClient):
    """."""
    qnode = qn.GetLatestCheckpointSequence()
    # print(qnode.query_as_string())
    handle_result(client.execute_query(with_query_node=qnode))


def do_sequence_cp(client: SuiGQLClient):
    """."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetCheckpointBySequence(sequence_number=18888268)
        )
    )


def do_digest_cp(client: SuiGQLClient):
    """."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetCheckpointByDigest(
                digest="EPVQ81Mpucuuf9CQ7aD2jcATZthSZJVqQ7Fh7hQSsMKF"
            )
        )
    )


def do_checkpoints(client: SuiGQLClient):
    """."""
    handle_result(client.execute_query(with_query_node=qn.GetCheckpoints()))


def do_refgas(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query(with_query_node=qn.GetReferenceGasPrice()))


def do_nameservice(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query(with_query_node=qn.GetNameServiceAddress(name="gql-frank"))
    )


def do_owned_nameservice(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query(
            with_query_node=qn.GetNameServiceNames(
                owner=client.config.active_address.address
            )
        )
    )


def do_validators_apy(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(client.execute_query(with_query_node=qn.GetValidatorsApy()))


def do_protcfg(client: SuiGQLClient):
    """Fetch the most current system state summary."""
    handle_result(
        client.execute_query(with_query_node=qn.GetProtocolConfig(version=30))
    )


if __name__ == "__main__":
    client_init = SuiGQLClient(
        write_schema=False,
        config=SuiConfig.default_config(),
    )
    ## QueryNodes (fetch)
    # do_coin_meta(client_init)
    # do_coins_for_type(client_init)
    # do_gas(client_init)
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
    # do_nameservice(client_init)
    # do_owned_nameservice(client_init)
    do_validators_apy(client_init)
    # do_refgas(client_init)
    ## Config
    # do_chain_id(client_init)
    # do_configs(client_init)
    # do_protcfg(client_init)
    client_init.client.close_sync()
