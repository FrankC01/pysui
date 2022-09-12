"""SUI Client Configuration Tests."""

import pathlib
import pytest

from src.sui import SuiConfig


def test_config_pass() -> None:
    """Test config loads presume at least 1 address."""
    config = SuiConfig.default()
    assert config is not None
    assert len(config.addresses) >= 1


def test_wallet_pass() -> None:
    """Test config loads presume at least 1 address."""
    config = SuiConfig.default()
    assert config is not None
    assert len(config.addresses) >= 1
    assert config.wallet is not None


def test_user_config_fail() -> None:
    """Fail test with path that does not exist."""
    with pytest.raises(Exception):
        SuiConfig.from_path(pathlib.Path("foo/bar"))
