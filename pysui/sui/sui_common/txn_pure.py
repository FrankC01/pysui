#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pure argument processor for transactions."""

import logging
from math import ceil
from functools import singledispatchmethod

# Standard library logging setup
logger = logging.getLogger(__name__)


from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_utils import serialize_uint32_as_uleb128
from pysui.sui.sui_common.instrumentation import sync_instrumented


class PureInput:
    """Pure inputs processing."""

    @singledispatchmethod
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput.pure")
    def pure(cls, arg):
        """Template dispatch method."""
        return f"I'm converting {arg} pure."

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bool) -> list:
        """."""
        logger.debug("bool->pure %s", arg)
        return list(int(arg is True).to_bytes(1, "little"))

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: int) -> list:
        """Convert int to minimal list of bytes."""
        logger.debug("int->pure %s", arg)
        ccount = ceil(arg.bit_length() / 8.0)
        return list(int.to_bytes(arg, ccount, "little"))

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.Optional) -> list:
        """Convert OptionalU8 to list of bytes."""
        logger.debug("Optional %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.SuiU8) -> list:
        """Convert unsigned int to bytes."""
        logger.debug("u8->pure %s", arg.value)
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.OptionalU8) -> list:
        """Convert OptionalU8 to list of bytes."""
        logger.debug("Optional<u8> %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.SuiU16) -> list:
        """Convert unsigned int to bytes."""
        logger.debug("u16->pure %s", arg.value)
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.OptionalU16) -> list:
        """Convert OptionalU16 to list of bytes."""
        logger.debug("Optional<u16> %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.SuiU32) -> list:
        """Convert unsigned int to bytes."""
        logger.debug("u32->pure %s", arg.value)
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.OptionalU32) -> list:
        """Convert OptionalU32 to list of bytes."""
        logger.debug("Optional<u32> %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.SuiU64) -> list:
        """Convert unsigned int to bytes."""
        logger.debug("u64->pure %s", arg.value)
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.OptionalU64) -> list:
        """Convert OptionalU64 to list of bytes."""
        logger.debug("Optional<u64> %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.SuiU128) -> list:
        """Convert unsigned int to bytes."""
        logger.debug("u128->pure %s", arg.value)
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.OptionalU128) -> list:
        """Convert OptionalU128 to list of bytes."""
        logger.debug("Optional<u128> %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.SuiU256) -> list:
        """Convert unsigned int to bytes."""
        logger.debug("u256->pure %s", arg.value)
        return list(arg.to_bytes())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.OptionalU256) -> list:
        """Convert OptionalU256 to list of bytes."""
        logger.debug("Optional<u256> %s", arg)
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: str) -> list:
        """Convert str to list of bytes."""
        logger.debug("str->pure %s", arg)
        byte_list = list(bytearray(arg, encoding="utf-8"))
        length_prefix = list(bytearray(serialize_uint32_as_uleb128(len(byte_list))))
        return length_prefix + byte_list

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bytes) -> list:
        """Bytes to list."""
        logger.debug("bytes->pure %s", arg)
        base_list = list(arg)
        return base_list

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.Address) -> list:
        """Convert bcs.Address to list of bytes."""
        logger.debug("bcs.Address->pure %s", arg.to_json())
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.Digest) -> list:
        """Convert bcs,Digest to list of bytes."""
        logger.debug("bcs.Digest->pure %s", arg.to_json())
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: bcs.Variable) -> list:
        """Convert bcs,Variable to list of bytes."""
        logger.debug("bcs.Variable->pure %s", arg.to_json())
        return list(arg.serialize())

    @pure.register
    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput._")
    def _(cls, arg: list) -> list:
        """uleb128 length encoded pure vector."""
        logger.debug("list->pure %s", arg)
        stage_list = [PureInput.pure(x) for x in arg]
        res_list = list(serialize_uint32_as_uleb128(len(stage_list)))
        for stage_pure in stage_list:
            res_list.extend(stage_pure)
        return res_list

    @classmethod
    @sync_instrumented("pysui.sui.sui_common.txn_pure.PureInput.as_input")
    def as_input(cls, args) -> bcs.BuilderArg:
        """Convert python and pysui types to a Pure BuilderArg type."""
        return bcs.BuilderArg("Pure", cls.pure(args))
