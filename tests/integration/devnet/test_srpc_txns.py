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

"""Synchronous RPC transaction testing."""

import base64
from pathlib import Path
from typing import Union
from pysui.sui import SuiClient, SuiRpcResult
from pysui.sui.sui_builders import MoveCall, Publish
from pysui.sui.sui_utils import build_b64_modules
from pysui.sui.sui_types import ObjectID, SuiAddress, SuiData, MoveDataDescriptor, SuiInteger, SuiString, TxEffectResult

from .test_srpc_gets import get_gas

TRACKER_MODULE: str = "dancer"
TRACKER_SIG: list[str] = ["", TRACKER_MODULE, "", "Tracker"]


def get_data(client: SuiClient, for_address: SuiAddress = None) -> list[SuiData]:
    """get_data Fetch all data objects for address.

    :param client: Synchronous http client
    :type client: SuiClient
    :param for_address: Address to get objects for, defaults to None and uses active-address
    :type for_address: SuiAddress, optional
    :return: List of data objects owned by address, maybe empty
    :rtype: list[SuiData]
    """
    result: SuiRpcResult = client.get_address_object_descriptors(MoveDataDescriptor, for_address)
    assert result.is_ok()
    ident_list = [desc.identifier for desc in result.result_data]
    result: SuiRpcResult = client.get_objects_for(ident_list)
    assert result.is_ok()
    return result.result_data


def get_tracker(client: SuiClient, for_address: SuiAddress = None) -> Union[SuiData, None]:
    """get_service_tracker Get data object specific to SuiTracker for active-address.

    :param client: Synchronous http client
    :type client: SuiClient
    :param for_address: Address to get objects for, defaults to None and uses active-address
    :type for_address: SuiAddress, optional
    :return: The SuiTracker data object or None if does not exist.
    :rtype: Union[SuiData],None]
    """
    data_objects: list[SuiData] = get_data(client, for_address)
    if data_objects:
        for data_obj in data_objects:
            type_sig = data_obj.type_signature.split(":")[1:]
            if type_sig == TRACKER_SIG:
                return data_obj
    return None


# Publish


def test_setup_chainmodule_pass(sui_client: SuiClient, sui_test_move_path: Path):
    """test_get_data_activeaddress_pass Test for any data objects owned by active-address.

    There may or may not be objects based on state when tests start
    :param sui_client: Synchronous http client
    :type sui_client: SuiClient
    :return: None
    :rtype: NoneType
    """
    tracker = get_tracker(sui_client)
    if tracker:
        assert tracker.data.has_public_transfer
        return
    modules = build_b64_modules(sui_test_move_path)
    assert modules
    gases = get_gas(sui_client)[0]
    assert gases
    builder = Publish(
        sender=sui_client.config.active_address,
        compiled_modules=modules,
        gas=gases.identifier,
        gas_budget=SuiInteger(3000),
    )
    assert builder
    result = sui_client.execute(builder)
    assert result.is_ok()
    txresult: TxEffectResult = result.result_data
    assert txresult.succeeded
    tracker = get_tracker(sui_client)
    assert tracker
    assert tracker.data.has_public_transfer


# Move Call


def test_move_call_single_arg_pass(sui_client: SuiClient):
    """test_move_call Test move call.

    :param sui_client: _description_
    :type sui_client: Synchronous http client
    """
    tracker = get_tracker(sui_client)
    assert tracker
    gases = get_gas(sui_client)[0]
    assert gases
    builder = MoveCall(
        signer=sui_client.config.active_address,
        package_object_id=ObjectID(tracker.type_signature.split(":")[0]),
        module=SuiString(TRACKER_MODULE),
        function=SuiString("add_value"),
        type_arguments=[],
        arguments=[tracker.identifier, SuiString("5")],
        gas_object=gases.identifier,
        gas_budget=SuiInteger(1000),
    )
    assert builder
    result = sui_client.execute(builder)
    assert result.is_ok()
    txresult: TxEffectResult = result.result_data
    assert txresult.succeeded
    tracker = get_tracker(sui_client)
    assert tracker
    assert len(tracker.data.fields["accumulator"]) > 0
    myres = [int(x) for x in list(base64.b64decode(tracker.data.fields["accumulator"]))]
    assert 5 in myres
    builder = MoveCall(
        signer=sui_client.config.active_address,
        package_object_id=ObjectID(tracker.type_signature.split(":")[0]),
        module=SuiString(TRACKER_MODULE),
        function=SuiString("remove_value"),
        type_arguments=[],
        arguments=[tracker.identifier, SuiString("5")],
        gas_object=gases.identifier,
        gas_budget=SuiInteger(1000),
    )
    assert builder
    result = sui_client.execute(builder)
    assert result.is_ok()
    txresult: TxEffectResult = result.result_data
    assert txresult.succeeded
    tracker = get_tracker(sui_client)
    assert tracker
    myres = [int(x) for x in list(base64.b64decode(tracker.data.fields["accumulator"]))]
    assert 5 not in myres


def test_transfer_tracker_pass(sui_client: SuiClient):
    """Test."""
    # Ensure active-address has a tracker
    tracker = get_tracker(sui_client)
    assert tracker
    # Ensure active-address has gas
    gases = get_gas(sui_client)[0]
    assert gases
    active_address = sui_client.config.active_address.address
    addresses = set(sui_client.config.addresses)
    # addresses.remove(active_address)
    assert addresses
    child_gases = child_address = None
    # Get address other than the active one
    for address in addresses:
        if address != active_address:
            child_address = SuiAddress(address)
            child_gases = get_gas(sui_client, child_address)
            if child_gases:
                child_gases = child_gases[0]
                break
    assert child_address
    assert child_gases
    # Transfer the tracker from active-address to some other address
    result = sui_client.transfer_object_txn(
        signer=sui_client.config.active_address,
        object_id=tracker.identifier,
        gas=gases.identifier,
        gas_budget=SuiInteger(1000),
        recipient=child_address,
    )
    assert result.is_ok()
    # Ensure child-address has the tracker back
    tracker = get_tracker(sui_client, child_address)
    assert tracker
    # Transfer the tracker back to active-address from some other address
    result = sui_client.transfer_object_txn(
        signer=child_address,
        object_id=tracker.identifier,
        gas=child_gases.identifier,
        gas_budget=SuiInteger(1000),
        recipient=sui_client.config.active_address,
    )
    assert result.is_ok()
    # Ensure active-address has the tracker back
    tracker = get_tracker(sui_client)
    assert tracker
