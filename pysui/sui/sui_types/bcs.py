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

"""Sui BCS Types."""

import binascii
from typing import Any, Union
import canoser

from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_utils import hexstring_to_list, b58str_to_list
from pysui.sui.sui_txresults.common import GenericRef

_BCS_ADDRESS_LENGTH: int = 20
_BCS_DIGEST_LENGTH: int = 32


class BCSAddress(canoser.Struct):
    """BCSAddress Represents a Sui Address or ObjectID as list of ints."""

    _fields = [("Address", canoser.ArrayT(canoser.Uint8, _BCS_ADDRESS_LENGTH, False))]

    def to_str(self) -> str:
        """."""
        return binascii.hexlify(bytes(getattr(self, "Address"))).decode()

    def to_address_str(self) -> str:
        """."""
        return f"0x{self.to_str()}"

    def to_sui_address(self) -> SuiAddress:
        """."""
        return SuiAddress(self.to_address_str())

    @classmethod
    def from_sui_address(cls, indata: SuiAddress) -> "BCSAddress":
        """."""
        return cls(hexstring_to_list(indata.address))

    @classmethod
    def from_str(cls, indata: str) -> "BCSAddress":
        """."""
        return cls(hexstring_to_list(indata))


class BCSDigest(canoser.Struct):
    """BCSDigest represents a transaction or object base58 value as list of ints."""

    _fields = [("Digest", canoser.ArrayT(canoser.Uint8, _BCS_DIGEST_LENGTH))]

    @classmethod
    def from_str(cls, indata: str) -> "BCSDigest":
        """."""
        return cls(b58str_to_list(indata))


class BCSObjectReference(canoser.Struct):
    """BCSObjectReference represents an object by it's objects reference fields."""

    _fields = [
        ("ObjectID", BCSAddress),
        ("SequenceNumber", canoser.Uint64),
        ("ObjectDigest", BCSDigest),
    ]

    @classmethod
    def from_generic_ref(cls, indata: GenericRef) -> "BCSObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: BCSSharedObjectReference
        """
        return cls(BCSAddress.from_str(indata.object_id), indata.version, BCSDigest.from_str(indata.digest))


class BCSSharedObjectReference(canoser.Struct):
    """BCSSharedObjectReference represents a shared object by it's objects reference fields."""

    _fields = [
        ("ObjectID", BCSAddress),  # canoser.ArrayT(canoser.Uint8, _BCS_ADDRESS_LENGTH)),
        ("SequenceNumber", canoser.Uint64),
        ("Mutable", bool),
    ]

    @classmethod
    def from_generic_ref(cls, indata: GenericRef) -> "BCSSharedObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: BCSSharedObjectReference
        """
        return cls(BCSAddress.from_str(indata.object_id), indata.version, BCSDigest.from_str(indata.digest))


class BCSOptionalU64(canoser.RustOptional):
    """BCSOptionalU64 Optional assignment of unsigned 64 bit int."""

    _type = canoser.Uint64


class Uint256(canoser.int_type.IntType):
    """Uint256 represents a 256 bit ulong as hack as canoser doesn't support."""

    byte_lens = 32
    max_value = 115792089237316195423570985008687907853269984665640564039457584007913129639935
    min_value = 0
    signed = False

    @classmethod
    def encode(cls, value):
        """encode Override canoser.int_type.IntType to return value as bytes.

        :param value: The inbound python int to covert
        :type value: int
        :return: Representation as bytes
        :rtype: bytes
        """
        return value.to_bytes(32, byteorder="little", signed=False)


class TypeTag(canoser.RustEnum):
    """TypeTag enum for move call type_arguments."""

    _enums = [
        ("Bool", bool),
        ("U8", canoser.Uint8),
        ("U64", canoser.Uint64),
        ("U128", canoser.Uint128),
        ("Address", BCSAddress),
        ("Signer", None),
        ("Vector", None),  # Injected below StructTag
        ("Struct", None),  # Injected below StructTag
        ("U16", canoser.Uint16),
        ("U32", canoser.Uint32),
        ("U256", Uint256),
    ]

    @classmethod
    def update_value_at(cls, index: int, value: Any):
        """update_value_at Updates the enum list.

        :param index: Index of enum
        :type index: int
        :param value: The BCS type value to insert at index
        :type value: Any
        """
        cls._enums[index] = (cls._enums[index][0], value)


class StructTag(canoser.Struct):
    """StructTag represents a type value (e.g. 0x2::sui::SUI) in BCS when used in MoveCall."""

    _fields = [("address", BCSAddress), ("module", str), ("name", str), ("type_parameters", [TypeTag])]

    @classmethod
    def from_type_str(cls, type_str: str) -> "StructTag":
        """from_type_str convert a type_arg to StructTag.

        :param type_str: Type string (e.g. 0x2::sui::SUI)
        :type type_str: str
        :return: Instance of StructTag
        :rtype: StructTag
        """
        if type_str.count("::") == 2:
            split_type = type_str.split("::")
            return cls(BCSAddress.from_str(split_type[0]), split_type[1], split_type[2], [])
        raise ValueError(f"Ill formed type_argument {type_str}")


# Overcome forward reference at init time with these injections
TypeTag.update_value_at(6, [TypeTag])
TypeTag.update_value_at(7, StructTag)


class ObjectArg(canoser.RustEnum):
    """ObjectArg enum for type of object and it's reference data when used in MoveCall."""

    _enums = [("ImmOrOwnedObject", BCSObjectReference), ("SharedObject", BCSSharedObjectReference)]


class CallArg(canoser.RustEnum):
    """CallArg represents an argument (parameters) of a MoveCall.

    Pure type is for scalares, or native, values.
    """

    _enums = [("Pure", [canoser.Uint8]), ("Object", ObjectArg), ("ObjVec", [ObjectArg])]


class BCSMoveCall(canoser.Struct):
    """BCSMoveCall represents a sui_moveCall structure in BCS."""

    _fields = [
        ("package", BCSAddress),
        ("module", str),
        ("function", str),
        ("type_arguments", [TypeTag]),
        ("arguments", [CallArg]),
    ]


class BCSPay(canoser.Struct):
    """BCSPay represents a sui_pay structure in BCS."""

    _fields = [
        ("coins", [BCSObjectReference]),
        ("recipients", [BCSAddress]),
        ("amounts", [canoser.Uint64]),
    ]


class BCSPaySui(canoser.Struct):
    """BCSPaySui represents a sui_paySui structure.

    **Not Supported in sui_devInspectTransaction yet.**
    """

    _fields = [
        ("coins", [BCSObjectReference]),
        ("recipients", [BCSAddress]),
        ("amounts", [canoser.Uint64]),
    ]


class BCSPayAllSui(canoser.Struct):
    """BCSPayAllSui represents a sui_payAllSui structure.

    **Not Supported in sui_devInspectTransaction yet.**
    """

    _fields = [
        ("coins", [BCSObjectReference]),
        ("recipient", BCSAddress),
    ]


class BCSTransferObject(canoser.Struct):
    """BCSTransferObject represents a sui_transferObjecrt structure in BCS."""

    _fields = [
        ("recipient", BCSAddress),
        ("object_ref", BCSObjectReference),
    ]


class BCSTransferSui(canoser.Struct):
    """BCSTransferSui represents a sui_transferSui structure in BCS."""

    _fields = [
        ("recipient", BCSAddress),
        ("amount", BCSOptionalU64),
    ]


class BCSPublish(canoser.Struct):
    """BCSPublish represents a sui_publish structure.

    **Not Supported in sui_devInspectTransaction yet.**
    """

    _fields = [("modules", canoser.ArrayT(canoser.ArrayT(canoser.Uint8)))]


class BCSSingleTransaction(canoser.RustEnum):
    """BCSSingleTransaction is enumeration of the different single (not batch) transactions."""

    _enums = [
        ("TransferObject", BCSTransferObject),  # Works
        ("Publish", BCSPublish),  # Not Works
        ("Call", BCSMoveCall),  # Works
        ("TransferSui", BCSTransferSui),  # Works
        ("Pay", BCSPay),  # Works
        ("PaySui", BCSPaySui),  # Not work
        ("PayAllSui", BCSPayAllSui),  # Not work
        ("ChangeEpoch", None),  # Not implemented
        ("Genesis", None),  # Not implemented
    ]

    @classmethod
    def variant_for_index(cls, index: int) -> Union[tuple[str, canoser.RustEnum], IndexError]:
        """variant_for_index returns the enum name and reference tuple from specific index.

        :param index: The index into list of enum values
        :type index: int
        :raises IndexError: When index provided is not valid
        :return: The name,value tuple of the enum index
        :rtype: Union[tuple[str, canoser.RustEnum], ValueError]
        """
        if index > len(cls._enums):
            raise IndexError(f"{cls.__name__} has only {len(cls._enums)} and index requested is greater {index}")
        return cls._enums[index]


class BCSBatchTransaction(canoser.Struct):
    """BCSBatchTransaction represents a sui_batchTransaction structure."""

    _fields = [("Singles", [BCSSingleTransaction])]


class BCSTransactionKind(canoser.RustEnum):
    """BCSTransactionKind is enumeration of different transaction types."""

    _enums = [
        ("Single", BCSSingleTransaction),
        ("Batch", BCSBatchTransaction),  # Not implemented
    ]

    @classmethod
    def variant_for_index(cls, index: int) -> Union[tuple[str, canoser.RustEnum], IndexError]:
        """variant_for_index returns the enum name and reference tuple from specific index.

        :param index: The index into list of enum values
        :type index: int
        :raises IndexError: When index provided is not valid
        :return: The name,value tuple of the enum index
        :rtype: Union[tuple[str, canoser.RustEnum], ValueError]
        """
        if index > len(cls._enums):
            raise IndexError(f"{cls.__name__} has only {len(cls._enums)} and index requested is greater {index}")
        return cls._enums[index]
