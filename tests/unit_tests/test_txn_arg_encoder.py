#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for transaction argument encoder singledispatch logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txn_arg_encoder import (
    _scalar_raw,
    _raw_value,
    encode_arg,
    _BaseArgParser,
)
from pysui.sui.sui_pgql.pgql_types import (
    OpenMoveScalarBodyGQL,
    OpenMoveVectorBodyGQL,
    OpenMoveDatatypeBodyGQL,
    OpenMoveTypeParamBodyGQL,
    OpenMoveTypeGQL,
    OpenMoveTypeSignatureGQL,
)


# ── Mock Parser ──────────────────────────────────────────────────────────────


class MockArgParser(_BaseArgParser):
    """Minimal mock parser for testing object resolution paths."""

    async def fetch_or_transpose_object(
        self, arg, is_receiving, is_mutable, expected_type=None
    ):
        obj_ref = bcs.ObjectReference(
            bcs.Address.from_str(arg) if isinstance(arg, str) else arg,
            1,
            bcs.Digest.from_bytes(b"\x00" * 32),
        )
        if is_receiving:
            return bcs.ObjectArg("Receiving", obj_ref)
        return bcs.ObjectArg("ImmOrOwnedObject", obj_ref)


# ── Scalar encoding ──────────────────────────────────────────────────────────


class TestScalarRaw:
    """Test _scalar_raw raw byte encoding."""

    def test_u8(self):
        assert _scalar_raw(5, "u8") == [5]
        assert _scalar_raw(0, "u8") == [0]
        assert _scalar_raw(255, "u8") == [255]

    def test_u64(self):
        raw = _scalar_raw(1000, "u64")
        assert len(raw) == 8

    def test_bool_true(self):
        assert _scalar_raw(True, "bool") == [1]

    def test_bool_false(self):
        assert _scalar_raw(False, "bool") == [0]

    def test_address(self):
        raw = _scalar_raw("0x1", "address")
        assert len(raw) == 32

    def test_string(self):
        raw = _scalar_raw("hello", "String")
        assert raw[0] == 5  # ULEB128 length
        assert raw[1:] == [ord(c) for c in "hello"]

    def test_unknown_scalar_type(self):
        with pytest.raises(ValueError, match="Unknown scalar type"):
            _scalar_raw(5, "unknown")


# ── Raw value dispatch (singledispatch) ──────────────────────────────────────


class TestRawValueDispatch:
    """Test _raw_value singledispatch over body variants."""

    def test_scalar_dispatch(self):
        body = OpenMoveScalarBodyGQL(scalar_type="u8")
        assert _raw_value(body, 42) == [42]

    def test_vector_scalar_depth_1(self):
        body = OpenMoveVectorBodyGQL(inner=OpenMoveScalarBodyGQL(scalar_type="u8"))
        raw = _raw_value(body, [1, 2, 3])
        assert raw[0] == 3  # ULEB128 length
        assert raw[1:] == [1, 2, 3]

    def test_vector_bytes_shorthand(self):
        body = OpenMoveVectorBodyGQL(inner=OpenMoveScalarBodyGQL(scalar_type="u8"))
        raw = _raw_value(body, b"\x01\x02\x03")
        assert raw[0] == 3
        assert raw[1:] == [1, 2, 3]

    def test_vector_nested_depth_2(self):
        inner_vector = OpenMoveVectorBodyGQL(
            inner=OpenMoveScalarBodyGQL(scalar_type="u8")
        )
        body = OpenMoveVectorBodyGQL(inner=inner_vector)
        raw = _raw_value(body, [[1, 2], [3, 4]])
        # Outer vector length: 2
        assert raw[0] == 2
        # First inner vector: length 2, then [1,2]
        # Second inner vector: length 2, then [3,4]
        assert raw[1] == 2
        assert raw[2:4] == [1, 2]
        assert raw[4] == 2
        assert raw[5:7] == [3, 4]

    def test_datatype_string(self):
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="string",
            type_name="String",
            type_parameters=[],
        )
        raw = _raw_value(body, "hello")
        assert raw[0] == 5
        assert raw[1:] == [ord(c) for c in "hello"]

    def test_datatype_id(self):
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="object",
            type_name="ID",
            type_parameters=[],
        )
        raw = _raw_value(body, "0x1")
        assert len(raw) == 32

    def test_option_none(self):
        inner = OpenMoveScalarBodyGQL(scalar_type="u64")
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="option",
            type_name="Option",
            type_parameters=[inner],
        )
        raw = _raw_value(body, None)
        assert raw == [0]

    def test_option_some(self):
        inner = OpenMoveScalarBodyGQL(scalar_type="u8")
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="option",
            type_name="Option",
            type_parameters=[inner],
        )
        raw = _raw_value(body, 42)
        assert raw[0] == 1  # Some tag
        assert raw[1] == 42

    def test_vecmap_scalar_keys_values(self):
        k_body = OpenMoveScalarBodyGQL(scalar_type="u64")
        v_body = OpenMoveScalarBodyGQL(scalar_type="u8")
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="vec_map",
            type_name="VecMap",
            type_parameters=[k_body, v_body],
        )
        raw = _raw_value(body, {1: 10, 2: 20})
        assert raw[0] == 2  # len=2


# ── Error cases: type mismatches ─────────────────────────────────────────────


class TestTypeErrors:
    """Test that encoder raises errors on type mismatches."""

    def test_vector_non_list(self):
        body = OpenMoveVectorBodyGQL(inner=OpenMoveScalarBodyGQL(scalar_type="u64"))
        with pytest.raises(ValueError, match="Expected list for vector"):
            _raw_value(body, 42)

    def test_string_from_int(self):
        with pytest.raises((TypeError, AttributeError)):
            _scalar_raw(123, "String")

    def test_address_invalid_format(self):
        with pytest.raises(ValueError):
            _scalar_raw("not-an-address", "address")

    def test_vecmap_wrong_type(self):
        k_body = OpenMoveScalarBodyGQL(scalar_type="u8")
        v_body = OpenMoveScalarBodyGQL(scalar_type="u8")
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="vec_map",
            type_name="VecMap",
            type_parameters=[k_body, v_body],
        )
        with pytest.raises((TypeError, ValueError)):
            _raw_value(body, "not a dict or list")

    def test_option_missing_type_param(self):
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="option",
            type_name="Option",
            type_parameters=[],  # Missing!
        )
        with pytest.raises(ValueError, match="Option missing type parameter"):
            _raw_value(body, 42)

    def test_vecset_missing_type_param(self):
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="vec_set",
            type_name="VecSet",
            type_parameters=[],  # Missing!
        )
        with pytest.raises(ValueError, match="VecSet missing type parameter"):
            _raw_value(body, [1, 2])

    def test_object_type_raw_encoding_fails(self):
        """Cannot raw-encode user-defined object types."""
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="my_module",
            type_name="MyStruct",
            type_parameters=[],
        )
        with pytest.raises(ValueError, match="Cannot raw-encode object type"):
            _raw_value(body, {})


# ── Top-level encode_arg (async) ────────────────────────────────────────────


@pytest.mark.asyncio
class TestEncodeArg:
    """Test encode_arg dispatcher with mocked parser."""

    async def test_scalar_u64(self):
        parser = MockArgParser(None)
        body = OpenMoveScalarBodyGQL(scalar_type="u64")
        result = await encode_arg(body, 1000, None, parser)
        assert result is not None

    async def test_scalar_bool(self):
        parser = MockArgParser(None)
        body = OpenMoveScalarBodyGQL(scalar_type="bool")
        result = await encode_arg(body, True, None, parser)
        assert result is not None

    async def test_scalar_address(self):
        parser = MockArgParser(None)
        body = OpenMoveScalarBodyGQL(scalar_type="address")
        result = await encode_arg(body, "0x1", None, parser)
        assert result is not None

    async def test_vector_u8(self):
        parser = MockArgParser(None)
        body = OpenMoveVectorBodyGQL(inner=OpenMoveScalarBodyGQL(scalar_type="u8"))
        result = await encode_arg(body, [1, 2, 3], None, parser)
        assert result is not None

    async def test_datatype_string(self):
        parser = MockArgParser(None)
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="string",
            type_name="String",
            type_parameters=[],
        )
        result = await encode_arg(body, "hello", None, parser)
        assert result is not None

    async def test_option_some(self):
        parser = MockArgParser(None)
        inner = OpenMoveScalarBodyGQL(scalar_type="u8")
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="option",
            type_name="Option",
            type_parameters=[inner],
        )
        result = await encode_arg(body, 42, None, parser)
        assert result is not None

    async def test_option_none(self):
        parser = MockArgParser(None)
        inner = OpenMoveScalarBodyGQL(scalar_type="u8")
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="option",
            type_name="Option",
            type_parameters=[inner],
        )
        result = await encode_arg(body, None, None, parser)
        assert result is not None

    async def test_object_type_calls_parser(self):
        parser = MockArgParser(None)
        body = OpenMoveDatatypeBodyGQL(
            package="0x1",
            module="my_module",
            type_name="MyObject",
            type_parameters=[],
        )
        result = await encode_arg(body, "0x2", None, parser)
        assert result is not None

    async def test_type_param_calls_parser(self):
        parser = MockArgParser(None)
        body = OpenMoveTypeParamBodyGQL(index=0)
        result = await encode_arg(body, "0x2", None, parser)
        assert result is not None

    async def test_scalar_type_error(self):
        parser = MockArgParser(None)
        body = OpenMoveScalarBodyGQL(scalar_type="u64")
        with pytest.raises((TypeError, ValueError)):
            await encode_arg(body, "not a number", None, parser)


# ── build_args integration ───────────────────────────────────────────────────


@pytest.mark.asyncio
class TestBuildArgs:
    """Test build_args with parameter lists."""

    async def test_single_scalar_param(self):
        parser = MockArgParser(None)
        params = [
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="u64"),
                ),
                repr="",
            )
        ]
        result = await parser.build_args([1000], params)
        assert len(result) == 1

    async def test_multiple_params(self):
        parser = MockArgParser(None)
        params = [
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="u64"),
                ),
                repr="",
            ),
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="bool"),
                ),
                repr="",
            ),
        ]
        result = await parser.build_args([1000, True], params)
        assert len(result) == 2

    async def test_argument_count_mismatch_too_few(self):
        parser = MockArgParser(None)
        params = [
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="u64"),
                ),
                repr="",
            ),
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="u64"),
                ),
                repr="",
            ),
        ]
        with pytest.raises(ValueError, match="Argument count mismatch"):
            await parser.build_args([1000], params)

    async def test_argument_count_mismatch_too_many(self):
        parser = MockArgParser(None)
        params = [
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="u64"),
                ),
                repr="",
            )
        ]
        with pytest.raises(ValueError, match="Argument count mismatch"):
            await parser.build_args([1000, 2000], params)

    async def test_bcs_argument_passthrough(self):
        parser = MockArgParser(None)
        bcs_arg = bcs.Argument("Result", 0)
        params = [
            OpenMoveTypeGQL(
                signature=OpenMoveTypeSignatureGQL(
                    ref=None,
                    body=OpenMoveScalarBodyGQL(scalar_type="u64"),
                ),
                repr="",
            )
        ]
        result = await parser.build_args([bcs_arg], params)
        assert result[0] == bcs_arg
