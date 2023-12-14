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

"""Pysui data classes for GraphQL results."""
from abc import ABC, abstractmethod

import dataclasses
from typing import Any, Optional, Union, Callable
import dataclasses_json
import json


def _fast_flat(in_dict: dict, out_dict: dict):
    """Flattens a nested dictionary."""

    for i_key, i_value in in_dict.items():
        if isinstance(i_value, dict):
            _fast_flat(i_value, out_dict)
        else:
            out_dict[i_key] = i_value


class PGQL_Type(ABC):
    """Base GraphQL to pysui data representation class."""

    @abstractmethod
    def from_query(self) -> "PGQL_Type":
        """Converts raw GraphQL result to dataclass type.

        :return: Object instance of implementing class
        :rtype: PGQL_Type
        """


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PagingCursor:
    """Static cursor controls used for paging results."""

    hasNextPage: bool = dataclasses.field(default=False)
    endCursor: Optional[str] = dataclasses.field(default_factory=str)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class NoopGQL(PGQL_Type):
    """."""

    next_cursor: PagingCursor
    data: list

    @classmethod
    def from_query(self) -> "NoopGQL":
        return NoopGQL(PagingCursor(), [])


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ErrorGQL(PGQL_Type):
    """."""

    next_cursor: PagingCursor
    data: list
    errors: Any

    @classmethod
    def from_query(self, errors: Any) -> "ErrorGQL":
        return ErrorGQL(PagingCursor(), [], errors)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinObjectGQL(PGQL_Type):
    """Coin object representation class."""

    coin_type: str
    version: int
    digest: str
    balance: str
    previous_transaction: str
    coin_owner: str
    has_public_transfer: bool
    coin_object_id: str

    @property
    def object_id(self) -> str:
        """Get as object_id."""
        return self.coin_object_id

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectGQL":
        """From raw GraphQL result data."""
        ser_dict: dict[str, Union[str, int]] = {}
        _fast_flat(in_data, ser_dict)
        return clz.from_dict(ser_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinObjectsGQL(PGQL_Type):
    """Collection of coin data objects."""

    data: list[SuiCoinObjectGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectsGQL":
        """Serializes query result to list of Sui gas coin objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'coin_objects'
        """
        # Get cursor
        in_data = in_data.pop("qres").pop("coins")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[SuiCoinObjectGQL] = [
            SuiCoinObjectGQL.from_query(i_coin) for i_coin in in_data["coin_objects"]
        ]
        return SuiCoinObjectsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadGQL(PGQL_Type):
    """Raw object representation class."""

    version: int  # Yes
    object_id: str  # Yes
    object_digest: str  # Yes
    previous_transaction_digest: str  # Yes
    object_kind: str  # Yes
    object_type: str  # Yes
    storage_rebate: str  # Yes
    has_public_transfer: bool  # Yes
    bcs: str  # Yes
    content: dict  # Yes
    owner_id: Optional[str] = None  # Yes

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectReadGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with nested dictionaries
        """
        in_data = in_data["object"] if "object" in in_data else in_data
        res_dict: dict = {}
        contents = in_data["as_move_content"]["as_object"].pop("content")
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        res_dict["content"] = contents
        return ObjectReadGQL.from_dict(res_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadsGQL(PGQL_Type):
    """Collection of object data objects."""

    data: list[ObjectReadGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectReadsGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'objects_data'
        """
        in_data = in_data.pop("objectConnection")
        # Get cursor
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[ObjectReadGQL] = [
            ObjectReadGQL.from_query(i_obj) for i_obj in in_data["objects_data"]
        ]
        return ObjectReadsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EventGQL(PGQL_Type):
    """Collection of event summaries."""

    package_id: str
    module_name: str
    event_type: str
    senders: list[str]
    timestamp: str
    json: dict

    @classmethod
    def from_query(clz, in_data: dict) -> "EventGQL":
        """Serializes query result to list of Sui objects."""
        in_mod_id = in_data.pop("sendingModuleId")
        to_merge: dict = {}
        _fast_flat(in_mod_id, to_merge)
        in_data |= to_merge
        in_data["json"] = json.loads(in_data["json"])
        in_data["event_type"] = in_data.pop("eventType")["event_type"]
        in_data["senders"] = [x["location"] for x in in_data["senders"]]
        return EventGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EventsGQL(PGQL_Type):
    """Collection of event summaries."""

    data: list[EventGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "EventsGQL":
        """Serializes query result to list of Sui objects.
        The in_data is a dictionary with 2 keys: 'cursor' and 'events'
        """

        in_data = in_data.pop("eventConnection")
        # Get cursor
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[ObjectReadGQL] = [
            EventGQL.from_query(i_obj) for i_obj in in_data["events"]
        ]
        return EventsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TxBlockListGQL(PGQL_Type):
    """Checkpoint data representation."""

    data: list[str]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "TxBlockListGQL":
        """Serializes query result of tx blocks in checkpoint."""
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[str] = [t_digest["digest"] for t_digest in in_data["tx_digests"]]
        return TxBlockListGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointGQL(PGQL_Type):
    """Checkpoint data representation."""

    digest: str
    sequence_number: int
    timestamp: str
    networkTotalTransactions: int
    transaction_blocks: TxBlockListGQL
    previous_checkpoint_digest: Optional[str]

    @classmethod
    def from_query(clz, in_data: dict) -> "CheckpointGQL":
        """Serializes query result of tx blocks in checkpoint."""
        in_data = in_data.pop("checkpoint", in_data)
        in_data["transaction_blocks"] = TxBlockListGQL.from_query(
            in_data["transaction_blocks"]
        )
        return CheckpointGQL.from_dict(in_data)

    @classmethod
    def from_last_checkpoint(clz, in_data: dict) -> "CheckpointGQL":
        """Serializes query result of tx blocks in checkpoint."""
        in_data = in_data.pop("checkpointConnection", None)
        in_data = in_data["nodes"][0]
        in_data["transaction_blocks"] = TxBlockListGQL.from_query(
            in_data["transaction_blocks"]
        )
        return CheckpointGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointsGQL(PGQL_Type):
    """Collection of Checkpoint summaries."""

    data: list[CheckpointGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "CheckpointsGQL":
        """."""
        in_data = in_data.pop("checkpointConnection")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        ndata: list[CheckpointGQL] = [
            CheckpointGQL.from_query(i_cp) for i_cp in in_data["checkpoints"]
        ]
        return CheckpointsGQL(ndata, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BalanceGQL(PGQL_Type):
    """Balance representation class."""

    coin_type: str
    coin_object_count: int
    total_balance: str
    owner: Optional[str] = ""

    @classmethod
    def from_query(clz, in_data: dict) -> "BalanceGQL":
        """Serializes query result of balance.

        The in_data is a dictionary with nested dictionaries
        """
        res_dict: dict = {}
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        return BalanceGQL.from_dict(res_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BalancesGQL(PGQL_Type):
    """Collection of balance objects."""

    owner_address: str
    data: list[BalanceGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "BalancesGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'objects_data'
        """
        # Get result
        in_data = in_data["qres"] if "qres" in in_data else in_data
        # Get cursor
        owner = in_data.pop("owner_address")
        balances = in_data.pop("balances")
        ncurs: PagingCursor = PagingCursor.from_dict(balances["cursor"])
        dlist: list[BalanceGQL] = [
            BalanceGQL.from_query(i_obj) for i_obj in balances["type_balances"]
        ]
        return BalancesGQL(owner, dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinMetadataGQL(PGQL_Type):
    """Coin metadata result representation class."""

    decimals: Optional[int] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    description: Optional[str] = None
    supply: Optional[str] = None
    meta_object_id: Optional[str] = None
    icon_url: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinMetadataGQL":
        """Serializes query result to Sui coin metadata object."""
        res_dict: dict = {}
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        return SuiCoinMetadataGQL.from_dict(res_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionResultGQL(PGQL_Type):
    """Transaction result representation class."""

    digest: str
    txn_kind: dict
    sender: dict
    expiration: Union[dict, None]
    gas_input: dict
    effects: dict

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionResultGQL":
        """."""
        return TransactionResultGQL.from_dict(in_data.pop("transactionBlock"))


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSummaryGQL(PGQL_Type):
    digest: str
    status: str
    timestamp: str
    errors: Optional[Any] = dataclasses.field(default_factory=list)

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionSummaryGQL":
        """."""
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        return TransactionSummaryGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSummariesGQL(PGQL_Type):
    """Transaction list of digest representation class."""

    data: list[TransactionSummaryGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionSummariesGQL":
        """."""
        in_data = in_data.pop("transactionBlockConnection")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        tsummary = [
            TransactionSummaryGQL.from_query(x) for x in in_data.pop("tx_blocks")
        ]
        return TransactionSummariesGQL(tsummary, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorGQL(PGQL_Type):
    """Validator representation class."""

    name: str
    validator_address: str
    description: str
    project_url: str
    staking_pool_sui_balance: str
    pending_stake: str
    pending_pool_token_withdraw: str
    pending_total_sui_withdraw: str
    voting_power: int
    commission_rate: int
    next_epoch_stake: str
    gas_price: str
    next_epoch_gas_price: str
    commission_rate: str
    next_epoch_commission_rate: int
    at_risk: Optional[int]

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorGQL":
        """."""
        in_data["validatorAddress"] = in_data["validatorAddress"]["location"]
        return ValidatorGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorSetGQL(PGQL_Type):
    """ValidatorSet representation class."""

    total_stake: int
    validators: list[ValidatorGQL]
    pending_removals: list[int]
    pending_active_validators_size: int
    stake_pool_mappings_size: int
    inactive_pools_size: int
    validator_candidates_size: int

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorSetGQL":
        """."""
        in_data["validators"] = [
            ValidatorGQL.from_query(v_obj) for v_obj in in_data["validators"]
        ]
        return ValidatorSetGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ReferenceGasPriceGQL(PGQL_Type):
    """ReferenceGasPriceGQL representation class."""

    reference_gas_price: str

    @classmethod
    def from_query(clz, in_data: dict) -> "ReferenceGasPriceGQL":
        in_data = in_data.pop("latestSuiSystemState", in_data)
        return ReferenceGasPriceGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SystemStateSummaryGQL(PGQL_Type):
    """SuiSystemStateSummary representation class."""

    system_state_version: str
    reference_gas_price: ReferenceGasPriceGQL
    system_parameters: dict
    stake_subsidy: dict
    validator_set: ValidatorSetGQL
    storage_fund: dict
    safe_mode: dict
    start_timestamp: str
    epoch: dict

    @classmethod
    def from_query(clz, in_data: dict) -> "SystemStateSummaryGQL":
        in_data = in_data.pop("qres", in_data)
        rgp = {"referenceGasPrice": in_data.pop("referenceGasPrice")}
        in_data["referenceGasPrice"] = ReferenceGasPriceGQL.from_query(rgp)
        in_data["validatorSet"] = ValidatorSetGQL.from_query(in_data["validatorSet"])
        return SystemStateSummaryGQL.from_dict(in_data)


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


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class KeyValue:
    """Generic map element."""

    key: str
    value: Union[bool, str]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ProtocolConfigGQL:
    """Sui ProtocolConfig representation."""

    protocolVersion: int
    configs: list[KeyValue]
    featureFlags: list[KeyValue]
    constraints: Optional[TransactionConstraints] = dataclasses.field(
        default_factory=TransactionConstraints
    )

    def _value_to_type(self, v: str) -> int:
        """."""
        if v:
            inner_v = v[v.index("(") + 1 : v.index(")")]
            return int(inner_v) if v[0] == "U" else float(inner_v)
        return None

    def __post_init__(self):
        """."""
        # Convert configs key/val to dict of key/int
        cfg_dict: dict = {}
        cnst_dict: dict = self.constraints.to_dict()
        # Turn to key addressable dict
        for ckv in self.configs:
            cfg_dict[ckv.key] = self._value_to_type(ckv.value)

        # Fetch the constraint and replace self.constraints
        for cnst_key in cnst_dict.keys():
            if cnst_key in cfg_dict:
                cnst_dict[cnst_key] = cfg_dict[cnst_key]
        self.constraints = TransactionConstraints.from_dict(cnst_dict)
        self.constraints.protocol_version = self.protocolVersion

        # Set appropriate features
        feat_dict: dict = {k.key: k.value for k in self.featureFlags}
        self.constraints.receive_objects = feat_dict["receive_objects"]

    @classmethod
    def from_query(clz, in_data: dict) -> "ProtocolConfigGQL":
        return ProtocolConfigGQL.from_dict(in_data.pop("protocolConfig"))
