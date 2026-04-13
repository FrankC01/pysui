#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared transaction types used across GraphQL and gRPC protocol layers."""

import dataclasses
from typing import Optional
import dataclasses_json


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class TransactionConstraints:
    """Subset of Protocol Constraints."""

    protocol_version: Optional[int] = 0
    max_arguments: Optional[int] = 0
    max_input_objects: Optional[int] = 0
    max_num_transferred_move_object_ids: Optional[int] = 0
    max_programmable_tx_commands: Optional[int] = 0
    max_pure_argument_size: Optional[int] = 0
    max_tx_size_bytes: Optional[int] = 0
    max_type_argument_depth: Optional[int] = 0
    max_type_arguments: Optional[int] = 0
    max_tx_gas: Optional[int] = 0
    receive_objects: bool = False
    enable_address_balance_gas_payments: bool = False
