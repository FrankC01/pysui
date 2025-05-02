#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Core Sui BCS Types."""

import binascii
import copy
import uuid
from typing import Any, Union
import json
import canoser
from deprecated.sphinx import deprecated, versionadded, versionchanged

from pysui.abstracts.client_keypair import PublicKey, SignatureScheme
from pysui.sui.sui_txresults.common import GenericRef
from pysui.sui.sui_txresults.single_tx import ObjectRead
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_utils import (
    b58str_to_list,
    hexstring_to_list,
    hexstring_to_sui_id,
    from_list_to_b58str,
)
import pysui.sui.sui_pgql.pgql_types as pgql_type

_ADDRESS_LENGTH: int = 32
_DIGEST_LENGTH: int = 32
_INTENT_LENGTH: int = 3


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

    def to_digest_str(self) -> str:
        """Convert bytes to base58 digest str."""
        return from_list_to_b58str(self.Digest)

    @classmethod
    def from_str(cls, indata: str) -> "Digest":
        """Digest from base58 string."""
        return cls(b58str_to_list(indata))

    @classmethod
    @versionadded(version="0.17.0", reason="Direct from bytes construction")
    def from_bytes(cls, indata: bytes) -> "Digest":
        """Digest from bytes."""
        return cls(list(indata))


class Intent(canoser.Struct):
    """Intent prefix."""

    _fields = [("Intent", canoser.ArrayT(canoser.Uint8, _INTENT_LENGTH, False))]

    @classmethod
    def from_list(cls, indata: list) -> "Intent":
        """Intent from list."""
        return cls(indata)


@versionadded(version="0.60.0", reason="Handle Sting, etc.")
class VariableArrayU8(canoser.Struct):
    """Variable length array"""

    _fields = [("Array", [])]


class Variable(canoser.Struct):
    """."""

    _fields = []

    @classmethod
    def bcs_var_length_field(
        cls, base_class: canoser.Struct, ready_data: list[int]
    ) -> "Variable":
        """."""
        new_class = type(f"a{uuid.uuid4()}", (Variable,), {"_fields": []})
        new_class._fields.append(("Data", [base_class, len(ready_data), False]))
        return new_class(ready_data)

    @classmethod
    def bcs_var_length_encoded_field(
        cls, base_class: canoser.Struct, encoder: Any, ready_data: list[int]
    ) -> "Variable":
        """."""
        res = encoder(ready_data)
        new_class = type(f"a{uuid.uuid4()}", (Variable,), {"_fields": []})
        new_class._fields.append(("Data", [base_class, len(res), True]))
        return new_class(res)

    @classmethod
    def decode(cls, cursor):
        return super().decode(cursor)


class IntentMessage(canoser.Struct):
    """Intent and message."""

    _fields = [("Intent", Intent), ("Message", Variable)]


class ArrayVar(canoser.Struct):
    """."""

    _fields = []

    @classmethod
    def bcs_array_for(cls, *, base_class, ready_data: list, depth: int = 0):
        """."""
        deep_copy = copy.deepcopy(ArrayVar)
        field_def: tuple[str, list] = ()
        type_list = base_class
        data_list = ready_data
        if depth:
            for _ in range(depth):
                type_list = [copy.deepcopy(type_list)]
            for _ in range(depth - 1):
                data_list = [copy.deepcopy(data_list)]
            field_def = ("Array", type_list)
        else:
            field_def = ("Array", [type_list])
        deep_copy._fields.append(field_def)
        return deep_copy(data_list)


class ObjectReference(canoser.Struct):
    """ObjectReference represents an object by it's objects reference fields."""

    _fields = [
        ("ObjectID", Address),
        ("SequenceNumber", canoser.Uint64),
        ("ObjectDigest", Digest),
    ]

    @classmethod
    @deprecated(version="0.54.0", reason="Transitioning to GraphQL")
    def from_generic_ref(cls, indata: GenericRef) -> "ObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: SharedObjectReference
        """
        if isinstance(indata, GenericRef):
            return cls(
                Address.from_str(indata.object_id),
                int(indata.version),
                Digest.from_str(indata.digest),
            )
        raise ValueError(f"{indata} is not valid")

    @classmethod
    @versionadded(version="0.54.0", reason="Support argument inferencing")
    def from_gql_ref(cls, indata: pgql_type.ObjectReadGQL) -> "ObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: SharedObjectReference
        """
        if isinstance(
            indata,
            (
                pgql_type.ObjectReadGQL,
                pgql_type.SuiCoinObjectGQL,
                pgql_type.SuiStakedCoinGQL,
                pgql_type.SuiCoinObjectSummaryGQL,
            ),
        ):
            return cls(
                Address.from_str(indata.object_id),
                indata.version,
                Digest.from_str(indata.object_digest),
            )
        raise ValueError(f"{indata} is not valid")


class SharedObjectReference(canoser.Struct):
    """SharedObjectReference represents a shared object by it's objects reference fields."""

    _IMMUTABLES: list[str] = [
        # hexstring_to_sui_id("0x5"),
        hexstring_to_sui_id("0x6"),
        hexstring_to_sui_id("0x7"),
        hexstring_to_sui_id("0x8"),
        hexstring_to_sui_id("0x403"),
    ]

    _fields = [
        (
            "ObjectID",
            Address,
        ),  # canoser.ArrayT(canoser.Uint8, _ADDRESS_LENGTH)),
        ("SequenceNumber", canoser.Uint64),
        ("Mutable", bool),
    ]

    @classmethod
    @deprecated(version="0.54.0", reason="Transitioning to GraphQL")
    def from_object_read(cls, indata: ObjectRead) -> "SharedObjectReference":
        """from_generic_ref init construct with GenericRef from ObjectRead structure.

        :param indata: The reference information for an Object from ObjectRead
        :type indata: GenericRef
        :return: The instantiated BCS object
        :rtype: SharedObjectReference
        """
        mutable = False if indata.object_id in cls._IMMUTABLES else True
        return cls(
            Address.from_str(indata.object_id),
            int(indata.owner.initial_shared_version),
            mutable,
        )

    @classmethod
    @versionadded(version="0.54.0", reason="Support argument inferencing")
    def from_gql_ref(
        cls, indata: pgql_type.ObjectReadGQL, is_mutable: bool = False
    ) -> "SharedObjectReference":
        """from_gql_ref init construct with ObjectReadGQL.

        :param indata: The reference information for an Object from ObjectReadGQL
        :type indata: ObjectReadGQL
        :return: The instantiated BCS object
        :rtype: SharedObjectReference
        """
        mutable = is_mutable if indata.object_id not in cls._IMMUTABLES else False
        return cls(
            Address.from_str(indata.object_id),
            indata.object_owner.initial_version,
            mutable,
        )


class Uint256(canoser.int_type.IntType):
    """Uint256 represents a 256 bit ulong as hack as canoser doesn't support."""

    byte_lens = 32
    max_value = (
        115792089237316195423570985008687907853269984665640564039457584007913129639935
    )
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


U8 = canoser.Uint8
U16 = canoser.Uint16
U32 = canoser.Uint32
U64 = canoser.Uint64
U128 = canoser.Uint128
U256 = Uint256


@versionadded(version="0.19.0", reason="Added")
@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalU8(canoser.RustOptional):
    """OptionalU8 Optional assignment of unsigned 8 bit int."""

    _type = U8


@versionadded(version="0.19.0", reason="Added")
@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalU16(canoser.RustOptional):
    """OptionalU16 Optional assignment of unsigned 16 bit int."""

    _type = U16


@versionadded(version="0.19.0", reason="Added")
@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalU32(canoser.RustOptional):
    """OptionalU32 Optional assignment of unsigned 32 bit int."""

    _type = U32


@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalU64(canoser.RustOptional):
    """OptionalU64 Optional assignment of unsigned 64 bit int."""

    _type = U64


@versionadded(version="0.19.0", reason="Added")
@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalU128(canoser.RustOptional):
    """OptionalU128 Optional assignment of unsigned 128 bit int."""

    _type = U128


@versionadded(version="0.19.0", reason="Added")
@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalU256(canoser.RustOptional):
    """OptionalU256 Optional assignment of unsigned 256 bit int."""

    _type = U256


OPTIONAL_SCALARS: list = [
    OptionalU8,
    OptionalU16,
    OptionalU32,
    OptionalU64,
    OptionalU128,
    OptionalU256,
]


class TypeTag(canoser.RustEnum):
    """TypeTag enum for move call type_arguments."""

    _LCASE_SCALARS: list[str] = [
        "bool",
        "u8",
        "u16",
        "u32",
        "u64",
        "u128",
        "u256",
    ]
    _UCASE_SCALARS: list[str] = [
        "Bool",
        "U8",
        "U16",
        "U32",
        "U64",
        "uU28",
        "U256",
    ]

    _enums = [
        ("Bool", None),
        ("U8", None),
        ("U64", None),
        ("U128", None),
        ("Address", None),
        ("Signer", None),
        ("Vector", None),  # Injected below StructTag
        ("Struct", None),  # Injected below StructTag
        ("U16", None),
        ("U32", None),
        ("U256", None),
    ]

    @classmethod
    def type_tag_from(cls, value: str) -> "TypeTag":
        """."""
        assert isinstance(value, str), f"Expected string, found {type(value)}"
        # Scalar types
        if value in cls._LCASE_SCALARS:
            index = cls._LCASE_SCALARS.index(value)
            return cls(cls._UCASE_SCALARS[index])
        if value in cls._UCASE_SCALARS:
            return cls(cls._UCASE_SCALARS[cls._UCASE_SCALARS.index(value)])
        # Struct types
        # Address types
        if value.count("::") == 0 and (
            value.startswith("0x") or value.startswith("0X")
        ):
            return cls("Address")
            # return cls("Address", Address.from_str(value))
        # Vector types
        vcount = value.count("vector")
        if vcount:
            # Get the most inner type tag
            inner_type_tag = cls.type_tag_from(
                value[value.rfind("<") + 1 : value.index(">")]
            )
            for _ in range(vcount):
                inner_type_tag = TypeTag.new_with_index_value(
                    TypeTag.get_index("Vector"), [inner_type_tag]
                )
            return inner_type_tag
        spliter = value.split("::")
        if len(spliter) > 2:
            return TypeTag.new_with_index_value(
                TypeTag.get_index("Struct"), StructTag.from_type_str(value)
            )
        raise ValueError(f"{value} not a recognized TypeTag")

    @classmethod
    def update_value_at(cls, index: int, value: Any):
        """update_value_at Updates the enum list.

        :param index: Index of enum
        :type index: int
        :param value: The BCS type value to insert at index
        :type value: Any
        """
        cls._enums[index] = (cls._enums[index][0], value)


@versionchanged(version="0.17.1", reason="Fixed nested types.")
@versionchanged(
    version="0.51.3", reason="PR fixed nested types that are arrays of types."
)
class StructTag(canoser.Struct):
    """StructTag represents a type value (e.g. 0x2::sui::SUI) in BCS when used in MoveCall."""

    _fields = [
        ("address", Address),
        ("module", str),
        ("name", str),
        ("type_parameters", [TypeTag]),
    ]

    @classmethod
    def from_type_str(cls, type_str: str) -> "StructTag":
        """from_type_str convert a type_arg to StructTag.

        :param type_str: Type string (e.g. 0x2::sui::SUI)
        :type type_str: str
        :return: Instance of StructTag
        :rtype: StructTag
        """

        def _reducer(accum: Union[TypeTag, list[TypeTag]], item: str) -> TypeTag:
            """Accumulate nested type tags."""
            new_s = item.strip().split("::")
            if not accum:
                return TypeTag(
                    "Struct",
                    cls(Address.from_str(new_s[0]), new_s[1], new_s[2], []),
                )
            return TypeTag(
                "Struct",
                cls(
                    Address.from_str(new_s[0]),
                    new_s[1],
                    new_s[2],
                    accum if isinstance(accum, list) else [accum],
                ),
            )

        inner_count = type_str.count("<")
        if inner_count:
            multi_struct = type_str.split("<")
            last_pos = len(multi_struct) - 1
            # Remove the residual '>' chars
            multi_struct[last_pos] = multi_struct[last_pos][:-inner_count]
            # Walk in reverse all but the first and create struct type tags
            lowest_level = None
            for last_one in multi_struct[1::][::-1]:
                # If has a array (comma separated) accumulate
                if last_one.count(","):
                    lowest_level = [_reducer(None, x) for x in last_one.split(",")]
                    continue
                lowest_level = _reducer(lowest_level, last_one)
            # Return the main struct tag container
            main_struct = multi_struct[0].split("::")
            if not isinstance(lowest_level, list):
                lowest_level = [lowest_level]
            return cls(
                Address.from_str(main_struct[0]),
                main_struct[1],
                main_struct[2],
                lowest_level,
            )
        split_type = type_str.split("::")
        return cls(Address.from_str(split_type[0]), split_type[1], split_type[2], [])


# Overcome forward reference at init time with these injections
TypeTag.update_value_at(6, [TypeTag])
TypeTag.update_value_at(7, StructTag)


class ObjectArg(canoser.RustEnum):
    """ObjectArg enum for type of object and it's reference data when used in MoveCall."""

    _enums = [
        ("ImmOrOwnedObject", ObjectReference),
        ("SharedObject", SharedObjectReference),
        ("Receiving", ObjectReference),
    ]


class UnresolvedObjectArg(canoser.Struct):
    """Unresolved call argument for ObjectTypes."""

    _fields = [
        ("ObjectStr", str),
        ("IsOptional", bool),
        ("IsReceiving", bool),
        ("RefType", U8),
        ("TypeStr", str),
    ]

    @classmethod
    def from_object_ref_type(
        cls, arg: str, ref: pgql_type.MoveObjectRefArg
    ) -> "UnresolvedObjectArg":
        """."""
        return cls(
            arg,
            ref.is_optional,
            ref.is_receiving,
            ref.ref_type,
            f"{ref.type_package}::{ref.type_module}::{ref.type_struct}",
        )

    @classmethod
    def from_optional_object_ref_type(
        cls,
        arg: str,
        ref: pgql_type.MoveObjectRefArg,
        type_str: str,
    ) -> "UnresolvedObjectArg":
        """."""
        return cls(
            arg,
            ref.is_optional,
            ref.is_receiving,
            ref.type_params[0].ref_type,
            type_str,
        )


class BuilderArg(canoser.RustEnum):
    """BuilderArg objects are generated in the TransactionBuilder."""

    _enums = [
        ("Object", Address),
        ("Pure", [canoser.Uint8]),
        ("ForcedNonUniquePure", None),
        ("Unresolved", str),
    ]

    def __hash__(self) -> int:
        """Override hash to use builder arg as key in dict."""
        # hself = hash(str(self))
        # return hself
        return id(self)


class CallArg(canoser.RustEnum):
    """CallArg represents an argument (parameters) of a MoveCall.

    Pure type is for scalars, or native, values.
    """

    _enums = [
        ("Pure", [canoser.Uint8]),
        ("Object", ObjectArg),
        ("UnresolvedObject", UnresolvedObjectArg),
    ]


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


@deprecated(version="0.54.0", reason="Transitioning to GraphQL")
class OptionalTypeTag(canoser.RustOptional):
    """OptionalTypeTag Optional assignment of TypeTag."""

    _type = TypeTag


class Optional(canoser.RustOptional):
    """Use from OptionalTypeFactor."""

    _type = canoser.Struct

    def to_json(self, indent=4):
        """."""
        json.dumps(self.to_json_serializable(), indent=indent)


class UnresolvedOptional(canoser.RustOptional):
    """Use from OptionalTypeFactor."""

    _type = canoser.Struct

    def to_json(self, indent=4):
        """."""
        json.dumps(self.to_json_serializable(), indent=indent)


@versionadded(version="0.54.0", reason="Support argument inferencing")
class OptionalTypeFactory:
    """Optional Optional assignment of any canoser type."""

    @classmethod
    def as_optional(cls, in_type: Any = canoser.Struct) -> canoser.RustOptional:
        """."""
        Optional._type = in_type.__class__

        # class AnOptional(canoser.RustOptional):
        #     """."""

        #     _type = in_type.__class__

        #     def to_json(self, indent=4):
        #         """."""
        #         json.dumps(self.to_json_serializable(), indent=indent)

        return Optional(None)

    @classmethod
    def as_unresolved_optional(
        cls, in_type: Any = canoser.Struct
    ) -> canoser.RustOptional:
        """."""
        UnresolvedOptional._type = in_type.__class__
        return UnresolvedOptional(None)


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

    _fields = [("FromCoin", Argument), ("Amount", [Argument])]


class MergeCoins(canoser.Struct):
    """It merges n-coins into the first coin."""

    _fields = [("ToCoin", Argument), ("FromCoins", [Argument])]


class Publish(canoser.Struct):
    """Publish represents a sui_publish structure."""

    _fields = [("Modules", [[canoser.Uint8]]), ("Dependents", [Address])]


class MakeMoveVec(canoser.Struct):
    """Given n-values of the same type, it constructs a vector."""

    _fields = [("TypeTag", OptionalTypeTag), ("Vector", [Argument])]


class Upgrade(canoser.Struct):
    """Upgrade an existing move package onchain."""

    _fields = [
        ("Modules", [[canoser.Uint8]]),
        ("Dependents", [Address]),
        ("Package", Address),
        ("UpgradeTicket", Argument),
    ]


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
    def variant_for_index(
        cls, index: int
    ) -> Union[tuple[str, canoser.RustEnum], IndexError]:
        """variant_for_index returns the enum name and reference tuple from specific index.

        :param index: The index into list of enum values
        :type index: int
        :raises IndexError: When index provided is not valid
        :return: The name,value tuple of the enum index
        :rtype: Union[tuple[str, canoser.RustEnum], ValueError]
        """
        if index > len(cls._enums):
            raise IndexError(
                f"{cls.__name__} has only {len(cls._enums)} and index requested is greater {index}"
            )
        return cls._enums[index]

    @classmethod
    def from_bytes(cls, in_data: bytes) -> "TransactionData":
        """."""
        return cls.deserialize(in_data)


# Multi-signature legacy
@versionadded(version="0.20.4", reason="Added to support in-code MultiSig signing.")
@deprecated(version="0.33.0", reason="Unused, scheduled for removal in 0.35.0")
class MsPublicKey(canoser.Struct):
    """Represents signing PublicKeys for serialization."""

    _fields = [("PublicKey", [U8]), ("Weight", U8)]


# Multi-signature
class MsEd25519PublicKey(canoser.Struct):
    """."""

    _fields = [("PublicKey", [U8, 32, False]), ("Weight", U8)]


class MsSecp256k1PublicKey(canoser.Struct):
    """."""

    _fields = [("PublicKey", [U8, 33, False]), ("Weight", U8)]


class MsSecp256r1PublicKey(canoser.Struct):
    """."""

    _fields = [("PublicKey", [U8, 33, False]), ("Weight", U8)]


class MsNewPublicKey(canoser.RustEnum):
    """Represents signing PublicKeys for serialization."""

    _enums = [
        ("Ed25519", MsEd25519PublicKey),
        ("Secp256k1", MsSecp256k1PublicKey),
        ("Secp256r1", MsSecp256r1PublicKey),
    ]

    @classmethod
    def from_pubkey(cls, key: PublicKey, weight: int = 0) -> "MsNewPublicKey":
        """."""
        scheme: SignatureScheme = key.scheme
        kbytes = list(key.scheme_and_key()[1:])
        if scheme == SignatureScheme.ED25519:
            res = MsNewPublicKey("Ed25519", MsEd25519PublicKey(kbytes, weight))
        elif scheme == SignatureScheme.SECP256K1:
            res = MsNewPublicKey("Secp256k1", MsSecp256k1PublicKey(kbytes, weight))
        elif scheme == SignatureScheme.SECP256R1:
            res = MsNewPublicKey("Secp256r1", MsSecp256r1PublicKey(kbytes, weight))
        else:
            raise ValueError(f"SignatureScheme {scheme} not supported")

        return res


@versionadded(
    version="0.26.0",
    reason="Added to support new MultiSig bitmap in Sui v1.5.0.",
)
class MsBitmap(canoser.Struct):
    """Represents signing PublicKeys indexes for serialization."""

    _fields = [("Bitmap", U16)]


@versionadded(version="0.20.4", reason="Added to support in-code MultiSig signing.")
class MsCompressedSig(canoser.Struct):
    """Represents compressed individual signed messages for serialization."""

    _fields = [("Sig", [U8, 65, False])]


@versionadded(
    version="0.26.0",
    reason="Sui converting from roaring bitmap to simple bitmap in 1.5.0",
)
class MultiSignature(canoser.Struct):
    """BCS representation of a MultiSig signature for executions."""

    _fields = [
        ("Scheme", U8),
        ("Sigs", [MsCompressedSig]),
        ("BitMap", MsBitmap),
        ("PkMap", [MsNewPublicKey]),
        ("Threshold", U16),
    ]


# SuiTransaction


class TxStringInt(canoser.Struct):
    """Key Value pair where value is int. Used in TxTransaction use table consstruct."""

    _fields = [
        ("Key", str),
        ("Value", U16),
    ]


class TxStringString(canoser.Struct):
    """Key Value pair where value is string. Used in TxTransaction use table consstruct."""

    _fields = [
        ("Key", str),
        ("Value", str),
    ]


class TxTransaction(canoser.Struct):
    """Table of builder constructs.

    Serialized out and use to validate deserialization back in
    """

    _fields = [
        ("Frequencies", [TxStringInt]),
        ("ObjectsInUse", [TxStringString]),
        ("Inputs", [BuilderArg]),
        ("Commands", [Command]),
    ]


class TxSenderMulti(canoser.Struct):
    """BCS Representation of a multi-sig sender/sponsor."""

    _fields = [
        ("MutliSigAddress", Address),
        ("MultiSigKeyAddress", [Address]),
        ("MultiSigPublicKeys", [MsNewPublicKey]),
        ("Threshold", U16),
        ("SigningKeyIndexes", MsBitmap),
    ]


class TxSenderSingle(canoser.Struct):
    """BCS representation of a single sender/sponsor."""

    _fields = [
        ("Address", Address),
        ("SigningPublicKeys", MsNewPublicKey),
    ]


class TxSender(canoser.RustEnum):
    """BCS representation of transaction sender/sponsor."""

    _enums = [
        ("NotSet", None),
        ("Single", TxSenderSingle),
        ("Multi", TxSenderMulti),
    ]


class SuiTransactionDataV1(canoser.Struct):
    """BCS representation of transaction builder."""

    _fields = [
        ("TxSender", TxSender),
        ("TxSponsor", TxSender),
        ("TxTransaction", TxTransaction),
    ]


class SuiTransaction(canoser.RustEnum):
    """BCS representation of serialized pysui SuiTransaction (a.k.a. builder)."""

    _enums = [("1.0.0", SuiTransactionDataV1)]
