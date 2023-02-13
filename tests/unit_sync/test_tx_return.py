#    Copyright 2022 Frank V. Castellucci
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

"""Transaction result tests."""

from pysui.sui.sui_txresults.package_meta import SuiMovePackage
from pysui.sui.sui_txresults.single_tx import (
    DelegatedStakes,
    FaucetGasRequest,
    ObjectInfo,
    ObjectRead,
    SuiSystemState,
)

from pysui.sui.sui_txresults.complex_tx import EffectsCertTx, EventQueryEnvelope, TxEffectResult, SubscribedTransaction


def test_sui_coin_descriptor(sui_coin_descriptor):
    """Valid result."""
    result = ObjectInfo.factory(sui_coin_descriptor)
    assert result is not None


def test_data_descriptor(data_descriptor):
    """Valid result."""
    result = ObjectInfo.factory(data_descriptor)
    assert result is not None


def test_descriptor_list(sui_coin_descriptor, data_descriptor):
    """Valid result."""
    result = ObjectInfo.factory([sui_coin_descriptor, sui_coin_descriptor, data_descriptor])
    assert result is not None


def test_data_objectread_pass(data_objectread_type):
    """Valid result."""
    result = ObjectRead.factory(data_objectread_type)
    assert result is not None


def test_suigas_objectread_pass(suicoin_objectread_type):
    """Valid result."""
    result = ObjectRead.factory(suicoin_objectread_type)
    balance = result.balance
    print(balance)
    assert result is not None


def test_paysui_result_pass(paysui_result):
    """Valid result."""
    result = TxEffectResult.factory(paysui_result)
    assert result.succeeded is True
    assert result.status == "success"


def test_package_track_result_pass(package_track_result):
    """Valid result."""
    result = SuiMovePackage.ingest_data(package_track_result)
    assert result is not None


def test_package_nest_result_pass(package_nest_result):
    """Valid result."""
    result = SuiMovePackage.ingest_data(package_nest_result)
    assert result is not None


def test_package_sui_result_pass(package_sui_result):
    """Valid result."""
    result = SuiMovePackage.ingest_data(package_sui_result)
    assert result is not None


def test_getevent_result_pass(get_event_result):
    """Valid result."""
    result = EventQueryEnvelope.from_dict(get_event_result)
    assert result is not None


def test_getfaucetgas_pass(get_gas_result):
    """Valid result."""
    result = FaucetGasRequest.from_dict(get_gas_result)
    assert result.error is None


def test_subtx_pass(get_txevent_result):
    """Valid result."""
    result = SubscribedTransaction.from_dict(get_txevent_result)
    assert result.succeeded


def test_get_delegation_stakes_pass(get_delegated_stakes_result):
    """Valid result."""
    result = DelegatedStakes.ingest_data(get_delegated_stakes_result)
    assert result is not None


def test_system_state_pass(get_system_state_result):
    """Valid result."""
    result = SuiSystemState.from_dict(get_system_state_result)
    assert result is not None
