#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for private funds derived-identifier helpers.

These are pure functions -- no client, no network -- so they are fully
offline-testable. They reproduce Sui's ``derived_object::derive_address``
client-side, and every derivation must stay stable: the values address real
on-chain objects, and ``session_id`` in particular is bound into the
Fiat-Shamir transcript of every proof pysui generates. A drift here produces
proofs the chain rejects with no client-side error.
"""

import pysui.private_transfer.utils as utils

PACKAGE_ID: str = "0x" + "ab" * 32
TOKEN_REGISTRY: str = "0x" + "cd" * 32
ACCOUNT_REGISTRY: str = "0x" + "12" * 32
OWNER: str = "0x" + "ef" * 32
ACCOUNT_ID: str = "0x" + "34" * 32
COIN_TYPE: str = "0x2::sui::SUI"


def _is_object_id(value: str) -> bool:
    """A Sui object id: ``0x`` followed by 64 lowercase hex characters."""
    if not value.startswith("0x"):
        return False
    body = value[2:]
    return len(body) == 64 and all(c in "0123456789abcdef" for c in body)


def test_session_id_is_exactly_20_bytes():
    """pysui-crypto hard-rejects any session_id that is not 20 bytes."""
    result = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    assert isinstance(result, bytes)
    assert len(result) == 20


def test_session_id_is_deterministic():
    """Identical inputs must always yield identical bytes."""
    first = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    second = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    assert first == second


def test_session_id_varies_by_account():
    """A different account must produce a different session id."""
    first = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    second = utils.session_id(
        package_id=PACKAGE_ID, account_id="0x" + "56" * 32, coin_type=COIN_TYPE
    )
    assert first != second


def test_session_id_varies_by_coin_type():
    """The coin type is part of the derivation, not incidental."""
    first = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    second = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type="0x2::coin::COIN"
    )
    assert first != second


def test_session_id_varies_by_package():
    """A redeployed package must not reuse the prior session id."""
    first = utils.session_id(
        package_id=PACKAGE_ID, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    second = utils.session_id(
        package_id="0x" + "99" * 32, account_id=ACCOUNT_ID, coin_type=COIN_TYPE
    )
    assert first != second


def test_account_id_shape_and_determinism():
    """``account_id`` returns a well-formed object id, stably."""
    first = utils.account_id(
        package_id=PACKAGE_ID, account_registry_id=ACCOUNT_REGISTRY, owner=OWNER
    )
    second = utils.account_id(
        package_id=PACKAGE_ID, account_registry_id=ACCOUNT_REGISTRY, owner=OWNER
    )
    assert _is_object_id(first)
    assert first == second


def test_account_id_varies_by_owner():
    """Two owners must not derive the same account."""
    first = utils.account_id(
        package_id=PACKAGE_ID, account_registry_id=ACCOUNT_REGISTRY, owner=OWNER
    )
    second = utils.account_id(
        package_id=PACKAGE_ID,
        account_registry_id=ACCOUNT_REGISTRY,
        owner="0x" + "78" * 32,
    )
    assert first != second


def test_confidential_token_id_shape_and_determinism():
    """``confidential_token_id`` returns a well-formed object id, stably."""
    first = utils.confidential_token_id(
        package_id=PACKAGE_ID, token_registry_id=TOKEN_REGISTRY, coin_type=COIN_TYPE
    )
    second = utils.confidential_token_id(
        package_id=PACKAGE_ID, token_registry_id=TOKEN_REGISTRY, coin_type=COIN_TYPE
    )
    assert _is_object_id(first)
    assert first == second


def test_confidential_token_id_varies_by_coin_type():
    """Each coin type gets its own confidential token object."""
    first = utils.confidential_token_id(
        package_id=PACKAGE_ID, token_registry_id=TOKEN_REGISTRY, coin_type=COIN_TYPE
    )
    second = utils.confidential_token_id(
        package_id=PACKAGE_ID,
        token_registry_id=TOKEN_REGISTRY,
        coin_type="0x2::coin::COIN",
    )
    assert first != second


def test_pool_id_shape_and_determinism():
    """``pool_id`` returns a well-formed object id, stably."""
    token_id = utils.confidential_token_id(
        package_id=PACKAGE_ID, token_registry_id=TOKEN_REGISTRY, coin_type=COIN_TYPE
    )
    first = utils.pool_id(package_id=PACKAGE_ID, confidential_token_id=token_id)
    second = utils.pool_id(package_id=PACKAGE_ID, confidential_token_id=token_id)
    assert _is_object_id(first)
    assert first == second


def test_derivations_are_mutually_distinct():
    """The four derivations must not collide on shared inputs."""
    token_id = utils.confidential_token_id(
        package_id=PACKAGE_ID, token_registry_id=TOKEN_REGISTRY, coin_type=COIN_TYPE
    )
    derived_account = utils.account_id(
        package_id=PACKAGE_ID, account_registry_id=ACCOUNT_REGISTRY, owner=OWNER
    )
    pool = utils.pool_id(package_id=PACKAGE_ID, confidential_token_id=token_id)
    assert len({token_id, derived_account, pool}) == 3
