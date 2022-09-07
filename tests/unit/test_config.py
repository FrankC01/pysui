"""SUI Client Configuration Tests."""
# import pytest

from src.sui import SuiConfig


def test_config() -> None:
    """Test config loads."""
    config = SuiConfig()
    assert config is not None
