#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move Datatypes for BCS deserialization."""

from typing import Any
import json
import pysui.sui.sui_bcs.bcs_stnd as bcse
import pysui.sui.sui_bcs.pysui_bcs as pbcsbase
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented


class Element_Scalar(pbcsbase.BCS_Struct):
    """Generated from 0x0000000000000000000000000000000000000000000000000000000000000002::group_ops::Element"""

    _fields = [("bytes", [bcse.U8, None, True])]


class Element_G(pbcsbase.BCS_Struct):
    """Generated from 0x0000000000000000000000000000000000000000000000000000000000000002::group_ops::Element"""

    _fields = [("bytes", [bcse.U8, None, True])]


class KeyConsistencyProof(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::nizk::KeyConsistencyProof"""

    _fields = [
        ("a1", [Element_G, None, True]),
        ("a2", [Element_G, None, True]),
        ("a3", Element_G),
        ("z1", [Element_Scalar, None, True]),
        ("z2", [Element_Scalar, None, True]),
    ]


class MultiRecipientEncryption(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::twisted_elgamal::MultiRecipientEncryption"""

    _fields = [("ciphertext", Element_G), ("decryption_handles", [Element_G, None, True])]


class KeyEncryption(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::auditors::KeyEncryption"""

    _fields = [
        ("ciphertext", [MultiRecipientEncryption, None, True]),
        ("proof", KeyConsistencyProof),
        ("range_proof", [bcse.U8, None, True]),
    ]


class Encryption(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::twisted_elgamal::Encryption"""

    _fields = [("ciphertext", Element_G), ("decryption_handle", Element_G)]


class EncryptedAmount(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::encrypted_amount::EncryptedAmount"""

    _fields = [
        ("l0", Encryption),
        ("l1", Encryption),
        ("l2", Encryption),
        ("l3", Encryption),
    ]


class PublicCoin(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::balance::PublicCoin"""

    _fields = [("value", bcse.U64)]


class EncryptedBalance(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::balance::EncryptedBalance"""

    _fields = [("amount", EncryptedAmount), ("upper_bound", bcse.U16)]


class VerifiedKeyEncryption(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::auditors::VerifiedKeyEncryption"""

    _fields = [
        ("ciphertext", [MultiRecipientEncryption, None, True]),
        ("version", bcse.U32),
    ]


class SessionId(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::session_id::SessionId"""

    _fields = [("id", [bcse.U8, None, True])]


class PublicKey(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::twisted_elgamal::PublicKey"""

    _fields = [("element", Element_G)]


class AccumulatedAmount(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::balance::AccumulatedAmount"""

    _fields = [("amount", EncryptedAmount), ("terms", bcse.U16)]


class Balances(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::balance::Balances"""

    _fields = [
        ("pk", PublicKey),
        ("active", AccumulatedAmount),
        ("pending", AccumulatedAmount),
        ("public_balance", bcse.U64),
    ]


class TokenAccount(pbcsbase.BCS_Struct):
    """Generated from 0xdbf579054d6a93d3eca02d549cf16d4008475c8930fdfda40bef763a7385fff1::contra::TokenAccount"""

    _fields = [
        ("session_id", SessionId),
        ("is_frozen", bool),
        ("accepts_deposits", bool),
        ("balance", Balances),
    ]
