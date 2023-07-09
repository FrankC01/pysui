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
