#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pure-Python types mirroring pysui_crypto native types.

These exist so callers can work with typed Python objects without pysui_crypto
installed. Properties that require parsing the ciphertext will raise ImportError
if pysui_crypto is absent.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


class SealDemType(str, Enum):
    """Python mirror of pysui_crypto.DemType for type-safe caller code."""

    AesGcm256 = "AesGcm256"
    Hmac256Ctr = "Hmac256Ctr"
    Plain = "Plain"


class SealEncryptedObject:
    """Pure-Python wrapper carrying SEAL ciphertext as raw bytes.

    The raw bytes representation (as_bytes / from_bytes) is always available.
    Structural properties (version, package_id, …) require pysui_crypto and
    raise ImportError if the native extension is absent.
    """

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._parsed: Optional[object] = None

    @classmethod
    def from_bytes(cls, data: bytes) -> SealEncryptedObject:
        """Construct from raw ciphertext bytes."""
        return cls(data)

    def as_bytes(self) -> bytes:
        """Return the raw ciphertext bytes."""
        return self._data

    def _ensure_parsed(self) -> object:
        if self._parsed is None:
            from pysui.zklogin_seal._ext import (
                EncryptedObject,
                _CRYPTO_AVAILABLE,
                INSTALL_HINT,
            )
            if not _CRYPTO_AVAILABLE:
                raise ImportError(INSTALL_HINT)
            self._parsed = EncryptedObject.parse(self._data)
        return self._parsed

    @property
    def version(self) -> int:
        return self._ensure_parsed().version  # type: ignore[union-attr]

    @property
    def package_id(self) -> bytes:
        return self._ensure_parsed().package_id  # type: ignore[union-attr]

    @property
    def id(self) -> bytes:
        return self._ensure_parsed().id  # type: ignore[union-attr]

    @property
    def threshold(self) -> int:
        return self._ensure_parsed().threshold  # type: ignore[union-attr]

    @property
    def services(self) -> list[tuple[bytes, int]]:
        return self._ensure_parsed().services  # type: ignore[union-attr]

    @property
    def dem_type(self) -> SealDemType:
        native = self._ensure_parsed().dem_type  # type: ignore[union-attr]
        return SealDemType(repr(native).split(".")[-1])
