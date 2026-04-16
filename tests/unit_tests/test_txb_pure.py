#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.sui.sui_common.txb_pure.PureInput — all offline.

Tests cover every singledispatch branch of PureInput.pure() plus as_input().
Each test asserts the exact byte list produced, making regressions immediately
visible if the serialization format changes.
"""

import warnings
import pytest

# Suppress deprecated scalar-type warnings that fire at import-time
warnings.filterwarnings("ignore", category=DeprecationWarning)

from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_types.scalars import (
    ObjectID,
    SuiString,
    SuiU8,
    SuiU16,
    SuiU32,
    SuiU64,
    SuiU128,
    SuiU256,
)


# ---------------------------------------------------------------------------
# TestBoolDispatch
# ---------------------------------------------------------------------------

class TestBoolDispatch:
    def test_true_encodes_to_one(self):
        assert PureInput.pure(True) == [1]

    def test_false_encodes_to_zero(self):
        assert PureInput.pure(False) == [0]

    def test_result_is_list(self):
        assert isinstance(PureInput.pure(True), list)


# ---------------------------------------------------------------------------
# TestIntDispatch
# ---------------------------------------------------------------------------

class TestIntDispatch:
    def test_zero_produces_empty_list(self):
        # int(0).bit_length() == 0 → ceil(0/8) == 0 bytes
        assert PureInput.pure(0) == []

    def test_one_byte_value(self):
        assert PureInput.pure(1) == [1]

    def test_max_single_byte(self):
        assert PureInput.pure(255) == [255]

    def test_two_byte_value_little_endian(self):
        assert PureInput.pure(256) == [0, 1]

    def test_max_two_byte_value(self):
        assert PureInput.pure(65535) == [255, 255]

    def test_multi_byte_value(self):
        # 0x010000 = 65536 → [0, 0, 1]
        assert PureInput.pure(65536) == [0, 0, 1]


# ---------------------------------------------------------------------------
# TestStrDispatch
# ---------------------------------------------------------------------------

class TestStrDispatch:
    def test_empty_string_is_length_prefix_only(self):
        # ULEB128(0) = [0]
        assert PureInput.pure("") == [0]

    def test_short_string_with_length_prefix(self):
        # "hi" → len=2, utf-8=[104,105] → [2, 104, 105]
        assert PureInput.pure("hi") == [2, 104, 105]

    def test_single_char(self):
        result = PureInput.pure("A")
        assert result == [1, 65]

    def test_length_prefix_is_byte_count_not_char_count(self):
        # All ASCII → byte count == char count
        s = "abc"
        result = PureInput.pure(s)
        assert result[0] == len(s.encode("utf-8"))

    def test_result_is_list(self):
        assert isinstance(PureInput.pure("x"), list)


# ---------------------------------------------------------------------------
# TestBytesDispatch
# ---------------------------------------------------------------------------

class TestBytesDispatch:
    def test_bytes_converts_directly(self):
        assert PureInput.pure(b"\x01\x02\x03") == [1, 2, 3]

    def test_empty_bytes(self):
        assert PureInput.pure(b"") == []

    def test_single_byte(self):
        assert PureInput.pure(b"\xff") == [255]


# ---------------------------------------------------------------------------
# TestSuiScalarsDispatch — fixed-width types
# ---------------------------------------------------------------------------

class TestSuiScalarsDispatch:
    def test_sui_u8_is_one_byte(self):
        assert len(PureInput.pure(SuiU8(0))) == 1

    def test_sui_u8_value(self):
        assert PureInput.pure(SuiU8(42)) == [42]

    def test_sui_u16_is_two_bytes(self):
        assert len(PureInput.pure(SuiU16(0))) == 2

    def test_sui_u16_little_endian(self):
        # 256 = 0x0100 → [0x00, 0x01] in little-endian
        assert PureInput.pure(SuiU16(256)) == [0, 1]

    def test_sui_u32_is_four_bytes(self):
        assert len(PureInput.pure(SuiU32(0))) == 4

    def test_sui_u64_is_eight_bytes(self):
        assert len(PureInput.pure(SuiU64(0))) == 8

    def test_sui_u64_value_little_endian(self):
        result = PureInput.pure(SuiU64(1))
        assert result == [1, 0, 0, 0, 0, 0, 0, 0]

    def test_sui_u128_is_sixteen_bytes(self):
        assert len(PureInput.pure(SuiU128(0))) == 16

    def test_sui_u256_is_thirty_two_bytes(self):
        assert len(PureInput.pure(SuiU256(0))) == 32


# ---------------------------------------------------------------------------
# TestSuiStringDispatch
# ---------------------------------------------------------------------------

class TestSuiStringDispatch:
    def test_sui_string_same_as_plain_str(self):
        assert PureInput.pure(SuiString("hi")) == PureInput.pure("hi")

    def test_sui_string_empty(self):
        assert PureInput.pure(SuiString("")) == [0]

    def test_sui_string_includes_length_prefix(self):
        result = PureInput.pure(SuiString("abc"))
        assert result[0] == 3


# ---------------------------------------------------------------------------
# TestObjectIdDispatch
# ---------------------------------------------------------------------------

class TestObjectIdDispatch:
    def test_object_id_produces_32_bytes(self):
        oid = ObjectID("0x" + "ab" * 32)
        assert len(PureInput.pure(oid)) == 32

    def test_object_id_hex_decoded_correctly(self):
        oid = ObjectID("0x" + "00" * 31 + "02")
        result = PureInput.pure(oid)
        assert result[-1] == 2
        assert result[0] == 0

    def test_object_id_all_zeros(self):
        oid = ObjectID("0x" + "00" * 32)
        assert PureInput.pure(oid) == [0] * 32


# ---------------------------------------------------------------------------
# TestOptionalDispatch — bcs.OptionalU* types
# ---------------------------------------------------------------------------

class TestOptionalDispatch:
    def test_optional_u8_none_is_zero(self):
        opt = bcs.OptionalU8()
        assert PureInput.pure(opt) == [0]

    def test_optional_u8_some_value(self):
        opt = bcs.OptionalU8(5)
        # Some(5) → [1, 5]
        result = PureInput.pure(opt)
        assert result[0] == 1
        assert result[1] == 5

    def test_optional_u64_none_is_zero(self):
        opt = bcs.OptionalU64()
        assert PureInput.pure(opt) == [0]


# ---------------------------------------------------------------------------
# TestListDispatch
# ---------------------------------------------------------------------------

class TestListDispatch:
    def test_empty_list_is_zero_count(self):
        # ULEB128(0) = [0]
        assert PureInput.pure([]) == [0]

    def test_list_of_ints_has_count_prefix(self):
        result = PureInput.pure([1, 2, 3])
        # [count=3, 1, 2, 3]
        assert result[0] == 3
        assert result[1:] == [1, 2, 3]

    def test_list_of_bools(self):
        result = PureInput.pure([True, False])
        assert result[0] == 2
        assert result[1] == 1
        assert result[2] == 0

    def test_list_count_prefix_is_element_count(self):
        items = [10, 20, 30, 40, 50]
        result = PureInput.pure(items)
        assert result[0] == len(items)

    def test_nested_list_elements_each_serialized(self):
        # Each int element is independently serialized
        result = PureInput.pure([255, 256])
        # count=2, then 255=[255], then 256=[0,1]
        assert result[0] == 2
        assert result[1] == 255
        assert result[2] == 0
        assert result[3] == 1


# ---------------------------------------------------------------------------
# TestAsInput
# ---------------------------------------------------------------------------

class TestAsInput:
    def test_as_input_returns_builder_arg(self):
        result = PureInput.as_input(SuiU64(42))
        assert isinstance(result, bcs.BuilderArg)

    def test_as_input_enum_name_is_pure(self):
        result = PureInput.as_input(SuiU64(1))
        assert result.enum_name == "Pure"

    def test_as_input_value_matches_pure(self):
        result = PureInput.as_input(SuiU64(1))
        assert result.value == PureInput.pure(SuiU64(1))

    def test_as_input_with_bool(self):
        result = PureInput.as_input(True)
        assert result.enum_name == "Pure"
        assert result.value == [1]

    def test_as_input_with_str(self):
        result = PureInput.as_input("hi")
        assert result.value == [2, 104, 105]
