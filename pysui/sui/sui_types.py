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


from abc import abstractmethod, ABC
import json
import base64
import binascii
import hashlib
from numbers import Number
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
    def move_event_struct_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def digest(self) -> str:
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


class SuiNumber(SuiScalarType):
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


class SuiRawDescriptor(SuiBaseType):
    """Base descriptor type."""

    def __init__(self, indata: dict, identifier: ObjectID) -> None:
        """Initiate base SUI type."""
        super().__init__(identifier)
        self._type_raw = indata

    @property
    @abstractmethod
    def version(self) -> Number:
        """Return the types version."""

    @property
    @abstractmethod
    def owner(self) -> str:
        """Return the types instance owner."""

    @property
    @abstractmethod
    def type_signature(self) -> str:
        """Return the types type."""

    def json(self) -> str:
        """Return as JSON compressed string."""
        return json.dumps(self._type_raw)

    def json_pretty(self, indent: int = 4) -> str:
        """Return as JSON pretty print string."""
        return json.dumps(self._type_raw, indent=indent)


class ObjectInfo(SuiRawDescriptor):
    """Base SUI Type Descriptor."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base descriptor."""
        super().__init__(indata, ObjectID(indata["objectId"]))
        self._version: int = indata["version"]
        self._digest: str = indata["digest"]
        self._owner: SuiAddress = SuiAddress.from_hex_string(indata["owner"]["AddressOwner"])
        self._previous_transaction: str = indata["previousTransaction"]
        self._type_signature: str = indata["type"]

    @property
    def version(self) -> int:
        """Return the types version."""
        return self._version

    @property
    def digest(self) -> str:
        """Return the type digest."""
        return self._digest

    @property
    def owner(self) -> SuiAddress:
        """Return the types instance owner."""
        return self._owner

    @property
    def previous_transaction(self) -> str:
        """Return the previous transaction base64 signature string."""
        return self._previous_transaction

    @property
    def type_signature(self) -> str:
        """Return the types type."""
        return self._type_signature


class SuiDataDescriptor(ObjectInfo):
    """Sui Data base type."""


class SuiNftDescriptor(ObjectInfo):
    """Sui NFT base type."""


class SuiCoinDescriptor(ObjectInfo):
    """Sui Coin but not necessarily gas."""

    def __init__(self, indata: dict, type_sig: str) -> None:
        """Initialize the base type."""
        super().__init__(indata)
        self._type_signature = type_sig


class SuiNativeCoinDescriptor(SuiCoinDescriptor):
    """Sui gas is a coin."""


class SuiRawObject(SuiBaseType):
    """Base object type."""

    def __init__(self, indata: dict, identifier: ObjectID) -> None:
        """Initiate base SUI type."""
        super().__init__(identifier)
        self._type_raw = indata

    @property
    @abstractmethod
    def data_type(self) -> str:
        """Return the data type."""

    @property
    @abstractmethod
    def type_signature(self) -> str:
        """Return the type signature."""

    @property
    @abstractmethod
    def has_public_transfer(self) -> bool:
        """Return the types type."""

    def json(self) -> str:
        """Return as JSON compressed string."""
        return json.dumps(self._type_raw)

    def json_pretty(self, indent: int = 4) -> str:
        """Return as JSON pretty print string."""
        return json.dumps(self._type_raw, indent=indent)


# Object Details


class ObjectRead(SuiRawObject):
    """Base SUI Type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base type data."""
        super().__init__(indata, ObjectID(indata["fields"]["id"]["id"]))
        self._type_signature = indata["type"]
        self._data_type = indata["dataType"]
        self._has_public_transfer = indata["has_public_transfer"]
        self._owner: SuiAddress = SuiAddress.from_hex_string(indata["owner"]["AddressOwner"])
        self._previous_transaction = indata["previousTransaction"]
        self._storage_rebate = indata["storageRebate"]
        self._digest = indata["digest"]
        self._version = indata["version"]

    @property
    def version(self) -> int:
        """Return the types version."""
        return self._version

    @property
    def digest(self) -> str:
        """Return the types digest."""
        return self._digest

    @property
    def data_type(self) -> str:
        """Return the data type."""
        return self._data_type

    @property
    def type_signature(self) -> str:
        """Return the types type."""
        return self._type_signature

    @property
    def has_public_transfer(self) -> bool:
        """Return the types transferability."""
        return self._has_public_transfer

    @property
    def owner(self) -> SuiAddress:
        """Return the types instance owner."""
        return self._owner

    @property
    def previous_transaction(self) -> str:
        """Return the previous transaction base64 signature string."""
        return self._previous_transaction

    @property
    def storage_rebate(self) -> int:
        """Return the storage rebate if object deleted."""
        return self._storage_rebate


class SuiNftType(ObjectRead):
    """Sui NFT base type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base Nft type."""
        super().__init__(indata)
        self._description = indata["fields"]["description"]
        self._name = indata["fields"]["name"]
        self._url = indata["fields"]["url"]

    @property
    def name(self) -> str:
        """Get name for Nft."""
        return self._name

    @property
    def description(self) -> str:
        """Get description for Nft."""
        return self._description

    @property
    def url(self) -> str:
        """Get Url for Nft."""
        return self._url


DT = TypeVar("DT", bound="SuiDataType")


class SuiDataType(ObjectRead):
    """Sui Data type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base Data type."""
        super().__init__(indata)
        self._children = []
        self._data = {}
        split = self.type_signature.split("::", 2)
        self._data_definition = dict(zip(["package", "module", "structure"], split))
        for key, value in indata["fields"].items():
            if not key == "id":
                self._data[key] = value

    @property
    def data_definition(self) -> dict:
        """Get the data definition meta data."""
        return self._data_definition

    @property
    def package(self) -> str:
        """Get the data objects owning package id."""
        return self.data_definition["package"]

    @property
    def module(self) -> str:
        """Get the data objects owning module id."""
        return self.data_definition["module"]

    @property
    def structure(self) -> str:
        """Get the data objects structure id."""
        return self.data_definition["structure"]

    @property
    def data(self) -> dict:
        """Get the actual objects data."""
        return self._data

    @property
    def children(self) -> list[DT]:
        """Get the children of this data."""
        return self._children

    def add_child(self, child: DT) -> None:
        """Store data child owned by self."""
        self.children.append(child)


class SuiCoinType(ObjectRead):
    """Sui Coin type but not necessarily gas type."""

    def __init__(self, indata: dict, type_sig: str) -> None:
        """Initialize the base type."""
        super().__init__(indata)
        self._type_signature = type_sig


class SuiGasType(SuiCoinType):
    """Sui gas is a coin."""

    def __init__(self, indata: dict, type_sig: str) -> None:
        """Initialize the base type."""
        super().__init__(indata, type_sig)
        self._balance = indata["fields"]["balance"]

    @property
    def balance(self) -> Number:
        """Get the balance for this coin object."""
        return self._balance


# Collection types


class SuiCollection(SuiBaseType):
    """Generic Collection Type."""


AT = TypeVar("AT", SuiAddress, ObjectID, SuiNumber, SuiString)


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
    def amounts(self) -> list[SuiNumber]:
        """Alias for transactions."""
        return self.array

    @property
    def split_amounts(self) -> list[SuiNumber]:
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

    @property
    def recipient(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map


# Package Type


class SuiRawPackage(SuiBaseType):
    """Sui package object."""

    def __init__(self, indata: dict) -> None:
        """Initialize a package construct."""
        super().__init__(ObjectID(indata["reference"]["objectId"]))
        self._data_type: str = indata["data"]["dataType"]
        self._modules: dict = indata["data"]["disassembled"]
        self._owner: SuiAddress = SuiAddress.from_hex_string(indata["owner"])
        self._previous_transaction = indata["previousTransaction"]
        self._storage_rebate: int = indata["storageRebate"]
        self._digest = indata["reference"]["digest"]
        self._version: int = indata["reference"]["version"]

    @property
    def data_type(self) -> str:
        """Return the type."""
        return self._data_type

    @property
    def modules(self) -> dict:
        """Return the package modules."""
        return self._modules

    @property
    def module_names(self) -> list[str]:
        """Return the package module names."""
        return list(self.modules.keys())

    @property
    def owner(self) -> SuiAddress:
        """Return the type."""
        return self._owner

    @property
    def previous_transaction(self) -> str:
        """Return the type."""
        return self._previous_transaction

    @property
    def storage_rebate(self) -> int:
        """Return the storage rebate if object deleted."""
        return self._storage_rebate

    @property
    def version(self) -> int:
        """Return the package version."""
        return self._version

    @property
    def digest(self) -> str:
        """Return the package digest."""
        return self._digest


def address_from_keystring(indata: str) -> SuiAddress:
    """From a 88 byte keypair string create a SuiAddress."""
    #   Check address is legit keypair
    from .sui_crypto import keypair_from_keystring

    _kp = keypair_from_keystring(indata)
    #   decode from base64 and generate
    return SuiAddress.from_bytes(base64.b64decode(indata))


def from_object_descriptor(indata: dict) -> ObjectInfo:
    """Parse an inbound JSON like dictionary to a Sui type."""
    # print(f"ObjectInfo {json.dumps(indata, indent=2)}")
    split = indata["type"].split("::", 2)
    if split[0] == "0x2":
        match split[1]:
            case "coin":
                split2 = split[2][5:-1].split("::")
                type_sig = "::".join(split2)
                if split2[2] == "SUI":
                    return SuiNativeCoinDescriptor(indata, type_sig)
                return SuiCoinDescriptor(indata, type_sig)
            case "devnet_nft":
                if split[2] == "DevNetNFT":
                    return SuiNftDescriptor(indata)
    else:
        if len(split) == 3:
            return SuiDataDescriptor(indata)

    return ObjectInfo(indata)


def from_object_type(inblock: dict) -> ObjectRead:
    """Parse an inbound JSON like dictionary to a Sui type."""
    # print(f"ObjectRead {json.dumps(indata, indent=2)}")
    indata = inblock["data"]
    match indata["dataType"]:
        case "moveObject":
            indata["previousTransaction"] = inblock["previousTransaction"]
            indata["storageRebate"] = inblock["storageRebate"]
            indata["digest"] = inblock["reference"]["digest"]
            indata["version"] = inblock["reference"]["version"]
            indata["owner"] = inblock["owner"]
            split = indata["type"].split("::", 2)

            if split[0] == "0x2":
                match split[1]:
                    case "coin":
                        split2 = split[2][5:-1].split("::")
                        type_sig = "::".join(split2)
                        if split2[2] == "SUI":
                            return SuiGasType(indata, type_sig)
                        return SuiCoinType(indata, type_sig)
                    case "devnet_nft":
                        if split[2] == "DevNetNFT":
                            return SuiNftType(indata)
            else:
                if len(split) == 3:
                    return SuiDataType(indata)
            return ObjectRead(indata)
        case "package":
            return SuiRawPackage(inblock)
        case _:
            raise ValueError(f"Don't recognize {indata['dataType']}")


# Transaction Results


class SuiTxReturnType(ABC):
    """Abstraction for all return objects."""


@dataclass
class GenericRef(SuiTxReturnType, DataClassJsonMixin):
    """Generic object reference."""

    object_id: ObjectID = field(metadata=config(letter_case=LetterCase.CAMEL))
    version: int
    digest: str


@dataclass
class CoinRef(GenericRef):
    """Coin representation."""


@dataclass
class PackageRef(GenericRef):
    """Package representation."""


@dataclass
class GenericOwnerRef(SuiTxReturnType, DataClassJsonMixin):
    """Owned coin referenece."""

    owner: Union[dict, str]
    reference: GenericRef

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
    arguments: list[str]
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
    deleted: Optional[list[GenericOwnerRef]] = field(default_factory=list)
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
            hydrated.append(_EVENT_LOOKUP[key].from_dict(ev_dict[key]))
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
