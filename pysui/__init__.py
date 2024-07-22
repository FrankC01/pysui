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
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.common import (
    PreExecutionResult,
    SuiRpcResult,
    handle_result,
)

from pysui.sui.sui_clients.sync_client import SuiClient as SyncClient
from pysui.sui.sui_clients.async_client import SuiClient as AsyncClient
from pysui.sui.sui_clients.subscribe import SuiClient as Subscribe
from pysui.sui.sui_pgql.config import PysuiConfiguration

from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient as SyncGqlClient
from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient as AsyncGqlClient
