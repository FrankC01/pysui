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
