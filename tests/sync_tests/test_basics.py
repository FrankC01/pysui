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

"""Testing basic client capabilities (no transactions)."""

# pylint:disable=unused-wildcard-import,wildcard-import
from pysui import SyncGqlClient, handle_result
from pysui.sui.sui_types.address import valid_sui_address
import pysui.sui.sui_pgql.pgql_query as qn
from tests.test_utils import gas_not_in


def test_addresses(sui_client: SyncGqlClient) -> None:
    """Addresses and keys should be greater than 0 and same sizes."""
    assert len(sui_client.config.active_group.address_list) > 0
    assert len(sui_client.config.active_group.key_list) > 0
    assert len(sui_client.config.active_group.address_list) == len(
        sui_client.config.active_group.key_list
    )


def test_base_types(sui_client: SyncGqlClient) -> None:
    """General types testing."""
    addy_strs1: list[str] = ["0x0", "0x1", "0x2", "0x3", "0x4", "0x5", "0x6"]
    for addy1 in addy_strs1:
        assert valid_sui_address(addy1)
    addy_strs_var: list[str] = [
        "0xa",
        "0xaa",
        "0xaaa",
        "0xaaaa",
        "0xaaaaa",
        "0xaaaaaa",
        "0xaaaaaaaaaa",
    ]
    for addy1 in addy_strs_var:
        assert valid_sui_address(addy1)
    addy_strs_fail: list[str] = [
        "",
        "0x",
        "zebra",
        "0x0xaaaaaa",
        "0x071351e7d15a3fee972b852ce1adbd4de39ee232ff9c372704bfb8f482bbe234333",
    ]
    for addy1 in addy_strs_fail:
        assert not valid_sui_address(addy1)


def test_gets(sui_client: SyncGqlClient) -> None:
    """Verify get operations."""
    # Coins and gas
    res = sui_client.execute_query_node(
        with_node=qn.GetCoins(owner=sui_client.config.active_address)
    )
    coins = res.result_data.data
    assert len(coins) > 0


#     assert len(coins) == len(gasses)
#     # fresult = sui_client.get_gas_from_faucet()
#     # assert fresult.is_ok()
#     # faucet_gas: list = fresult.result_data.transferred_gas_objects
#     # new_gasses = sui_client.get_gas().result_data.data
#     # all_gas_len = len(coins) + len(faucet_gas)
#     # assert all_gas_len == len(new_gasses)

#     # Objects at this point are all gas
#     # objects = sui_client.get_objects().result_data.data
#     # assert all_gas_len == len(objects)

#     # Get Builders
#     assert sui_client.execute(GetCoinMetaData()).is_ok()
#     assert sui_client.execute(
#         GetAllCoinBalances(owner=sui_client.config.active_address)
#     ).is_ok()
#     assert sui_client.execute((GetLatestSuiSystemState())).is_ok()
#     assert sui_client.execute(GetPackage(package="0x2")).is_ok()
#     assert sui_client.execute(GetModule(package="0x2", module_name="coin")).is_ok()
#     assert sui_client.execute(GetCommittee()).is_ok()
#     assert sui_client.execute(GetTotalTxCount()).is_ok()
#     assert sui_client.execute(
#         GetDelegatedStakes(sui_client.config.active_address)
#     ).is_ok()
#     assert sui_client.execute(GetLatestCheckpointSequence()).is_ok()
#     assert sui_client.execute(GetReferenceGasPrice()).is_ok()

#     # Deeper on checkpoints
#     checkp = sui_client.execute(GetCheckpoints())
#     assert checkp.is_ok()
#     checkp: list[Checkpoint] = checkp.result_data.data
#     assert len(checkp) > 0
#     checki = checkp[0]
#     assert sui_client.execute(GetCheckpointBySequence(checki.sequence_number)).is_ok()
#     assert sui_client.execute(GetCheckpointByDigest(checki.digest)).is_ok()

#     # Deeper Transactions
#     assert len(checki.transactions) > 0
#     txi = sui_client.execute(GetTx(digest=checki.transactions[0]))
#     assert txi.is_ok()
#     txi = txi.result_data
#     assert txi.checkpoint == checki.sequence_number
#     for (
#         k_straint,
#         v_straint,
#     ) in sui_client.protocol.transaction_constraints.to_dict().items():
#         assert v_straint


# def test_object_gets(sui_client: SyncGqlClient) -> None:
#     """Verify object get and options operations."""
#     # Get a gas object
#     faucet_gas = sui_client.get_gas().result_data.data
#     # faucet_gas: list = handle_result(
#     #     sui_client.get_gas_from_faucet()
#     # ).transferred_gas_objects
#     # Pluck one
#     target_gas = faucet_gas[0].object_id
#     options: dict = {
#         "showType": True,
#         "showOwner": True,
#         "showPreviousTransaction": True,
#         "showDisplay": True,
#         "showContent": True,
#         "showBcs": True,
#         "showStorageRebate": True,
#     }

#     entries = [dict([x]) for x in options.items()]
#     for entry in entries:
#         _ = handle_result(
#             sui_client.execute(GetObject(object_id=target_gas, options=entry))
#         )


# def test_txn_gets(sui_client: SyncGqlClient) -> None:
#     """Verify transaction get and options operations."""
#     options = {
#         "showEffects": True,
#         "showEvents": True,
#         "showBalanceChanges": True,
#         "showObjectChanges": True,
#         "showRawInput": True,
#         "showInput": True,
#     }
#     main_coin = gas_not_in(sui_client)
#     target = main_coin.previous_transaction
#     entries = [dict([x]) for x in options.items()]
#     for entry in entries:
#         _ = handle_result(sui_client.execute(GetTx(digest=target, options=entry)))
