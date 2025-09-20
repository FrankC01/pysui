#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL configuration and constraings."""


import dataclasses
from typing import Any, Optional, Union, Callable
import dataclasses_json

import pysui.sui.sui_pgql.pgql_types as pgql_type


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
    protocolConfigs: pgql_type.ProtocolConfigGQL
    checkpoint: CheckpointNodeGQL
    gqlEnvironment: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiConfigGQL":
        """."""
        return SuiConfigGQL.from_dict(in_data)


def pgql_config(env: str, sversion: Optional[str] = None) -> tuple[str, Callable]:
    """Get the configuration for Sui GraphQL."""
    return _QUERY_BETA, SuiConfigGQL.from_query
