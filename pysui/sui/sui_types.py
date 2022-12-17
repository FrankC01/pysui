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
import re

# import json
import base64
import binascii
import hashlib
from typing import Any, Generic, TypeVar, Union, Optional
from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin, LetterCase, config

from pysui.abstracts import AbstractType
from pysui.sui.sui_constants import SUI_ADDRESS_STRING_LEN, SUI_HEX_ADDRESS_STRING_LEN
from pysui.sui.sui_excepts import SuiInvalidAddress

__partstring_pattern: re.Pattern = re.compile(r"[0-9a-fA-F]{38}")
__fullstring_pattern: re.Pattern = re.compile(r"0[xX][0-9a-fA-F]{40}")


def valid_sui_address(instr: str) -> bool:
    """Verify Sui address string."""
    inlen = len(instr)
    match instr:
        case "0x2" | "Immutable":
            return True
        case _:
            if inlen > SUI_HEX_ADDRESS_STRING_LEN or inlen < SUI_ADDRESS_STRING_LEN:
                return False
            # _kp = keypair_from_keystring(instr)
            if inlen == SUI_HEX_ADDRESS_STRING_LEN and __fullstring_pattern.findall(instr):
                return True
            return __partstring_pattern.findall(instr)


class SuiBaseType(AbstractType):
    """Base most SUI object type."""

    def __init__(self, identifier: Any) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A native python type
        :type identifier: Any
        """
        super().__init__(identifier)


class SuiNullType(SuiBaseType):
    """SuiNullType A null type.

    :param SuiBaseType: Super class
    :type SuiBaseType: _type_
    :return: _description_
    :rtype: SuiNullType
    """

    def __init__(self, identifier: Any) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A native python type
        :type identifier: Any
        """
        super().__init__(None)

    @property
    def limit(self) -> Any:
        """Alias for transactions."""
        return self.value

    @property
    def cursor(self) -> Any:
        """Alias for transactions."""
        return self.value


class SuiScalarType(SuiBaseType):
    """Base most SUI scalar type."""

    def __init__(self, identifier: Any) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A native python type
        :type identifier: Any
        """
        super().__init__(identifier)


class SuiString(SuiScalarType):
    """Sui String type."""

    def __init__(self, identifier: str) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A python str
        :type identifier: str
        """
        super().__init__(identifier)

    @property
    def function(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def function_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def module(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def module_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def struct_name(self) -> str:
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

    @property
    def coin_type(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def limit(self) -> str:
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


class SuiTransactionDigest(SuiString):
    """Sui Base58 digest."""

    @property
    def digest(self) -> str:
        """Alias for transaction."""
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

    def __init__(self, value: int) -> None:
        """Initialize type."""
        super().__init__(value)

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

    @property
    def version(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value

    @property
    def split_count(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value


class SuiAddress(SuiBaseType):
    """Sui Address Type."""

    def __init__(self, identifier: Union[SuiString, str]) -> None:
        """Initialize address."""
        testvalid: str = identifier if isinstance(identifier, str) else identifier.value
        if valid_sui_address(testvalid):
            testvalid = testvalid if testvalid.startswith("0x") else format(f"0x{testvalid}")
            super().__init__(SuiString(testvalid))
        else:
            raise ValueError(f"{testvalid} is not valid address string")
        # Alias for transaction validation
        self.address = testvalid

    @property
    def signer(self) -> str:
        """Alias for signer in transaction validation."""
        return self.address

    @property
    def owner(self) -> str:
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
    type_arg: str = field(default_factory=str)

    def __post_init__(self):
        """Post init processing for parameters."""
        ref = self.type_.split("<")
        if len(ref) > 1:
            self.type_arg = ref[1][:-1]
        if "id" in self.fields:
            self.fields["id"] = self.fields["id"]["id"]


@dataclass
class ObjectPackageReadData(DataClassJsonMixin):
    """ObjectPackageReadData describes the data structure of package."""

    disassembled: dict
    data_type: str = field(metadata=config(field_name="dataType"))
    type_: Optional[str] = ""

    def __post_init__(self):
        """Post init processing for parameters."""
        self.type_ = self.data_type


@dataclass
class ObjectNotExist(DataClassJsonMixin):
    """ObjectNotExist."""

    object_id: str
    object_state: str = "Object does not exist."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectVersionNotFound(DataClassJsonMixin):
    """ObjectNotExist."""

    object_id: str
    version_requested: int
    object_state: str = "Object version not found."

    @property
    def identifier(self) -> ObjectID:
        """Alias object_id."""
        return ObjectID(self.object_id)


@dataclass
class ObjectVersionTooHigh(DataClassJsonMixin):
    """ObjectVersionTooHigh."""

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
    """ObjectDeleted."""

    reference: GenericRef
    object_state: str = "Object has been deleted."

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
    """ObjectRead is base ObjectRead result."""

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

    @property
    def single_transaction_params(self) -> list[dict]:
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


@dataclass
class MoveEvent(SuiTxReturnType, DataClassJsonMixin):
    """Event Type."""

    package_id: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    transaction_module: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    sender: str
    type: str = field(metadata=config(letter_case=LetterCase.CAMEL))
    bcs: str
    fields: dict


_EVENT_LOOKUP = {
    "coinBalanceChange": CoinBalanceChangeEvent,
    "newObject": NewObjectEvent,
    "transferObject": TransferObjectEvent,
    "mutateObject": MutateObjectEvent,
    "deleteObject": DeleteObjectEvent,
    "epochChange": EpochChangeEvent,
    "newCheckPoint": NewCheckpointEvent,
    "publish": PublishEvent,
    "moveEvent": MoveEvent,
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


class SuiMoveType:
    """SuiMoveType is a factory of generalized Normalized types."""

    @classmethod
    def resolve(cls, parm: Union[str, dict]) -> DataClassJsonMixin:
        """resolve Dispatches data loaders based on parm dictionary.

        :param parm: A dictionary containing a SuiMoveNormalizedType
        :type parm: dict
        :raises ValueError: Type signature is an unknown type
        :return: A pysui Sui data object
        :rtype: DataClassJsonMixin
        """
        if isinstance(parm, str):
            return SuiMoveScalarArgument.from_dict({"scalar_type": parm})
        match_key = list(parm.keys())[0]
        match match_key:
            case "Reference" | "MutableReference":
                parm["reference_type"] = match_key
                parm["reference_to"] = parm[match_key]
                parm.pop(match_key)
                result = SuiParameterReference.from_dict(parm)
            case "Struct":
                result = SuiParameterStruct.from_dict(parm[match_key])
            case "TypeParameter":
                result = SuiMoveParameterType.from_dict(parm)
            case "Vector":
                vmapper = {"vector_of": parm[match_key]}
                result = SuiMoveVector.from_dict(vmapper)
            case _:
                raise ValueError(f"Unknown handler for {match_key}")
        return result


# Sui Normalized Data Types


@dataclass
class SuiMoveField(DataClassJsonMixin):
    """From getNormalized."""

    name: str
    type_: Union[str, dict]  # = field(default_factory=list)

    def __post_init__(self):
        """Post init processing for field_type."""
        if isinstance(self.type_, dict):
            self.type_ = SuiMoveType.resolve(self.type_)


@dataclass
class SuiMoveAbilitySet(DataClassJsonMixin):
    """From getNormalized."""

    abilities: list[str]

    def __post_init__(self):
        """Post init processing for field_type."""


@dataclass
class SuiMoveStructTypeParameter(DataClassJsonMixin):
    """From getNormalized."""

    constraints: SuiMoveAbilitySet
    is_phantom: bool = False


@dataclass
class SuiMoveStruct(DataClassJsonMixin):
    """From getNormalized."""

    abilities: SuiMoveAbilitySet
    fields: list[SuiMoveField]
    type_parameters: list[SuiMoveStructTypeParameter]

    def __post_init__(self):
        """Post init processing for type parameters."""

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMoveStruct":
        """ingest_data Ingest results of direct call to `sui_getNormalizedMoveStruct`.

        :param indata: Dictionary containing structure defintion
        :type indata: dict
        :return: Instance of SuiMoveStruct
        :rtype: SuiMoveFunction
        """
        return SuiMoveStruct.from_dict(indata)


@dataclass
class SuiMoveVector(DataClassJsonMixin):
    """From getNormalized."""

    vector_of: Union[str, dict]  # list[str] = field(default_factory=list)

    def __post_init__(self):
        """Post init."""
        if isinstance(self.vector_of, dict):
            self.vector_of = SuiMoveType.resolve(self.vector_of)


@dataclass
class SuiMoveParameterType(DataClassJsonMixin):
    """From getNormalized."""

    type_parameters_index: int = field(metadata=config(field_name="TypeParameter"), default_factory=None)


@dataclass
class SuiParameterStruct(DataClassJsonMixin):
    """From getNormalize."""

    address: str
    module: str
    name: str
    type_arguments: list[Any]

    def __post_init__(self):
        """Post init."""
        if self.type_arguments:
            new_type_ars = []
            for type_arg in self.type_arguments:
                new_type_ars.append(SuiMoveType.resolve(type_arg))
            self.type_arguments = new_type_ars


@dataclass
class SuiParameterReference(DataClassJsonMixin):
    """From getNormalize."""

    reference_type: str
    reference_to: dict
    is_mutable: bool = False

    def __post_init__(self):
        """Post init."""
        self.is_mutable = self.reference_type == "MutableReference"
        if self.reference_to:
            self.reference_to = SuiMoveType.resolve(self.reference_to)


@dataclass
class SuiMoveScalarArgument(DataClassJsonMixin):
    """From getNormalized."""

    scalar_type: str


@dataclass
class SuiMoveFunctionArgumentTypes(DataClassJsonMixin):
    """From getNormalized."""

    arg_list: list[Union[str, dict[str, str]]]

    @classmethod
    def ingest_data(cls, indata: list) -> "SuiMoveFunctionArgumentTypes":
        """ingest_data Ingest results of calling `sui_getMoveFunctionArgTypes`.

        :param indata: list containing function argument types
        :type indata: list
        :return: Instance of SuiMoveFunctionArgumentTypes
        :rtype: SuiMoveFunctionArgumentTypes
        """
        return SuiMoveFunctionArgumentTypes.from_dict({"arg_list": indata})


@dataclass
class SuiMoveFunction(DataClassJsonMixin):
    """From getNormalized."""

    visibility: str
    is_entry: bool
    type_parameters: list[SuiMoveAbilitySet]
    parameters: list[Union[str, dict]]
    returns: list[Union[str, dict]] = field(metadata=config(field_name="return_"), default_factory=list)

    def __post_init__(self):
        """Post init processing for parameters and returns."""
        # Transition parameters
        new_parms = []
        for parm in self.parameters:
            new_parms.append(SuiMoveType.resolve(parm))
            # if isinstance(parm, dict):
            #     new_parms.append(SuiMoveType.resolve(parm))
            # else:
            #     new_parms.append(parm)
        self.parameters = new_parms
        # Transition returns
        new_rets = []
        for parm in self.returns:
            new_rets.append(SuiMoveType.resolve(parm))
            # if isinstance(parm, dict):
            #     new_rets.append(SuiMoveType.resolve(parm))
            # else:
            #     new_rets.append(parm)
        self.returns = new_rets

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMoveFunction":
        """ingest_data Ingest results of calling `sui_getNormalizedMoveFunction`.

        :param indata: Dictionary containing function defintion
        :type indata: dict
        :return: Instance of SuiMoveFunction
        :rtype: SuiMoveFunction
        """
        return SuiMoveFunction.from_dict(indata)


# Module module information type
@dataclass
class SuiMoveModuleId(DataClassJsonMixin):
    """MoveModuleId Is a reference to a module's address and name.

    Found in a modules 'friends' list
    """

    address: str
    name: str


@dataclass
class SuiMoveModule(DataClassJsonMixin):
    """From getNormalized."""

    name: str
    address: str
    file_format_version: int
    friends: list[SuiMoveModuleId]
    structs: dict[str, SuiMoveStruct]
    exposed_functions: dict[str, SuiMoveFunction]

    def __post_init__(self):
        """Post init processing for parameters."""

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMoveModule":
        """ingest_data Ingest results of calling `sui_getNormalizedMoveModule`.

        :param indata: Dictionary containing module defintion
        :type indata: dict
        :return: Instance of SuiMoveModule
        :rtype: SuiMoveModule
        """
        return SuiMoveModule.from_dict(indata)


@dataclass
class SuiMovePackage(DataClassJsonMixin):
    """From getNormalized."""

    modules: dict

    def __post_init__(self):
        """Post init processing for parameters."""
        self.modules = {x: SuiMoveModule.from_dict(y) for x, y in self.modules.items()}

    @classmethod
    def ingest_data(cls, indata: dict) -> "SuiMovePackage":
        """Ingest from external call."""
        new_mods = {}
        for mod_key, mod_value in indata.items():
            new_mods[mod_key] = mod_value
        indata["modules"] = new_mods
        return SuiMovePackage.from_dict(indata)


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
        """."""
        return cls.from_dict({"items": indata})


@dataclass
class SuiTxnAuthSigners(DataClassJsonMixin):
    """From sui_getTransactionAuthSigners."""

    signers: list[str]
