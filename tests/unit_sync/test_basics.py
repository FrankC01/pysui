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


from pysui.sui.sui_clients.sync_client import SuiClient


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
