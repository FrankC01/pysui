"""Provides version checking and export the Configuration."""
import sys

from sui.sui_config import SuiConfig

if sys.version_info < (3, 10):
    raise EnvironmentError("Python 3.10 or above is required")
