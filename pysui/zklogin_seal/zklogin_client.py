#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""zkLogin client: ZkClient, ZkSession, and generate_user_salt utility."""

import base64
import secrets
from enum import Enum
from typing import Optional

import httpx

from pysui import SuiRpcResult, PysuiConfiguration
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.zklogin_seal._ext import _CRYPTO_AVAILABLE, INSTALL_HINT
from pysui.zklogin_seal.config import ZkSealConfig
from pysui.zklogin_seal.crypto import ZkLoginKeyPair
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented

if _CRYPTO_AVAILABLE:
    from pysui.zklogin_seal._ext import (  # type: ignore[assignment]
        generate_ephemeral_keypair,
        compute_nonce,
        extract_jwt_claims,
        compute_address_seed,
        compute_zklogin_address,
    )


_SESSION_TOKEN = object()


class ZkClaimKey(str, Enum):
    """Selects which JWT claim anchors the zkLogin address derivation."""
    SUBJECT = "sub"
    AUDIENCE = "aud"


@sync_instrumented("pysui.zklogin_seal.zklogin_client.generate_user_salt")
def generate_user_salt() -> str:
    """Return a random 128-bit decimal string suitable for use as a zkLogin user salt."""
    return str(int.from_bytes(secrets.token_bytes(16), "big"))


class ZkSession:
    """Per-login zkLogin flow. Created via ZkClient.session()."""

    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.__init__")
    def __init__(
        self,
        *,
        _token: object = None,
        client: "ZkClient",
        provider: str,
        epk_bytes: bytes,
        prv_bytes: bytes,
        nonce: str,
        max_epoch: int,
        randomness: str,
        as_secp256r1: bool,
    ) -> None:
        """Initialise a ZkLogin proof session.

        .. note::
            Do not instantiate directly — use :meth:`ZkClient.session` instead.

        :param client: ZkClient that owns this session and provides config and salt.
        :type client: ZkClient
        :param provider: OAuth provider name (e.g. ``"google"``); must match a configured provider.
        :type provider: str
        :param epk_bytes: Ephemeral public key bytes derived from the generated keypair.
        :type epk_bytes: bytes
        :param prv_bytes: Ephemeral private key bytes; used to construct ZkLoginKeyPair after proof.
        :type prv_bytes: bytes
        :param nonce: Nonce embedded in the OAuth JWT; must match the value returned by ``session.nonce``.
        :type nonce: str
        :param max_epoch: Maximum Sui epoch at which the ephemeral keypair remains valid.
        :type max_epoch: int
        :param randomness: Random string used in nonce computation.
        :type randomness: str
        :param as_secp256r1: Use SECP256R1 ephemeral key scheme; defaults to ED25519 when False.
        :type as_secp256r1: bool
        :raises TypeError: If not instantiated via ZkClient.session().
        """
        if _token is not _SESSION_TOKEN:
            raise TypeError("ZkSession must be created via ZkClient.session()")
        self._client = client
        self._provider = provider
        self._epk_bytes = epk_bytes
        self._prv_bytes = prv_bytes
        self._nonce = nonce
        self._max_epoch = max_epoch
        self._randomness = randomness
        self._as_secp256r1 = as_secp256r1
        self._address_seed: Optional[bytes] = None
        self._address: Optional[str] = None
        self._keypair: Optional[ZkLoginKeyPair] = None
        self._jwt: Optional[str] = None
        self._key_claim_name: str = "sub"

    @property
    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.nonce")
    def nonce(self) -> str:
        return self._nonce

    @property
    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.address")
    def address(self) -> Optional[str]:
        return self._address

    @property
    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.salt")
    def salt(self) -> str:
        return self._client.salt

    @property
    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.keypair")
    def keypair(self) -> ZkLoginKeyPair:
        if self._keypair is None:
            raise RuntimeError("keypair unavailable until get_proof() succeeds")
        return self._keypair

    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.process_jwt")
    def process_jwt(
        self,
        *,
        jwt: str,
        key_claim_name: ZkClaimKey = ZkClaimKey.SUBJECT,
        legacy: bool = False,
    ) -> str:
        """Extract claims from JWT and derive zkLogin address. Synchronous, no network I/O."""
        try:
            iss, sub, aud, jwt_nonce = extract_jwt_claims(jwt)
            if key_claim_name == ZkClaimKey.SUBJECT:
                claim_value = sub
            elif key_claim_name == ZkClaimKey.AUDIENCE:
                claim_value = aud
            else:
                raise ValueError(f"key_claim_name must be ZkClaimKey.SUBJECT or ZkClaimKey.AUDIENCE, got '{key_claim_name}'")
            address_seed = compute_address_seed(key_claim_name, claim_value, aud, self._client.salt)
            address = compute_zklogin_address(iss, address_seed, legacy)
        except Exception as exc:
            raise ValueError(f"Failed to process JWT: {exc}") from exc
        if jwt_nonce != self._nonce:
            raise ValueError(
                f"Nonce mismatch: JWT contains '{jwt_nonce}', expected '{self._nonce}'"
            )
        self._address_seed = address_seed
        self._address = address
        self._key_claim_name = key_claim_name
        self._jwt = jwt
        return address

    @instrumented("pysui.zklogin_seal.zklogin_client.ZkSession.get_proof")
    async def get_proof(self, *, pysui_config: PysuiConfiguration) -> SuiRpcResult:
        """POST to the ZK proving service and cache ZkLoginKeyPair. Asynchronous."""
        if self._address_seed is None or self._jwt is None:
            raise RuntimeError("process_jwt() must be called before get_proof()")
        jwt = self._jwt

        provider_entry = next(
            (p for p in self._client.config.active_group.zklogin_providers if p.name == self._provider),
            None,
        )
        if provider_entry is None:
            raise ValueError(f"Provider '{self._provider}' not found in active config group")

        flag = 0x02 if self._as_secp256r1 else 0x00
        extended_epk = str(int.from_bytes(bytes([flag]) + self._epk_bytes, "big"))

        payload = {
            "jwt": jwt,
            "extendedEphemeralPublicKey": extended_epk,
            "maxEpoch": self._max_epoch,
            "jwtRandomness": self._randomness,
            "salt": self._client.salt,
            "keyClaimName": self._key_claim_name,
        }

        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    provider_entry.prover_url, json=payload, timeout=30.0
                )
                response.raise_for_status()
                proof_json = response.text
        except httpx.HTTPError as exc:
            return SuiRpcResult(False, str(exc), None)

        scheme = SignatureScheme.SECP256R1 if self._as_secp256r1 else SignatureScheme.ED25519
        self._keypair = ZkLoginKeyPair.create(
            scheme=scheme,
            pub_bytes=self._epk_bytes,
            prv_bytes=self._prv_bytes,
            proof_json=proof_json,
            address_seed=self._address_seed,
            max_epoch=self._max_epoch,
        )
        pysui_config.active_group.add_transient_keypair(
            profile_name=pysui_config.active_group.using_profile,
            address=self._address,
            keypair=self._keypair,
        )
        return SuiRpcResult(True, None, proof_json)


class ZkClient:
    """Long-lived zkLogin client. Holds persistent state across sessions."""

    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkClient.__init__")
    def __init__(self, *, config: ZkSealConfig, salt: Optional[str] = None) -> None:
        """Initialise the zkLogin client.

        :param config: ZkSeal configuration providing provider endpoints and network group.
        :type config: ZkSealConfig
        :param salt: 128-bit decimal user salt; generated randomly if omitted. Store for address stability.
        :type salt: Optional[str], optional
        :raises ImportError: If pysui-crypto is not installed.
        """
        if not _CRYPTO_AVAILABLE:
            raise ImportError(INSTALL_HINT)
        self._config = config
        self._salt = salt if salt is not None else generate_user_salt()

    @property
    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkClient.salt")
    def salt(self) -> str:
        return self._salt

    @property
    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkClient.config")
    def config(self) -> ZkSealConfig:
        return self._config

    @sync_instrumented("pysui.zklogin_seal.zklogin_client.ZkClient.session")
    def session(
        self,
        *,
        provider: str,
        current_epoch: int,
        max_epoch: int,
        randomness: Optional[str] = None,
        as_secp256r1: bool = False,
    ) -> ZkSession:
        """Create a new ZkSession for one login flow. Synchronous."""
        if max_epoch > current_epoch + 30:
            raise ValueError(
                f"max_epoch ({max_epoch}) exceeds current_epoch + 30 ({current_epoch + 30})"
            )
        if randomness is None:
            randomness = str(int.from_bytes(secrets.token_bytes(16), "big"))

        kp = generate_ephemeral_keypair(as_secp256r1=as_secp256r1)
        return ZkSession(
            _token=_SESSION_TOKEN,
            client=self,
            provider=provider,
            epk_bytes=kp["public_key"],
            prv_bytes=kp["private_key"],
            nonce=compute_nonce(kp["public_key"], max_epoch, randomness),
            max_epoch=max_epoch,
            randomness=randomness,
            as_secp256r1=as_secp256r1,
        )
