#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Optional pysui_crypto import guard — single point of control for the native extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysui.zklogin_seal.types import SealDemType

_CRYPTO_AVAILABLE: bool = False

try:
    from pysui_crypto import (
        generate_ephemeral_keypair,
        extract_jwt_claims,
        compute_nonce,
        compute_address_seed,
        compute_zklogin_address,
        build_zklogin_signature,
        seal_encrypt as _seal_encrypt_raw,  # private — do not rename or re-export; conversion boundary for seal_encrypt wrapper below
        seal_decrypt,
        DemType as _DemType,  # private — do not rename or re-export; used only in seal_encrypt wrapper below
        EncryptedObject,
        generate_session_keypair,
        generate_elgamal_keypair,
        elgamal_decrypt,
        verify_user_secret_key,
        seal_signed_message,
    )
    _CRYPTO_AVAILABLE = True
except ImportError:
    pass


INSTALL_HINT: str = (
    "pysui_crypto is not installed. "
    "Download the appropriate wheel from https://github.com/FrankC01/pysui-crypto/releases "
    "and install with: pip install <wheel-file>"
)


def seal_encrypt(
    pkg_id: bytes,
    inner_id: bytes,
    server_ids: list[bytes],
    ibe_pks: list[bytes],
    threshold: int,
    data: bytes,
    dem_type: SealDemType,
    aad: bytes | None = None,
) -> tuple[bytes, bytes | None]:
    """Wrap pysui_crypto.seal_encrypt, converting SealDemType to native DemType.

    pysui_crypto.seal_encrypt returns tuple[bytes, bytes | None]:
      [0] BCS-serialized EncryptedObject bytes
      [1] DEM key — None for AesGcm256/Hmac256Ctr; only set for Plain mode

    Returns (encrypted_bytes, dem_key) so callers can surface the Plain-mode DEM key.
    """
    if not _CRYPTO_AVAILABLE:
        raise ImportError(INSTALL_HINT)
    encrypted_bytes, dem_key = _seal_encrypt_raw(
        pkg_id, inner_id, server_ids, ibe_pks, threshold, data,
        getattr(_DemType, dem_type.value), aad=aad
    )
    return encrypted_bytes, dem_key
