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
from pysui.sui.sui_txresults.single_tx import ObjectRead

from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_utils import hexstring_to_list, b58str_to_list
from pysui.sui.sui_txresults.common import GenericRef

_ADDRESS_LENGTH: int = 32
_DIGEST_LENGTH: int = 32


class Address(canoser.Struct):
    """Address Represents a Sui Address or ObjectID as list of ints."""

    _fields = [("Address", canoser.ArrayT(canoser.Uint8, _ADDRESS_LENGTH, False))]

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
    def from_sui_address(cls, indata: SuiAddress) -> "Address":
        """."""
        return cls(hexstring_to_list(indata.address))

    @classmethod
    def from_str(cls, indata: str) -> "Address":
        """."""
        return cls(hexstring_to_list(indata))


class Digest(canoser.Struct):
    """Digest represents a transaction or object base58 value as list of ints."""

    _fields = [("Digest", canoser.ArrayT(canoser.Uint8, _DIGEST_LENGTH))]

    @classmethod
    def from_str(cls, indata: str) -> "Digest":
        """."""
        return cls(b58str_to_list(indata))


class ObjectReference(canoser.Struct):
    """ObjectReference represents an object by it's objects reference fields."""

    _fields = [
        ("ObjectID", Address),
        ("SequenceNumber", canoser.Uint64),
        ("ObjectDigest", Digest),
    ]

    @classmethod
    def from_generic_ref(cls, indata: GenericRef) -> "ObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: SharedObjectReference
        """
        if isinstance(indata, ObjectRead):
            return cls(Address.from_str(indata.object_id), indata.version, Digest.from_str(indata.digest))
        raise ValueError(f"{indata} is not valid")


class SharedObjectReference(canoser.Struct):
    """SharedObjectReference represents a shared object by it's objects reference fields."""

    _fields = [
        ("ObjectID", Address),  # canoser.ArrayT(canoser.Uint8, _ADDRESS_LENGTH)),
        ("SequenceNumber", canoser.Uint64),
        ("Mutable", bool),
    ]

    @classmethod
    def from_generic_ref(cls, indata: GenericRef) -> "SharedObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: SharedObjectReference
        """
        return cls(Address.from_str(indata.object_id), indata.version, Digest.from_str(indata.digest))


class OptionalU64(canoser.RustOptional):
    """OptionalU64 Optional assignment of unsigned 64 bit int."""

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
        ("Address", Address),
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

    _fields = [("address", Address), ("module", str), ("name", str), ("type_parameters", [TypeTag])]

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
            return cls(Address.from_str(split_type[0]), split_type[1], split_type[2], [])
        raise ValueError(f"Ill formed type_argument {type_str}")


# Overcome forward reference at init time with these injections
TypeTag.update_value_at(6, [TypeTag])
TypeTag.update_value_at(7, StructTag)


class ObjectArg(canoser.RustEnum):
    """ObjectArg enum for type of object and it's reference data when used in MoveCall."""

    _enums = [("ImmOrOwnedObject", ObjectReference), ("SharedObject", SharedObjectReference)]


class CallArg(canoser.RustEnum):
    """CallArg represents an argument (parameters) of a MoveCall.

    Pure type is for scalares, or native, values.
    """

    _enums = [("Pure", [canoser.Uint8]), ("Object", ObjectArg)]


class BCSMoveCall(canoser.Struct):
    """BCSMoveCall represents a sui_moveCall structure in BCS."""

    _fields = [
        ("package", Address),
        ("module", str),
        ("function", str),
        ("type_arguments", [TypeTag]),
        ("arguments", [CallArg]),
    ]


class BCSPay(canoser.Struct):
    """BCSPay represents a sui_pay structure in BCS."""

    _fields = [
        ("coins", [ObjectReference]),
        ("recipients", [Address]),
        ("amounts", [canoser.Uint64]),
    ]


class BCSPaySui(canoser.Struct):
    """BCSPaySui represents a sui_paySui structure.

    **Not Supported in sui_devInspectTransaction yet.**
    """

    _fields = [
        ("coins", [ObjectReference]),
        ("recipients", [Address]),
        ("amounts", [canoser.Uint64]),
    ]


class BCSPayAllSui(canoser.Struct):
    """BCSPayAllSui represents a sui_payAllSui structure.

    **Not Supported in sui_devInspectTransaction yet.**
    """

    _fields = [
        ("coins", [ObjectReference]),
        ("recipient", Address),
    ]


class BCSTransferObject(canoser.Struct):
    """BCSTransferObject represents a sui_transferObjecrt structure in BCS."""

    _fields = [
        ("recipient", Address),
        ("object_ref", ObjectReference),
    ]


class BCSTransferSui(canoser.Struct):
    """BCSTransferSui represents a sui_transferSui structure in BCS."""

    _fields = [
        ("recipient", Address),
        ("amount", OptionalU64),
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


class GasData(canoser.Struct):
    """."""

    _fields = [
        ("Payment", [ObjectReference]),
        ("Owner", Address),
        ("Price", canoser.Uint64),
        ("Budget", canoser.Uint64),
    ]


class Argument(canoser.RustEnum):
    """."""

    _enums = [
        ("GasCoin", None),
        ("Input", canoser.Uint16),
        ("Result", canoser.Uint16),
        ("NestedResult", (canoser.Uint16, canoser.Uint16)),
    ]


class OptionalTypeTag(canoser.RustOptional):
    """OptionalTypeTag Optional assignment of TypeTag."""

    _type = TypeTag


class ProgrammableMoveCall(canoser.Struct):
    """A call to either an entry or a public Move function."""

    _fields = [
        # The module or function containing Package ID
        ("Package", Address),
        # Module name
        ("Module", str),
        # Function name
        ("Function", str),
        # Array of types for generic substitution
        ("Type_Arguments", [TypeTag]),
        # Arguments to the function or entry point
        ("Arguments", [Argument]),
    ]


class TransferObjects(canoser.Struct):
    """It sends n-objects to the specified address."""

    _fields = [("Objects", [Argument]), ("Address", Argument)]


class SplitCoin(canoser.Struct):
    """It splits off some amount into a new coin."""

    _fields = [("FromCoin", Argument), ("Amount", Argument)]


class MergeCoins(canoser.Struct):
    """It merges n-coins into the first coin."""

    _fields = [("ToCoin", Argument), ("FromCoins", [Argument])]


class Publish(canoser.Struct):
    """Publish represents a sui_publish structure."""

    _fields = [("Modules", canoser.ArrayT(canoser.ArrayT(canoser.Uint8)))]


class MakeMoveVec(canoser.Struct):
    """Given n-values of the same type, it constructs a vector."""

    _fields = [("TypeTag", OptionalTypeTag), ("Vector", [Argument])]


class Upgrade(canoser.Struct):
    """Upgrade an existing move package onchain."""

    _fields = [("Modules", canoser.ArrayT(canoser.ArrayT(canoser.Uint8))), ("OIDs", [Address]), ("Arg", Argument)]


class Command(canoser.RustEnum):
    """."""

    _enums = [
        ("MoveCall", ProgrammableMoveCall),
        ("TransferObjects", TransferObjects),
        ("SplitCoin", SplitCoin),
        ("MergeCoins", MergeCoins),
        ("Publish", Publish),
        ("MakeMoveVec", MakeMoveVec),
        ("Upgrade", Upgrade),
    ]


class ProgrammableTransaction(canoser.Struct):
    """."""

    _fields = [("Inputs", [CallArg]), ("Command", [Command])]


class TransactionKind(canoser.RustEnum):
    """TransactionKind is enumeration of transaction kind.

    Deserialization (from_bytes) should only called if attempting to deserialize from
    the results of calling a transaction (i.e. unsafe_pay) with the first byte and last bytes
    have been pruned.

    This is a stopgap until programmable txns implemented with TransactionBuilder
    """

    _enums = [
        ("ProgrammableTransaction", ProgrammableTransaction),
        ("ChangeEpoch", None),
        ("Genesis", None),
        ("ConsensusCommitPrologue", None),
    ]

    @classmethod
    def from_bytes(cls, in_data: bytes) -> "TransactionKind":
        """."""
        return cls.deserialize(in_data)


class TransactionExpiration(canoser.RustEnum):
    """."""

    _enums = [("None", None), ("Epoch", canoser.Uint64)]


class TransactionDataV1(canoser.Struct):
    """."""

    _fields = [
        ("TransactionKind", TransactionKind),
        ("Sender", Address),
        ("GasData", GasData),
        ("TransactionExpiration", TransactionExpiration),
    ]


class TransactionData(canoser.RustEnum):
    """TransactionData is enumeration of transaction kind.

    Deserialization (from_bytes) should only called if attempting to deserialize from
    the results of calling a transaction (i.e. unsafe_pay).
    """

    _enums = [("V1", TransactionDataV1)]

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

    @classmethod
    def from_bytes(cls, in_data: bytes) -> "TransactionData":
        """."""
        return cls.deserialize(in_data)
