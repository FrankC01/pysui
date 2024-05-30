#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL configuration and constraings."""


import dataclasses
from typing import Any, Optional, Union, Callable
import dataclasses_json

import pysui.sui.sui_pgql.pgql_types as pgql_type

# TODO: Temporary Protocol Config hack, remove when ready
_QUERY = """

    query {
        chainIdentifier
        checkpoints (last: 1) {
            nodes {
                sequenceNumber
                timestamp
                epoch {
                        referenceGasPrice
                    }
            }
        }
        serviceConfig {
            availableVersions
            enabledFeatures
            maxQueryDepth
            maxQueryNodes
            maxOutputNodes
            maxDbQueryCost
            defaultPageSize
            maxPageSize
            mutationTimeoutMs
            requestTimeoutMs
            maxQueryPayloadSize
            maxTypeArgumentDepth
            maxTypeNodes
            maxMoveValueDepth
        }
      protocolConfig(protocolVersion:44) {
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

    availableVersions: list[str]
    mutationTimeoutMs: int
    maxTypeArgumentDepth: int
    maxTypeNodes: int
    maxMoveValueDepth: int

    enabledFeatures: list[str]
    maxQueryDepth: int
    maxQueryNodes: int
    maxOutputNodes: int
    defaultPageSize: int
    maxDbQueryCost: int
    maxPageSize: int
    requestTimeoutMs: int
    maxQueryPayloadSize: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointNodeGQL:
    sequenceNumber: int
    timestamp: str
    epoch: Any
    reference_gas_price: Optional[str] = None

    def __post_init__(self):
        """."""
        if "referenceGasPrice" in self.epoch:
            self.reference_gas_price = self.epoch["referenceGasPrice"]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointConnectionGQL:
    nodes: list[CheckpointNodeGQL]


# TODO: Make primary when changes moved through mainnet
@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiConfigGQL:
    chainIdentifier: str
    serviceConfig: ServiceConfigGQL
    protocolConfig: pgql_type.ProtocolConfigGQL
    checkpoints: CheckpointConnectionGQL
    gqlEnvironment: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiConfigGQL":
        """."""
        return SuiConfigGQL.from_dict(in_data)


def pgql_config(env: str) -> tuple[str, Callable]:
    """."""
    return _QUERY, SuiConfigGQL.from_query
