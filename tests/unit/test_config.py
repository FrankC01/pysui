"""SUI Client Configuration Tests."""

import pathlib
import pytest

from src.sui import SuiConfig, SuiFileNotFound


def test_config_pass() -> None:
    """Test config loads presume at least 1 address."""
    config = SuiConfig.default()
    assert config is not None
    assert len(config.addresses) >= 1


def test_user_config_fail() -> None:
    """Fail test with path that does not exist."""
    with pytest.raises(SuiFileNotFound):
        SuiConfig.from_path(pathlib.Path("foo/bar"))
