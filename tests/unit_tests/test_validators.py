#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui validator utilities — all offline, no live node required.

Covers:
  - valid_sui_address() from sui_common/validators.py
  - TypeValidator.check_object_id() from pgql_validators.py
  - TypeValidator.check_object_ids() from pgql_validators.py
  - TypeValidator.check_target_triplet() from pgql_validators.py
"""

import pytest

from pysui.sui.sui_common.validators import valid_sui_address
from pysui.sui.sui_pgql.pgql_validators import TypeValidator
from pysui.sui.sui_constants import SUI_HEX_ADDRESS_STRING_LEN

# Helpers
_MAX_ADDR = "0x" + "a" * 64   # 66 chars — maximum valid address with prefix
_MIN_ADDR = "0xa"              # 3 chars — minimum valid address with prefix


# ---------------------------------------------------------------------------
# TestValidSuiAddress — valid_sui_address() pure function
# ---------------------------------------------------------------------------

class TestValidSuiAddress:
    """Tests for valid_sui_address() covering all branches."""

    # --- Happy path ---

    def test_full_length_address_with_prefix(self):
        assert valid_sui_address(_MAX_ADDR) is True

    def test_short_address_with_prefix(self):
        assert valid_sui_address(_MIN_ADDR) is True

    def test_lowercase_x_prefix(self):
        assert valid_sui_address("0x" + "f" * 32) is True

    def test_uppercase_x_prefix(self):
        assert valid_sui_address("0X" + "a" * 10) is True

    def test_no_prefix_valid_hex(self):
        # Without 0x prefix, bare hex chars are accepted
        assert valid_sui_address("abc") is True

    def test_immutable_special_case(self):
        assert valid_sui_address("Immutable") is True

    def test_real_sui_framework_address(self):
        addr = "0x" + "0" * 63 + "2"  # 0x000...002
        assert valid_sui_address(addr) is True

    def test_mixed_case_hex(self):
        assert valid_sui_address("0xAbCdEf") is True

    # --- Boundary ---

    def test_exactly_max_length(self):
        assert valid_sui_address(_MAX_ADDR) is True
        assert len(_MAX_ADDR) == SUI_HEX_ADDRESS_STRING_LEN

    def test_one_over_max_length_rejected(self):
        too_long = "0x" + "a" * 65   # 67 chars
        assert valid_sui_address(too_long) is False

    def test_prefix_only_rejected(self):
        assert valid_sui_address("0x") is False

    # --- Failure path ---

    def test_empty_string_rejected(self):
        assert valid_sui_address("") is False

    def test_invalid_hex_chars_rejected(self):
        assert valid_sui_address("0xGGGGGGGG") is False

    def test_non_hex_without_prefix_rejected(self):
        # 'z' is not a hex char
        assert valid_sui_address("zzzzzz") is False

    def test_only_prefix_chars_rejected(self):
        # '0' and 'x' individually fail the hex-only length/content check
        # "0x" → too short after stripping prefix
        assert valid_sui_address("0x") is False


# ---------------------------------------------------------------------------
# TestCheckObjectId — TypeValidator.check_object_id()
# ---------------------------------------------------------------------------

class TestCheckObjectId:
    """Tests for TypeValidator.check_object_id()."""

    # --- Happy path ---

    def test_full_length_id_accepted(self):
        result = TypeValidator.check_object_id(_MAX_ADDR)
        assert result == _MAX_ADDR

    def test_short_id_accepted(self):
        result = TypeValidator.check_object_id(_MIN_ADDR)
        assert result == _MIN_ADDR

    def test_uppercase_x_prefix_accepted(self):
        addr = "0X" + "b" * 10
        result = TypeValidator.check_object_id(addr)
        assert result == addr

    def test_returns_original_string(self):
        addr = "0x" + "c" * 20
        assert TypeValidator.check_object_id(addr) is addr

    # --- Failure path ---

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="length"):
            TypeValidator.check_object_id("0x")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="length"):
            TypeValidator.check_object_id("0x" + "a" * 65)

    def test_missing_0x_prefix_raises(self):
        with pytest.raises(ValueError, match="prefix"):
            TypeValidator.check_object_id("abc123")

    def test_invalid_hex_chars_raises(self):
        with pytest.raises(ValueError, match="Invalid Sui object id string"):
            TypeValidator.check_object_id("0xGGGGGGGG")

    def test_immutable_string_raises(self):
        # "Immutable" is accepted by valid_sui_address but NOT by check_object_id
        # (no 0x prefix)
        with pytest.raises(ValueError, match="prefix"):
            TypeValidator.check_object_id("Immutable")


# ---------------------------------------------------------------------------
# TestCheckObjectIds — TypeValidator.check_object_ids()
# ---------------------------------------------------------------------------

class TestCheckObjectIds:
    """Tests for TypeValidator.check_object_ids()."""

    def test_single_valid_id(self):
        result = TypeValidator.check_object_ids([_MIN_ADDR])
        assert result == [_MIN_ADDR]

    def test_multiple_valid_ids(self):
        ids = ["0xa", "0xb", "0x" + "c" * 32]
        result = TypeValidator.check_object_ids(ids)
        assert result == ids

    def test_empty_list(self):
        assert TypeValidator.check_object_ids([]) == []

    def test_one_invalid_raises(self):
        with pytest.raises(ValueError):
            TypeValidator.check_object_ids(["0xa", "bad_id", "0xb"])

    def test_preserves_order(self):
        ids = ["0x" + str(i) * 2 for i in range(1, 6)]
        result = TypeValidator.check_object_ids(ids)
        assert result == ids


# ---------------------------------------------------------------------------
# TestCheckTargetTriplet — TypeValidator.check_target_triplet()
# ---------------------------------------------------------------------------

class TestCheckTargetTriplet:
    """Tests for TypeValidator.check_target_triplet()."""

    # --- Happy path ---

    def test_basic_triplet_parses(self):
        pkg, mod, name = TypeValidator.check_target_triplet("0x2::coin::Coin")
        assert pkg == "0x2"
        assert mod == "coin"
        assert name == "Coin"

    def test_full_address_triplet(self):
        addr = "0x" + "0" * 63 + "2"
        pkg, mod, name = TypeValidator.check_target_triplet(f"{addr}::token::Token")
        assert pkg == addr
        assert mod == "token"
        assert name == "Token"

    def test_returns_tuple_of_three(self):
        result = TypeValidator.check_target_triplet("0x1::module::Type")
        assert len(result) == 3

    def test_package_is_validated_as_object_id(self):
        # The package part must pass check_object_id
        pkg, _, _ = TypeValidator.check_target_triplet("0xdead::mod::Name")
        assert pkg == "0xdead"

    # --- Failure path ---

    def test_only_two_colons_raises(self):
        with pytest.raises(ValueError, match="Malformed"):
            TypeValidator.check_target_triplet("0x2::coin")

    def test_no_colons_raises(self):
        with pytest.raises(ValueError, match="Malformed"):
            TypeValidator.check_target_triplet("justaplainstring")

    def test_invalid_package_address_raises(self):
        # Package address is not hex — no 0x prefix
        with pytest.raises(ValueError):
            TypeValidator.check_target_triplet("notanaddress::mod::Name")

    def test_generic_type_with_extra_colons_raises(self):
        # "0x2::coin::Coin<0x2::sui::SUI>" has 4 :: separators, not 2
        with pytest.raises(ValueError, match="Malformed"):
            TypeValidator.check_target_triplet("0x2::coin::Coin<0x2::sui::SUI>")
