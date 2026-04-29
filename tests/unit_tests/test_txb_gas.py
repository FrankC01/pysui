#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for the gas selection redesign — all offline, no network required.

Covers:
    - compute_gas_budget  (pysui.sui.sui_common.txb_gas)
    - coins_for_budget    (pysui.sui.sui_common.txb_gas)
    - No DeprecationWarning emitted by gas modules at import time
    - budget=0 regression guard (coins_for_budget treats 0 as a real budget)
    - _SuiTransactionBase._inspect_ptb_for_gas_coin (trxn_base)
"""

import logging
import warnings

import pytest
from unittest.mock import MagicMock, patch

# Suppress import-time deprecations from transitively imported legacy modules.
warnings.filterwarnings("ignore", category=DeprecationWarning)

from pysui.sui.sui_common.txb_gas import (
    _GAS_SAFE_OVERHEAD,
    _MAX_GAS_PAYMENT_OBJECTS,
    coins_for_budget,
    compute_gas_budget,
)
from pysui.sui.sui_bcs import bcs

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _make_coin(balance: int):
    """Simple mock coin with a .balance attribute."""
    c = MagicMock()
    c.balance = balance
    return c


def _balance(c) -> int:
    return c.balance


def _ref(c):
    """Identity ref_fn — returns the coin object so tests can inspect selection."""
    return c


def _make_pure_u64(value: int) -> bcs.CallArg:
    """Build a Pure CallArg encoding an unsigned 64-bit integer (little-endian)."""
    raw = list(value.to_bytes(8, "little"))
    return bcs.CallArg("Pure", raw)


# ---------------------------------------------------------------------------
# _FakeTxn — minimal stand-in for _SuiTransactionBase
#
# Provides only the `builder` attribute accessed by _inspect_ptb_for_gas_coin.
# Borrows the method directly from _SuiTransactionBase so we test the real code
# without constructing a live client.
# ---------------------------------------------------------------------------

from pysui.sui.sui_common.trxn_base import _SuiTransactionBase  # noqa: E402


class _FakeTxn:
    """Minimal _SuiTransactionBase stand-in for PTB inspection tests."""

    def __init__(self, commands: list, inputs: dict):
        self.builder = MagicMock()
        self.builder.commands = commands
        self.builder.inputs = inputs

    # Borrow the real implementation; `self` is bound to _FakeTxn instances.
    _inspect_ptb_for_gas_coin = _SuiTransactionBase._inspect_ptb_for_gas_coin


# ---------------------------------------------------------------------------
# TestComputeGasBudget
# ---------------------------------------------------------------------------


class TestComputeGasBudget:
    """compute_gas_budget correctness: overhead, rebate handling, branch selection."""

    def test_overhead_applied_to_computation_cost(self):
        """overhead = GAS_SAFE_OVERHEAD * gas_price is always added to computation cost."""
        comp, gas_price = 1_000_000, 1000
        result = compute_gas_budget(comp, storage_cost=0, storage_rebate=0, gas_price=gas_price)
        assert result == comp + _GAS_SAFE_OVERHEAD * gas_price

    def test_zero_rebate_storage_added(self):
        """With zero rebate and positive storage, second branch wins (comp + overhead + storage)."""
        comp, storage, gas_price = 1_000_000, 500_000, 1000
        overhead = _GAS_SAFE_OVERHEAD * gas_price
        result = compute_gas_budget(comp, storage, storage_rebate=0, gas_price=gas_price)
        assert result == comp + overhead + storage

    def test_partial_rebate_reduces_storage_net(self):
        """Partial rebate shrinks the net storage component; second branch still wins."""
        comp, storage, rebate, gas_price = 1_000_000, 500_000, 200_000, 1000
        overhead = _GAS_SAFE_OVERHEAD * gas_price
        result = compute_gas_budget(comp, storage, rebate, gas_price)
        assert result == comp + overhead + storage - rebate

    def test_rebate_exceeds_storage_first_branch_wins(self):
        """rebate > storage → second branch is smaller than first; first branch is returned."""
        comp, storage, rebate, gas_price = 1_000_000, 300_000, 500_000, 1000
        overhead = _GAS_SAFE_OVERHEAD * gas_price
        # second branch = comp + overhead + 300k - 500k = comp + overhead - 200k < first branch
        result = compute_gas_budget(comp, storage, rebate, gas_price)
        assert result == comp + overhead

    def test_zero_gas_price_produces_zero_overhead(self):
        """gas_price=0 → overhead=0; budget equals computation cost alone (edge case)."""
        result = compute_gas_budget(
            computation_cost=2_000_000, storage_cost=0, storage_rebate=0, gas_price=0
        )
        assert result == 2_000_000

    def test_gas_safe_overhead_constant_is_1000(self):
        """_GAS_SAFE_OVERHEAD must remain 1000 gas units per TS SDK contract."""
        assert _GAS_SAFE_OVERHEAD == 1000


# ---------------------------------------------------------------------------
# TestCoinsForBudget
# ---------------------------------------------------------------------------


class TestCoinsForBudget:
    """coins_for_budget: single-fit, merge, 256-cap, and edge cases."""

    def test_single_coin_fits_returned_alone(self):
        """The largest coin whose balance > budget is returned as a single-element list."""
        coins = [_make_coin(500_000_000), _make_coin(100_000_000)]
        result = coins_for_budget(coins, 200_000_000, _balance, _ref)
        assert len(result) == 1
        assert result[0].balance == 500_000_000

    def test_single_fit_picks_largest_when_multiple_qualify(self):
        """After sorting descending, the largest coin is always chosen for single-fit."""
        coins = [_make_coin(300_000_000), _make_coin(600_000_000), _make_coin(400_000_000)]
        result = coins_for_budget(coins, 250_000_000, _balance, _ref)
        assert len(result) == 1
        assert result[0].balance == 600_000_000

    def test_no_single_fit_merge_false_raises(self):
        """No single coin covers the budget and merge=False → ValueError mentioning merge_gas_budget."""
        coins = [_make_coin(100_000), _make_coin(200_000)]
        with pytest.raises(ValueError, match="merge_gas_budget=True"):
            coins_for_budget(coins, 500_000, _balance, _ref, merge=False)

    def test_merge_true_accumulates_descending(self):
        """merge=True accumulates coins descending by balance until budget is covered."""
        coins = [_make_coin(300_000), _make_coin(200_000), _make_coin(100_000)]
        # 300k + 200k = 500k >= 450k; third coin is not needed
        result = coins_for_budget(coins, 450_000, _balance, _ref, merge=True)
        assert len(result) == 2
        assert {c.balance for c in result} == {300_000, 200_000}

    def test_merge_true_insufficient_total_raises(self):
        """merge=True but total balance of all coins < budget → ValueError."""
        coins = [_make_coin(100_000), _make_coin(100_000)]
        with pytest.raises(ValueError, match="transaction requires"):
            coins_for_budget(coins, 500_000, _balance, _ref, merge=True)

    def test_256_coin_cap_applied_before_selection(self):
        """Coins beyond the 256 protocol limit are discarded before selection.

        300 coins × 1 MIST each = 300 total, but only 256 are kept after the cap.
        Budget of 270 exceeds 256, so the call must raise even though the uncapped
        total would have been sufficient.
        """
        coins = [_make_coin(1) for _ in range(300)]
        with pytest.raises(ValueError, match="transaction requires"):
            coins_for_budget(coins, 270, _balance, _ref, merge=True)

    def test_256_cap_keeps_highest_balance_coins(self):
        """When more than 256 coins are provided, the 256 with the highest balance are kept."""
        high = [_make_coin(1_000_000) for _ in range(10)]
        low = [_make_coin(1) for _ in range(290)]
        # Deliberately pass them unsorted to verify sorting is done internally.
        result = coins_for_budget(low + high, 5_000_000, _balance, _ref, merge=True)
        assert all(c.balance == 1_000_000 for c in result)

    def test_budget_zero_is_satisfied_by_any_positive_coin(self):
        """budget=0 is a valid literal value — coins_for_budget must not skip selection.

        Regression guard: the old `if not budget:` guard treated 0 as 'no budget',
        which was fixed to `if budget is None:` in the caller. This test confirms
        the selection path handles a zero budget without raising.
        """
        coins = [_make_coin(1)]
        result = coins_for_budget(coins, 0, _balance, _ref)
        assert len(result) == 1

    def test_ref_fn_is_applied_to_returned_coins(self):
        """ref_fn is called on every selected coin; its return value is what is returned."""
        sentinel = object()
        coin = _make_coin(999_999_999)
        result = coins_for_budget([coin], 100_000, _balance, lambda c: sentinel)
        assert result == [sentinel]

    def test_max_gas_payment_objects_constant_is_256(self):
        """_MAX_GAS_PAYMENT_OBJECTS must remain 256 per protocol constraint."""
        assert _MAX_GAS_PAYMENT_OBJECTS == 256


# ---------------------------------------------------------------------------
# TestNoDeprecationWarning
# ---------------------------------------------------------------------------


class TestNoDeprecationWarning:
    """Gas modules must not emit DeprecationWarning at import time.

    The Step 0 change swapped DryRunTransactionKind (deprecated) for
    SimulateTransactionKind. These tests guard against regression.
    """

    def test_pgql_txb_gas_no_deprecation_on_import(self):
        """pgql_txb_gas must not raise DeprecationWarning when imported."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            import pysui.sui.sui_pgql.pgql_txb_gas  # noqa: F401

        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert deprecations == [], (
            "Unexpected DeprecationWarning(s) from pgql_txb_gas: "
            + str([str(w.message) for w in deprecations])
        )

    def test_txb_gas_async_get_gas_data_importable(self):
        """async_get_gas_data must be importable from sui_common.txb_gas (unified path)."""
        from pysui.sui.sui_common.txb_gas import async_get_gas_data  # noqa: F401

        assert callable(async_get_gas_data)


# ---------------------------------------------------------------------------
# TestInspectPtbForGasCoin
# ---------------------------------------------------------------------------


class TestInspectPtbForGasCoin:
    """_SuiTransactionBase._inspect_ptb_for_gas_coin PTB scanning logic."""

    # -- Helpers --

    @staticmethod
    def _cmd(name: str, val) -> bcs.Command:
        return bcs.Command(name, val)

    # -- No GasCoin cases --

    def test_empty_commands_returns_false_zero(self):
        """No commands → (False, 0)."""
        txn = _FakeTxn(commands=[], inputs={})
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is False
        assert draw == 0

    def test_transfer_no_gas_coin_returns_false_zero(self):
        """TransferObjects with no GasCoin references → (False, 0)."""
        cmd = self._cmd(
            "TransferObjects",
            bcs.TransferObjects(
                [bcs.Argument("Input", 0)],
                bcs.Argument("Input", 1),
            ),
        )
        txn = _FakeTxn(commands=[cmd], inputs={})
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is False
        assert draw == 0

    # -- SplitCoin(GasCoin) detection and draw accumulation --

    def test_split_gas_coin_pure_amount_accumulated(self):
        """SplitCoin(GasCoin, [Input(0)]) → uses_gas_coin=True, draw=amount."""
        amount = 1_000_000_000
        inputs = {MagicMock(): _make_pure_u64(amount)}
        cmd = self._cmd(
            "SplitCoin",
            bcs.SplitCoin(bcs.Argument("GasCoin"), [bcs.Argument("Input", 0)]),
        )
        txn = _FakeTxn(commands=[cmd], inputs=inputs)
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == amount

    def test_split_gas_coin_multiple_pure_amounts_summed(self):
        """Multiple pure amounts in one SplitCoin(GasCoin) are all summed into draw."""
        a1, a2 = 500_000_000, 300_000_000
        inputs = {MagicMock(): _make_pure_u64(a1), MagicMock(): _make_pure_u64(a2)}
        cmd = self._cmd(
            "SplitCoin",
            bcs.SplitCoin(
                bcs.Argument("GasCoin"),
                [bcs.Argument("Input", 0), bcs.Argument("Input", 1)],
            ),
        )
        txn = _FakeTxn(commands=[cmd], inputs=inputs)
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == a1 + a2

    def test_split_non_gas_coin_source_not_accumulated(self):
        """SplitCoin from a non-GasCoin source → uses_gas_coin=False, draw=0."""
        cmd = self._cmd(
            "SplitCoin",
            bcs.SplitCoin(bcs.Argument("Input", 0), [bcs.Argument("Input", 1)]),
        )
        txn = _FakeTxn(commands=[cmd], inputs={})
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is False
        assert draw == 0

    def test_split_gas_coin_result_amount_warns_and_draw_zero(self):
        """SplitCoin(GasCoin, [Result(0)]) → uses_gas_coin=True, draw=0, warning logged."""
        cmd = self._cmd(
            "SplitCoin",
            bcs.SplitCoin(bcs.Argument("GasCoin"), [bcs.Argument("Result", 0)]),
        )
        txn = _FakeTxn(commands=[cmd], inputs={})
        with patch.object(
            logging.getLogger("pysui.sui.sui_common.trxn_base"), "warning"
        ) as mock_warn:
            uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == 0
        assert mock_warn.called
        assert "Dynamic amount" in mock_warn.call_args[0][0]

    def test_two_split_gas_coin_commands_draw_summed(self):
        """Two SplitCoin(GasCoin) commands accumulate draw from both."""
        a1, a2 = 200_000_000, 800_000_000
        inputs = {MagicMock(): _make_pure_u64(a1), MagicMock(): _make_pure_u64(a2)}
        cmd1 = self._cmd(
            "SplitCoin",
            bcs.SplitCoin(bcs.Argument("GasCoin"), [bcs.Argument("Input", 0)]),
        )
        cmd2 = self._cmd(
            "SplitCoin",
            bcs.SplitCoin(bcs.Argument("GasCoin"), [bcs.Argument("Input", 1)]),
        )
        txn = _FakeTxn(commands=[cmd1, cmd2], inputs=inputs)
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == a1 + a2

    # -- MergeCoins detection --

    def test_merge_coins_to_gas_sets_flag_no_draw(self):
        """MergeCoins(ToCoin=GasCoin) → uses_gas_coin=True, draw=0 (adds balance, not draw)."""
        cmd = self._cmd(
            "MergeCoins",
            bcs.MergeCoins(bcs.Argument("GasCoin"), [bcs.Argument("Input", 0)]),
        )
        txn = _FakeTxn(commands=[cmd], inputs={})
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == 0

    def test_merge_coins_from_gas_sets_flag(self):
        """MergeCoins(ToCoin=Input, FromCoins=[GasCoin]) → uses_gas_coin=True."""
        cmd = self._cmd(
            "MergeCoins",
            bcs.MergeCoins(bcs.Argument("Input", 0), [bcs.Argument("GasCoin")]),
        )
        txn = _FakeTxn(commands=[cmd], inputs={})
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == 0

    # -- TransferObjects detection --

    def test_transfer_objects_gas_coin_in_objects_sets_flag(self):
        """TransferObjects([GasCoin], addr) → uses_gas_coin=True."""
        cmd = self._cmd(
            "TransferObjects",
            bcs.TransferObjects([bcs.Argument("GasCoin")], bcs.Argument("Input", 0)),
        )
        txn = _FakeTxn(commands=[cmd], inputs={})
        uses, draw = txn._inspect_ptb_for_gas_coin()
        assert uses is True
        assert draw == 0
