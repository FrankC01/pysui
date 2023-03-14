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

"""Types return from single transactions."""


from dataclasses import dataclass, field
from typing import Any, Optional, Union
from dataclasses_json import DataClassJsonMixin, config, LetterCase
from pysui.sui.sui_txresults.package_meta import SuiMoveStruct
from pysui.sui.sui_types import ObjectID, SuiAddress
from pysui.sui.sui_txresults.common import GenericRef


# Faucet results


@dataclass
class FaucetGas(DataClassJsonMixin):
    """Faucet Gas Object."""

    amount: int
    object_id: str = field(metadata=config(field_name="id"))
    transfer_tx_digest: str


@dataclass
class FaucetGasRequest(DataClassJsonMixin):
    """Result of faucet get gas."""

    transferred_gas_objects: list[FaucetGas]
    error: Optional[dict] = None


# ObjectInfo


@dataclass
class ObjectInfo(DataClassJsonMixin):
    """Base ObjectInfo type."""

    object_id: str = field(metadata=config(field_name="objectId"))
    version: int
    digest: str
    type_: str = field(metadata=config(field_name="type"))
    owner: dict
    previous_transaction: str = field(metadata=config(field_name="previousTransaction"))

    def __post_init__(self):
        """Post init processing for parameters."""
        if "AddressOwner" in self.owner:
            self.owner = self.owner["AddressOwner"]
        elif "ObjectOwner" in self.owner:
            self.owner = self.owner["ObjectOwner"]

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)

    @property
    def owner_address(self) -> SuiAddress:
        """owner_address Return owner as SuiAddress.

        :return: owner
        :rtype: SuiAddress
        """
        return SuiAddress.from_hex_string(self.owner)

    @classmethod
    def _differentiate(cls, indata: dict) -> Any:
        """Derive which description type."""
        split = indata["type"].split("::", 2)
        if split[0] == "0x2":
            match split[1]:
                case "coin":
                    split2 = split[2][5:-1].split("::")
                    if split2[2] == "SUI":
                        return SuiGasDescriptor.from_dict(indata)
                    return CoinDescriptor.from_dict(indata)
                case _:
                    return MoveDataDescriptor.from_dict(indata)
        else:
            return MoveDataDescriptor.from_dict(indata)

    @classmethod
    def factory(cls, indata: Union[dict, list[dict]]) -> Union[Any, list]:
        """Instantiate descriptor types."""
        if isinstance(indata, list):
            return [cls._differentiate(x) for x in indata]
        return cls._differentiate(indata)


@dataclass
class CoinDescriptor(ObjectInfo):
    """Base Coin descriptor."""


class SuiGasDescriptor(CoinDescriptor):
    """SUI Coin descriptor."""


@dataclass
class MoveDataDescriptor(ObjectInfo):
    """Data descriptor."""


# ObjectRead


@dataclass
class ObjectReadData(DataClassJsonMixin):
    """From sui_getObject."""

    has_public_transfer: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    fields: dict
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: str = field(metadata=config(field_name="type"))
    type_arg: str = field(default_factory=str)

    def __post_init__(self):
        """Post init processing for parameters."""
        ref = self.type_.split("<")
        if len(ref) > 1:
            inner_ref = ref[1][:-1].split(",")
            if len(inner_ref) > 1:
                self.type_arg = [x.strip() for x in inner_ref]
            else:
                self.type_arg = ref[1][:-1]
        if "id" in self.fields:
            self.fields["id"] = self.fields["id"]["id"]


@dataclass
class ObjectPackageReadData(DataClassJsonMixin):
    """From sui_getObject."""

    disassembled: dict
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: Optional[str] = ""

    def __post_init__(self):
        """Post init processing for parameters."""
        self.type_ = self.data_type


@dataclass
class ObjectNotExist(DataClassJsonMixin):
    """From sui_getObject."""

    object_id: str
    object_state: str = "Object does not exist."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectVersionNotFound(DataClassJsonMixin):
    """From sui_getObject."""

    object_id: str
    version_requested: int
    object_state: str = "Object version not found."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectVersionTooHigh(DataClassJsonMixin):
    """From sui_getObject."""

    asked_version: int
    latest_version: int
    object_id: str
    object_state: str = "Object version requested too high."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectDeleted(DataClassJsonMixin):
    """From sui_getObject."""

    reference: GenericRef
    object_state: str = "Object has been deleted."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return self.reference.object_id


@dataclass
class AddressOwner(DataClassJsonMixin):
    """From sui_getObject."""

    owner_type: str
    address_owner: str = field(metadata=config(field_name="owner"))


@dataclass
class ObjectOwner(DataClassJsonMixin):
    """From sui_getObject."""

    owner_type: str
    object_owner: str = field(metadata=config(field_name="owner"))


@dataclass
class SharedOwner(DataClassJsonMixin):
    """From sui_getObject."""

    owner_type: str
    initial_shared_version: int


@dataclass
class ImmutableOwner(DataClassJsonMixin):
    """From sui_getObject."""

    owner_type: str


# Object Raw Data


@dataclass
class ObjectRawData(DataClassJsonMixin):
    """From sui_getRawObject."""

    version: int
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: Optional[str] = field(metadata=config(field_name="type"), default_factory=str)
    has_public_transfer: Optional[bool] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=bool)
    bcs_bytes: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=str)
    module_map: Optional[dict] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=dict)


@dataclass
class ObjectRead(DataClassJsonMixin):
    """ObjectRead is base sui_getObject result."""

    version: int
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    # content: Optional[Union[dict, ObjectReadData, ObjectPackageReadData]]
    object_type: Optional[str] = field(metadata=config(field_name="type"))
    previous_transaction: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_rebate: Optional[int] = field(metadata=config(field_name="storageRebate"))
    content: Optional[dict] = field(default_factory=dict)
    bcs: Optional[dict] = field(default_factory=dict)
    digest: Optional[str] = field(default_factory=str)
    display: Optional[str] = field(default_factory=str)
    owner: Optional[Any] = field(default_factory=str)

    # reference: GenericRef

    def __post_init__(self):
        """Post init processing for parameters."""
        # Check if pure raw pacakge

        if self.content and self.content["dataType"] == "package":
            self.bcs = self.content = SuiPackage.from_dict(self.content)
        elif self.bcs and self.bcs["dataType"] == "package":
            self.bcs = self.content = ObjectRawData.from_dict(self.bcs)
        else:
            split = self.content["type"].split("::", 2)
            if split[0] == "0x2":
                match split[1]:
                    case "coin":
                        split2 = split[2][5:-1].split("::")
                        if split2[2] == "SUI":
                            self.content = SuiGas.from_dict(self.content)
                        else:
                            self.content = SuiCoin.from_dict(self.content)
                    case _:
                        self.content = SuiData.from_dict(self.content)
            else:
                self.content = SuiData.from_dict(self.content)

        if isinstance(self.owner, str):
            match self.owner:
                case "Immutable":
                    self.owner = ImmutableOwner.from_dict({"owner_type": "Immutable"})
                case _:
                    raise AttributeError(f"{self.owner} not handled")
        else:
            vlist = list(self.owner.items())
            match vlist[0][0]:
                case "AddressOwner":
                    sdict = {}
                    sdict["owner"] = vlist[0][1]
                    sdict["owner_type"] = "AddressOwner"
                    self.owner = AddressOwner.from_dict(sdict)
                case "ObjectOwner":
                    sdict = {}
                    sdict["owner"] = vlist[0][1]
                    sdict["owner_type"] = "ObjectOwner"
                    self.owner = ObjectOwner.from_dict(sdict)
                case "Shared":
                    sdict = vlist[0][1]
                    sdict["owner_type"] = "Shared"
                    self.owner = SharedOwner.from_dict(sdict)
                case "Immutable":
                    self.owner = ImmutableOwner.from_dict({})

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)
        # return ObjectID(self.data.fields["id"]["id"])

    @property
    def balance(self) -> str:
        """Alias balance for coin types."""
        if isinstance(self.content, SuiCoin):
            return self.content.balance
        raise AttributeError(f"Object {self.identifier} is not a 0x2:coin:Coin type.")

    @property
    def type_signature(self) -> str:
        """Alias type_signature."""
        return self.content.type_

    @property
    def owner_address(self) -> SuiAddress:
        """owner_address Return owner as SuiAddress.

        :return: owner
        :rtype: SuiAddress
        """
        return SuiAddress.from_hex_string(self.owner)

    @classmethod
    def _differentiate(cls, indata: dict) -> Union["ObjectRead", ObjectNotExist, ObjectDeleted]:
        """_differentiate determines concrete type and instantiates it.

        :param indata: Dictionary mapped from JSON result of `sui_getObject`
        :type indata: dict
        :return: If it exists, ObjectRead subclass, if not ObjectNotExist or ObjectDeleted if it has been
        :rtype: Union[ObjectRead, ObjectNotExist, ObjectDeleted]
        """
        read_object = indata["details"]
        match indata["status"]:
            case "Exists" | "VersionFound":
                result = ObjectRead.from_dict(read_object)
            case "ObjectNotExists" | "NotExists":
                result: ObjectRead = ObjectNotExist.from_dict({"object_id": read_object})
            case "VersionNotFound":
                result: ObjectRead = ObjectVersionNotFound.from_dict(
                    {"object_id": read_object[0], "version_requested": read_object[1]}
                )
            case "Deleted":
                result: ObjectRead = ObjectDeleted.from_dict({"reference": read_object})
            case "VersionTooHigh":
                result: ObjectRead = ObjectVersionTooHigh.from_dict(read_object)
        return result

    @classmethod
    def factory(cls, indata: Union[dict, list[dict]]) -> Union[Any, list]:
        """factory that consumes inbound data result.

        :param indata: Data received from `sui_getObject`
        :type indata: Union[dict, list[dict]]
        :return: results of `indata` parse
        :rtype: Union[Any, list]
        """
        if isinstance(indata, list):
            return [cls._differentiate(x) for x in indata]
        return cls._differentiate(indata)


@dataclass
class ObjectRawPackage(DataClassJsonMixin):
    """From sui_getRawObject."""

    package_id: str = field(metadata=config(field_name="id"))
    data_type: str = field(metadata=config(field_name="dataType"))
    module_map: dict
    version: int


@dataclass
class ObjectRawRead(DataClassJsonMixin):
    """From sui_getRawObject."""

    data: Union[dict, ObjectRead, ObjectRawData, ObjectRawPackage]
    owner: Any
    reference: GenericRef
    storage_rebate: int = field(metadata=config(field_name="storageRebate"))
    previous_transaction: str = field(metadata=config(field_name="previousTransaction"))

    def __post_init__(self):
        """Post init processing for parameters."""
        if self.data["dataType"] == "package":
            self.data = ObjectRawPackage.from_dict(self.data)
        else:
            self.data = ObjectRawData.from_dict(self.data)

    @classmethod
    def _differentiate(cls, indata: dict) -> Union["ObjectRawRead", ObjectNotExist, ObjectDeleted]:
        """_differentiate determines concrete type and instantiates it.

        :param indata: Dictionary mapped from JSON result of `sui_getRawObject`
        :type indata: dict
        :return: If it exists, ObjectRawRead subclass, if not ObjectNotExist or ObjectDeleted if it has been
        :rtype: Union[ObjectRawRead, ObjectNotExist, ObjectDeleted]
        """
        read_object = indata["details"]
        match indata["status"]:
            case "Exists":
                result = ObjectRawRead.from_dict(read_object)
            case "ObjectNotExists" | "NotExists":
                result: ObjectRead = ObjectNotExist.from_dict({"object_id": read_object})
            case "Deleted":
                result: ObjectRead = ObjectDeleted.from_dict({"reference": read_object})
        return result

    @classmethod
    def factory(cls, indata: Union[dict, list[dict]]) -> Union[Any, list]:
        """factory that consumes inbound data result.

        :param indata: Data received from `sui_getRawObject`
        :type indata: Union[dict, list[dict]]
        :return: results of `indata` parse
        :rtype: Union[Any, list]
        """
        if isinstance(indata, list):
            return [cls._differentiate(x) for x in indata]
        return cls._differentiate(indata)


@dataclass
class SuiPackage(ObjectPackageReadData):
    """SuiPackage is a package object.

    :param ObjectPackageReadData: superclass
    :type ObjectPackageReadData: ObjectPackageReadData
    :return: Instance of SuiPackage
    :rtype: SuiPackage
    """


@dataclass
class SuiData(ObjectReadData):
    """SuiData is object that is not coins.

    :param ObjectReadData: superclass
    :type ObjectReadData: ObjectReadData
    :return: Instance of SuiData
    :rtype: SuiData
    """


@dataclass
class SuiCoin(ObjectReadData):
    """SuiCoinType is the generic coin.

    :param ObjectReadData: superclass
    :type ObjectReadData: ObjectReadData
    :return: Instance of SuiCoin
    :rtype: SuiCoin
    """


@dataclass
class SuiGas(SuiCoin):
    """SuiGasType is SUI Gas coin object type.

    :param SuiCoin: superclass
    :type SuiCoin: SuiCoin
    :return: Instance of SuiGas
    :rtype: SuiGas
    """

    @property
    def balance(self) -> int:
        """balance returns the balance of coin<type> for this object.

        :return: balance value
        :rtype: int
        """
        return int(self.fields["balance"])


# Committee


@dataclass
class Committee(DataClassJsonMixin):
    """From sui_getCommittee."""

    authority_key: str
    staked_units: int


@dataclass
class CommitteeInfo(DataClassJsonMixin):
    """From sui_getCommittee."""

    epoch: int
    validators: list[Committee]
    # protocol_version: int

    def __post__init__(self):
        """Post initializaation."""

    @classmethod
    def factory(cls, indata: dict) -> "CommitteeInfo":
        """factory generates a CommitteeInfo type.

        :param indata: return from RPC API
        :type indata: dict
        :return: An instance of a CommitteeInfo object
        :rtype: CommitteeInfo
        """
        temp_list = []
        if indata["validators"]:
            for intcomm in indata["validators"]:
                temp_list.append({"authority_key": intcomm[0], "staked_units": intcomm[1]})
        indata["validators"] = temp_list
        return CommitteeInfo.from_dict(indata)


# TODO: Deprecated
# @dataclass
# class SystemParameters(DataClassJsonMixin):
#     """From sui_getSuiSystemState."""

#     governance_start_epoch: int
#     max_validator_count: int
#     min_validator_stake: int


@dataclass
class Table(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    size: int
    table_id: str = field(metadata=config(field_name="id"))


# TODO: Deprecated
# @dataclass
# class TableVec(DataClassJsonMixin):
#     """From sui_getSuiSystemState."""

#     contents: dict[str, int]


# TODO: Deprecated
# @dataclass
# class LinkedTableForObjectID(DataClassJsonMixin):
#     """From sui_getSuiSystemState."""

#     head: dict[str, list[str]]
#     tail: dict[str, list[str]]
#     size: int
#     linked_object_id: str = field(metadata=config(field_name="id"))


@dataclass
class StakingPool(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    activation_epoch: list[int]
    deactivation_epoch: list[int]
    exchange_rates: dict
    stakinig_pool_id: str = field(metadata=config(field_name="id"))
    pending_delegation: int
    pending_pool_token_withdraw: int
    pending_total_sui_withdraw: int
    pool_token_balance: int
    rewards_pool: Union[dict, int]
    # starting_epoch: int
    sui_balance: int

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        self.rewards_pool = self.rewards_pool["value"]


# pylint: disable=too-many-instance-attributes
@dataclass
class ValidatorMetaData(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    # consensus_address: list[int]
    description: str  # list[int]
    image_url: str  # list[int]
    name: str  # list[int]
    net_address: list[int]
    network_pubkey_bytes: list[int]
    next_epoch_net_address: Optional[list[int]]
    next_epoch_network_pubkey_bytes: Optional[list[int]]
    next_epoch_p2p_address: Optional[list[int]]
    next_epoch_primary_address: Optional[list[int]]
    next_epoch_proof_of_possession: Optional[list[int]]
    next_epoch_protocol_pubkey_bytes: Optional[list[int]]
    next_epoch_worker_address: Optional[list[int]]
    next_epoch_worker_pubkey_bytes: Optional[list[int]]
    p2p_address: list[int]
    primary_address: list[int]
    project_url: str
    proof_of_possession_bytes: list[int]
    protocol_pubkey_bytes: list[int]
    sui_address: str
    worker_address: list[int]
    worker_pubkey_bytes: list[int]


# TODO: Deprecated
# @dataclass
# class Validators(DataClassJsonMixin):
#     """From sui_getValidators."""

#     validator_metadata: list[ValidatorMetaData]

#     @classmethod
#     def ingest_data(cls, indata: list) -> "Validators":
#         """ingest_data Ingest validators.

#         :param indata: List of ValidatorMetaData objects
#         :type indata: list
#         :return: Instance of Validators
#         :rtype: Validators
#         """
#         return cls.from_dict({"validator_metadata": indata})


@dataclass
class Validator(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    commission_rate: int
    gas_price: int
    metadata: ValidatorMetaData
    next_epoch_commission_rate: int
    next_epoch_gas_price: int
    next_epoch_stake: int
    voting_power: int
    staking_pool: StakingPool


@dataclass
class ValidatorSummary(DataClassJsonMixin):
    """From sui_getLatestSuiSystemState."""

    commission_rate: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    description: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    exchange_rates_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    exchange_rates_size: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_price: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    image_url: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    name: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    net_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    network_pubkey_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_commission_rate: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_gas_price: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_net_address: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_network_pubkey_bytes: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_p2p_address: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_primary_address: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_proof_of_possession: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_protocol_pubkey_bytes: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_stake: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_worker_address: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_worker_pubkey_bytes: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL))
    operation_cap_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    p2p_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_stake: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_pool_token_withdraw: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_total_sui_withdraw: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    pool_token_balance: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    primary_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    project_url: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    proof_of_possession_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    protocol_pubkey_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    rewards_pool: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_activation_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_deactivation_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_sui_balance: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    sui_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    voting_power: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    worker_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    worker_pubkey_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))


# TODO: Deprecated
@dataclass
class ValidatorSet(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    active_validators: list[Validator]
    inactive_pools: Table
    pending_active_validators: dict
    validator_candidates: Table
    pending_removals: list[int]
    staking_pool_mappings: Table
    total_stake: int

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        if self.pending_active_validators:
            self.pending_active_validators = Table.from_dict(self.pending_active_validators["contents"])


# TODO: Deprecated
# @dataclass
# class VecSetForSuiAddress(DataClassJsonMixin):
#     """From sui_getSuiSystemState."""

#     contents: list[str] = field(default_factory=list)


# TODO: Deprecated
# @dataclass
# class ValidatorReportRecords(DataClassJsonMixin):
#     """From sui_getSuiSystemState."""

#     contents: list[dict[str, VecSetForSuiAddress]] = field(default_factory=list)

# TODO: Deprecated
# @dataclass
# class SuiSystemState(DataClassJsonMixin):
#     """From sui_getSuiSystemState."""

#     epoch: int
#     epoch_start_timestamp_ms: int
#     parameters: SystemParameters
#     protocol_version: int
#     reference_gas_price: int
#     safe_mode: bool
#     stake_subsidy: StakeSubsidy
#     storage_fund: Union[dict, int]
#     validator_report_records: ValidatorReportRecords
#     validators: ValidatorSet

#     def __post_init__(self):
#         """Post hydrate parameter fixups."""
#         self.storage_fund = self.storage_fund["value"]


@dataclass
class SuiLatestSystemState(DataClassJsonMixin):
    """."""

    active_validators: list[ValidatorSummary] = field(metadata=config(letter_case=LetterCase.CAMEL))
    at_risk_validators: list[dict] = field(metadata=config(letter_case=LetterCase.CAMEL))
    epoch: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    epoch_duration_ms: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    epoch_start_timestamp_ms: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    governance_start_epoch: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    inactive_pools_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    inactive_pools_size: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_active_validators_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_active_validators_size: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_removals: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    protocol_version: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    reference_gas_price: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    safe_mode: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    stake_subsidy_balance: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    stake_subsidy_current_epoch_amount: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    stake_subsidy_epoch_counter: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_mappings_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_mappings_size: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_fund: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    system_state_version: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    total_stake: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_candidates_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_candidates_size: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_report_records: list[Any] = field(metadata=config(letter_case=LetterCase.CAMEL))


# @dataclass
# class Delegation(DataClassJsonMixin):
#     """From sui_getDelegatedStakes."""

#     delegation_id: dict = field(metadata=config(field_name="id"))
#     pool_tokens: Union[dict, int]
#     principal_sui_amount: int
#     staked_sui_id: str

#     def __post_init__(self):
#         """Post hydrate parameter fixups."""
#         self.delegation_id = self.delegation_id["id"]
#         self.pool_tokens = self.pool_tokens["value"]


@dataclass
class StakedSui(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    staked_sui_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    stake_active_epoch: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    principal: int
    # token_lock: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL))
    status: str
    stage_request_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)
    estimated_reward: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=int)


@dataclass
class DelegatedStake(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    stakes: list[StakedSui]
    staking_pool: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class DelegatedStakes(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    delegated_stakes: list[DelegatedStake]

    @classmethod
    def ingest_data(cls, in_data: list) -> "DelegatedStakes":
        """Handle multiple delegated stake results."""
        return cls.from_dict({"delegated_stakes": in_data})


@dataclass
class SuiCoinMetadata(DataClassJsonMixin):
    """From sui_getCoinMetaData."""

    decimals: int
    name: str
    symbol: str
    description: str
    id_: Optional[str] = field(metadata=config(field_name="id"))
    icon_url: Optional[str] = field(metadata=config(field_name="iconUrl"))


@dataclass
class SuiCoinBalance(DataClassJsonMixin):
    """From sui_getBalance."""

    coin_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_object_count: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    locked_balance: dict = field(metadata=config(letter_case=LetterCase.CAMEL))
    total_balance: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class CoinBalances(DataClassJsonMixin):
    """From sui_getBalance."""

    items: list[SuiCoinBalance] = field(default_factory=list)

    @classmethod
    def ingest_data(cls, indata: list) -> "CoinBalances":
        """ingest_data Ingest balances.

        :param indata: Result of SUI tx
        :type indata: array of balances
        :return: Instance of CoinBalances
        :rtype: CoinBalances
        """
        return cls.from_dict({"items": indata})


@dataclass
class SuiCoinObject(DataClassJsonMixin):
    """From sui_getCoins."""

    coin_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    digest: str
    balance: int
    previous_transaction: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    locked_until_epoch: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL))

    @property
    def identifier(self) -> ObjectID:
        """Get the identifer as ObjectID."""
        return ObjectID(self.coin_object_id)


@dataclass
class SuiCoinObjects(DataClassJsonMixin):
    """From sui_getCoins."""

    data: list[SuiCoinObject]
    next_cursor: Union[str, None] = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class DynamicFieldInfo(DataClassJsonMixin):
    """From sui_getDynamicFields."""

    digest: str
    name: str
    bcs_name: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    field_type: str = field(metadata=config(field_name="type"))
    version: int


@dataclass
class DynamicFields(DataClassJsonMixin):
    """From sui_getDynamicFields."""

    data: list[DynamicFieldInfo]
    has_next_page: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_cursor: Union[str, None] = field(metadata=config(letter_case=LetterCase.CAMEL))
