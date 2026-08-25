#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for private funds BCS structures.

These verify that ``pf_bcs`` mirrors the on-chain Move struct layout at
confidential-transfers ``c2f842c``. BCS is positional and carries no field
names, so a wrong field order or a missing field deserializes silently into
the wrong values rather than raising. The tests therefore deserialize blobs
laid out to the Move definition and assert each value lands where expected --
a self-consistent serialize/deserialize round trip alone would pass even if
the order were wrong.
"""

import pysui.private_transfer.pf_bcs as pf_bcs


def _element(fill: int) -> bytes:
    """A 32-byte group element, ULEB128 length-prefixed."""
    return bytes([32]) + bytes([fill] * 32)


def _encryption(ciphertext: int, handle: int) -> bytes:
    """An ``Encryption``: ciphertext element followed by decryption handle."""
    return _element(ciphertext) + _element(handle)


def _encrypted_amount(base: int) -> bytes:
    """An ``EncryptedAmount``: four ``Encryption`` limbs, l0 through l3."""
    return b"".join(_encryption(base + i, base + i + 100) for i in range(4))


def _accumulated_amount(base: int, terms: int) -> bytes:
    """An ``AccumulatedAmount``: an ``EncryptedAmount`` then a u16 term count."""
    return _encrypted_amount(base) + terms.to_bytes(2, "little")


def _balances(
    *, pk_fill: int, active_base: int, active_terms: int,
    pending_base: int, pending_terms: int, public_balance: int
) -> bytes:
    """A ``Balances<T>``: pk, active, pending, public_balance."""
    return (
        _element(pk_fill)
        + _accumulated_amount(active_base, active_terms)
        + _accumulated_amount(pending_base, pending_terms)
        + public_balance.to_bytes(8, "little")
    )


def _token_account(
    *, session: bytes, is_frozen: bool, accepts_deposits: bool, balances: bytes
) -> bytes:
    """A ``TokenAccount<T>``: session_id, is_frozen, accepts_deposits, balance."""
    return (
        bytes([len(session)])
        + session
        + bytes([1 if is_frozen else 0])
        + bytes([1 if accepts_deposits else 0])
        + balances
    )


def test_token_account_field_order():
    """Every field lands in its Move-defined position."""
    session = bytes(range(20))
    blob = _token_account(
        session=session,
        is_frozen=False,
        accepts_deposits=True,
        balances=_balances(
            pk_fill=0xAA,
            active_base=1,
            active_terms=3,
            pending_base=50,
            pending_terms=7,
            public_balance=12345,
        ),
    )
    account = pf_bcs.TokenAccount.deserialize(blob)

    assert bytes(account.session_id.id) == session
    assert not account.is_frozen
    assert account.accepts_deposits
    assert bytes(account.balance.pk.element.bytes) == bytes([0xAA] * 32)
    assert account.balance.active.terms == 3
    assert account.balance.pending.terms == 7
    assert account.balance.public_balance == 12345


def test_token_account_round_trip():
    """Deserializing then reserializing reproduces the original bytes."""
    blob = _token_account(
        session=bytes(range(20, 40)),
        is_frozen=True,
        accepts_deposits=False,
        balances=_balances(
            pk_fill=0x11,
            active_base=2,
            active_terms=0,
            pending_base=60,
            pending_terms=65535,
            public_balance=0,
        ),
    )
    assert pf_bcs.TokenAccount.deserialize(blob).serialize() == blob


def test_session_id_is_a_wrapper_struct():
    """``session_id`` is a ``SessionId`` struct, not a bare byte vector."""
    blob = _token_account(
        session=bytes(range(20)),
        is_frozen=False,
        accepts_deposits=False,
        balances=_balances(
            pk_fill=0, active_base=0, active_terms=0,
            pending_base=0, pending_terms=0, public_balance=0,
        ),
    )
    account = pf_bcs.TokenAccount.deserialize(blob)
    assert isinstance(account.session_id, pf_bcs.SessionId)


def test_public_key_is_a_wrapper_struct():
    """``pk`` is a ``PublicKey`` wrapping an element, not a bare element."""
    blob = _token_account(
        session=bytes(range(20)),
        is_frozen=False,
        accepts_deposits=False,
        balances=_balances(
            pk_fill=0x77, active_base=0, active_terms=0,
            pending_base=0, pending_terms=0, public_balance=0,
        ),
    )
    account = pf_bcs.TokenAccount.deserialize(blob)
    assert isinstance(account.balance.pk, pf_bcs.PublicKey)
    assert isinstance(account.balance.pk.element, pf_bcs.Element_G)


def test_balances_is_nested_not_flat():
    """Balance fields sit under ``balance``, not directly on the account."""
    blob = _token_account(
        session=bytes(range(20)),
        is_frozen=False,
        accepts_deposits=False,
        balances=_balances(
            pk_fill=0, active_base=0, active_terms=0,
            pending_base=0, pending_terms=0, public_balance=999,
        ),
    )
    account = pf_bcs.TokenAccount.deserialize(blob)
    assert isinstance(account.balance, pf_bcs.Balances)
    assert account.balance.public_balance == 999
    assert not hasattr(account, "public_balance")
    assert not hasattr(account, "active")


def test_accumulated_amount_limbs():
    """``AccumulatedAmount`` carries the four-limb ``EncryptedAmount``."""
    blob = _token_account(
        session=bytes(range(20)),
        is_frozen=False,
        accepts_deposits=False,
        balances=_balances(
            pk_fill=0, active_base=1, active_terms=1,
            pending_base=50, pending_terms=1, public_balance=0,
        ),
    )
    account = pf_bcs.TokenAccount.deserialize(blob)
    amount = account.balance.active.amount

    assert isinstance(amount, pf_bcs.EncryptedAmount)
    assert bytes(amount.l0.ciphertext.bytes) == bytes([1] * 32)
    assert bytes(amount.l0.decryption_handle.bytes) == bytes([101] * 32)
    assert bytes(amount.l3.ciphertext.bytes) == bytes([4] * 32)
    assert bytes(amount.l3.decryption_handle.bytes) == bytes([104] * 32)
