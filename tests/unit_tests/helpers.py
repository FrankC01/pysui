#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Shared helper functions for pysui unit tests."""


def mock_paging_cursor(*, has_next: bool = False, end_cursor: str = None) -> dict:
    """Return a minimal PageInfo dict as GQL would return it."""
    return {"hasNextPage": has_next, "endCursor": end_cursor}


def mock_owner_address(addr: str = "0xabc") -> dict:
    """Return an AddressOwner-shaped owner dict."""
    return {
        "obj_owner_kind": "AddressOwner",
        "address_id": {"address": addr},
    }


def mock_owner_shared() -> dict:
    """Return a Shared owner dict."""
    return {
        "obj_owner_kind": "Shared",
        "initial_version": 1,
    }


def mock_owner_object(parent: str = "0xparent") -> dict:
    """Return an ObjectOwner-shaped owner dict."""
    return {
        "obj_owner_kind": "ObjectOwner",
        "parent_id": {"address": parent},
    }


def mock_owner_immutable() -> dict:
    """Return an Immutable owner dict."""
    return {"obj_owner_kind": "Immutable"}


def mock_coin_object(
    *,
    coin_object_id: str = "0xcoin",
    coin_type: str = "0x2::coin::Coin<0x2::sui::SUI>",
    balance: str = "1000000000",
    version: int = 1,
    object_digest: str = "digestabc",
    has_public_transfer: bool = True,
    owner: dict = None,
    previous_transaction: str = "txdigest",
) -> dict:
    """Return a minimal SuiCoinObjectGQL-shaped dict (post-flatten)."""
    return {
        "coin_object_id": coin_object_id,
        "coin_type": coin_type,
        "balance": balance,
        "version": version,
        "object_digest": object_digest,
        "has_public_transfer": has_public_transfer,
        "owner": owner if owner is not None else mock_owner_address(),
        "previous_transaction": previous_transaction,
    }
