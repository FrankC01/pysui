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
from pysui.sui.sui_builders.get_builders import *
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_txresults.complex_tx import Checkpoint
from pysui.sui.sui_types.scalars import SuiString


def test_addresses(sui_client: SuiClient) -> None:
    """Addresses and keys should be greater than 0 and same sizes."""
    assert len(sui_client.config.addresses) > 0
    assert len(sui_client.config.keystrings) > 0
    assert len(sui_client.config.addresses) == len(sui_client.config.keystrings)


def test_base_info(sui_client: SuiClient) -> None:
    """General information all clients carry."""
    assert sui_client.current_gas_price > 0
    assert sui_client.is_synchronous is True
    assert len(sui_client.rpc_api_names) > 0
    assert sui_client.rpc_version
    assert sui_client.api_exists("suix_getLatestSuiSystemState")


def test_gets(sui_client: SuiClient) -> None:
    """Verify get operations."""
    # Coins and gas
    coins = sui_client.get_coin(SuiString("0x2::sui::SUI")).result_data.data
    assert len(coins) > 0
    gasses = sui_client.get_gas().result_data.data
    assert len(coins) == len(gasses)
    fresult = sui_client.get_gas_from_faucet()
    assert fresult.is_ok()
    faucet_gas: list = fresult.result_data.transferred_gas_objects
    new_gasses = sui_client.get_gas().result_data.data
    all_gas_len = len(coins) + len(faucet_gas)
    assert all_gas_len == len(new_gasses)

    # Objects at this point are all gas
    objects = sui_client.get_objects().result_data.data
    assert all_gas_len == len(objects)

    # Get Builders
    assert sui_client.execute(GetCoinMetaData()).is_ok()
    assert sui_client.execute(GetAllCoinBalances(owner=sui_client.config.active_address)).is_ok()
    assert sui_client.execute((GetLatestSuiSystemState())).is_ok()
    assert sui_client.execute(GetPackage(package="0x2")).is_ok()
    assert sui_client.execute(GetModule(package="0x2", module_name="coin")).is_ok()
    assert sui_client.execute(GetCommittee()).is_ok()
    assert sui_client.execute(GetTotalTxCount()).is_ok()
    assert sui_client.execute(GetDelegatedStakes(sui_client.config.active_address)).is_ok()
    assert sui_client.execute(GetLatestCheckpointSequence()).is_ok()
    assert sui_client.execute(GetReferenceGasPrice()).is_ok()

    # Deeper on checkpoints
    checkp = sui_client.execute(GetCheckpoints())
    assert checkp.is_ok()
    checkp: list[Checkpoint] = checkp.result_data.data
    assert len(checkp) > 0
    checki = checkp[0]
    assert sui_client.execute(GetCheckpointBySequence(checki.sequence_number)).is_ok()
    assert sui_client.execute(GetCheckpointByDigest(checki.digest)).is_ok()

    # Deeper Transactions
    assert len(checki.transactions) > 0
    txi = sui_client.execute(GetTx(digest=checki.transactions[0]))
    assert txi.is_ok()
    txi = txi.result_data
    assert txi.checkpoint == checki.sequence_number
