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

import subprocess
import pytest

from pysui import SyncClient, SuiConfig

LOCALNET_PROC_SET_REPO: str = ["bash", "localnet", "set-sui-repo"]
LOCALNET_PROC_SET_ACTIVE: str = ["bash", "localnet", "set-active"]
LOCALNET_PROC_REGEN: str = ["bash", "localnet", "regen"]
LOCALNET_PROC_STOP: str = ["bash", "localnet", "stop"]


def sui_base_anynet_start() -> bool:
    """Use any suibase net settings in test."""
    result = subprocess.run(
        LOCALNET_PROC_REGEN, capture_output=True, text=True
    )
    if result.returncode == 0:
        return True
    raise ValueError(f"Result of localnet regen {result.stderr}")


def sui_base_localnet_start() -> bool:
    """Regenerate (start sui-base localnet) and set localnet active."""
    result = subprocess.run(
        LOCALNET_PROC_SET_REPO, capture_output=True, text=True
    )
    if result.returncode == 0:
        result = subprocess.run(
            LOCALNET_PROC_SET_ACTIVE, capture_output=True, text=True
        )
        if result.returncode == 0:
            result = subprocess.run(
                LOCALNET_PROC_REGEN, capture_output=True, text=True
            )
            if result.returncode == 0:
                return True
    raise ValueError(f"Result of localnet regen {result.stderr}")


def sui_base_localnet_stop() -> bool:
    """With normal teardown and/or exception stop the localnet."""
    result = subprocess.run(LOCALNET_PROC_STOP, capture_output=True, text=True)
    if result.returncode == 0:
        return True
    raise ValueError(f"Result of localnet stop {result.stderr}")


@pytest.fixture(scope="package")
def sui_client() -> SyncClient:
    """Fixture to create a test session wide client pointed to sui-base localnet."""
    # Use for jump ahead versions
    # sui_base_anynet_start()
    # Use for devnet versions
    sui_base_localnet_start()
    client = SyncClient(SuiConfig.sui_base_config())
    # Turn this fixture into a generator
    yield client
    sui_base_localnet_stop()
