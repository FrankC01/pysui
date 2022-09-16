"""Provides version checking and export the Configuration."""
import sys

from sui.sui_builders import GetObjectsOwnedByAddress, GetObject, GetObjectsOwnedByObject, GetPackage
from sui.sui_config import SuiConfig
from sui.sui_rpc import SuiClient, SuiRpcResult
from sui.sui_types import parse_sui_object_descriptors, parse_sui_object_type, parse_keystring_to_address, SuiAddress


from sui.sui_crypto import *

if sys.version_info < (3, 10):
    raise EnvironmentError("Python 3.10 or above is required")
