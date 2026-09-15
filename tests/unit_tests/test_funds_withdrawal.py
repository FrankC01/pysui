#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for SENDER_ALLOWANCE funds-withdrawal support (BCS layer and PTB builder helper)."""

import pytest
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.txn_base import FundsSource
from pysui.sui.sui_common.async_txn import _build_withdraw_from
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot

_FUNDER = "0x" + "11" * 32
_ALLOWANCE = "0x" + "22" * 32


class TestSenderAllowanceBCS:
    """Test the SenderAllowance struct and WithdrawFrom SENDER_ALLOWANCE variant."""

    def test_sender_allowance_fields(self):
        """SenderAllowance should hold Funder and Allowance as Address values."""
        sa = bcs.SenderAllowance(
            bcs.Address.from_str(_FUNDER), bcs.Address.from_str(_ALLOWANCE)
        )
        assert sa.Funder.to_address_str() == _FUNDER
        assert sa.Allowance.to_address_str() == _ALLOWANCE

    def test_withdraw_from_sender_allowance_variant(self):
        """WithdrawFrom should carry a SenderAllowance value under the SENDER_ALLOWANCE variant."""
        sa = bcs.SenderAllowance(
            bcs.Address.from_str(_FUNDER), bcs.Address.from_str(_ALLOWANCE)
        )
        wf = bcs.WithdrawFrom("SENDER_ALLOWANCE", sa)
        assert wf.enum_name == "SENDER_ALLOWANCE"
        assert wf.value.Funder.to_address_str() == _FUNDER
        assert wf.value.Allowance.to_address_str() == _ALLOWANCE

    def test_withdraw_from_sender_allowance_serialize_roundtrip(self):
        """WithdrawFrom SENDER_ALLOWANCE should survive a BCS serialize/deserialize roundtrip."""
        sa = bcs.SenderAllowance(
            bcs.Address.from_str(_FUNDER), bcs.Address.from_str(_ALLOWANCE)
        )
        wf = bcs.WithdrawFrom("SENDER_ALLOWANCE", sa)
        raw = wf.serialize()
        restored = bcs.WithdrawFrom.deserialize(raw)
        assert restored.enum_name == "SENDER_ALLOWANCE"
        assert restored.value.Funder.to_address_str() == _FUNDER
        assert restored.value.Allowance.to_address_str() == _ALLOWANCE

    def test_withdraw_from_sender_variant_unchanged(self):
        """Pre-existing SENDER/SPONSOR variants (no associated data) must be unaffected."""
        wf = bcs.WithdrawFrom("SENDER")
        assert wf.enum_name == "SENDER"
        assert wf.value is None


class TestFundsWithdrawalToGrpcInput:
    """Test FundsWithdrawal.to_grpc_input() across all three WithdrawFrom variants."""

    def _funds_withdrawal(self, source: bcs.WithdrawFrom) -> bcs.FundsWithdrawal:
        return bcs.FundsWithdrawal(
            bcs.Reservation("Amount", 1000),
            bcs.WithdrawalType("Balance", bcs.StructTag.sui_coin()),
            source,
        )

    def test_sender_allowance_populates_funder_and_allowance(self):
        """SENDER_ALLOWANCE branch must populate the gRPC funder/allowance fields."""
        sa = bcs.SenderAllowance(
            bcs.Address.from_str(_FUNDER), bcs.Address.from_str(_ALLOWANCE)
        )
        fw = self._funds_withdrawal(bcs.WithdrawFrom("SENDER_ALLOWANCE", sa))
        gi = fw.to_grpc_input()
        assert gi.funds_withdrawal.source == sui_prot.FundsWithdrawalSource.SENDER_ALLOWANCE
        assert gi.funds_withdrawal.funder == _FUNDER
        assert gi.funds_withdrawal.allowance == _ALLOWANCE

    def test_sender_leaves_funder_and_allowance_none(self):
        """SENDER branch must not populate funder/allowance (regression guard)."""
        fw = self._funds_withdrawal(bcs.WithdrawFrom("SENDER"))
        gi = fw.to_grpc_input()
        assert gi.funds_withdrawal.source == sui_prot.FundsWithdrawalSource.SENDER
        assert gi.funds_withdrawal.funder is None
        assert gi.funds_withdrawal.allowance is None

    def test_sponsor_leaves_funder_and_allowance_none(self):
        """SPONSOR branch must not populate funder/allowance (regression guard)."""
        fw = self._funds_withdrawal(bcs.WithdrawFrom("SPONSOR"))
        gi = fw.to_grpc_input()
        assert gi.funds_withdrawal.source == sui_prot.FundsWithdrawalSource.SPONSOR
        assert gi.funds_withdrawal.funder is None
        assert gi.funds_withdrawal.allowance is None


class TestBuildWithdrawFrom:
    """Test the async_txn._build_withdraw_from validation-gate helper."""

    def test_sender_allowance_with_both_values(self):
        """SENDER_ALLOWANCE with funder and allowance builds the correct BCS variant."""
        wf = _build_withdraw_from(
            source=FundsSource.SENDER_ALLOWANCE, funder=_FUNDER, allowance=_ALLOWANCE
        )
        assert wf.enum_name == "SENDER_ALLOWANCE"
        assert wf.value.Funder.to_address_str() == _FUNDER
        assert wf.value.Allowance.to_address_str() == _ALLOWANCE

    def test_sender_allowance_missing_funder_raises(self):
        """SENDER_ALLOWANCE without funder must raise."""
        with pytest.raises(ValueError):
            _build_withdraw_from(
                source=FundsSource.SENDER_ALLOWANCE, funder=None, allowance=_ALLOWANCE
            )

    def test_sender_allowance_missing_allowance_raises(self):
        """SENDER_ALLOWANCE without allowance must raise."""
        with pytest.raises(ValueError):
            _build_withdraw_from(
                source=FundsSource.SENDER_ALLOWANCE, funder=_FUNDER, allowance=None
            )

    def test_sender_allowance_missing_both_raises(self):
        """SENDER_ALLOWANCE without funder or allowance must raise."""
        with pytest.raises(ValueError):
            _build_withdraw_from(
                source=FundsSource.SENDER_ALLOWANCE, funder=None, allowance=None
            )

    @pytest.mark.parametrize("source", [FundsSource.SENDER, FundsSource.SPONSOR])
    def test_non_allowance_source_with_funder_raises(self, source):
        """SENDER/SPONSOR must reject a funder value (prevents silent drop)."""
        with pytest.raises(ValueError):
            _build_withdraw_from(source=source, funder=_FUNDER, allowance=None)

    @pytest.mark.parametrize("source", [FundsSource.SENDER, FundsSource.SPONSOR])
    def test_non_allowance_source_with_allowance_raises(self, source):
        """SENDER/SPONSOR must reject an allowance value (prevents silent drop)."""
        with pytest.raises(ValueError):
            _build_withdraw_from(source=source, funder=None, allowance=_ALLOWANCE)

    @pytest.mark.parametrize("source", [FundsSource.SENDER, FundsSource.SPONSOR])
    def test_non_allowance_source_without_values_unchanged(self, source):
        """SENDER/SPONSOR with no funder/allowance must build the pre-existing no-data variant."""
        wf = _build_withdraw_from(source=source, funder=None, allowance=None)
        assert wf.enum_name == source.name
        assert wf.value is None
