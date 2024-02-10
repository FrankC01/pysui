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

    # TODO: Need to handle different owner types
    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectReadGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with nested dictionaries
        """
        if in_data.get("object"):
            in_data = in_data["object"] if "object" in in_data else in_data
            res_dict: dict = {}
            contents = in_data["as_move_content"]["as_object"].pop("content")
            # Flatten dictionary
            _fast_flat(in_data, res_dict)
            res_dict["content"] = contents
            return ObjectReadGQL.from_dict(res_dict)
        return NoopGQL.from_query()


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
        in_data = in_data.pop("objects")
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
    timestamp: str
    json: str
    sender: Optional[str]

    @classmethod
    def from_query(clz, in_data: dict) -> "EventGQL":
        """Serializes query result to list of Sui objects."""
        in_mod_id = in_data.pop("sendingModule")
        to_merge: dict = {}
        _fast_flat(in_mod_id, to_merge)
        in_data |= to_merge
        in_data["json"] = json.dumps(in_data["json"])
        in_data["event_type"] = in_data.pop("type")["event_type"]
        # in_data["sender"] = [x["address"] for x in in_data["sender"]]
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

        in_data = in_data.pop("events")
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
        in_data = in_data.pop("checkpoints", None)
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
        in_data = in_data.pop("checkpoints")
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
    address: Optional[str] = None
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

    sender: dict
    expiration: Union[dict, None]
    gas_input: dict
    effects: dict
    digest: Optional[str] = ""

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionResultGQL":
        """."""
        if in_data.get("transactionBlock"):
            return TransactionResultGQL.from_dict(in_data.pop("transactionBlock"))
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DryRunResultGQL(PGQL_Type):
    """DryRun result representation class."""

    transaction_block: TransactionResultGQL
    error: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "DryRunResultGQL":
        """."""
        if in_data:
            in_data = in_data.get("dryRun")
            if in_data:
                dr_err = in_data.pop("error")
                tblock = TransactionResultGQL.from_query(in_data)
                return DryRunResultGQL.from_dict(
                    {"error": dr_err, "transaction_block": tblock}
                )
        return NoopGQL.from_query()


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
        in_data = in_data.pop("transactionBlocks")
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
    # staking_pool_sui_balance: str
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
        in_data["validatorAddress"] = in_data["validatorAddress"]["address"]
        return ValidatorGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorSetGQL(PGQL_Type):
    """ValidatorSet representation class."""

    total_stake: int
    validators: list[ValidatorGQL]
    pending_removals: Optional[list[int]]
    pending_active_validators_size: Optional[int]
    inactive_pools_size: Optional[int]
    validator_candidates_size: Optional[int]

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorSetGQL":
        """."""
        in_data["validators"] = [
            ValidatorGQL.from_query(v_obj) for v_obj in in_data["validators"]["nodes"]
        ]
        return ValidatorSetGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ReferenceGasPriceGQL(PGQL_Type):
    """ReferenceGasPriceGQL representation class."""

    reference_gas_price: str

    @classmethod
    def from_query(clz, in_data: dict) -> "ReferenceGasPriceGQL":
        in_data = in_data.pop("epoch", in_data)
        return ReferenceGasPriceGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SystemStateSummaryGQL(PGQL_Type):
    """SuiSystemStateSummary representation class."""

    system_state_version: str
    total_transactions: int
    reference_gas_price: ReferenceGasPriceGQL
    system_parameters: dict
    validator_set: ValidatorSetGQL
    storage_fund: dict
    safe_mode: dict

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
    value: Union[bool, str, None]


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

    def _value_to_type(self, v: Any) -> Union[int, bool]:
        """."""
        if v:
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                if v.count("."):
                    return float(v)
                return int(v, base=0)
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


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructureGQL:
    """Sui MoveStucture representation."""

    struct_name: str
    abilities: list[str]
    fields: list[dict]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveStructureGQL":
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            return MoveStructureGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructuresGQL:
    """Sui collection of MoveStuctures."""

    structures: list[MoveStructureGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveStructuresGQL":
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            return MoveStructuresGQL.from_dict(
                {"structures": [MoveStructureGQL.from_query(x) for x in fdict["nodes"]]}
            )
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionGQL:
    """Sui MoveFunction representation."""

    function_name: str
    is_entry: bool
    visibility: str
    type_parameters: list
    parameters: list[dict]
    returns: Optional[list] = dataclasses.field(default_factory=list)

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveFunctionGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        return MoveFunctionGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionsGQL:
    """Sui MoveFunction representation."""

    functions: list[MoveFunctionGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveFunctionsGQL":
        """."""
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            return MoveFunctionsGQL.from_dict(
                {"functions": [MoveFunctionGQL.from_query(x) for x in fdict["nodes"]]}
            )
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveModuleGQL:
    """Sui MoveModule representation."""

    module_name: str
    module_structures: MoveStructuresGQL
    module_functions: MoveFunctionsGQL

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveModuleGQL":
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            if "structure_list" in fdict:
                fdict["module_structures"] = []
            # fdict["module_structures"] = fdict.get("module_structures", [])
            fdict["module_structures"] = MoveStructuresGQL.from_query(
                {"nodes": fdict["module_structures"]}
            )
            fdict["module_functions"] = MoveFunctionsGQL.from_query(
                {"nodes": fdict["module_functions"]}
            )
            return MoveModuleGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MovePackageGQL:
    """Sui MovePackage representation."""

    package_id: str
    package_version: int
    modules: list[MoveModuleGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "MovePackageGQL":
        if in_data.get("object"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["modules"] = [MoveModuleGQL.from_query(x) for x in fdict["nodes"]]
            fdict.pop("nodes")
            return MovePackageGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorGQL:
    """Sui ValidatorSet representation."""

    validator_name: str
    validator_address: str
    description: str
    imageUrl: str
    projectUrl: str
    stakingPoolSuiBalance: str
    stakingPoolActivationEpoch: int
    exchangeRatesSize: int
    rewardsPool: str
    poolTokenBalance: str
    pendingStake: str
    pendingTotalSuiWithdraw: str
    pendingPoolTokenWithdraw: str
    votingPower: int
    gasPrice: str
    commissionRate: int
    nextEpochStake: str
    nextEpochGasPrice: str
    nextEpochCommissionRate: 1200
    apy: int
    atRisk: Optional[int] = None
    operating_cap_address: Optional[str] = None
    exchange_rates_address: Optional[str] = None
    staking_pool_address: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorSetGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        if "operatingCap" in fdict:
            fdict["operating_cap_address"] = None
            fdict.pop("operatingCap")
        if "exchangeRate" in fdict:
            fdict["exchange_rates_address"] = None
            fdict.pop("exchangeRate")
        if "stakingPool" in fdict:
            fdict["staking_pool_address"] = None
            fdict.pop("stakingPool")
        return ValidatorGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorSetGQL:
    """Sui ValidatorSet representation."""

    totalStake: str
    pendingRemovals: list
    pendingActiveValidatorsId: str
    pendingActiveValidatorsSize: int
    stakingPoolMappingsId: str
    inactivePoolsId: str
    validatorCandidatesId: str
    validatorCandidatesSize: int
    validators: list[ValidatorGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorSetGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        fdict["next_cursor"] = PagingCursor(
            fdict.pop("hasNextPage"), fdict.pop("endCursor")
        )
        fdict["validators"] = [ValidatorGQL.from_query(x) for x in fdict["validators"]]
        return ValidatorSetGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorApyGQL:
    """Sui ValidatorApy representation."""

    name: str
    apy: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorApysGQL:
    """Sui ValidatorApy representation."""

    next_cursor: PagingCursor
    validators_apy: list[ValidatorApyGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorApysGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        fdict["next_cursor"] = PagingCursor(
            fdict.pop("hasNextPage"), fdict.pop("endCursor")
        )
        return ValidatorApysGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DynamicFieldGQL:
    """Sui Object's Dynamic Field representation."""

    name: dict
    field_kind: str
    field_data: dict


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DynamicFieldsGQL:
    """Sui Object's Dynamic Fields representation."""

    parent_object_id: str
    version: int
    next_cursor: PagingCursor
    dynamic_fields: list[DynamicFieldGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "DynamicFieldsGQL":
        if in_data.get("objects"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["next_cursor"] = PagingCursor(
                fdict.pop("hasNextPage"), fdict.pop("endCursor")
            )
            return DynamicFieldsGQL.from_dict(fdict)
        return NoopGQL.from_query()
