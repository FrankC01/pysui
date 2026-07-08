#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confidential Transfer (private funds) client-side id derivation utilities.

These helpers reproduce the Sui derived-object id derivation used by the
Confidential Transfer protocol (mirroring ``@mysten/sui`` ``deriveObjectID``),
so object ids such as the shared ``ConfidentialToken<T>`` can be computed
client-side without an on-chain round trip.
"""

import hashlib
from typing import Union

from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.instrumentation import sync_instrumented

_DERIVED_OBJECT_PREFIX: bytes = b"\xf0"
"""Domain-separation prefix byte for Sui derived-object id hashing."""


@sync_instrumented("pysui.private_transfer.utils._derive_object_id")
def _derive_object_id(*, parent_id: str, type_tag: str, key: bytes) -> str:
    """Compute a Sui derived-object id (``@mysten/sui`` ``deriveObjectID``).

    The derivation wraps ``type_tag`` in ``0x2::derived_object::DerivedObjectKey``
    and hashes, in order, a ``0xf0`` prefix byte, the 32-byte parent id, the
    little-endian ``u64`` key length, the key bytes, and the BCS-serialized
    ``TypeTag``, with BLAKE2b-256.

    :param parent_id: The parent object id (e.g. a registry) the id derives from
    :type parent_id: str
    :param type_tag: The inner Move type tag string (without the DerivedObjectKey wrapper)
    :type type_tag: str
    :param key: The BCS-serialized derivation key bytes
    :type key: bytes
    :returns: The derived object id as a ``0x``-prefixed hex string
    :rtype: str
    """
    wrapped: str = f"0x2::derived_object::DerivedObjectKey<{type_tag}>"
    tag_bytes: bytes = bcs.TypeTag.type_tag_from(wrapped).serialize()
    parent_bytes: bytes = bytes.fromhex(parent_id.removeprefix("0x").zfill(64))
    hasher = hashlib.blake2b(digest_size=32)
    hasher.update(_DERIVED_OBJECT_PREFIX)
    hasher.update(parent_bytes)
    hasher.update(len(key).to_bytes(8, "little"))
    hasher.update(key)
    hasher.update(tag_bytes)
    return "0x" + hasher.hexdigest()


@sync_instrumented("pysui.private_transfer.utils.confidential_token_id")
def confidential_token_id(
    *, package_id: str, token_registry_id: str, coin_type: str
) -> str:
    """Derive the shared ``ConfidentialToken<T>`` object id.

    :param package_id: The Confidential Transfer package id
    :type package_id: str
    :param token_registry_id: The TokenRegistry shared-object id (derivation parent)
    :type token_registry_id: str
    :param coin_type: The coin type ``T`` (fully-qualified Move type string)
    :type coin_type: str
    :returns: The derived ``ConfidentialToken<T>`` object id as a ``0x`` hex string
    :rtype: str
    """
    type_tag: str = f"{package_id}::contra::TokenKey<{coin_type}>"
    return _derive_object_id(
        parent_id=token_registry_id, type_tag=type_tag, key=b"\x00"
    )


@sync_instrumented("pysui.private_transfer.utils.account_id")
def account_id(
    *, package_id: str, account_registry_id: str, owner: Union[str, bcs.Address]
) -> str:
    """Derive the per-owner shared ``Account`` object id.

    The derived id is deterministic and is expected to be stored in the sender's
    sidecar once the owner address is registered.

    :param package_id: The Confidential Transfer package id
    :type package_id: str
    :param account_registry_id: The AccountRegistry shared-object id (derivation parent)
    :type account_registry_id: str
    :param owner: The owner Sui address, as a ``0x`` hex string or a ``bcs.Address``.
    :type owner: Union[str, bcs.Address]
    :returns: The derived ``Account`` object id as a ``0x`` hex string
    :rtype: str
    """
    if isinstance(owner, bcs.Address):
        owner_key: bytes = bytes(getattr(owner, "Address"))
    else:
        owner_key = bytes.fromhex(owner.removeprefix("0x").zfill(64))
    return _derive_object_id(
        parent_id=account_registry_id,
        type_tag=f"{package_id}::contra::AccountKey",
        key=owner_key,
    )


@sync_instrumented("pysui.private_transfer.utils.session_id")
def session_id(*, package_id: str, account_id: str, coin_type: str) -> bytes:
    """Derive the 20-byte ``session_id`` for the owner's ``TokenAccount<T>``.

    The session id is the first 20 bytes of the derived-object address for
    ``TokenAccountKey<T>`` parented on the owner's ``Account`` id.

    :param package_id: The Confidential Transfer package id
    :type package_id: str
    :param account_id: The sender's derived ``Account`` object id (from the sidecar store)
    :type account_id: str
    :param coin_type: The coin type ``T`` (fully-qualified Move type string)
    :type coin_type: str
    :returns: The 20-byte session id
    :rtype: bytes
    """
    derived: str = _derive_object_id(
        parent_id=account_id,
        type_tag=f"{package_id}::contra::TokenAccountKey<{coin_type}>",
        key=b"\x00",
    )
    return bytes.fromhex(derived.removeprefix("0x"))[:20]


@sync_instrumented("pysui.private_transfer.utils.pool_id")
def pool_id(*, package_id: str, confidential_token_id: str) -> str:
    """Derive the shared ``Pool<T>`` object id for a confidential token.

    The pool is derived on-chain via ``derived_object::claim(&mut ct.id, PoolKey())``
    — a single un-parameterized ``PoolKey`` per token, parented on the
    ``ConfidentialToken<T>`` object. There is exactly one pool per token.

    :param package_id: The Confidential Transfer package id
    :type package_id: str
    :param confidential_token_id: The ``ConfidentialToken<T>`` object id (derivation parent)
    :type confidential_token_id: str
    :returns: The derived ``Pool<T>`` object id as a ``0x`` hex string
    :rtype: str
    """
    return _derive_object_id(
        parent_id=confidential_token_id,
        type_tag=f"{package_id}::contra::PoolKey",
        key=b"\x00",
    )
