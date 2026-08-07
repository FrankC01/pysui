#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui gRPC subscription filter builders."""

from typing import Callable, NamedTuple, Optional, cast

import betterproto2

import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot


class Literal(NamedTuple):
    """One signed predicate literal in a subscription DNF filter.

    :param predicate: Name of the predicate to apply; must be one of the keys
        supported by the target filter (transaction or event predicate set).
    :param value: The predicate's value (unused for ``package_write``, which
        takes no value).
    :param negated: When True, matches items the predicate does *not* match.
    """

    predicate: str
    value: Optional[str] = None
    negated: bool = False


Term = list[Literal]
"""One conjunction (ANDed literals) in a DNF filter."""


PredicateBuilder = Callable[[Optional[str]], betterproto2.Message]

_TX_PREDICATES: dict[str, PredicateBuilder] = {
    "sender": lambda v: sui_prot.SenderFilter(address=v),
    "affected_address": lambda v: sui_prot.AffectedAddressFilter(address=v),
    "affected_object": lambda v: sui_prot.AffectedObjectFilter(object_id=v),
    "move_call": lambda v: sui_prot.MoveCallFilter(function=v),
    "emit_module": lambda v: sui_prot.EmitModuleFilter(module=v),
    "event_type": lambda v: sui_prot.EventTypeFilter(event_type=v),
    "event_stream_head": lambda v: sui_prot.EventStreamHeadFilter(stream_id=v),
    "package_write": lambda _: sui_prot.PackageWriteFilter(),
}

_EVENT_PREDICATES: dict[str, PredicateBuilder] = {
    key: _TX_PREDICATES[key]
    for key in ("sender", "emit_module", "event_type", "event_stream_head")
}


def _build_dnf_filter(
    terms: list[Term],
    *,
    predicates: dict[str, PredicateBuilder],
    term_cls: Callable[..., betterproto2.Message],
    literal_cls: Callable[..., betterproto2.Message],
    filter_cls: Callable[..., betterproto2.Message],
) -> betterproto2.Message:
    """Convert nested Term/Literal tuples into a protocol DNF filter message.

    :param terms: Outer list of ORed terms; each term is a list of ANDed literals.
    :param predicates: Mapping of predicate name to a leaf-message constructor.
    :param term_cls: The protobuf Term message constructor (e.g. TransactionTerm).
    :param literal_cls: The protobuf Literal message constructor (e.g.
        TransactionLiteral).
    :param filter_cls: The protobuf Filter message constructor (e.g.
        TransactionFilter).
    :raises ValueError: If a literal specifies a predicate name that is not
        supported by ``predicates``.
    :return: The constructed filter message.
    """
    proto_terms = []
    for literals in terms:
        proto_literals = []
        for literal in literals:
            if literal.predicate not in predicates:
                raise ValueError(f"Unsupported predicate '{literal.predicate}'")
            # The oneof field name is only known at runtime (validated against
            # `predicates` above), so it can't be a static keyword argument;
            # mypy cannot verify a dynamic **kwargs call against the concrete
            # message class's fields.
            proto_literals.append(
                literal_cls(
                    negated=literal.negated,
                    **{
                        literal.predicate: predicates[literal.predicate](
                            literal.value
                        )
                    },
                )  # type: ignore[call-arg]
            )
        proto_terms.append(term_cls(literals=proto_literals))  # type: ignore[call-arg]
    return filter_cls(terms=proto_terms)  # type: ignore[call-arg]


def build_transaction_filter(*, terms: list[Term]) -> sui_prot.TransactionFilter:
    """Build a TransactionFilter DNF proto from nested Term/Literal tuples.

    :param terms: Outer list of ORed terms; each term is a list of ANDed
        literals. Each literal's ``predicate`` must be one of: sender,
        affected_address, affected_object, move_call, emit_module, event_type,
        event_stream_head, package_write.
    :return: The constructed TransactionFilter.
    """
    return cast(
        sui_prot.TransactionFilter,
        _build_dnf_filter(
            terms,
            predicates=_TX_PREDICATES,
            term_cls=sui_prot.TransactionTerm,
            literal_cls=sui_prot.TransactionLiteral,
            filter_cls=sui_prot.TransactionFilter,
        ),
    )


def build_event_filter(*, terms: list[Term]) -> sui_prot.EventFilter:
    """Build an EventFilter DNF proto from nested Term/Literal tuples.

    :param terms: Outer list of ORed terms; each term is a list of ANDed
        literals. Each literal's ``predicate`` must be one of: sender,
        emit_module, event_type, event_stream_head.
    :return: The constructed EventFilter.
    """
    return cast(
        sui_prot.EventFilter,
        _build_dnf_filter(
            terms,
            predicates=_EVENT_PREDICATES,
            term_cls=sui_prot.EventTerm,
            literal_cls=sui_prot.EventLiteral,
            filter_cls=sui_prot.EventFilter,
        ),
    )
