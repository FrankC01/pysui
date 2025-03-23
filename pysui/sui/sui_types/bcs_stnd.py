#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Core Sui BCS Types."""

import binascii
from typing import Any
import canoser

from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_utils import (
    b58str_to_list,
    hexstring_to_list,
    hexstring_to_sui_id,
    from_list_to_b58str,
)

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

    def to_digest_str(self) -> str:
        """Convert bytes to base58 digest str."""
        return from_list_to_b58str(self.Digest)

    @classmethod
    def from_str(cls, indata: str) -> "Digest":
        """Digest from base58 string."""
        return cls(b58str_to_list(indata))

    @classmethod
    def from_bytes(cls, indata: bytes) -> "Digest":
        """Digest from bytes."""
        return cls(list(indata))


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
String = canoser.StrT
Balance = U64

MOVE_STD_SCALAR_REFS: dict[str, str] = {
    "u8": "bcse.U8",
    "u16": "bcse.U16",
    "u32": "bcse.U32",
    "u64": "bcse.U64",
    "u128": "bcse.U128",
    "u256": "bcse.U256",
    "address": "bcse.Address",
}

MOVE_OPTIONAL_TYPE: str = (
    "0x0000000000000000000000000000000000000000000000000000000000000001::option::Option"
)

MOVE_STD_STRUCT_REFS: dict[str, str] = {
    "0x0000000000000000000000000000000000000000000000000000000000000002::object::UID": "bcse.Address",
    "0x0000000000000000000000000000000000000000000000000000000000000002::balance::Balance": "bcse.Balance",
    "0x0000000000000000000000000000000000000000000000000000000000000001::string::String": "bcse.String",
}
