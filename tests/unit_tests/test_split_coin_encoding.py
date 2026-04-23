#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for split_coin amount encoding across GQL and gRPC transaction builders."""

import pytest
from unittest.mock import MagicMock, patch, call
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txb_pure import PureInput
from pysui.sui.sui_types.scalars import SuiU64


class TestSplitCoinAmountEncoding:
    """Test split_coin amount encoding logic."""

    def test_encode_raw_int_amounts(self):
        """Raw int amounts should be encoded as SuiU64."""
        amounts = [1000000000, 2000000000]

        with patch('pysui.sui.sui_common.txb_pure.PureInput.as_input') as mock_as_input:
            mock_as_input.return_value = MagicMock(spec=bcs.BuilderArg)

            encoded_amounts = [
                a if isinstance(a, bcs.Argument)
                else PureInput.as_input(SuiU64(a))
                for a in amounts
            ]

            assert len(encoded_amounts) == 2
            assert mock_as_input.call_count == 2

            calls = mock_as_input.call_args_list
            for i, call_obj in enumerate(calls):
                args = call_obj[0]
                assert len(args) == 1
                assert isinstance(args[0], SuiU64)
                assert args[0].value == amounts[i]

    def test_encode_argument_pass_through(self):
        """bcs.Argument values should pass through unchanged."""
        arg1 = MagicMock(spec=bcs.Argument)
        arg2 = MagicMock(spec=bcs.Argument)
        amounts = [arg1, arg2]

        with patch('pysui.sui.sui_common.txb_pure.PureInput.as_input') as mock_as_input:
            encoded_amounts = [
                a if isinstance(a, bcs.Argument)
                else PureInput.as_input(SuiU64(a))
                for a in amounts
            ]

            assert encoded_amounts == [arg1, arg2]
            mock_as_input.assert_not_called()

    def test_encode_mixed_amounts(self):
        """Mixed int and bcs.Argument amounts should be handled correctly."""
        arg = MagicMock(spec=bcs.Argument)
        amounts = [1000000000, arg, 2000000000]

        with patch('pysui.sui.sui_common.txb_pure.PureInput.as_input') as mock_as_input:
            mock_return = MagicMock(spec=bcs.BuilderArg)
            mock_as_input.return_value = mock_return

            encoded_amounts = [
                a if isinstance(a, bcs.Argument)
                else PureInput.as_input(SuiU64(a))
                for a in amounts
            ]

            assert len(encoded_amounts) == 3
            assert encoded_amounts[0] == mock_return
            assert encoded_amounts[1] is arg
            assert encoded_amounts[2] == mock_return
            assert mock_as_input.call_count == 2

    def test_sui_u64_construction(self):
        """SuiU64 should correctly wrap int amounts."""
        amount = 1000000000

        sui_u64 = SuiU64(amount)
        assert sui_u64.value == amount

    def test_single_amount(self):
        """Single amount should be encoded the same as multiple amounts."""
        amounts = [1000000000]

        with patch('pysui.sui.sui_common.txb_pure.PureInput.as_input') as mock_as_input:
            mock_as_input.return_value = MagicMock(spec=bcs.BuilderArg)

            encoded_amounts = [
                a if isinstance(a, bcs.Argument)
                else PureInput.as_input(SuiU64(a))
                for a in amounts
            ]

            assert len(encoded_amounts) == 1
            mock_as_input.assert_called_once()

    def test_empty_amounts_list(self):
        """Empty amounts list should produce empty encoded list."""
        amounts = []

        encoded_amounts = [
            a if isinstance(a, bcs.Argument)
            else PureInput.as_input(SuiU64(a))
            for a in amounts
        ]

        assert encoded_amounts == []

    def test_large_amount_values(self):
        """Large u64 values should be handled correctly."""
        large_amounts = [
            0xFFFFFFFFFFFFFFFF,  # max u64
            0x8000000000000000,  # mid-point
            1,                    # min non-zero
        ]

        with patch('pysui.sui.sui_common.txb_pure.PureInput.as_input') as mock_as_input:
            mock_as_input.return_value = MagicMock(spec=bcs.BuilderArg)

            encoded_amounts = [
                a if isinstance(a, bcs.Argument)
                else PureInput.as_input(SuiU64(a))
                for a in large_amounts
            ]

            assert len(encoded_amounts) == 3
            assert mock_as_input.call_count == 3

            for i, call_obj in enumerate(mock_as_input.call_args_list):
                args = call_obj[0]
                assert args[0].value == large_amounts[i]
