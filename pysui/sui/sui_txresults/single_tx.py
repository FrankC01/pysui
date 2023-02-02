#    Copyright 2022 Frank V. Castellucci
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

    has_public_transfer: bool
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


@dataclass
class ObjectRead(DataClassJsonMixin):
    """ObjectRead is base sui_getObject result."""

    data: Union[dict, ObjectReadData, ObjectPackageReadData]
    owner: Any
    reference: GenericRef
    storage_rebate: int = field(metadata=config(field_name="storageRebate"))
    previous_transaction: str = field(metadata=config(field_name="previousTransaction"))

    def __post_init__(self):
        """Post init processing for parameters."""
        if self.data["dataType"] == "package":
            self.data = SuiPackage.from_dict(self.data)
        else:
            split = self.data["type"].split("::", 2)
            if split[0] == "0x2":
                match split[1]:
                    case "coin":
                        split2 = split[2][5:-1].split("::")
                        if split2[2] == "SUI":
                            self.data = SuiGas.from_dict(self.data)
                        else:
                            self.data = SuiCoin.from_dict(self.data)
                    case _:
                        self.data = SuiData.from_dict(self.data)
            else:
                self.data = SuiData.from_dict(self.data)

        if isinstance(self.owner, str):
            match self.owner:
                case "Immutable":
                    self.owner = ImmutableOwner.from_dict({})
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
        return ObjectID(self.reference.object_id)
        # return ObjectID(self.data.fields["id"]["id"])

    @property
    def balance(self) -> str:
        """Alias balance for coin types."""
        if isinstance(self.data, SuiCoin):
            return self.data.balance
        raise AttributeError(f"Object {self.identifier} is not a 0x2:coin:Coin type.")

    @property
    def version(self) -> int:
        """Alias version."""
        return self.reference.version

    @property
    def digest(self) -> str:
        """Alias digest."""
        return self.reference.digest

    @property
    def type_signature(self) -> str:
        """Alias type_signature."""
        return self.data.type_

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


# Object Raw Data


@dataclass
class ObjectRawData(DataClassJsonMixin):
    """From sui_getRawObject."""

    has_public_transfer: bool
    bcs_bytes: str
    version: int
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: str = field(metadata=config(field_name="type"))


@dataclass
class ObjectRawPackage(DataClassJsonMixin):
    """From sui_getRawObject."""

    package_id: str = field(metadata=config(field_name="id"))
    data_type: str = field(metadata=config(field_name="dataType"))
    module_map: dict


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
    committee_info: list[Committee]

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
        if indata["committee_info"]:
            for intcomm in indata["committee_info"]:
                sdict = {"authority_key": intcomm[0], "staked_units": intcomm[1]}
                temp_list.append(sdict)
        indata["committee_info"] = temp_list
        return CommitteeInfo.from_dict(indata)


@dataclass
class SystemParameters(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    min_validator_stake: int
    max_validator_candidate_count: int


@dataclass
class TableVec(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    contents: dict[str, int]


@dataclass
class LinkedTableForObjectID(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    head: dict[str, list[str]]
    tail: dict[str, list[str]]
    size: int
    linked_object_id: str = field(metadata=config(field_name="id"))


@dataclass
class StakingPool(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    delegation_token_supply: Union[dict, int]
    rewards_pool: Union[dict, int]
    starting_epoch: int
    sui_balance: int
    validator_address: str
    pending_delegations: LinkedTableForObjectID
    pending_withdraws: TableVec

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        self.delegation_token_supply = self.delegation_token_supply["value"]
        self.rewards_pool = self.rewards_pool["value"]


@dataclass
class StakeSubsidy(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    balance: dict
    current_epoch_amount: int
    epoch_counter: int

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        self.balance = self.balance["value"]


# pylint: disable=too-many-instance-attributes
@dataclass
class ValidatorMetaData(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    consensus_address: list[int]
    description: list[int]
    image_url: list[int]
    project_url: list[int]
    sui_address: str
    pubkey_bytes: list[int]
    network_pubkey_bytes: list[int]
    proof_of_possession_bytes: list[int]
    name: list[int]
    net_address: list[int]
    next_epoch_stake: int
    next_epoch_delegation: int
    next_epoch_gas_price: int
    next_epoch_commission_rate: int
    worker_address: list[int]
    worker_pubkey_bytes: list[int]


@dataclass
class Validators(DataClassJsonMixin):
    """From sui_getValidators."""

    validator_metadata: list[ValidatorMetaData]

    @classmethod
    def ingest_data(cls, indata: list) -> "Validators":
        """ingest_data Ingest validators.

        :param indata: List of ValidatorMetaData objects
        :type indata: list
        :return: Instance of Validators
        :rtype: Validators
        """
        return cls.from_dict({"validator_metadata": indata})


@dataclass
class ValidatorAddressPair(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    from_address: str = field(metadata=config(field_name="from"))
    to_address: str = field(metadata=config(field_name="iconUrl"))


@dataclass
class VecMapForValidatorPairAndTableVec(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    contents: list[dict[ValidatorAddressPair, TableVec]] = field(default_factory=list)


@dataclass
class Validator(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    metadata: ValidatorMetaData
    voting_power: int
    stake_amount: int
    pending_stake: int
    pending_withdraw: int
    gas_price: int
    delegation_staking_pool: StakingPool
    commission_rate: int


@dataclass
class ValidatorSet(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    active_validators: list[Validator]  # list[Validator]
    delegation_stake: int
    next_epoch_validators: list[ValidatorMetaData]
    pending_delegation_switches: VecMapForValidatorPairAndTableVec
    pending_removals: list[int]
    pending_validators: list[Validator]
    validator_stake: int


@dataclass
class VecSetForSuiAddress(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    contents: list[str] = field(default_factory=list)


@dataclass
class ValidatorReportRecords(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    contents: list[dict[str, VecSetForSuiAddress]] = field(default_factory=list)


@dataclass
class SuiSystemState(DataClassJsonMixin):
    """From sui_getSuiSystemState."""

    epoch: int
    epoch_start_timestamp_ms: int
    info_uid: Union[dict, int] = field(metadata=config(field_name="info"))
    parameters: SystemParameters
    reference_gas_price: int
    safe_mode: bool
    stake_subsidy: StakeSubsidy
    storage_fund: Union[dict, int]
    treasury_cap: Union[dict, int]
    validator_report_records: ValidatorReportRecords
    validators: ValidatorSet

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        self.info_uid = self.info_uid["id"]
        self.storage_fund = self.storage_fund["value"]
        self.treasury_cap = self.treasury_cap["value"]


@dataclass
class StakedSui(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    delegation_request_epoch: int
    stake_id: str = field(metadata=config(field_name="id"))
    pool_starting_epoch: int
    principal: Union[dict, int]
    sui_token_lock: int
    validator_address: str

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        self.principal = self.principal["value"]
        self.stake_id = self.stake_id["id"]


@dataclass
class Delegation(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    delegation_id: dict = field(metadata=config(field_name="id"))
    pool_tokens: Union[dict, int]
    principal_sui_amount: int
    staked_sui_id: str

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        self.delegation_id = self.delegation_id["id"]
        self.pool_tokens = self.pool_tokens["value"]


@dataclass
class DelegatedStake(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    staked_sui: StakedSui
    delegation_status: Union[str, dict]

    def __post_init__(self):
        """Post hydrate parameter fixups."""
        if isinstance(self.delegation_status, dict):
            self.delegation_status = Delegation.from_dict(self.delegation_status["Active"])


@dataclass
class DelegatedStakes(DataClassJsonMixin):
    """From sui_getDelegatedStakes."""

    delegated_stakes: list[DelegatedStake]

    @classmethod
    def ingest_data(cls, in_data: list) -> "DelegatedStakes":
        """Handle multiple delegated stake results."""
        return cls.from_dict({"delegated_stakes": in_data})


@dataclass
class SuiTxnAuthSigners(DataClassJsonMixin):
    """From sui_getTransactionAuthSigners."""

    signers: list[str]


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
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    field_type: str = field(metadata=config(field_name="type"))
    version: int


@dataclass
class DynamicFields(DataClassJsonMixin):
    """From sui_getDynamicFields."""

    data: list[DynamicFieldInfo]
    next_cursor: Union[str, None] = field(metadata=config(letter_case=LetterCase.CAMEL))
