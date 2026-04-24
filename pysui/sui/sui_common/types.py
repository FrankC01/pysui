#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Protocol-agnostic shared types for pysui executor layer."""

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


@dataclasses.dataclass
class ExecutionStatus:
    """Execution status indicator."""

    success: bool
    error: Optional[str] = None


@dataclasses.dataclass
class GasCostSummary:
    """Summary of gas costs incurred during execution."""

    computation_cost: int
    storage_cost: int
    storage_rebate: int
    non_refundable_storage_fee: int = 0


@dataclasses.dataclass
class Owner:
    """Protocol-agnostic owner description."""

    kind: str
    address: Optional[str] = None
    initial_shared_version: Optional[int] = None


@dataclasses.dataclass
class ChangedObject:
    """Description of an object changed during transaction execution."""

    object_id: str
    output_state: str
    output_digest: Optional[str] = None
    output_owner: Optional[Owner] = None


@dataclasses.dataclass
class TransactionEffects:
    """Protocol-agnostic transaction effects after execution."""

    transaction_digest: str
    status: ExecutionStatus
    gas_used: GasCostSummary
    lamport_version: int
    changed_objects: list[ChangedObject]
    gas_object: Optional[ChangedObject] = None
