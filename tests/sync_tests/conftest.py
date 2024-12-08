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

"""Fixtures for testing."""

import pytest

from pysui import PysuiConfiguration, SyncGqlClient


@pytest.fixture(scope="package")
def sui_client() -> SyncGqlClient:  # type: ignore
    """Fixture to create a test session wide client pointed to sui-base localnet."""
    # sui_base_anynet_start()
    # Use for devnet versions
    # sui_base_localnet_start()
    cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        profile_name="devnet",
        persist=False,
    )
    client = SyncGqlClient(pysui_config=cfg)
    # Turn this fixture into a generator
    yield client
