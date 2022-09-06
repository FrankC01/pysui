"""Provides version checking and export the Configuration."""
import sys

from sui.sui_builders import ObjectsForAddress
from sui.sui_config import SuiConfig
from sui.sui_rpc import SuiClient
from sui.sui_types import parse_sui_object_descriptors

if sys.version_info < (3, 10):
    raise EnvironmentError("Python 3.10 or above is required")
