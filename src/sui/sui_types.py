"""Sui Types."""


from abc import abstractmethod
import json
from numbers import Number
from typing import TypeVar
from abstracts import (
    ClientAbstractClassType,
    ClientAbstractScalarType,
)


class SuiScalarType(ClientAbstractScalarType):
    """Base most SUI scalar type."""


class SuiString(SuiScalarType):
    """Sui String type."""


class SuiNumber(SuiScalarType):
    """Sui Number type."""


class ObjectID(SuiString):
    """Sui Object id type."""

    def __init__(self, value: str) -> None:
        """Initialize with identifier."""
        super().__init__(value)
        self.object_id = value


class SuiType(ClientAbstractClassType):
    """Base most SUI object type."""


class SuiRawDescriptor(SuiType):
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
        self._version = indata["version"]
        self._digest = indata["digest"]
        # TODO: Convert to SuiAddress
        self._owner = indata["owner"]["AddressOwner"]
        self._previous_transaction = indata["previousTransaction"]
        self._type_signature = indata["type"]

    @property
    def version(self) -> int:
        """Return the types version."""
        return self._version

    @property
    def digest(self) -> str:
        """Return the type digest."""
        return self._digest

    # TODO: Change to return SuiAddress when constructor fixed
    @property
    def owner(self) -> str:
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


class SuiNativeCoinDescriptor(SuiCoinDescriptor):
    """Sui gas is a coin."""


class SuiRawObject(SuiType):
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


class ObjectRead(SuiRawObject):
    """Base SUI Type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base type data."""
        super().__init__(indata, ObjectID(indata["fields"]["id"]["id"]))
        self._type_signature = indata["type"]
        self._data_type = indata["dataType"]
        self._has_public_transfer = indata["has_public_transfer"]
        # TODO: Convert to SuiAddress
        self._owner = indata["owner"]["AddressOwner"]
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
    def owner(self) -> str:
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


class SuiGasType(SuiCoinType):
    """Sui gas is a coin."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base type."""
        super().__init__(indata)
        self._balance = indata["fields"]["balance"]

    @property
    def balance(self) -> Number:
        """Get the balance for this coin object."""
        return self._balance


class SuiPackage(SuiType):
    """Sui package."""

    def __init__(self, indata: dict) -> None:
        """Initialize a package construct."""
        super().__init__(ObjectID(indata["reference"]["objectId"]))
        self._data_type: str = indata["data"]["dataType"]
        self._modules: dict = indata["data"]["disassembled"]
        self._owner: str = indata["owner"]
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
    def owner(self) -> str:
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


def from_object_descriptor(indata: dict) -> ObjectInfo:
    """Parse an inbound JSON like dictionary to a Sui type."""
    # print(indata)
    split = indata["type"].split("::", 2)
    if split[0] == "0x2":
        match split[1]:
            case "coin":
                split2 = split[2][5:-1].split("::")
                if split2[2] == "SUI":
                    return SuiNativeCoinDescriptor(indata)
                return SuiCoinDescriptor(indata)
            case "devnet_nft":
                if split[2] == "DevNetNFT":
                    return SuiNftDescriptor(indata)
    else:
        if len(split) == 3:
            return SuiDataDescriptor(indata)

    return ObjectInfo(indata)


def from_object_type(inblock: dict) -> ObjectRead:
    """Parse an inbound JSON like dictionary to a Sui type."""
    # print(inblock)
    indata = inblock["data"]
    match indata["dataType"]:
        case "moveObject":
            indata["previousTransaction"] = inblock["previousTransaction"]
            indata["storageRebate"] = inblock["storageRebate"]
            indata["digest"] = inblock["reference"]["digest"]
            indata["version"] = inblock["reference"]["version"]
            indata["owner"] = inblock["owner"]
            # print(indata)
            split = indata["type"].split("::", 2)

            if split[0] == "0x2":
                match split[1]:
                    case "coin":
                        split2 = split[2][5:-1].split("::")
                        if split2[2] == "SUI":
                            return SuiGasType(indata)
                        return SuiCoinType(indata)
                    case "devnet_nft":
                        if split[2] == "DevNetNFT":
                            return SuiNftType(indata)
            else:
                if len(split) == 3:
                    return SuiDataType(indata)
            return ObjectRead(indata)
        case "package":
            return SuiPackage(inblock)
        case _:
            raise ValueError(f"Don't recognize {indata['dataType']}")


if __name__ == "__main__":
    pass
    # known_package = "0xdf43f7fa8f94c8046587b745616bf11c1d732d45"
