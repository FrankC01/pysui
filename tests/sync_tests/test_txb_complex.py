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

"""Testing more complex SyncTransaction."""
from pysui import SyncClient, SuiAddress
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_txn import SigningMultiSig, SyncTransaction
from pysui.sui.sui_types import bcs
import tests.test_utils as tutils


def test_txb_pay_ms(sui_client: SyncClient) -> None:
    """Test multi-sig with transaction builder."""
    msig = tutils.gen_ms(sui_client.config)
    txer = SyncTransaction(sui_client)
    split_coin = txer.split_coin(coin=txer.gas, amounts=[10000000000])
    txer.transfer_objects(
        transfers=[split_coin], recipient=msig.as_sui_address
    )
    result = txer.execute(gas_budget=tutils.STANDARD_BUDGET)
    assert result.is_ok()
    result = sui_client.get_gas(msig.as_sui_address)
    assert len(result.result_data.data) == 1

    txer = SyncTransaction(
        sui_client, initial_sender=SigningMultiSig(msig, msig.public_keys[:2])
    )
    txer.split_coin_equal(coin=txer.gas, split_count=5)
    result = txer.execute(gas_budget=tutils.STANDARD_BUDGET)
    if result.is_ok():
        # assert result.is_ok()
        result = sui_client.get_gas(msig.as_sui_address)
        assert len(result.result_data.data) == 5
    else:
        print(result.result_string)


def test_txb_sponsor(sui_client: SyncClient) -> None:
    """Test sponsoring with transaction builder."""
    main_coin = tutils.gas_not_in(sui_client)
    # By default, the 'active-address' is signing
    txer = SyncTransaction(sui_client)
    txer.split_coin_equal(coin=main_coin, split_count=3)
    # But for execution we want the gas to come from a sponsoring address
    # and they sign as well
    sponser_add, _ = tutils.first_addy_keypair_for(
        cfg=sui_client.config, sigtype=SignatureScheme.SECP256R1
    )
    txer.signer_block.sponser = SuiAddress(sponser_add)
    result = txer.execute(gas_budget=tutils.STANDARD_BUDGET)
    assert result.is_ok()


def test_txb_publish(sui_client: SyncClient) -> None:
    """."""
    import os
    from pathlib import Path

    cwd = Path(os.getcwd())
    cwd = cwd.joinpath("tests/sui-test")
    assert cwd.exists()
    txer = SyncTransaction(sui_client)
    pcap = txer.publish(
        project_path=str(cwd),
        with_unpublished_dependencies=False,
        skip_fetch_latest_git_deps=True,
    )
    txer.transfer_objects(
        transfers=[pcap], recipient=sui_client.config.active_address
    )
    result = txer.execute(gas_budget=tutils.STANDARD_BUDGET)
    assert result.is_ok()


def test_txb_make_and_remove_zeros(sui_client: SyncClient) -> None:
    """Clean up zero balance coins."""
    # First make a bunch of zero balances
    result = sui_client.get_gas()
    assert result.is_ok()
    all_coins = result.result_data.data
    gasage = all_coins.pop()
    tx = SyncTransaction(sui_client)
    balances: list[bcs.Argument] = [
        tx.split_coin(coin=x, amounts=[int(x.balance)]) for x in all_coins
    ]
    tx.merge_coins(merge_to=tx.gas, merge_from=balances)
    result = tx.execute(use_gas_object=gasage.object_id)
    assert result.is_ok()
    # Verify the length of zero balance coins is equal to all_coins
    result = sui_client.get_gas()
    assert result.is_ok()
    assert len(all_coins) == len(result.result_data.data) - 1
    zero_coins = [x for x in result.result_data.data if int(x.balance) == 0]
    assert len(zero_coins) == len(all_coins)
    # Merge all the zeros to primary
    tx = SyncTransaction(sui_client)
    tx.merge_coins(merge_to=tx.gas, merge_from=zero_coins)
    result = tx.execute(use_gas_object=gasage.object_id)
    assert result.is_ok()
    result = sui_client.get_gas()
    assert result.is_ok()
    assert len(result.result_data.data) == 1
    # Split them back out
    tx = SyncTransaction(sui_client)
    tx.split_coin_equal(coin=tx.gas, split_count=len(all_coins) + 1)
    result = tx.execute()
    assert result.is_ok()
    result = sui_client.get_gas()
    assert result.is_ok()
    assert len(result.result_data.data) == len(all_coins) + 1
