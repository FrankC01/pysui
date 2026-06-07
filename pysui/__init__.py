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

from typing import Any

from pysui.abstracts.client_rpc import RpcResult


class SuiRpcResult(RpcResult):
    """Sui RpcResult.

    Captures information returned from simple and complex RPC API calls
    """

    def __init__(
        self, result_status: bool, result_string: str, result_data: Any = None
    ) -> None:
        """__init__ SuiRpcResult constructor."""
        super().__init__()
        self._status: bool = result_status
        self._result_str: str = result_string
        self._data: Any = result_data

    def is_ok(self) -> bool:
        """Ease of use status."""
        return self._status

    def is_err(self) -> bool:
        """Ease of use status."""
        return not self._status

    @property
    def result_data(self) -> Any:
        """Get result data."""
        return self._data

    @property
    def result_string(self) -> str:
        """Get result string."""
        return self._result_str

from .version import __version__

SDK_CURRENT_VERSION: list[str] = [int(x) for x in __version__.split(".")]

from pysui.sui.sui_common.config import PysuiConfiguration
from pysui.sui.sui_common.config.confgroup import GroupProtocol
from pysui.sui.sui_common.client import PysuiClient
from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.factory import client_factory
from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient
from pysui.sui.sui_grpc.pgrpc_clients import GrpcProtocolClient

from pysui.sui.sui_common.executors.serial_executor import SerialExecutor
from pysui.sui.sui_common.executors.exec_types import (
    GasMode,
    GasStatus,
    ExecutorContext,
    ExecutorOptions,
)
from pysui.sui.sui_common.executors.parallel_executor import ParallelExecutor

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
    GetChainIdentifier,
    GetLatestSuiSystemState,
    GetCurrentValidators,
    GetTransaction,
    GetTransactions,
    GetTransactionKind,
    VerifyTransactionSignature,
    VerifyPersonalMessageSignature,
)
