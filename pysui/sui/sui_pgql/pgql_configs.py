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

"""Sui GraphQL configuration and constraings."""


import dataclasses
from typing import Optional, Union, Callable
import dataclasses_json

import pysui.sui.sui_pgql.pgql_types as pgql_type

_QUERY = """

    query {
        chainIdentifier
        checkpointConnection (last: 1) {
            nodes {
                sequenceNumber
                timestamp
            }
        }
        serviceConfig {
            enabledFeatures
            maxQueryDepth
            maxQueryNodes
            maxDbQueryCost
            maxPageSize
            requestTimeoutMs
            maxQueryPayloadSize
        }
      protocolConfig {
          protocolVersion
          configs {
            key
            value
          }
          featureFlags {
            key
            value
          }
        }
    }
"""


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ServiceConfigGQL:
    """Sui GraphQL service controls."""

    enabledFeatures: list[str]
    maxQueryDepth: int
    maxQueryNodes: int
    maxDbQueryCost: str
    maxPageSize: str
    requestTimeoutMs: str
    maxQueryPayloadSize: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointNodeGQL:
    sequenceNumber: int
    timestamp: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointConnectionGQL:
    nodes: list[CheckpointNodeGQL]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiConfigGQL:
    chainIdentifier: str
    serviceConfig: ServiceConfigGQL
    protocolConfig: pgql_type.ProtocolConfigGQL
    checkpointConnection: CheckpointConnectionGQL


def pgql_config() -> tuple[str, Callable]:
    """."""
    return _QUERY, SuiConfigGQL.from_dict
