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

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_clients.common import handle_result
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_builders.exec_builders import PayAllSui, SplitCoinEqually
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import ObjectID
from tests.test_utils import first_addy_keypair_for, gas_not_in, STANDARD_BUDGET


def test_split_equal(sui_client: SuiClient) -> None:
    """Simple split coin and verify count.

    Also excercises signing.
    """
    # Get first ed25519 address
    address, _ = first_addy_keypair_for(cfg=sui_client.config, sigtype=SignatureScheme.ED25519)
    main_coin = gas_not_in(sui_client, address)
    not_ins = [main_coin.coin_object_id]
    gas_coin = gas_not_in(sui_client, address, not_ins)

    # Get total gas for client
    first_g = sui_client.get_gas(address)
    assert first_g.is_ok()
    gasses = first_g.result_data.data
    pre_split_len = len(gasses)
    tfr_builder = SplitCoinEqually(
        signer=address,
        coin_object_id=main_coin.coin_object_id,
        split_count="2",
        gas=gas_coin.coin_object_id,
        gas_budget=STANDARD_BUDGET,
    )
    t_run = sui_client.execute(tfr_builder)
    assert t_run.is_ok()
    next_g = sui_client.get_gas(address)
    assert next_g.is_ok()
    new_gasses = next_g.result_data.data
    assert len(new_gasses) == pre_split_len + 1


def test_pay_all_keys(sui_client: SuiClient) -> None:
    """Primarily tests all key type signing round robit as well as Pay API."""
    ed_addy, _ = first_addy_keypair_for(cfg=sui_client.config, sigtype=SignatureScheme.ED25519)
    k1_addy, _ = first_addy_keypair_for(cfg=sui_client.config, sigtype=SignatureScheme.SECP256K1)
    r1_addy, _ = first_addy_keypair_for(cfg=sui_client.config, sigtype=SignatureScheme.SECP256R1)

    main_coin = gas_not_in(sui_client, ed_addy)
    mc_id = ObjectID(main_coin.coin_object_id)
    tfr_builder = PayAllSui(
        signer=ed_addy,
        input_coins=[mc_id],
        recipient=k1_addy,
        gas_budget=STANDARD_BUDGET,
    )
    assert sui_client.execute(tfr_builder).is_ok()
    data = handle_result(sui_client.get_object(mc_id))
    assert data.owner.address_owner == k1_addy

    main_coin = gas_not_in(sui_client, k1_addy)
    mc_id = ObjectID(main_coin.coin_object_id)

    tfr_builder = PayAllSui(
        signer=k1_addy,
        input_coins=[mc_id],
        recipient=r1_addy,
        gas_budget=STANDARD_BUDGET,
    )
    assert sui_client.execute(tfr_builder).is_ok()
    data = handle_result(sui_client.get_object(mc_id))
    assert data.owner.address_owner == r1_addy

    main_coin = gas_not_in(sui_client, r1_addy)
    mc_id = ObjectID(main_coin.coin_object_id)

    tfr_builder = PayAllSui(
        signer=r1_addy,
        input_coins=[mc_id],
        recipient=ed_addy,
        gas_budget=STANDARD_BUDGET,
    )
    assert sui_client.execute(tfr_builder).is_ok()
    data = handle_result(sui_client.get_object(mc_id))
    assert data.owner.address_owner == ed_addy
