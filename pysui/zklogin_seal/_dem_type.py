#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""SealDemType — zero-dependency enum shared by pysui.zklogin_seal._ext and pysui.zklogin_seal.types.

Lives in its own module so `_ext.py` (native extension boundary) and `types.py`
(pure-Python type mirror) can both import it without creating a circular import.
"""
from __future__ import annotations

from enum import Enum


class SealDemType(str, Enum):
    """Python mirror of pysui_crypto.DemType for type-safe caller code."""

    AesGcm256 = "AesGcm256"
    Hmac256Ctr = "Hmac256Ctr"
    Plain = "Plain"
