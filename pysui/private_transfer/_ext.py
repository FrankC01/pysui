#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Optional pysui_crypto import guard for Confidential Transfer — single point of control for the native extension."""

MINIMUM_PYSUI_CRYPTO_VERSION: tuple[int, int] = (0, 2)

INSTALL_HINT: str = (
    "pysui_crypto (>= 0.2) is required for private transfer (confidential "
    "transfer) support and is either not installed or below the minimum "
    "version. Download the appropriate wheel from "
    "https://github.com/Suitters/pysui-crypto/releases and install with: "
    "pip install <wheel-file>"
)

_CRYPTO_AVAILABLE: bool = False

try:
    from pysui_crypto import (
        pysui_crypto_version,
        BsgsTable,
        TransferRandomness,
        generate_twisted_elgamal_keypair,
        decrypt_balance,
        subtract_encrypted,
        encrypt_amount_with_proofs,
        register_with_auditors,
        unwrap_proof,
        batched_transfer_proofs,
        rekey_proofs,
        recover_transfer_randomness,
        decrypt_transfer_amount,
    )

    if pysui_crypto_version() >= MINIMUM_PYSUI_CRYPTO_VERSION:
        _CRYPTO_AVAILABLE = True
except ImportError:
    pass


def raise_for_crypto() -> None:
    """Raise ``RuntimeError`` if pysui_crypto is unavailable or below the minimum version."""
    if not _CRYPTO_AVAILABLE:
        raise RuntimeError(INSTALL_HINT)
