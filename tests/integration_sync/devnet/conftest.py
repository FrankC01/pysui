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

"""Fixtures for testing."""

import os
from pathlib import Path
import pytest
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_clients.sync_client import SuiClient

TRACKER_DIR: str = "/sui-test"


@pytest.fixture(scope="package")
def sui_test_move_path():
    """sui_test_move Sets up test move module."""
    my_path = os.getenv("PYTEST_CURRENT_TEST").split("/")[0] + TRACKER_DIR
    return Path(os.path.abspath(my_path))


@pytest.fixture(scope="package")
def sui_configuration():
    """configuration Get a SuiConfig for devnet.

    :return: Configuration loaded from ~/.sui/sui_config/client.yaml
    :rtype: SuiConfig
    """
    config: SuiConfig = SuiConfig.default()
    if len(config.addresses) == 1:
        config.create_new_keypair_and_address(SignatureScheme.ED25519)

    return config


@pytest.fixture(scope="package")
def sui_client(sui_configuration):
    """client Get a SuiClient (synch) for devnet.

    :param configuration: The input configuration
    :type configuration: SuiConfig
    """
    config = sui_configuration
    client: SuiClient = SuiClient(config)
    result: SuiRpcResult = client.get_gas()
    if result.is_ok():
        if len(result.result_data) == 0:
            client.get_gas_from_faucet(config.active_address)
    else:
        raise ValueError(f"Error making get_address_object_descriptors call: {result.result_string}")
    return client
