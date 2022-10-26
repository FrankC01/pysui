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


"""SUI Client Configuration Tests."""


import pytest

from pysui.sui.sui_config import SuiConfig


def test_config_pass() -> None:
    """Test config default load."""
    config = SuiConfig.default()
    assert config is not None


def test_from_config_pass() -> None:
    """Test loading well known config."""
    config = SuiConfig.from_config_file("~/.sui/sui_config/client.yaml")
    assert config is not None


@pytest.mark.xfail(raises=Exception)
def test_from_config_fail() -> None:
    """Test loading well known config."""
    _ = SuiConfig.from_config_file("~/does_not_exist/client.yaml")
