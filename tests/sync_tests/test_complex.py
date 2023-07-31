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

"""Testing more complex client capabilities (no transactions)."""

from pysui import SyncClient, SuiAddress, ObjectID, handle_result
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_txn import SyncTransaction
from tests.test_utils import (
    first_addy_keypair_for,
    gas_not_in,
    STANDARD_BUDGET,
)


def test_split_equal(sui_client: SyncClient) -> None:
    """Simple split coin and verify count.

    Also excercises signing.
    """
    # Get first ed25519 address
    address, _ = first_addy_keypair_for(
        cfg=sui_client.config, sigtype=SignatureScheme.ED25519
    )
    main_coin = gas_not_in(sui_client, address)
    not_ins = [main_coin.coin_object_id]
    gas_coin = gas_not_in(sui_client, address, not_ins)

    # Get total gas for client
    first_g = sui_client.get_gas(address)
    assert first_g.is_ok()
    gasses = first_g.result_data.data
    pre_split_len = len(gasses)
    txn = SyncTransaction(sui_client, initial_sender=SuiAddress(address))
    txn.split_coin_equal(coin=main_coin, split_count=2)
    t_run = txn.execute(use_gas_object=gas_coin.object_id)
    assert t_run.is_ok()
    next_g = sui_client.get_gas(address)
    assert next_g.is_ok()
    new_gasses = next_g.result_data.data
    assert len(new_gasses) == pre_split_len + 1


def test_pay_all_keys(sui_client: SyncClient) -> None:
    """Primarily tests all key type signing round robit as well as Pay API."""
    ed_addy, _ = first_addy_keypair_for(
        cfg=sui_client.config, sigtype=SignatureScheme.ED25519
    )
    k1_addy, _ = first_addy_keypair_for(
        cfg=sui_client.config, sigtype=SignatureScheme.SECP256K1
    )
    r1_addy, _ = first_addy_keypair_for(
        cfg=sui_client.config, sigtype=SignatureScheme.SECP256R1
    )

    main_coin = gas_not_in(sui_client, ed_addy)
    mc_id = ObjectID(main_coin.coin_object_id)
    txn = SyncTransaction(sui_client, initial_sender=SuiAddress(ed_addy))
    txn.transfer_objects(transfers=[main_coin], recipient=SuiAddress(k1_addy))
    t_run = txn.execute()
    assert t_run.is_ok()

    data = handle_result(sui_client.get_object(mc_id))
    assert data.owner.address_owner == k1_addy

    main_coin = gas_not_in(sui_client, k1_addy)
    mc_id = ObjectID(main_coin.coin_object_id)
    txn = SyncTransaction(sui_client, initial_sender=SuiAddress(k1_addy))
    txn.transfer_objects(transfers=[main_coin], recipient=SuiAddress(r1_addy))
    t_run = txn.execute()
    assert t_run.is_ok()

    data = handle_result(sui_client.get_object(mc_id))
    assert data.owner.address_owner == r1_addy

    main_coin = gas_not_in(sui_client, r1_addy)
    mc_id = ObjectID(main_coin.coin_object_id)

    txn = SyncTransaction(sui_client, initial_sender=SuiAddress(r1_addy))
    txn.transfer_objects(transfers=[main_coin], recipient=SuiAddress(ed_addy))
    t_run = txn.execute()
    assert t_run.is_ok()

    data = handle_result(sui_client.get_object(mc_id))
    assert data.owner.address_owner == ed_addy
