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

from dataclasses_json import DataClassJsonMixin, LetterCase, config
from deprecated.sphinx import versionchanged

from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_types import ObjectID, SuiAddress

# pylint:disable=too-many-instance-attributes
# Faucet results


@dataclass
class FaucetGas(DataClassJsonMixin):
    """Faucet Gas Object."""

    amount: int
    transfer_tx_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(field_name="id"))


@dataclass
class FaucetGasRequest(DataClassJsonMixin):
    """Result of faucet get gas."""

    transferred_gas_objects: list[FaucetGas] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    error: Optional[dict] = field(default_factory=dict)


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
        ref = self.type_.split("<", 1)
        if len(ref) > 1:
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
    # asked_version: Optional[int]
    code: Optional[str]

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectVersionNotFound(DataClassJsonMixin):
    """From sui_getObject."""

    object_id: str
    asked_version: str
    latest_version: str

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectVersionTooHigh(DataClassJsonMixin):
    """From sui_getObject."""

    asked_version: str
    latest_version: str
    object_id: str
    code: str = "Object version requested too high."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectDeleted(DataClassJsonMixin):
    """From sui_getObject."""

    code: str
    object_id: str
    digest: str
    version: str

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return self.object_id


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
    initial_shared_version: str
    mutable: Optional[bool] = None


@dataclass
class ImmutableOwner(DataClassJsonMixin):
    """From sui_getObject."""

    owner_type: str


@dataclass
class NotRequestedOwner(DataClassJsonMixin):
    """From sui_getObject."""

    owner_type: str


# Object Raw Data


@dataclass
class ObjectRawData(DataClassJsonMixin):
    """From sui_getRawObject."""

    version: str
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: Optional[str] = field(
        metadata=config(field_name="type"), default_factory=str
    )
    has_public_transfer: Optional[bool] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=bool
    )
    bcs_bytes: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=str
    )
    module_map: Optional[dict] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=dict
    )


@dataclass
class DisplayFields(DataClassJsonMixin):
    """From GetObject."""

    data: Any
    error: Optional[dict]


@dataclass
class ObjectRead(DataClassJsonMixin):
    """ObjectRead is base sui_getObject result."""

    version: str
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    # content: Optional[Union[dict, ObjectReadData, ObjectPackageReadData]]
    previous_transaction: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=str
    )
    object_type: Optional[str] = field(
        metadata=config(field_name="type"), default_factory=str
    )
    storage_rebate: Optional[str] = field(
        metadata=config(field_name="storageRebate"), default=0
    )
    content: Optional[dict] = field(default_factory=dict)
    bcs: Optional[dict] = field(default_factory=dict)
    digest: Optional[str] = field(default_factory=str)
    display: Optional[dict] = field(default_factory=dict)
    owner: Optional[Any] = field(default_factory=str)
    # reference: GenericRef

    def __post_init__(self):
        """Post init processing for parameters."""
        # Check if pure raw pacakge

        if self.display:
            self.display = DisplayFields.from_dict(self.display)
        if self.content and self.content["dataType"] == "package":
            self.bcs = self.content = SuiPackage.from_dict(self.content)
        elif self.bcs and self.bcs["dataType"] == "package":
            self.bcs = self.content = ObjectRawData.from_dict(self.bcs)
        else:
            if self.content and "type" in self.content:
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
                    self.owner = NotRequestedOwner.from_dict(
                        {"owner_type": "Filter excluded"}
                    )
                    # raise AttributeError(f"{self.owner} not handled")
        else:
            vlist = list(self.owner.items())
            match vlist[0][0]:
                case "AddressOwner":
                    sdict = {}
                    sdict["address_owner"] = vlist[0][1]
                    sdict["owner_type"] = "AddressOwner"
                    self.owner = AddressOwner.from_dict(sdict)
                case "ObjectOwner":
                    sdict = {}
                    sdict["object_owner"] = vlist[0][1]
                    sdict["owner_type"] = "ObjectOwner"
                    self.owner = ObjectOwner.from_dict(sdict)
                case "Shared":
                    sdict = vlist[0][1]
                    sdict["owner_type"] = "Shared"
                    if self.content and self.content.has_public_transfer:
                        sdict["mutable"] = True
                    else:
                        sdict["mutable"] = False
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
        return SuiAddress(self.owner)

    @classmethod
    def differentiate(
        cls, indata: dict
    ) -> Union["ObjectRead", ObjectNotExist, ObjectDeleted]:
        """_differentiate determines concrete type and instantiates it.

        :param indata: Dictionary mapped from JSON result of `sui_getObject`
        :type indata: dict
        :return: If it exists, ObjectRead subclass, if not ObjectNotExist or ObjectDeleted if it has been
        :rtype: Union[ObjectRead, ObjectNotExist, ObjectDeleted]
        """
        if "status" in indata:
            instatus = indata["status"]
            indata = indata["details"]
            match instatus:
                case "VersionFound":
                    result = ObjectRead.from_dict(indata)
                case "VersionNotFound":
                    vth = {
                        "code": "notExist",
                        "asked_version": indata[1],
                        "object_id": indata[0],
                    }
                    result = ObjectNotExist.from_dict(vth)
                case "VersionTooHigh":
                    indata["code"] = instatus
                    result = ObjectVersionTooHigh.from_dict(indata)
                case "ObjectNotExists":
                    vth = {"code": "notExist", "object_id": indata}
                    result = ObjectNotExist.from_dict(vth)
                case "ObjectDeleted":
                    vth = {
                        "code": instatus,
                        "digest": indata["digest"],
                        "object_id": indata["objectId", "version" : indata["version"]],
                    }
                    ObjectDeleted.from_dict(vth)
                case _:
                    result = None
        elif "data" in indata:
            target = indata["data"]
            result = ObjectRead.from_dict(target)
        else:
            indata = indata["error"]
            match indata["code"]:
                case "notExists":
                    result = ObjectNotExist.from_dict(indata)
                case "deleted":
                    result = ObjectDeleted.from_dict(indata)
                case _:
                    return indata["error"]
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
            return [cls.differentiate(x) for x in indata]
        return cls.differentiate(indata)


@dataclass
class ObjectReadPage(DataClassJsonMixin):
    """From sui_getOwnedObjects."""

    data: list[dict]
    has_next_page: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_cursor: Union[str, None] = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing for parameters."""
        self.data = [ObjectRead.differentiate(x) for x in self.data]


@dataclass
class ObjectRawPackage(DataClassJsonMixin):
    """From sui_getRawObject."""

    package_id: str = field(metadata=config(field_name="id"))
    data_type: str = field(metadata=config(field_name="dataType"))
    module_map: dict
    version: str


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
    def _differentiate(
        cls, indata: dict
    ) -> Union["ObjectRawRead", ObjectNotExist, ObjectDeleted]:
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
                result: ObjectRead = ObjectNotExist.from_dict(
                    {"object_id": read_object}
                )
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

    epoch: str
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
                temp_list.append(
                    {"authority_key": intcomm[0], "staked_units": intcomm[1]}
                )
        indata["validators"] = temp_list
        return CommitteeInfo.from_dict(indata)


@dataclass
class Table(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    size: int
    table_id: str = field(metadata=config(field_name="id"))


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


@dataclass
class ValidatorSummary(DataClassJsonMixin):
    """From sui_getLatestSuiSystemState."""

    commission_rate: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    description: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    exchange_rates_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    exchange_rates_size: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_price: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    image_url: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    name: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    net_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    network_pubkey_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_commission_rate: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_gas_price: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_net_address: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_network_pubkey_bytes: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_p2p_address: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_primary_address: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_proof_of_possession: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_protocol_pubkey_bytes: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_stake: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_epoch_worker_address: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    next_epoch_worker_pubkey_bytes: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    operation_cap_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    p2p_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_stake: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    pending_pool_token_withdraw: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    pending_total_sui_withdraw: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    pool_token_balance: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    primary_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    project_url: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    proof_of_possession_bytes: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    protocol_pubkey_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    rewards_pool: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_activation_epoch: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    staking_pool_deactivation_epoch: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    staking_pool_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_sui_balance: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sui_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    voting_power: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    worker_address: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    worker_pubkey_bytes: str = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class SuiLatestSystemState(DataClassJsonMixin):
    """."""

    active_validators: list[ValidatorSummary] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    at_risk_validators: list[dict] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    epoch: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    epoch_duration_ms: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    epoch_start_timestamp_ms: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    inactive_pools_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    inactive_pools_size: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    max_validator_count: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    min_validator_joining_stake: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    pending_active_validators_id: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    pending_active_validators_size: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    pending_removals: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    protocol_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    reference_gas_price: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    safe_mode: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    safe_mode_computation_rewards: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    safe_mode_non_refundable_storage_fee: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    safe_mode_storage_rebates: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    safe_mode_storage_rewards: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    stake_subsidy_balance: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    stake_subsidy_current_distribution_amount: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    stake_subsidy_decrease_rate: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    stake_subsidy_distribution_counter: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    stake_subsidy_period_length: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    stake_subsidy_start_epoch: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    staking_pool_mappings_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    staking_pool_mappings_size: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    storage_fund_non_refundable_balance: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    storage_fund_total_object_storage_rebates: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    system_state_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    total_stake: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_candidates_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    validator_candidates_size: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    validator_low_stake_threshold: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    validator_report_records: list[Any] = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    validator_very_low_stake_threshold: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    validator_low_stake_grace_period: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )


@dataclass
class StakedSui(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    staked_sui_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    stake_active_epoch: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    principal: str
    # token_lock: Optional[int] = field(metadata=config(letter_case=LetterCase.CAMEL))
    status: str
    stage_request_epoch: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=str
    )
    estimated_reward: Optional[str] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=str
    )


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
    def factory(cls, in_data: list) -> "DelegatedStakes":
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
    total_balance: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    locked_balance: str = field(
        metadata=config(letter_case=LetterCase.CAMEL), default=""
    )


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
@versionchanged(version="0.20.0", reason="Removed 'locked_until_epoch")
class SuiCoinObject(DataClassJsonMixin):
    """From sui_getCoins."""

    coin_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: str
    digest: str
    balance: str
    previous_transaction: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    # locked_until_epoch: Optional[str] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=str)

    @property
    def identifier(self) -> ObjectID:
        """Get the identifer as ObjectID."""
        return ObjectID(self.coin_object_id)

    @property
    def object_id(self) -> str:
        """Get as object_id."""
        return self.coin_object_id

    @classmethod
    def from_read_object(cls, inbound: ObjectRead) -> "SuiCoinObject":
        """Create SuiCoinObject from generic coin ObjectRead."""
        coin = cls(
            inbound.object_type,
            inbound.object_id,
            inbound.version,
            inbound.digest,
            inbound.content.fields["balance"],
            inbound.previous_transaction,
        )
        setattr(coin, "owner", inbound.owner.address_owner)
        return coin


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
    version: str


@dataclass
class DynamicFields(DataClassJsonMixin):
    """From sui_getDynamicFields."""

    data: list[DynamicFieldInfo]
    has_next_page: bool = field(metadata=config(letter_case=LetterCase.CAMEL))
    next_cursor: Union[str, None] = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class ValidatorApy(DataClassJsonMixin):
    """From suix_getValidatorsApy."""

    address: str
    apy: float


@dataclass
class ValidatorApys(DataClassJsonMixin):
    """From suix_getValidatorsApy."""

    apys: list[ValidatorApy]
    epoch: str


@dataclass
class TransactionConstraints(DataClassJsonMixin):
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
    feature_dict: Optional[dict] = field(default_factory=dict)


@dataclass
class ProtocolConfig(DataClassJsonMixin):
    """From sui_getProtocolConfig."""

    max_supported_protocol_version: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    min_supported_protocol_version: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )
    protocol_version: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    feature_flags: dict = field(metadata=config(letter_case=LetterCase.CAMEL))
    attributes: dict
    transaction_constraints: Optional[TransactionConstraints] = field(
        default_factory=TransactionConstraints
    )

    @classmethod
    def loader(cls, indata: dict) -> "ProtocolConfig":
        """Loader to resolve constraints."""
        pc = ProtocolConfig.from_dict(indata)
        pc.transaction_constraints.protocol_version = int(pc.protocol_version)
        pc.transaction_constraints.max_arguments = int(
            pc.attributes["max_arguments"]["u32"]
        )
        pc.transaction_constraints.max_input_objects = int(
            pc.attributes["max_input_objects"]["u64"]
        )
        pc.transaction_constraints.max_num_transferred_move_object_ids = int(
            pc.attributes["max_num_transferred_move_object_ids"]["u64"]
        )
        pc.transaction_constraints.max_programmable_tx_commands = int(
            pc.attributes["max_programmable_tx_commands"]["u32"]
        )
        pc.transaction_constraints.max_pure_argument_size = int(
            pc.attributes["max_pure_argument_size"]["u32"]
        )
        pc.transaction_constraints.max_tx_size_bytes = int(
            pc.attributes["max_tx_size_bytes"]["u64"]
        )
        pc.transaction_constraints.max_type_argument_depth = int(
            pc.attributes["max_type_argument_depth"]["u32"]
        )
        pc.transaction_constraints.max_type_arguments = int(
            pc.attributes["max_type_arguments"]["u32"]
        )
        pc.transaction_constraints.max_tx_gas = int(pc.attributes["max_tx_gas"]["u64"])
        pc.transaction_constraints.feature_dict = pc.feature_flags
        return pc
