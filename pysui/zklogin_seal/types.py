#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pure-Python types mirroring pysui_crypto native types.

These exist so callers can work with typed Python objects without pysui_crypto
installed. Properties that require parsing the ciphertext will raise ImportError
if pysui_crypto is absent.
"""
from __future__ import annotations

from typing import Optional

from pysui.zklogin_seal._dem_type import SealDemType


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
        """Return the SEAL encrypted object's format version."""
        return self._ensure_parsed().version  # type: ignore[attr-defined]

    @property
    def package_id(self) -> bytes:
        """Return the SEAL package ID the ciphertext was encrypted under."""
        return self._ensure_parsed().package_id  # type: ignore[attr-defined]

    @property
    def id(self) -> bytes:
        """Return the ciphertext's identity (inner) ID."""
        return self._ensure_parsed().id  # type: ignore[attr-defined]

    @property
    def threshold(self) -> int:
        """Return the threshold number of key servers required to decrypt."""
        return self._ensure_parsed().threshold  # type: ignore[attr-defined]

    @property
    def services(self) -> list[tuple[bytes, int]]:
        """Return the list of (server object ID, share index) pairs used for encryption."""
        return self._ensure_parsed().services  # type: ignore[attr-defined]

    @property
    def dem_type(self) -> SealDemType:
        """Return the DEM (data encryption mode) type used for this ciphertext."""
        native = self._ensure_parsed().dem_type  # type: ignore[attr-defined]
        return SealDemType(repr(native).split(".")[-1])
