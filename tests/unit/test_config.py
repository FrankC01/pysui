"""SUI Client Configuration Tests."""
import pytest

from src.sui import SuiConfig


def test_config() -> None:
    """Test config loads."""
    x = SuiConfig()
    assert x is not None
