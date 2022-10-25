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

"""Provides version checking and export the Configuration."""
import sys

from sui.sui_constants import *
from sui.sui_excepts import SuiInvalidAddress
from sui.sui_apidesc import SuiApi, build_api_descriptors
from sui.sui_builders import (
    SuiBaseBuilder,
    GetObjectsOwnedByAddress,
    GetObject,
    GetObjectsOwnedByObject,
    GetRawPackage,
    GetPackage,
    GetRpcAPI,
    TransferSui,
    Pay,
    MergeCoin,
    SplitCoin,
    MoveCall,
    Publish,
    ExecuteTransaction,
    DryRunTransaction,
    SuiRequestType,
)
from sui.sui_config import SuiConfig
from sui.sui_rpc import SuiClient, SuiRpcResult
from sui.sui_types import *
from sui.sui_crypto import keypair_from_keystring
from sui.sui_txn_validator import validate_api, valid_sui_address
from sui.sui_utils import *

if sys.version_info < (3, 10):
    raise EnvironmentError("Python 3.10 or above is required")
