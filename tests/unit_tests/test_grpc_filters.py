#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.sui.sui_grpc.pgrpc_filters — all offline, no live node required.

Tests cover:
  - Literal default/explicit values
  - build_transaction_filter DNF composition (single predicate, AND within a
    term, OR across terms, negation, each predicate mapping, invalid predicate)
  - build_event_filter DNF composition and its narrower predicate set
"""

import pytest

import pysui.sui.sui_grpc.pgrpc_filters as pgf
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot


class TestLiteral:
    """Tests for the Literal NamedTuple."""

    def test_defaults(self):
        literal = pgf.Literal(predicate="sender")
        assert literal.predicate == "sender"
        assert literal.value is None
        assert literal.negated is False

    def test_explicit_values(self):
        literal = pgf.Literal(
            predicate="move_call", value="0xpkg::mod::fn", negated=True
        )
        assert literal.value == "0xpkg::mod::fn"
        assert literal.negated is True


class TestBuildTransactionFilter:
    """Tests for build_transaction_filter."""

    def test_single_predicate_single_term(self):
        result = pgf.build_transaction_filter(
            terms=[[pgf.Literal(predicate="sender", value="0xabc")]]
        )
        assert isinstance(result, sui_prot.TransactionFilter)
        assert len(result.terms) == 1
        assert len(result.terms[0].literals) == 1
        literal = result.terms[0].literals[0]
        assert literal.negated is False
        assert literal.sender.address == "0xabc"

    def test_and_within_term(self):
        result = pgf.build_transaction_filter(
            terms=[
                [
                    pgf.Literal(predicate="sender", value="0xabc"),
                    pgf.Literal(predicate="move_call", value="0xpkg::mod::fn"),
                ]
            ]
        )
        assert len(result.terms) == 1
        assert len(result.terms[0].literals) == 2
        assert result.terms[0].literals[0].sender.address == "0xabc"
        assert result.terms[0].literals[1].move_call.function == "0xpkg::mod::fn"

    def test_or_across_terms(self):
        result = pgf.build_transaction_filter(
            terms=[
                [pgf.Literal(predicate="sender", value="0xabc")],
                [pgf.Literal(predicate="event_type", value="0xpkg::mod::Event")],
            ]
        )
        assert len(result.terms) == 2
        assert result.terms[0].literals[0].sender.address == "0xabc"
        assert (
            result.terms[1].literals[0].event_type.event_type
            == "0xpkg::mod::Event"
        )

    def test_negation(self):
        result = pgf.build_transaction_filter(
            terms=[[pgf.Literal(predicate="sender", value="0xabc", negated=True)]]
        )
        assert result.terms[0].literals[0].negated is True

    def test_package_write_predicate_no_value(self):
        result = pgf.build_transaction_filter(
            terms=[[pgf.Literal(predicate="package_write")]]
        )
        literal = result.terms[0].literals[0]
        assert isinstance(literal.package_write, sui_prot.PackageWriteFilter)

    @pytest.mark.parametrize(
        "predicate,value,attr,field",
        [
            ("sender", "0xabc", "sender", "address"),
            ("affected_address", "0xabc", "affected_address", "address"),
            ("affected_object", "0xobj", "affected_object", "object_id"),
            ("move_call", "0xpkg::mod::fn", "move_call", "function"),
            ("emit_module", "0xpkg::mod", "emit_module", "module"),
            ("event_type", "0xpkg::mod::Event", "event_type", "event_type"),
            ("event_stream_head", "0xstream", "event_stream_head", "stream_id"),
        ],
    )
    def test_each_predicate_maps_correctly(self, predicate, value, attr, field):
        result = pgf.build_transaction_filter(
            terms=[[pgf.Literal(predicate=predicate, value=value)]]
        )
        leaf = getattr(result.terms[0].literals[0], attr)
        assert getattr(leaf, field) == value

    def test_invalid_predicate_raises(self):
        with pytest.raises(ValueError):
            pgf.build_transaction_filter(
                terms=[[pgf.Literal(predicate="not_a_real_predicate", value="x")]]
            )


class TestBuildEventFilter:
    """Tests for build_event_filter."""

    def test_single_predicate(self):
        result = pgf.build_event_filter(
            terms=[[pgf.Literal(predicate="sender", value="0xabc")]]
        )
        assert isinstance(result, sui_prot.EventFilter)
        assert result.terms[0].literals[0].sender.address == "0xabc"

    @pytest.mark.parametrize(
        "predicate,value,attr,field",
        [
            ("sender", "0xabc", "sender", "address"),
            ("emit_module", "0xpkg::mod", "emit_module", "module"),
            ("event_type", "0xpkg::mod::Event", "event_type", "event_type"),
            ("event_stream_head", "0xstream", "event_stream_head", "stream_id"),
        ],
    )
    def test_each_predicate_maps_correctly(self, predicate, value, attr, field):
        result = pgf.build_event_filter(
            terms=[[pgf.Literal(predicate=predicate, value=value)]]
        )
        leaf = getattr(result.terms[0].literals[0], attr)
        assert getattr(leaf, field) == value

    def test_tx_only_predicate_rejected(self):
        with pytest.raises(ValueError):
            pgf.build_event_filter(
                terms=[[pgf.Literal(predicate="move_call", value="0xpkg::mod::fn")]]
            )

    def test_affected_object_rejected(self):
        with pytest.raises(ValueError):
            pgf.build_event_filter(
                terms=[[pgf.Literal(predicate="affected_object", value="0xobj")]]
            )
