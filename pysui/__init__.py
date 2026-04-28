#    Copyright Frank V. Castellucci
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
"""pysui package."""
import sys
import logging
from pysui.version import __version__

logger = logging.getLogger("pysui")
if not logging.getLogger().handlers:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False

logger.info("Initializing pysui")
if sys.version_info < (3, 10):
    raise EnvironmentError("Python 3.10 or above is required")

# Convenience imports

from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import ObjectID
from pysui.sui.sui_clients.common import (
    PreExecutionResult,
    SuiRpcResult,
    handle_result,
)

from .version import __version__

SDK_CURRENT_VERSION: list[str] = [int(x) for x in __version__.split(".")]

from pysui.sui.sui_common.config import PysuiConfiguration
from pysui.sui.sui_common.config.confgroup import GroupProtocol
from pysui.sui.sui_common.client import PysuiClient
from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.factory import client_factory
from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
from pysui.sui.sui_grpc.pgrpc_clients import SuiGrpcClient

from pysui.sui.sui_pgql.execute.serial_exec import GqlSerialTransactionExecutor
from pysui.sui.sui_pgql.execute.parallel_exec import GqlParallelTransactionExecutor
from pysui.sui.sui_grpc.grpc_serial_exec import GrpcSerialTransactionExecutor
from pysui.sui.sui_grpc.grpc_parallel_exec import GrpcParallelTransactionExecutor

from pysui.sui.sui_common.sui_command import SuiCommand
from pysui.sui.sui_common.sui_commands import (
    ExecuteTransaction,
    SimulateTransaction,
    SimulateTransactionKind,
    GetCoinMetaData,
    GetAddressCoinBalance,
    GetAddressCoinBalances,
    GetCoins,
    GetGas,
    GetStaked,
    GetDelegatedStakes,
    GetObject,
    GetPastObject,
    GetMultipleObjects,
    GetMultiplePastObjects,
    GetObjectsOwnedByAddress,
    GetDynamicFields,
    GetEpoch,
    GetBasicCurrentEpochInfo,
    GetLatestCheckpoint,
    GetCheckpointBySequence,
    GetMultipleObjectContent,
    GetProtocolConfig,
    GetObjectContent,
    GetObjectsForType,
    GetCoinSummary,
    GetPackage,
    GetPackageVersions,
    GetModule,
    GetMoveDataType,
    GetStructure,
    GetStructures,
    GetFunction,
    GetFunctions,
    GetNameServiceAddress,
    GetNameServiceNames,
)
