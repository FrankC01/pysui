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

"""Sample module for pysui beta Transaction Builder leveraging Sui GraphQL."""

import base64
from pysui import SuiConfig
from pysui.sui.sui_clients.common import SuiRpcResult
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pgql_type
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction
from pysui.sui.sui_txresults.complex_tx import TxInspectionResult


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


def transaction_inspect(txb: SuiTransaction):
    """Uses defaults for DryRunTransaction and just the TransactionKind"""
    raw_kind = txb.raw_kind()
    # Print the TransactionType BCS (pre-serialized) structure
    print(raw_kind.to_json(indent=2))
    # Execute the dry run
    handle_result(
        txb.client.execute_query(
            with_query_node=qn.DryRunTransactionKind(
                tx_bytestr=base64.b64encode(raw_kind.serialize()).decode()
            )
        )
    )


def transaction_dryrun(txb: SuiTransaction):
    """Uses fully built TransactionData for DryRunTransaction"""
    raw_kind = txb.transaction_data()
    # Print the TransactionData BCS (pre-serialized) structure
    print(raw_kind.to_json(indent=2))
    # Execute the dry run
    handle_result(
        txb.client.execute_query(
            with_query_node=qn.DryRunTransaction(
                tx_bytestr=base64.b64encode(raw_kind.serialize()).decode()
            )
        )
    )


def transaction_dryrun_with_gas(txb: SuiTransaction, coin_ids: list[str]):
    """Uses fully built TransactionData for DryRunTransaction"""
    raw_kind = txb.transaction_data(use_gas_objects=coin_ids)
    # Print the TransactionData BCS (pre-serialized) structure
    print(raw_kind.to_json(indent=2))
    # Execute the dry run
    handle_result(
        txb.client.execute_query(
            with_query_node=qn.DryRunTransaction(
                tx_bytestr=base64.b64encode(raw_kind.serialize()).decode()
            )
        )
    )


def transaction_execute(txb: SuiTransaction):
    """Uses fully built and serialized TransactionData for ExecuteTransaction."""
    tx_b64 = txb.build()
    # Still returns legacy SuiSignature array
    sig_array = txb.signer_block.get_signatures(
        config=txb.client.config, tx_bytes=tx_b64
    )
    # Execute the transaction
    handle_result(
        txb.client.execute_query(
            with_query_node=qn.ExecuteTransaction(
                tx_bytestr=tx_b64, sig_array=[x.value for x in sig_array]
            )
        )
    )


def demo_tx_split(client: SuiGQLClient):
    """Demonstrate GraphQL Beta PTB with split and transfer."""
    txb = SuiTransaction(client=client)
    scoin = txb.split_coin(
        coin=txb.gas,
        amounts=[100000000],
    )
    txb.transfer_objects(
        transfers=[scoin], recipient=client.config.active_address.address
    )
    #### Uncomment the action to take
    # transaction_inspect(txb)
    transaction_dryrun(txb)
    # transaction_dryrun_with_gas(
    #     txb,
    #     [
    #         "<ENTER ONE OR MORE COIN IDS TO PAY",
    #     ],
    # )
    # transaction_execute(txb)


def demo_tx_unstake(client: SuiGQLClient):
    """Demonstrate GraphQL Beta PTB with unstaking 1 coin if found."""
    owner = client.config.active_address.address

    skblk: pgql_type.SuiStakedCoinsGQL = handle_result(
        client.execute_query(with_query_node=qn.GetDelegatedStakes(owner=owner))
    )
    # Only execute if staked coin found
    if skblk.staked_coins:
        txb = SuiTransaction(client=client)
        txb.unstake_coin(staked_coin=skblk.staked_coins[0])
        # transaction_inspect(txb)
        transaction_dryrun(txb)
        # transaction_dryrun_with_gas(
        #     txb,
        #     [
        #         "<ENTER ONE OR MORE COIN IDS TO PAY",
        #     ],
        # )
        # transaction_execute(txb)
    else:
        print("No staked coins found")


def demo_tx_transfer_sui(client: SuiGQLClient):
    """Demonstrate GraphQL Beta PTB with transferring sui."""
    txb = SuiTransaction(client=client)
    txb.transfer_sui(
        recipient="<ENTER RECIPIENT ADDRESS STRING>",
        from_coin=txb.gas,
        amount=100000000,
    )
    transaction_inspect(txb)
    # transaction_dryrun(txb)
    # transaction_dryrun_with_gas(
    #     txb,
    #     [
    #         "<ENTER ONE OR MORE COIN IDS TO PAY",
    #     ],
    # )
    # transaction_execute(txb)


if __name__ == "__main__":
    client_init = SuiGQLClient(
        write_schema=False,
        config=SuiConfig.default_config(),
    )
    print(f"Schema version {client_init.schema_version}")
    demo_tx_split(client_init)
    # demo_tx_unstake(client_init)
    # demo_tx_transfer_sui(client_init)
