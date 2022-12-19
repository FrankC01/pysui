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
from pysui.sui import SuiClient
from pysui.sui.sui_builders import (
    BatchTransaction,
    GetTxAuthSignatures,
    MoveCallRequestParams,
    Publish,
    TransferObjectParams,
    MoveCall,
)
from pysui.sui.sui_utils import build_b64_modules
from pysui.sui.sui_types import (
    ObjectID,
    SuiAddress,
    SuiArray,
    SuiData,
    SuiInteger,
    SuiString,
    SuiTransactionDigest,
    TxEffectResult,
)

from .test_srpc_gets import get_gas, get_data

TRACKER_MODULE: str = "dancer"
TRACKER_SIG: list[str] = ["", TRACKER_MODULE, "", "Tracker"]


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


def get_address_not_active(client: SuiClient, all_unique: bool = False) -> Union[SuiAddress, list[SuiAddress], None]:
    """get_address_not_active Get one or more addresses that are not the active address.

    :param client: Synchronous http client
    :type client: SuiClient
    :param all_unique: If True, returns all non-active addresses otherwise just the first, defaults to False
    :type all_unique: bool, optional
    :return: Either a single unique address or the list of addresses that are not-active or None if none exist
    :rtype: Union[SuiAddress, list[SuiAddress],None]
    """
    # Get a non-active set of addresses
    active_address = client.config.active_address.address
    addresses = set(client.config.addresses)
    addresses.remove(active_address)
    if addresses:
        if all_unique:
            return [SuiAddress(x) for x in addresses]
        return SuiAddress(list(addresses)[0])
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
    result = sui_client.move_call_txn(
        signer=sui_client.config.active_address,
        package_object_id=ObjectID(tracker.type_signature.split(":")[0]),
        module=SuiString(TRACKER_MODULE),
        function=SuiString("add_value"),
        type_arguments=[],
        arguments=[tracker.identifier, SuiString("5")],
        gas=gases.identifier,
        gas_budget=SuiInteger(1000),
    )
    assert result.is_ok()
    txresult: TxEffectResult = result.result_data
    assert txresult.succeeded
    tracker = get_tracker(sui_client)
    assert tracker
    assert len(tracker.data.fields["accumulator"]) > 0
    assert 5 in tracker.data.fields["accumulator"]
    result = sui_client.move_call_txn(
        signer=sui_client.config.active_address,
        package_object_id=ObjectID(tracker.type_signature.split(":")[0]),
        module=SuiString(TRACKER_MODULE),
        function=SuiString("remove_value"),
        type_arguments=[],
        arguments=[tracker.identifier, SuiString("5")],
        gas=gases.identifier,
        gas_budget=SuiInteger(1000),
    )
    assert result.is_ok()
    txresult: TxEffectResult = result.result_data
    assert txresult.succeeded
    tracker = get_tracker(sui_client)
    assert tracker


def test_transfer_tracker_pass(sui_client: SuiClient):
    """Test."""
    # Ensure active-address has a tracker
    tracker = get_tracker(sui_client)
    assert tracker
    # Ensure active-address has gas
    gases = get_gas(sui_client)[0]
    assert gases
    child_address = get_address_not_active(sui_client)
    assert child_address
    child_gases = get_gas(sui_client, child_address)[0]
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


def test_transfer_gas_pass(sui_client: SuiClient):
    """Test."""
    # Ensure active-address has gas
    active_gases = get_gas(sui_client)
    assert active_gases
    assert len(active_gases) > 1
    active_gas = active_gases[0]
    unique_gas_id = active_gas.identifier
    other_address = get_address_not_active(sui_client)
    assert other_address
    assert isinstance(other_address, SuiAddress)
    # Send it to another address
    result = sui_client.pay_allsui_txn(
        signer=sui_client.config.active_address,
        input_coins=SuiArray([unique_gas_id]),
        recipient=other_address,
        gas_budget=SuiInteger(1000),
    )
    assert result.is_ok()
    # Find it in our recipient's list of gas
    other_gasses = get_gas(sui_client, other_address)
    filtered = list(filter(lambda x: x.identifier == unique_gas_id, other_gasses))
    assert filtered
    assert len(filtered) == 1
    assert filtered[0].identifier == unique_gas_id
    # Send it back
    result = sui_client.pay_allsui_txn(
        signer=other_address,
        input_coins=SuiArray([unique_gas_id]),
        recipient=sui_client.config.active_address,
        gas_budget=SuiInteger(1000),
    )
    assert result.is_ok()
    active_gases = get_gas(sui_client)
    filtered = list(filter(lambda x: x.identifier == unique_gas_id, active_gases))
    assert filtered
    assert len(filtered) == 1
    assert filtered[0].identifier == unique_gas_id


def test_batch_transaction_transfer_pass(sui_client: SuiClient):
    """Test batch transaction with transfer."""
    active_gases = get_gas(sui_client)
    assert len(active_gases) > 1
    transfer_gas_object = active_gases[0]
    batch_gas_object = active_gases[1]
    other_address = get_address_not_active(sui_client)
    assert other_address
    assert isinstance(other_address, SuiAddress)
    transfer_params = SuiArray([TransferObjectParams(receiver=other_address, transfer_object=transfer_gas_object)])
    builder = BatchTransaction(
        sui_client.config.active_address, transfer_params, batch_gas_object.identifier, SuiInteger(3000)
    )
    result = sui_client.execute(builder)
    assert result.is_ok()


def test_batch_transaction_movecall_pass(sui_client: SuiClient):
    """Test batch transaction with movecall."""
    active_gases = get_gas(sui_client)
    assert len(active_gases) > 1
    tracker = get_tracker(sui_client)
    assert tracker
    package_id = tracker.type_signature.split(":")[0]
    batch_gas_object = active_gases[0]
    move_params = SuiArray(
        [
            MoveCallRequestParams(
                package_object=ObjectID(package_id),
                module_str=SuiString(TRACKER_MODULE),
                function_str=SuiString("add_value"),
                type_arguments=SuiArray([]),
                arguments=SuiArray([tracker.identifier, SuiString("6")]),
            ),
        ]
    )
    builder = BatchTransaction(
        sui_client.config.active_address, move_params, batch_gas_object.identifier, SuiInteger(3000)
    )
    result = sui_client.execute(builder)
    assert result.is_ok()
    tracker_out = get_tracker(sui_client)
    assert tracker_out
    move_params = SuiArray(
        [
            MoveCallRequestParams(
                package_object=ObjectID(package_id),
                module_str=SuiString(TRACKER_MODULE),
                function_str=SuiString("remove_value"),
                type_arguments=SuiArray([]),
                arguments=SuiArray([tracker.identifier, SuiString("6")]),
            ),
        ]
    )
    builder = BatchTransaction(
        sui_client.config.active_address, move_params, batch_gas_object.identifier, SuiInteger(3000)
    )
    result = sui_client.execute(builder)
    assert result.is_ok()
    tracker_out = get_tracker(sui_client)
    assert tracker_out


def test_dryrun_pass(sui_client: SuiClient):
    """0.4.0: Test of new rpc execution type: dry_run."""
    active_gases = get_gas(sui_client)
    assert len(active_gases) > 1
    batch_gas_object = active_gases[0]
    tracker = get_tracker(sui_client)
    assert tracker
    package_id = tracker.type_signature.split(":")[0]
    builder = MoveCall(
        signer=sui_client.config.active_address,
        package_object_id=ObjectID(package_id),
        module=SuiString(TRACKER_MODULE),
        function=SuiString("add_value"),
        type_arguments=SuiArray([]),
        arguments=SuiArray([tracker.identifier, SuiString("8")]),
        gas=batch_gas_object.identifier,
        gas_budget=SuiInteger(1000),
    )
    result = sui_client.dry_run(builder)
    assert result.is_ok()


def test_defer_execution_pass(sui_client: SuiClient):
    """0.4.0: Test of new rpc execution types: execute_no_sign and sign_and_submit and GetTxAuthSignatures."""
    active_gases = get_gas(sui_client)
    assert len(active_gases) > 1
    batch_gas_object = active_gases[0]
    tracker = get_tracker(sui_client)
    assert tracker
    package_id = tracker.type_signature.split(":")[0]
    builder = MoveCall(
        signer=sui_client.config.active_address,
        package_object_id=ObjectID(package_id),
        module=SuiString(TRACKER_MODULE),
        function=SuiString("add_value"),
        type_arguments=SuiArray([]),
        arguments=SuiArray([tracker.identifier, SuiString("8")]),
        gas=batch_gas_object.identifier,
        gas_budget=SuiInteger(1000),
    )
    result = sui_client.execute_no_sign(builder)
    assert result.is_ok()
    signer, tx_bytes = result.result_data
    result = sui_client.sign_and_submit(signer, tx_bytes)
    assert result.is_ok()
    builder = GetTxAuthSignatures(
        txn_digest=SuiTransactionDigest(result.result_data.effects_cert.certificate.transaction_digest)
    )
    result = sui_client.execute(builder)
    assert result.is_ok()
