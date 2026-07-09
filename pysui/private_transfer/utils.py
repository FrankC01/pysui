#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confidential Transfer (private funds) client-side id derivation and account utilities.

These helpers reproduce the Sui derived-object id derivation used by the
Confidential Transfer protocol (mirroring ``@mysten/sui`` ``deriveObjectID``),
so object ids such as the shared ``ConfidentialToken<T>`` can be computed
client-side without an on-chain round trip.

They also provide :func:`account_balances`, the public read of an owner's decrypted
Confidential Transfer balances, usable standalone with any async client.
"""

import hashlib
from typing import Union

from pysui.abstracts.async_client import AsyncClientBase
from pysui.private_transfer import _ext
from pysui.private_transfer import pf_bcs
from pysui.sui.sui_bcs import bcs
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented
from pysui.sui.sui_common.sui_commands import GetDynamicFields

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


@instrumented("pysui.private_transfer.utils._token_account")
async def _token_account(
    *,
    client: AsyncClientBase,
    package_id: str,
    account_id: str,
    coin_type: str,
) -> pf_bcs.TokenAccount:
    """Fetch and deserialize an owner's ``TokenAccount<T>`` from chain.

    ``TokenAccount<T>`` is a plain dynamic field (``has store``, no ``key``) hung off
    the owner's shared ``Account`` object under the ``TokenAccountKey<T>`` name. Its
    BCS payload carries the owner's ElGamal public key (``pk``), the confidential
    ``active`` and ``pending`` balances, the plaintext ``public_balance``, and the
    ``verified_key_encryption`` auditor stamp.

    :param client: An async client used to read the dynamic fields.
    :type client: AsyncClientBase
    :param package_id: The Confidential Transfer package id.
    :type package_id: str
    :param account_id: The owner's derived ``Account`` object id (``0x`` hex string).
    :type account_id: str
    :param coin_type: The coin type ``T`` (fully-qualified Move type string).
    :type coin_type: str
    :raises ValueError: If the dynamic field query fails, or no ``TokenAccount<T>``
        for ``coin_type`` is hung off ``account_id``.
    :returns: The deserialized ``TokenAccount<T>``.
    :rtype: pf_bcs.TokenAccount
    """
    target_type: str = f"{package_id}::contra::TokenAccount<{coin_type}>"
    result = await client.execute_for_all(
        command=GetDynamicFields(object_id=account_id)
    )
    if result.is_err():
        raise ValueError(
            f"GetDynamicFields failed for Account {account_id}: {result.result_string}"
        )
    observed: list[str] = []
    for field in result.result_data.dynamic_fields:
        if field.value_type == target_type:
            return pf_bcs.TokenAccount.deserialize(field.value.value)
        if field.value_type:
            observed.append(field.value_type)
    raise ValueError(
        f"Account {account_id} has no {target_type} dynamic field; observed: {observed}"
    )


@instrumented("pysui.private_transfer.utils.account_balances")
async def account_balances(
    *,
    client: AsyncClientBase,
    package_id: str,
    account_id: str,
    coin_type: str,
    private_key: bytes,
) -> tuple[int, int, int]:
    """Read and decrypt an owner's confidential balances for ``coin_type``.

    The sole public read for Confidential Transfer account state. Fetches the owner's
    on-chain ``TokenAccount<T>`` and returns its balances as plaintext integers, so
    callers never handle BCS constructs or ciphertext.

    ``active`` is the spendable confidential balance. ``pending`` holds value received
    from transfers or wraps and is not spendable until merged. ``public_balance`` is
    the plaintext deposit balance, also folded in by a merge.

    :param client: An async client used to read the dynamic fields.
    :type client: AsyncClientBase
    :param package_id: The Confidential Transfer package id.
    :type package_id: str
    :param account_id: The owner's derived ``Account`` object id (``0x`` hex string).
    :type account_id: str
    :param coin_type: The coin type ``T`` (fully-qualified Move type string).
    :type coin_type: str
    :param private_key: The owner's 32-byte ElGamal private key.
    :type private_key: bytes
    :raises RuntimeError: If pysui_crypto is unavailable or below the minimum version.
    :raises ValueError: If no ``TokenAccount<T>`` exists for ``coin_type``, or a
        balance is malformed or outside the decryptable range.
    :returns: The ``(active, pending, public_balance)`` plaintext balances.
    :rtype: tuple[int, int, int]
    """
    account = await _token_account(
        client=client,
        package_id=package_id,
        account_id=account_id,
        coin_type=coin_type,
    )
    return (
        _decrypt_amount(private_key=private_key, amount=account.active.amount),
        _decrypt_amount(private_key=private_key, amount=account.pending.amount),
        int(account.public_balance.value),
    )


@sync_instrumented("pysui.private_transfer.utils._decrypt_amount")
def _decrypt_amount(*, private_key: bytes, amount: pf_bcs.EncryptedAmount) -> int:
    """Decrypt a confidential ``EncryptedAmount`` to its plaintext value.

    Flattens the four 64-byte limbs to the 256-byte wire form pysui-crypto expects,
    then recovers the plaintext with the process-wide baby-step/giant-step table.

    :param private_key: The owner's 32-byte ElGamal private key.
    :type private_key: bytes
    :param amount: The deserialized ``EncryptedAmount`` (an ``active``, ``pending``,
        or transfer amount).
    :type amount: pf_bcs.EncryptedAmount
    :raises RuntimeError: If pysui_crypto is unavailable or below the minimum version.
    :raises ValueError: If the amount is malformed or any limb is outside the
        decryptable range.
    :returns: The plaintext amount.
    :rtype: int
    """
    return _ext.decrypt_balance(
        private_key, _flatten_encrypted_amount(amount=amount), _ext.get_bsgs_table()
    )


def _flatten_encrypted_amount(*, amount: pf_bcs.EncryptedAmount) -> bytes:
    """Flatten a deserialized ``EncryptedAmount`` to its 256-byte wire form.

    pysui-crypto expects the encrypted balance as four 64-byte limbs, each limb the
    concatenation ``ciphertext || decryption_handle``. BCS deserialization yields the
    group elements as length-prefixed vectors, so they are re-concatenated here.

    :param amount: The deserialized ``EncryptedAmount``.
    :type amount: pf_bcs.EncryptedAmount
    :returns: The flat 256-byte encrypted amount.
    :rtype: bytes
    """
    flattened = bytearray()
    for limb in (amount.l0, amount.l1, amount.l2, amount.l3):
        flattened.extend(bytes(limb.ciphertext.bytes))
        flattened.extend(bytes(limb.decryption_handle.bytes))
    return bytes(flattened)


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
