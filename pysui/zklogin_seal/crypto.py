#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Crypto credential objects for zkLogin and SEAL."""
from __future__ import annotations

import time

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_crypto import SuiKeyPair, SuiPublicKey, SuiPrivateKey


class ZkLoginKeyPair(SuiKeyPair):
    """Ephemeral keypair carrying ZkLogin proof state for transaction signing.

    Created via ZkSession.get_proof() — not directly instantiated.
    The ephemeral key (ed25519 or secp256r1) signs transactions; the ZK proof
    wraps that signature into a ZkLoginAuthenticator for the Sui network.
    """

    def __init__(self) -> None:
        super().__init__()
        self._proof_json: str = ""
        self._address_seed: bytes = b""
        self._max_epoch: int = 0

    @classmethod
    def create(
        cls,
        scheme: SignatureScheme,
        pub_bytes: bytes,
        prv_bytes: bytes,
        proof_json: str,
        address_seed: bytes,
        max_epoch: int,
    ) -> "ZkLoginKeyPair":
        """Create from ephemeral key bytes and ZkLogin proof state."""
        from pysui.zklogin_seal._ext import _CRYPTO_AVAILABLE, INSTALL_HINT

        if not _CRYPTO_AVAILABLE:
            raise ImportError(INSTALL_HINT)
        kp = cls()
        kp._scheme = SignatureScheme.ZKLOGINAUTHENTICATOR
        kp._public_key = SuiPublicKey(scheme, pub_bytes)
        kp._private_key = SuiPrivateKey(scheme, prv_bytes)
        kp._proof_json = proof_json
        kp._address_seed = address_seed
        kp._max_epoch = max_epoch
        return kp

    @property
    def ephemeral_scheme(self) -> SignatureScheme:
        """Scheme of the underlying ephemeral key (ED25519 or SECP256R1)."""
        if self._public_key:
            return self._public_key.scheme
        return SignatureScheme.ED25519

    def new_sign_secure(self, tx_data: str) -> str:
        """Sign transaction data, returning a base64 ZkLoginAuthenticator."""
        from pysui.zklogin_seal._ext import build_zklogin_signature

        assert self._private_key, "Cannot sign with invalid ephemeral private key"
        ephemeral_sig = bytes(self._private_key.sign_secure(tx_data))
        return build_zklogin_signature(
            self._proof_json,
            ephemeral_sig,
            self._address_seed,
            self._max_epoch,
        )

    def sign_personal_message(self, message: str) -> str:
        """Sign a personal message, returning a base64 ZkLoginAuthenticator."""
        from pysui.zklogin_seal._ext import build_zklogin_signature

        assert self._private_key, "Cannot sign with invalid ephemeral private key"
        ephemeral_sig = bytes(self._private_key.sign_secure_personal_message(message))
        return build_zklogin_signature(
            self._proof_json,
            ephemeral_sig,
            self._address_seed,
            self._max_epoch,
        )

    @classmethod
    def from_b64(cls, indata: str) -> "ZkLoginKeyPair":
        raise NotImplementedError(
            "ZkLoginKeyPair is created via ZkSession.get_proof(), not from a keystring."
        )

    @classmethod
    def from_bech32(cls, indata: str) -> "ZkLoginKeyPair":
        raise NotImplementedError(
            "ZkLoginKeyPair is created via ZkSession.get_proof(), not from a bech32 string."
        )

    @classmethod
    def from_bytes(cls, indata: bytes) -> "ZkLoginKeyPair":
        raise NotImplementedError(
            "ZkLoginKeyPair is created via ZkSession.get_proof(), not from bytes."
        )


class SealCredentials:
    """Reusable SEAL credential bundle for encrypt/decrypt operations.

    Created via SealClient.make_credentials() — not directly instantiated.
    Encapsulates the ephemeral session keypair and ElGamal keypair needed
    to interact with SEAL key servers.
    """

    def __init__(
        self,
        session_sk: bytes,
        session_pk: bytes,
        elgamal_sk: bytes,
        elgamal_pk: bytes,
        elgamal_vk: bytes,
        keypair: SuiKeyPair,
        server_urls: list[str],
        session_minutes: int,
        creation_time_ms: int,
        sui_address: str,
    ) -> None:
        self._session_sk = session_sk
        self._session_pk = session_pk
        self._elgamal_sk = elgamal_sk
        self._elgamal_pk = elgamal_pk
        self._elgamal_vk = elgamal_vk
        self._keypair = keypair
        self._server_urls = server_urls
        self._session_minutes = session_minutes
        self._creation_time_ms = creation_time_ms
        self._sui_address = sui_address

    @classmethod
    def create(
        cls,
        keypair: SuiKeyPair,
        server_urls: list[str],
        session_minutes: int,
        sui_address: str,
    ) -> "SealCredentials":
        """Generate a fresh SEAL credential bundle."""
        from pysui.zklogin_seal._ext import (
            _CRYPTO_AVAILABLE,
            INSTALL_HINT,
            generate_elgamal_keypair,
            generate_session_keypair,
        )

        if not _CRYPTO_AVAILABLE:
            raise ImportError(INSTALL_HINT)
        session_kp = generate_session_keypair()
        elg_kp = generate_elgamal_keypair()
        return cls(
            session_sk=session_kp["secret_key"],
            session_pk=session_kp["public_key"],
            elgamal_sk=elg_kp["secret_key"],
            elgamal_pk=elg_kp["public_key"],
            elgamal_vk=elg_kp["verification_key"],
            keypair=keypair,
            server_urls=server_urls,
            session_minutes=session_minutes,
            creation_time_ms=int(time.time() * 1000),
            sui_address=sui_address,
        )

    @property
    def session_pk(self) -> bytes:
        """Session public key for key server authentication."""
        return self._session_pk

    @property
    def elgamal_pk(self) -> bytes:
        """ElGamal public key for key server encryption of shares."""
        return self._elgamal_pk

    @property
    def elgamal_vk(self) -> bytes:
        """ElGamal verification key."""
        return self._elgamal_vk

    @property
    def server_urls(self) -> list[str]:
        """Copy of configured key server URLs."""
        return self._server_urls.copy()

    @property
    def keypair(self) -> SuiKeyPair:
        """The user's real Sui keypair."""
        return self._keypair

    @property
    def session_minutes(self) -> int:
        """Session TTL in minutes."""
        return self._session_minutes

    @property
    def creation_time_ms(self) -> int:
        """Unix timestamp (ms) when this credential bundle was created."""
        return self._creation_time_ms

    @property
    def sui_address(self) -> str:
        """Sui address string ('0x...') of the credential owner."""
        return self._sui_address

    def sign_request(self, data: bytes) -> bytes:
        """Ed25519-sign data with the session secret key."""
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        prv = Ed25519PrivateKey.from_private_bytes(self._session_sk)
        return prv.sign(data)

    def signed_message(self, package_id: str, creation_time: int, ttl_min: int) -> str:
        """Generate a signed request message for key server authentication."""
        from pysui.zklogin_seal._ext import seal_signed_message

        return seal_signed_message(package_id, self._session_pk, creation_time, ttl_min)

    def decrypt_share(self, encrypted_share: bytes) -> bytes:
        """ElGamal-decrypt a single key share from a key server response."""
        from pysui.zklogin_seal._ext import elgamal_decrypt

        return elgamal_decrypt(self._elgamal_sk, encrypted_share)
