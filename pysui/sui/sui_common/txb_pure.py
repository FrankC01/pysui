#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pure argument processor for transactions."""

import binascii
import logging
from math import ceil
from functools import singledispatchmethod

# Standard library logging setup
logger = logging.getLogger()


from pysui.sui.sui_types import bcs
from pysui.sui.sui_utils import serialize_uint32_as_uleb128

from pysui.sui.sui_types.scalars import (
    ObjectID,
    SuiString,
    SuiU128,
    SuiU16,
    SuiU256,
    SuiU32,
    SuiU64,
    SuiU8,
)


class PureInput:
    """Pure inputs processing."""

    @singledispatchmethod
    @classmethod
    def pure(cls, arg):
        """Template dispatch method."""
        return f"I'm converting {arg} pure."

    @pure.register
    @classmethod
    def _(cls, arg: bool) -> list:
        """."""
        logger.debug(f"bool->pure {arg}")
        return list(int(arg is True).to_bytes(1, "little"))

    @pure.register
    @classmethod
    def _(cls, arg: int) -> list:
        """Convert int to minimal list of bytes."""
        logger.debug(f"int->pure {arg}")
        ccount = ceil(arg.bit_length() / 8.0)
        return list(int.to_bytes(arg, ccount, "little"))

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Optional) -> list:
        """Convert OptionalU8 to list of bytes."""
        logger.debug(f"Optional {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU8) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u8->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU8) -> list:
        """Convert OptionalU8 to list of bytes."""
        logger.debug(f"Optional<u8> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU16) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u16->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU16) -> list:
        """Convert OptionalU16 to list of bytes."""
        logger.debug(f"Optional<u16> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU32) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u32->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU32) -> list:
        """Convert OptionalU32 to list of bytes."""
        logger.debug(f"Optional<u32> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU64) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u64->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU64) -> list:
        """Convert OptionalU64 to list of bytes."""
        logger.debug(f"Optional<u64> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU128) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u128->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU128) -> list:
        """Convert OptionalU128 to list of bytes."""
        logger.debug(f"Optional<u128> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: SuiU256) -> list:
        """Convert unsigned int to bytes."""
        logger.debug(f"u256->pure {arg.value}")
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.OptionalU256) -> list:
        """Convert OptionalU256 to list of bytes."""
        logger.debug(f"Optional<u256> {arg}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: str) -> list:
        """Convert str to list of bytes."""
        logger.debug(f"str->pure {arg}")
        byte_list = list(bytearray(arg, encoding="utf-8"))
        length_prefix = list(bytearray(serialize_uint32_as_uleb128(len(byte_list))))
        return length_prefix + byte_list

    @pure.register
    @classmethod
    def _(cls, arg: SuiString) -> list:
        """Convert int to minimal list of bytes."""
        return cls.pure(arg.value)

    @pure.register
    @classmethod
    def _(cls, arg: bytes) -> list:
        """Bytes to list."""
        logger.debug(f"bytes->pure {arg}")
        base_list = list(arg)
        return base_list

    @pure.register
    @classmethod
    def _(cls, arg: ObjectID) -> list:
        """Convert ObjectID to list of bytes."""
        logger.debug(f"ObjectID->pure {arg.value}")
        return cls.pure(binascii.unhexlify(arg.value[2:]))

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Address) -> list:
        """Convert bcs.Address to list of bytes."""
        logger.debug(f"bcs.Address->pure {arg.to_json()}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Digest) -> list:
        """Convert bcs,Digest to list of bytes."""
        logger.debug(f"bcs.Digest->pure {arg.to_json()}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: bcs.Variable) -> list:
        """Convert bcs,Variable to list of bytes."""
        logger.debug(f"bcs.Variable->pure {arg.to_json()}")
        return list(arg.serialize())

    @pure.register
    @classmethod
    def _(cls, arg: list) -> list:
        """uleb128 length encoded pure vector."""
        logger.debug(f"list->pure {arg}")
        stage_list = [PureInput.pure(x) for x in arg]
        res_list = list(serialize_uint32_as_uleb128(len(stage_list)))
        for stage_pure in stage_list:
            res_list.extend(stage_pure)
        return res_list

    @classmethod
    def as_input(cls, args) -> bcs.BuilderArg:
        """Convert python and pysui types to a Pure BuilderArg type."""
        return bcs.BuilderArg("Pure", cls.pure(args))
