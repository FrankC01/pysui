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

import pytest
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui import SuiConfig, SuiClient


@pytest.fixture(scope="package")
def configuration():
    """configuration Get a SuiConfig for devnet.

    :return: Configuration loaded from ~/.sui/sui_config/client.yaml
    :rtype: SuiConfig
    """
    config = SuiConfig.default()
    if len(config.addresses) == 1:
        config.create_new_keypair_and_address(SignatureScheme.ED25519)

    return config


@pytest.fixture(scope="package")
def client(configuration: SuiConfig):
    """client Get a SuiClient (synch) for devnet.

    :param configuration: The input configuration
    :type configuration: SuiConfig
    """
    return SuiClient(configuration)
