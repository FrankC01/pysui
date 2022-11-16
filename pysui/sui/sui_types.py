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


"""Sui Types."""


from abc import ABC

# import json
import base64
import binascii
import hashlib
from typing import Any, Generic, TypeVar, Union, Optional
from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin, LetterCase, config

from ..abstracts import AbstractType

from .sui_constants import SUI_ADDRESS_STRING_LEN
from .sui_txn_validator import valid_sui_address
from .sui_excepts import SuiInvalidAddress


class SuiBaseType(AbstractType):
    """Base most SUI object type."""


class SuiScalarType(SuiBaseType):
    """Base most SUI scalar type."""


class SuiString(SuiScalarType):
    """Sui String type."""

    @property
    def function(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def module(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def arguments(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def type_arguments(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def compiled_modules(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def cursor(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def move_event_struct_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def digest(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def query(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def recipient(self) -> str:
        """Alias for transactions."""
        return self.value


class SuiTxBytes(SuiString):
    """Sui Base64 tx_bytes string."""

    @property
    def tx_bytes(self) -> str:
        """Satisfy transaction verification."""
        return str(self)


class SuiSignature(SuiString):
    """Sui Base64 signature."""

    @property
    def signature(self) -> str:
        """Satisfy transaction verification."""
        return str(self)


class ObjectID(SuiString):
    """Sui Object id type."""

    def __init__(self, value: str) -> None:
        """Initialize with identifier."""
        super().__init__(value)

    @property
    def object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def object(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def package(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def package_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def sui_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def coin_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def gas(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def input_coins(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def primary_coin(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def coin_to_merge(self) -> str:
        """Alias over value."""
        return self.value


class SuiBoolean(SuiScalarType):
    """Sui Bool type."""

    @property
    def descending_order(self) -> bool:
        """Alias for transactions."""
        return self.value


class SuiInteger(SuiScalarType):
    """Sui Number type."""

    @property
    def gas_budget(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def amount(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def amounts(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def split_amounts(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def count(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def limit(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def start_time(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def end_time(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def epoch(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value


class SuiAddress(SuiBaseType):
    """Sui Address Type."""

    def __init__(self, identifier: str) -> None:
        """Initialize address."""
        identifier = identifier if len(identifier) != SUI_ADDRESS_STRING_LEN else SuiString(f"0x{identifier}")
        super().__init__(SuiString(identifier))
        # Alias for transaction validation
        self.address = identifier

    @property
    def signer(self) -> str:
        """Alias for signer in transaction validation."""
        return self.address

    @property
    def sender(self) -> str:
        """Alias for signer in transaction validation."""
        return self.address

    @property
    def recipient(self) -> str:
        """Alias for recipient in transaction validation."""
        return self.address

    @property
    def recipients(self) -> str:
        """Alias for recipients in transaction validation."""
        return self.address

    @classmethod
    def from_hex_string(cls, instr: Union[str, SuiString]) -> "SuiAddress":
        """Instantiate instance of SuiAddress from hex string."""
        instr = instr if isinstance(instr, str) else str(instr)
        if valid_sui_address(instr):
            return cls(instr)
        raise SuiInvalidAddress(f"{instr} is not a valid address string.")

    @classmethod
    def from_keypair_string(cls, keystring: str) -> "SuiAddress":
        """Address from base64 encoded keypair string with no validation."""
        return cls.from_bytes(base64.b64decode(keystring))

    @classmethod
    def from_bytes(cls, in_bytes: bytes) -> "SuiAddress":
        """Create address from bytes."""
        # print(f"In bytes = {in_bytes}")
        digest = in_bytes[0:33] if in_bytes[0] == 0 else in_bytes[0:34]
        glg = hashlib.sha3_256()
        glg.update(digest)
        hash_bytes = binascii.hexlify(glg.digest())[0:40]
        return cls(hash_bytes.decode("utf-8"))


@dataclass
class GenericRef(DataClassJsonMixin):
    """Generic object reference."""

    object_id: ObjectID = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    digest: str


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
        self.owner = self.owner["AddressOwner"]

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
    """ObjectReadData describes the data structure of type."""

    has_public_transfer: bool
    fields: dict
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: str = field(metadata=config(field_name="type"))


@dataclass
class ObjectNotExist(DataClassJsonMixin):
    """ObjectNotExist."""

    object_id: str

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectDeleted(DataClassJsonMixin):
    """ObjectDeleted."""

    reference: GenericRef

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return self.reference.object_id


@dataclass
class AddressOwner(DataClassJsonMixin):
    """AddressOwner owner type."""

    owner_type: str
    address_owner: str = field(metadata=config(field_name="owner"))


@dataclass
class ObjectOwner(DataClassJsonMixin):
    """ObjectOwner owner type."""

    owner_type: str
    object_owner: str = field(metadata=config(field_name="owner"))


@dataclass
class SharedOwner(DataClassJsonMixin):
    """SharedOwner owner type."""

    owner_type: str
    initial_shared_version: int


@dataclass
class ImmutableOwner(DataClassJsonMixin):
    """ImmutableOwner owner type."""


@dataclass
class ObjectRead(DataClassJsonMixin):
    """DObjectRead is base ObjectRead result."""

    data: ObjectReadData
    owner: dict
    reference: GenericRef
    storage_rebate: int = field(metadata=config(field_name="storageRebate"))
    previous_transaction: str = field(metadata=config(field_name="previousTransaction"))

    def __post_init__(self):
        """Post init processing for parameters."""
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
        return ObjectID(self.data.fields["id"]["id"])

    @property
    def version(self) -> int:
        """Alias object_id."""
        return self.reference.version

    @property
    def digest(self) -> str:
        """Alias object_id."""
        return self.reference.digest

    @property
    def type_signature(self) -> str:
        """Alias object_id."""
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
        # print(indata)
        read_object = indata["details"]
        match indata["status"]:
            case "Exists":
                split = read_object["data"]["type"].split("::", 2)
                if split[0] == "0x2":
                    match split[1]:
                        case "coin":
                            split2 = split[2][5:-1].split("::")
                            if split2[2] == "SUI":
                                return SuiGas.from_dict(read_object)
                            return SuiCoin.from_dict(read_object)
                        case _:
                            return SuiData.from_dict(read_object)
                else:
                    return SuiData.from_dict(read_object)
            case "NotExists":
                return ObjectNotExist.from_dict({"object_id": read_object})
            case "Deleted":
                return ObjectDeleted.from_dict({"reference": read_object})

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
class SuiData(ObjectRead):
    """DSuiData is object that is not coins.

    :param DObjectRead: superclass
    :type DObjectRead: DObjectRead
    :return: Instance of DSuiData
    :rtype: DSuiData
    """


@dataclass
class SuiCoin(ObjectRead):
    """DSuiCoinType is the generic coin.

    :param DObjectRead: superclass
    :type DObjectRead: DObjectRead
    :return: Instance of DSuiCoin
    :rtype: DSuiCoin
    """

    @property
    def balance(self) -> int:
        """balance returns the balance of coin<type> for this object.

        :return: balance value
        :rtype: int
        """
        return self.data.fields["balance"]


@dataclass
class SuiGas(SuiCoin):
    """DSuiGasType is SUI Gas coin.

    :param DSuiCoin: superclass
    :type DSuiCoin: DSuiCoin
    :return: Instance of DSuiGas
    :rtype: DSuiGas
    """


# Committee


@dataclass
class Committee(DataClassJsonMixin):
    """Committee detail."""

    authority_key: str
    staked_units: int


@dataclass
class CommitteeInfo(DataClassJsonMixin):
    """Committee Info."""

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


# Collection types


class SuiCollection(SuiBaseType):
    """Generic Collection Type."""


AT = TypeVar("AT", SuiAddress, ObjectID, SuiInteger, SuiString)


class SuiArray(SuiCollection, Generic[AT]):
    """Array type."""

    def __init__(self, array: list[AT]) -> None:
        """Initialize collection."""
        super().__init__(None)
        self.array = array if array else list[AT]()

    def append(self, item: AT) -> list[AT]:
        """Append and item to array."""
        self.array.append(item)
        return self.array

    def extend(self, items: list[AT]) -> list[AT]:
        """Append and item to array."""
        self.array.extend(items)
        return self.array

    @property
    def input_coins(self) -> list[ObjectID]:
        """Alias for transactions."""
        return self.array

    @property
    def recipients(self) -> list[SuiAddress]:
        """Alias for transactions."""
        return self.array

    @property
    def amounts(self) -> list[SuiInteger]:
        """Alias for transactions."""
        return self.array

    @property
    def split_amounts(self) -> list[SuiInteger]:
        """Alias for transactions."""
        return self.array

    @property
    def type_arguments(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array

    @property
    def arguments(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array

    @property
    def compiled_modules(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array


class SuiMap(SuiCollection):
    """Dictionary Type."""

    def __init__(self, key: str, value: Any) -> None:
        """Initialize collection."""
        super().__init__(None)
        self.map = {key: value}

    def add_kv_pair(self, key: str, value: Any) -> "SuiMap":
        """Add key value pair to map."""
        self.map[key] = value
        return self

    @property
    def cursor(self) -> dict:
        """Alias for query."""
        return self.map

    @property
    def recipient(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map

    @property
    def query(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map


class EventID(SuiMap):
    """Event ID specifier."""

    def __init__(self, event_seq: int, tx_seq: int):
        """Initialize EventID."""
        super().__init__("eventSeq", event_seq)
        self.map["txSeq"] = tx_seq


def address_from_keystring(indata: str) -> SuiAddress:
    """From a 88 byte keypair string create a SuiAddress."""
    #   Check address is legit keypair
    from .sui_crypto import keypair_from_keystring

    _kp = keypair_from_keystring(indata)
    #   decode from base64 and generate
    return SuiAddress.from_bytes(base64.b64decode(indata))


# Transaction Results


class SuiTxReturnType(ABC):
    """Abstraction for all return objects."""


@dataclass
class CoinRef(GenericRef):
    """Coin representation."""


@dataclass
class PackageRef(GenericRef):
    """Package representation."""


@dataclass
class GenericOwnerRef(SuiTxReturnType, DataClassJsonMixin):
    """Owned coin referenece."""

    reference: GenericRef
    owner: Union[dict, str] = field(default_factory=str)

    def __post_init__(self):
        """Post init processing.

        Convert owner to Address (based on result)
        """
        if isinstance(self.owner, str):
            self.owner = self.owner
        else:
            self.owner = self.owner["AddressOwner"]


@dataclass
class MoveCallTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_moveCall transaction."""

    function: str
    module: str
    package: PackageRef
    arguments: Optional[list[str]] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=list)
    type_arguments: Optional[list[str]] = field(metadata=config(letter_case=LetterCase.CAMEL), default_factory=list)


@dataclass
class PayTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_pay transaction."""

    coins: list[CoinRef]
    amounts: list[int]
    recipients: list[str]


@dataclass
class PayAllSuiTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_payAllSui transaction."""

    coins: list[CoinRef]
    recipient: str


@dataclass
class PaySuiTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_paySui transaction."""

    coins: list[CoinRef]
    amounts: list[int]
    recipients: list[str]


@dataclass
class PublishTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_publish transaction."""

    disassembled: dict[str, str]


@dataclass
class TransferObjectTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_transferObject transaction."""

    object_ref: GenericRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    recipient: str


@dataclass
class TransferSuiTx(SuiTxReturnType, DataClassJsonMixin):
    """sui_transferSui transaction."""

    recipient: str
    amount: int


@dataclass
class AuthSignerInfo(SuiTxReturnType, DataClassJsonMixin):
    """Authorized signer info."""

    epoch: int
    signature: str
    signers_map: list[int]


_TRANSACTION_LOOKUP = {
    "Call": MoveCallTx,
    "Pay": PayTx,
    "PaySui": PaySuiTx,
    "PayAllSui": PayAllSuiTx,
    "Publish": PublishTx,
    "TransferObject": TransferObjectTx,
    "TransferSui": TransferSuiTx,
}


@dataclass
class TransactionData(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Data."""

    sender: str
    gas_payment: CoinRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_budget: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    transactions: list[Any] = None

    def __post_init__(self):
        """Post init processing.

        Loops through the transactions list to resolve hydrating different transaction type classes
        """
        hydrated = []
        for tx_dict in self.transactions:
            key = list(tx_dict.keys())[0]
            hydrated.append(_TRANSACTION_LOOKUP[key].from_dict(tx_dict[key]))
        self.transactions = hydrated


# Events


@dataclass
class CoinBalanceChangeEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    owner: dict
    change_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    coin_object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    amount: int

    def __post_init__(self):
        """Post init processing.

        Convert various to SuiTypes
        """
        self.owner = self.owner["AddressOwner"]


@dataclass
class NewObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    recipient: Union[dict, str]
    version: int
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing.

        Convert various to SuiTypes
        """
        if isinstance(self.recipient, str):
            if self.recipient == "Immutable":
                self.recipient = self.recipient
        else:
            self.recipient = self.recipient["AddressOwner"]


@dataclass
class TransferObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    recipient: dict
    version: int
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))

    def __post_init__(self):
        """Post init processing.

        Convert various to SuiTypes
        """
        self.recipient = self.recipient["AddressOwner"]


@dataclass
class MutateObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    object_type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int


@dataclass
class DeleteObjectEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    object_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int


@dataclass
class EpochChangeEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    epoch_change: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class NewCheckpointEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    checkpoint: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class PublishEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str


_EVENT_LOOKUP = {
    "coinBalanceChange": CoinBalanceChangeEvent,
    "newObject": NewObjectEvent,
    "transferObject": TransferObjectEvent,
    "mutateObject": MutateObjectEvent,
    "deleteObject": DeleteObjectEvent,
    "epochChange": EpochChangeEvent,
    "newCheckPoint": NewCheckpointEvent,
    "publish": PublishEvent,
}


@dataclass
class GasCostSummary(SuiTxReturnType, DataClassJsonMixin):
    """Gas used."""

    computation_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_cost: int = field(metadata=config(letter_case=LetterCase.CAMEL))
    storage_rebate: int = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class Status(SuiTxReturnType, DataClassJsonMixin):
    """Status of transaction."""

    status: str
    error: Optional[str] = None
    succeeded: bool = field(init=False)

    def __post_init__(self):
        """Post init processing."""
        self.succeeded = self.status == "success"


@dataclass
class Effects(SuiTxReturnType, DataClassJsonMixin):
    """Effects Certification."""

    status: Status
    gas_used: GasCostSummary = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    gas_object: GenericOwnerRef = field(metadata=config(letter_case=LetterCase.CAMEL))
    events: list[dict]
    dependencies: list[str] = field(default_factory=list)
    mutated: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    created: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    deleted: Optional[list[GenericRef]] = field(default_factory=list)
    wrapped: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    unwrapped: Optional[list[GenericOwnerRef]] = field(default_factory=list)
    shared_objects: Optional[list[GenericOwnerRef]] = field(
        metadata=config(letter_case=LetterCase.CAMEL), default_factory=list
    )

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events and other types
        """
        hydrated = []
        for ev_dict in self.events:
            key = list(ev_dict.keys())[0]
            hydrated.append({key: _EVENT_LOOKUP[key].from_dict(ev_dict[key])})
        self.events = hydrated


@dataclass
class EffectsBlock(SuiTxReturnType, DataClassJsonMixin):
    """Effects Block."""

    transaction_effects_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    effects: Effects
    auth_sign_info: AuthSignerInfo = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class Certificate(SuiTxReturnType, DataClassJsonMixin):
    """Effects Certification."""

    transaction_digest: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    data: TransactionData
    tx_signature: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    auth_sign_info: AuthSignerInfo = field(metadata=config(letter_case=LetterCase.CAMEL))


@dataclass
class EffectsCertTx(SuiTxReturnType, DataClassJsonMixin):
    """Effects Certification."""

    certificate: Certificate
    effects: EffectsBlock
    confirmed_local_execution: bool


@dataclass
class TxEffectResult(SuiTxReturnType, DataClassJsonMixin):
    """Transaction Result."""

    effects_cert: EffectsCertTx = field(metadata=config(field_name="EffectsCert"))

    @property
    def succeeded(self) -> bool:
        """Check if transaction result is successful."""
        return self.effects_cert.effects.effects.status.succeeded

    @property
    def status(self) -> str:
        """Get underlying status string."""
        if self.succeeded:
            return "success"
        return f"{self.effects_cert.effects.effects.status.status} - {self.effects_cert.effects.effects.status.error}"


# Event query results


@dataclass
class EventEnvelopID(DataClassJsonMixin):
    """From getEvents."""

    transaction_sequence: int = field(metadata=config(field_name="txSeq"))
    event_sequence: int = field(metadata=config(field_name="eventSeq"))


@dataclass
class EventEnvelope(DataClassJsonMixin):
    """From getEvents."""

    timestamp: int
    transaction_digest: str = field(metadata=config(field_name="txDigest"))
    event_id: EventEnvelopID = field(metadata=config(field_name="id"))
    event: dict

    def __post_init__(self):
        """Post init processing.

        Hydrate relevant Events and other types
        """
        ev_map = list(self.event.items())
        event_key = ev_map[0][0]
        event_value = ev_map[0][1]
        self.event[event_key] = _EVENT_LOOKUP[event_key].from_dict(event_value)


@dataclass
class EventQueryEnvelope(DataClassJsonMixin):
    """From getEvents."""

    data: list[EventEnvelope]
    next_cursor: Union[None, EventID] = field(metadata=config(field_name="nextCursor"))


@dataclass
class TransactionQueryEnvelope(DataClassJsonMixin):
    """From getTransactions."""

    data: list[str]
    next_cursor: Union[None, dict] = field(metadata=config(field_name="nextCursor"))


# Packages


@dataclass
class MoveModuleId(DataClassJsonMixin):
    """From getNormalized."""

    address: str
    name: str


@dataclass
class MoveStructReference(DataClassJsonMixin):
    """From getNormalized."""

    address: str
    module: str
    name: str
    type_arguments: list["MoveStructReference"] = field(default_factory=list)


@dataclass
class MoveStructField(DataClassJsonMixin):
    """From getNormalized."""

    name: str
    type_: Union[str, dict[str, MoveStructReference]]  # = field(default_factory=list)

    def __post_init__(self):
        """Post init processing for field_type."""


@dataclass
class MoveStructAbilities(DataClassJsonMixin):
    """From getNormalized."""

    abilities: list[str]

    def __post_init__(self):
        """Post init processing for field_type."""


@dataclass
class MoveStruct(DataClassJsonMixin):
    """From getNormalized."""

    abilities: MoveStructAbilities
    fields: list[MoveStructField]
    type_parameters: list[Union[str, dict]]

    def __post_init__(self):
        """Post init processing for type parameters."""


@dataclass
class MoveFunction(DataClassJsonMixin):
    """From getNormalized."""

    visibility: str
    is_entry: bool
    type_parameters: list[str]
    parameters: list[Union[str, dict]]
    return_: list[str]

    def __post_init__(self):
        """Post init processing for parameters."""


@dataclass
class MoveModule(DataClassJsonMixin):
    """From getNormalized."""

    name: str
    address: str
    file_format_version: int
    friends: list[MoveModuleId]
    structs: dict[str, MoveStruct]
    exposed_functions: dict[str, MoveFunction]

    def __post_init__(self):
        """Post init processing for parameters."""


@dataclass
class MovePackage(DataClassJsonMixin):
    """From getNormalized."""

    modules: dict[str, MoveModule]

    @classmethod
    def ingest_data(cls, indata: dict) -> "MovePackage":
        """Ingest from external call."""
        return cls.from_dict({"modules": indata})
