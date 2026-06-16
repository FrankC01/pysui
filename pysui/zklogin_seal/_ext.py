#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Optional pysui_crypto import guard — single point of control for the native extension."""

_CRYPTO_AVAILABLE: bool = False

try:
    from pysui_crypto import (
        generate_ephemeral_keypair,
        extract_jwt_claims,
        compute_nonce,
        compute_address_seed,
        compute_zklogin_address,
        build_zklogin_signature,
        seal_encrypt,
        seal_decrypt,
        DemType,
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
