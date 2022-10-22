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
