#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""pysui private transfer (Confidential Transfer / CT) support.

Client-side surface for Sui confidential transfers: configuration, self-identity
key management, BCS types, id-derivation helpers, and the private-funds
transaction builder.  Documented BETA; depends on the external ``pysui-crypto``
extension (see :mod:`pysui.private_transfer._ext`).
"""
