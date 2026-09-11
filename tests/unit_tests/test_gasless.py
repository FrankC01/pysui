#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for gasless stablecoin transfer eligibility — all offline, no live node."""

import dataclasses
from types import SimpleNamespace
from typing import Optional
import pytest
from unittest.mock import AsyncMock

from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.txn_base import _TransactionBase
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_grpc.suimsgs.google import protobuf as _google_protobuf


# ---------------------------------------------------------------------------
# Test Constants
# ---------------------------------------------------------------------------

_USDC = "0xdba34672e30cb065b1f93e3ab55318768fd6fef66c15942c9f7cb846e2f900e7::usdc::USDC"
_USDSUI = "0x44f838219cf67b058f3b37907b655f226153c18e33dfcd0da559a844fea9b1c1::usdsui::USDSUI"
_AUSD = "0x2053d08c1e2bd02791056171aab0fd12bd7cd7efad2ab8f6b9c8902f14df2ff2::ausd::AUSD"
_WAL = "0x8270feb7375eee355e64fdb69c50abb6b5f9393a722883c1cf45f8e26048810a::wal::WAL"

_ALLOWLIST = [[_USDC, "10000"], [_USDSUI, "10000"], [_AUSD, "10000"]]
"""Real mainnet gasless_allowed_token_types entries (protocol v129, dumped 2026-07-30) — confirms multiple stablecoins are allow-listed simultaneously, preventing single-token assumption tests."""


# ---------------------------------------------------------------------------
# Minimal concrete AsyncClientBase for testing gasless_for
# ---------------------------------------------------------------------------

class _MockAsyncClient(AsyncClientBase):
    """Minimal concrete client for testing gasless_for."""

    _protocol: str = "gql"

    @property
    def config(self):
        """Stub."""
        return None

    async def transaction(self, **kwargs):
        """Stub."""
        return None

    async def __aenter__(self):
        """Stub."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stub."""
        pass

    async def execute(self, *, command, timeout=None, headers=None):
        """Stub — replaced per test via mock."""
        raise NotImplementedError("replace with mock")


# ---------------------------------------------------------------------------
# Tests for gasless_for method
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGaslessFor:
    """Tests for AsyncClientBase.gasless_for() method."""

    async def test_enable_gasless_false_returns_false(self):
        """When enable_gasless is False, gasless_for returns False."""
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(False),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDC])

        assert output is False

    async def test_enable_gasless_key_absent_returns_false(self):
        """When enable_gasless key is absent from configs, gasless_for returns False."""
        client = _MockAsyncClient()
        configs = {}
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDC])

        assert output is False

    async def test_enable_gasless_true_but_allowlist_absent_returns_false(self):
        """When enable_gasless is True but allowlist key absent (GraphQL case), returns False."""
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDC])

        assert output is False

    async def test_allowlist_first_token_usdc_returns_true(self):
        """When coin_token matches first allowlist entry (USDC), returns True."""
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
            "gasless_allowed_token_types": _google_protobuf.Value.from_dict(_ALLOWLIST),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDC])

        assert output is True

    async def test_allowlist_second_token_usdsui_returns_true(self):
        """When coin_token matches second allowlist entry (USDSUI), returns True.

        This test explicitly verifies that multiple tokens in the allowlist work,
        preventing single-token assumption.
        """
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
            "gasless_allowed_token_types": _google_protobuf.Value.from_dict(_ALLOWLIST),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDSUI])

        assert output is True

    async def test_token_not_in_allowlist_returns_false(self):
        """When coin_token is not in the allowlist, returns False."""
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
            "gasless_allowed_token_types": _google_protobuf.Value.from_dict(_ALLOWLIST),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_WAL])

        assert output is False

    async def test_caches_protocol_config_on_second_call(self):
        """Protocol config is cached after first fetch; execute called once for two gasless_for calls."""
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
            "gasless_allowed_token_types": _google_protobuf.Value.from_dict(_ALLOWLIST),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        result1 = await client.gasless_for(coin_tokens=[_USDC])
        result2 = await client.gasless_for(coin_tokens=[_USDSUI])

        assert result1 is True
        assert result2 is True
        assert client.execute.await_count == 1

    async def test_execute_failure_raises_value_error(self):
        """When execute returns is_ok() False, gasless_for raises ValueError."""
        client = _MockAsyncClient()
        result = SimpleNamespace(
            is_ok=lambda: False,
            result_string="config fetch failed",
        )
        client.execute = AsyncMock(return_value=result)

        with pytest.raises(ValueError, match="config fetch failed"):
            await client.gasless_for(coin_tokens=[_USDC])

    async def test_all_tokens_match_allowlist_returns_true(self):
        """When every coin_token in coin_tokens matches the allowlist, returns True."""
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
            "gasless_allowed_token_types": _google_protobuf.Value.from_dict(_ALLOWLIST),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDC, _USDSUI, _AUSD])

        assert output is True

    async def test_one_token_not_in_allowlist_returns_false(self):
        """When even one coin_token in coin_tokens is not allowlisted, returns False even if others match.

        This explicitly verifies the "all must match" semantics — a PTB
        cannot get gasless sponsorship by mixing an allowlisted stablecoin
        with a non-allowlisted token.
        """
        client = _MockAsyncClient()
        configs = {
            "enable_gasless": _google_protobuf.Value.from_dict(True),
            "gasless_allowed_token_types": _google_protobuf.Value.from_dict(_ALLOWLIST),
        }
        result_data = SimpleNamespace(configs=configs)
        result = SimpleNamespace(
            is_ok=lambda: True,
            result_data=result_data,
        )
        client.execute = AsyncMock(return_value=result)

        output = await client.gasless_for(coin_tokens=[_USDC, _WAL])

        assert output is False


# ---------------------------------------------------------------------------
# Tests for _inspect_ptb_for_gasless method
# ---------------------------------------------------------------------------

def _build_move_call_command(
    package: str,
    module: str,
    function: str,
    type_arg: bcs.TypeTag,
) -> bcs.Command:
    """Helper to build a MoveCall command with given package, module, function, and type argument.

    :param package: Package address as string (e.g., "0x2")
    :param module: Module name as string
    :param function: Function name as string
    :param type_arg: TypeTag for the type argument
    :returns: A bcs.Command with enum_name "MoveCall"
    """
    package_addr = bcs.Address.from_str(package)
    prog_call = bcs.ProgrammableMoveCall(package_addr, module, function, [type_arg], [])
    return bcs.Command("MoveCall", prog_call)


def _build_transfer_objects_command() -> bcs.Command:
    """Build a minimal valid TransferObjects command for disqualification testing.

    The payload is never inspected by _inspect_ptb_for_gasless; this returns None
    for any non-MoveCall command, so the TransferObjects payload only needs to be
    a valid canoser instance.

    :returns: A bcs.Command with enum_name "TransferObjects"
    """
    transfer_obj = bcs.TransferObjects(
        [bcs.Argument("GasCoin")],
        bcs.Argument("Input", 0),
    )
    return bcs.Command("TransferObjects", transfer_obj)


def _build_split_coin_command() -> bcs.Command:
    """Build a minimal valid SplitCoin command for passthrough testing.

    The payload is part of _GASLESS_PASSTHRU_COMMANDS and is skipped during
    gasless eligibility inspection, so the payload only needs to be a valid
    canoser instance.

    :returns: A bcs.Command with enum_name "SplitCoin"
    """
    split_coin = bcs.SplitCoin(
        bcs.Argument("GasCoin"),
        [bcs.Argument("Input", 0)],
    )
    return bcs.Command("SplitCoin", split_coin)


def _build_merge_coins_command() -> bcs.Command:
    """Build a minimal valid MergeCoins command for passthrough testing.

    The payload is part of _GASLESS_PASSTHRU_COMMANDS and is skipped during
    gasless eligibility inspection, so the payload only needs to be a valid
    canoser instance.

    :returns: A bcs.Command with enum_name "MergeCoins"
    """
    merge_coins = bcs.MergeCoins(
        bcs.Argument("GasCoin"),
        [bcs.Argument("Input", 0)],
    )
    return bcs.Command("MergeCoins", merge_coins)


class TestInspectPtbForGasless:
    """Tests for _TransactionBase._inspect_ptb_for_gasless() method."""

    def test_single_coin_send_funds_at_0x2_returns_usdc_type(self):
        """Single coin::send_funds move call at 0x2 with USDC type arg returns USDC type string."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == [_USDC]

    def test_single_balance_send_funds_at_0x2_returns_usdc_type(self):
        """Single balance::send_funds move call at 0x2 with USDC type arg returns USDC type string."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x2",
                        "balance",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == [_USDC]

    def test_transfer_objects_command_returns_none(self):
        """A TransferObjects command (not in passthru, not MoveCall) returns None."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_transfer_objects_command(),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result is None

    def test_split_coin_plus_move_call_returns_coin_type(self):
        """SplitCoin command (passthru) plus valid coin::send_funds move call returns coin type."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_split_coin_command(),
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == [_USDC]

    def test_merge_coins_plus_move_call_returns_coin_type(self):
        """MergeCoins command (passthru) plus valid coin::send_funds move call returns coin type."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_merge_coins_command(),
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == [_USDC]

    def test_only_split_and_merge_no_move_call_returns_none(self):
        """Only SplitCoin and MergeCoins commands, no MoveCall, returns None."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_split_coin_command(),
                    _build_merge_coins_command(),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result is None

    def test_two_different_coin_types_returns_both_types(self):
        """Two move calls with different coin types (USDC and USDSUI) returns both types (heterogeneous stablecoins permitted)."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDSUI),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == sorted([_USDC, _USDSUI])

    def test_move_call_at_0x3_returns_none(self):
        """Move call at 0x3 (not 0x2) with whitelisted module/function returns None."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x3",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result is None

    def test_non_whitelisted_function_returns_none(self):
        """Move call at 0x2 with non-whitelisted (module, function) returns None."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "mint",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result is None

    def test_balance_wrapped_type_argument_returns_inner_type(self):
        """funds_accumulator::withdrawal_split with Balance<USDC> type arg returns inner USDC type string."""
        balance_usdc = bcs.TypeTag.type_tag_from(
            "0x2::balance::Balance<" + _USDC + ">"
        )
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x2",
                        "funds_accumulator",
                        "withdrawal_split",
                        balance_usdc,
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == [_USDC]

    def test_three_different_real_stablecoins_returns_all_types(self):
        """Three move calls with three distinct real mainnet stablecoin types (USDC, USDSUI, AUSD) returns all three, sorted."""
        stub_txn = SimpleNamespace(
            builder=SimpleNamespace(
                commands=[
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDC),
                    ),
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_USDSUI),
                    ),
                    _build_move_call_command(
                        "0x2",
                        "coin",
                        "send_funds",
                        bcs.TypeTag.type_tag_from(_AUSD),
                    ),
                ]
            )
        )

        result = _TransactionBase._inspect_ptb_for_gasless(stub_txn)

        assert result == sorted([_USDC, _USDSUI, _AUSD])
