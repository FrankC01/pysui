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

"""Synchronous RPC testing."""


from pysui.sui import SuiClient, SuiRpcResult
from pysui.sui.sui_builders import GetCommittee
from pysui.sui.sui_types import SuiGasDescriptor, SuiAddress, SuiGas


def get_gas(client: SuiClient, for_address: SuiAddress = None) -> list[SuiGas]:
    """get_gas Utility func to refresh gas for address.

    :param client: _description_
    :type client: SuiClient
    :return: _description_
    :rtype: list[SuiGas]
    """
    result: SuiRpcResult = client.get_address_object_descriptors(SuiGasDescriptor, for_address)
    assert result.is_ok()
    ident_list = [desc.identifier for desc in result.result_data]
    result: SuiRpcResult = client.get_objects_for(ident_list)
    assert result.is_ok()
    return result.result_data


def test_get_gas_activeaddress_pass(sui_client: SuiClient):
    """test_get_gasobjects_pass Fetch gas objects.

    Tests filtered descriptor fetch and convenience sui_getObject
    :param sui_client: Synchronous http client
    :type sui_client: SuiClient
    """
    gas_objects = get_gas(sui_client)
    assert len(gas_objects) > 3
    gas_balances = [gas.balance for gas in gas_objects]
    total_balance = sum(gas_balances)
    assert total_balance > 0


def test_get_gas_anyaddress_pass(sui_client: SuiClient):
    """test_get_gas_anyaddress_pass Check any other address has gas.

    :param sui_client: Synchronous http client
    :type sui_client: SuiClient
    :return: The unique non-active-address SuiAddress and it's gas objects or None if one does not exist
    :rtype: Union[SuiAddress, None]
    """
    active_address = sui_client.config.active_address
    addresses = set(sui_client.config.addresses)
    addresses.remove(active_address.identifier)
    for anyaddress in addresses:
        inaddr = SuiAddress.from_hex_string(anyaddress)
        gas_objects = get_gas(sui_client, inaddr)
        if gas_objects:
            gas_balances = [gas.balance for gas in gas_objects]
            total_balance = sum(gas_balances)
            assert total_balance > 0


def test_committee(sui_client: SuiClient) -> None:
    """test_committee Expect 4 addresses with 1 staked_units each.

    :param sui_client: Synchronous http client
    :type sui_client: SuiClient
    """
    result = sui_client.execute(GetCommittee())
    assert result.is_ok()
    assert len(result.result_data.committee_info) == 4
    for committee in result.result_data.committee_info:
        assert committee.staked_units == 1
