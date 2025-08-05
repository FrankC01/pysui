#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL configuration and constraings."""


import dataclasses
from typing import Any, Optional, Union, Callable
import dataclasses_json

import pysui.sui.sui_pgql.pgql_types as pgql_type

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
            maxTypeArgumentWidth
            maxTransactionIds
            maxTypeNodes
            maxMoveValueDepth
            maxTransactionPayloadSize
            maxTransactionIds
            maxScanLimit
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

_QUERY_BETA = """

    query {
        chainIdentifier
        checkpoint {
            sequenceNumber
            timestamp
            epoch {
                    referenceGasPrice
                }
        }
        serviceConfig {
            mutationTimeoutMs
            queryTimeoutMs
            maxQueryDepth
            maxQueryNodes
            maxOutputNodes
            maxTransactionPayloadSize
            maxQueryPayloadSize
            maxTypeArgumentDepth
            maxTypeArgumentWidth
            maxTypeNodes
            maxMoveValueDepth
        }
      protocolConfigs {
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
    maxOutputNodes: int
    defaultPageSize: int
    maxDbQueryCost: int
    maxPageSize: int
    requestTimeoutMs: int
    maxQueryPayloadSize: int
    maxTypeArgumentDepth: int
    maxTypeArgumentWidth: int
    maxTypeNodes: int
    maxMoveValueDepth: int
    mutationTimeoutMs: Optional[int] = dataclasses.field(default=None)
    maxTransactionPayloadSize: Optional[int] = dataclasses.field(default=None)
    maxTransactionIds: Optional[int] = dataclasses.field(default=None)
    maxScanLimit: Optional[int] = dataclasses.field(default=None)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ServiceConfigBetaGQL:
    """Sui GraphQL service controls."""

    maxQueryDepth: int
    maxQueryNodes: int
    maxOutputNodes: int
    maxQueryPayloadSize: int
    # defaultPageSize: int
    # maxPageSize: str
    maxTypeArgumentDepth: int
    maxTypeArgumentWidth: int
    maxTypeNodes: int
    maxMoveValueDepth: int
    mutationTimeoutMs: Optional[int] = dataclasses.field(default=None)
    queryTimeoutMs: Optional[int] = dataclasses.field(default=None)
    maxTransactionPayloadSize: Optional[int] = dataclasses.field(default=None)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointNodeGQL:
    sequenceNumber: int
    timestamp: str
    epoch: Any
    reference_gas_price: Optional[int] = None

    def __post_init__(self):
        """."""
        if "referenceGasPrice" in self.epoch:
            self.reference_gas_price = int(self.epoch["referenceGasPrice"])


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
    checkpoints: CheckpointConnectionGQL
    gqlEnvironment: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiConfigGQL":
        """."""
        return SuiConfigGQL.from_dict(in_data)


# TODO: Make primary when changes moved through mainnet
@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiConfigBetaGQL:
    chainIdentifier: str
    serviceConfig: ServiceConfigBetaGQL
    protocolConfigs: pgql_type.ProtocolConfigGQL
    checkpoint: CheckpointNodeGQL
    gqlEnvironment: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiConfigGQL":
        """."""
        return SuiConfigBetaGQL.from_dict(in_data)


def pgql_config(env: str, sversion: Optional[str] = None) -> tuple[str, Callable]:
    """Get the configuration for Sui GraphQL."""
    if env == "betatest" or env == "betamain":
        return _QUERY_BETA, SuiConfigBetaGQL.from_query
    return _QUERY, SuiConfigGQL.from_query
