#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""SEAL key server client for encrypting and decrypting data."""
from __future__ import annotations

import base64

import httpx

from pysui import SuiRpcResult
from pysui.sui.sui_pgql.pgql_clients import AsyncClientBase
from pysui.sui.sui_common.sui_commands import GetDynamicFields
from pysui.zklogin_seal.config import ZkSealConfig, SealKeyServer
from pysui.zklogin_seal.types import SealDemType, SealEncryptedObject
from pysui.zklogin_seal.crypto import SealCredentials


def _uleb128(n: int) -> bytes:
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            break
    return bytes(result)


def _signed_request_bytes(ptb_bcs: bytes, enc_key_raw: bytes, enc_vk_raw: bytes) -> bytes:
    """BCS of RequestFormat {ptb: Vec<u8>, enc_key: Vec<u8>, enc_vk: Vec<u8>}."""
    def bcs_vec(data: bytes) -> bytes:
        return _uleb128(len(data)) + data
    return bcs_vec(ptb_bcs) + bcs_vec(enc_key_raw) + bcs_vec(enc_vk_raw)


class SealClient:
    """SEAL key server client for IBE-based encryption and threshold decryption."""

    def __init__(self, *, client: AsyncClientBase, config: ZkSealConfig) -> None:
        if config.active_group.group_name == "devnet":
            raise ValueError("SEAL is not supported on devnet")
        if not config.active_group.key_server_sets:
            raise ValueError(
                f"No SEAL key servers configured for group '{config.active_group.group_name}'. "
                "Add key servers via ZkSealConfig.add_key_server_set()"
            )
        self._client = client
        self._config = config

    @property
    def pysui_client(self) -> AsyncClientBase:
        return self._client

    @property
    def config(self) -> ZkSealConfig:
        return self._config

    def credentials(self, *, session_minutes: int = 30) -> SealCredentials:
        """Create a fresh SEAL credential bundle for the active address."""
        cfg = self._client.config
        keypair = cfg.active_group.keypair_for_address(address=cfg.active_address)
        sui_address = str(cfg.active_address)
        server_urls = [
            s.url
            for kss in self._config.active_group.key_server_sets
            for s in kss.servers
        ]
        return SealCredentials.create(
            keypair=keypair,
            server_urls=server_urls,
            session_minutes=session_minutes,
            sui_address=sui_address,
        )

    def _find_server(self, object_id_hex: str) -> SealKeyServer | None:
        """Search all sets in the active group for a server by object ID."""
        normalised = object_id_hex.lower().removeprefix("0x")
        for kss in self._config.active_group.key_server_sets:
            for srv in kss.servers:
                if srv.object_id.lower().removeprefix("0x") == normalised:
                    return srv
        return None

    async def _fetch_ibe_pk(self, server: SealKeyServer) -> bytes:
        """Fetch IBE public key (G2, 96 raw bytes) from on-chain dynamic fields."""
        result = await self._client.execute(command=GetDynamicFields(object_id=server.object_id))
        if not result.is_ok():
            raise ValueError(
                f"Failed to fetch dynamic fields for {server.object_id}: {result.result_string}"
            )
        for df in result.result_data.dynamic_fields:
            if df.field_object is None or df.field_object.json is None:
                continue
            value = df.field_object.json.to_dict().get("value", {})
            if isinstance(value, dict) and "pk" in value:
                return base64.b64decode(value["pk"])
        raise ValueError(f"IBE public key not found in dynamic fields for {server.object_id}")

    def _build_fetch_key_request(
        self,
        credentials: SealCredentials,
        ptb_bcs: bytes,
        package_id_str: str,
    ) -> dict:
        """Assemble the FetchKeyRequest JSON body for one key server."""
        enc_key_b64 = base64.b64encode(credentials.elgamal_pk).decode()
        enc_vk_b64 = base64.b64encode(credentials.elgamal_vk).decode()

        sr_bytes = _signed_request_bytes(ptb_bcs, credentials.elgamal_pk, credentials.elgamal_vk)
        request_sig_b64 = base64.b64encode(credentials.sign_request(sr_bytes)).decode()

        msg_str = credentials.signed_message(
            package_id=package_id_str,
            creation_time=credentials.creation_time_ms,
            ttl_min=credentials.session_minutes,
        )
        msg_b64 = base64.b64encode(msg_str.encode()).decode()
        cert_sig = credentials.keypair.sign_personal_message(msg_b64)

        return {
            "ptb": base64.b64encode(ptb_bcs).decode(),
            "enc_key": enc_key_b64,
            "enc_verification_key": enc_vk_b64,
            "request_signature": request_sig_b64,
            "certificate": {
                "user": credentials.sui_address,
                "session_vk": base64.b64encode(credentials.session_pk).decode(),
                "creation_time": credentials.creation_time_ms,
                "ttl_min": credentials.session_minutes,
                "signature": cert_sig,
                "mvr_name": None,
            },
        }

    async def encrypt(
        self,
        *,
        package_id: str,
        inner_id: bytes,
        key_servers: list[tuple[str, ...]],
        threshold: int,
        data: bytes,
        encryption_mode: SealDemType = SealDemType.AesGcm256,
        auth_context: Optional[bytes] = None,
    ) -> SuiRpcResult:
        """Encrypt data under SEAL IBE using the given key servers."""
        from pysui.zklogin_seal._ext import (
            _CRYPTO_AVAILABLE,
            INSTALL_HINT,
            seal_encrypt,
        )

        if not _CRYPTO_AVAILABLE:
            return SuiRpcResult(False, INSTALL_HINT, None)

        group_name = self._config.active_group.group_name
        server_objects: list[SealKeyServer] = []
        for tup in key_servers:
            set_name = tup[0]
            for alias in tup[1:]:
                srv = self._config.resolve_server(
                    group_name=group_name, set_name=set_name, alias_or_object_id=alias
                )
                if srv is None:
                    return SuiRpcResult(
                        False,
                        f"Key server '{alias}' not found in set '{set_name}'",
                        None,
                    )
                server_objects.append(srv)

        ibe_pks: list[bytes] = []
        for srv in server_objects:
            try:
                ibe_pks.append(await self._fetch_ibe_pk(srv))
            except ValueError as exc:
                return SuiRpcResult(False, str(exc), None)

        server_ids = [
            bytes.fromhex(srv.object_id.removeprefix("0x")) for srv in server_objects
        ]
        pkg_id_bytes = bytes.fromhex(package_id.removeprefix("0x"))
        try:
            encrypted_bytes, dem_key = seal_encrypt(
                pkg_id_bytes,
                inner_id,
                server_ids,
                ibe_pks,
                threshold,
                data,
                encryption_mode,
                aad=auth_context,
            )
        except Exception as exc:
            return SuiRpcResult(False, str(exc), None)

        return SuiRpcResult(True, "", (SealEncryptedObject.from_bytes(encrypted_bytes), dem_key))

    async def decrypt(
        self,
        *,
        encrypted_object: SealEncryptedObject,
        transaction_kind: bytes,
        credentials: SealCredentials,
    ) -> SuiRpcResult:
        """Fetch key shares from SEAL servers and decrypt the encrypted object."""
        from pysui.zklogin_seal._ext import (
            _CRYPTO_AVAILABLE,
            INSTALL_HINT,
            seal_decrypt,
            verify_user_secret_key,
        )

        if not _CRYPTO_AVAILABLE:
            return SuiRpcResult(False, INSTALL_HINT, None)

        try:
            eo_services = encrypted_object.services
            eo_package_id_bytes = encrypted_object.package_id
        except Exception as exc:
            return SuiRpcResult(False, f"Failed to parse encrypted object: {exc}", None)

        package_id_str = "0x" + eo_package_id_bytes.hex()
        ptb_bcs = transaction_kind[1:]  # strip 1-byte TransactionKind discriminant; caller must pass raw_kind().serialize() output

        user_secret_keys: list[tuple[bytes, bytes]] = []
        server_ibe_pks: list[bytes] = []

        async with httpx.AsyncClient() as http:
            for server_id_bytes, _index in eo_services:
                server_oid = "0x" + server_id_bytes.hex()
                srv = self._find_server(server_oid)
                if srv is None:
                    return SuiRpcResult(
                        False, f"Key server {server_oid} not found in config", None
                    )

                try:
                    ibe_pk = await self._fetch_ibe_pk(srv)
                except ValueError as exc:
                    return SuiRpcResult(False, str(exc), None)

                request_body = self._build_fetch_key_request(credentials, ptb_bcs, package_id_str)

                try:
                    resp = await http.post(
                        f"{srv.url.rstrip('/')}/v1/fetch_key",
                        json=request_body,
                        headers={
                            "Client-Sdk-Version": "1.1.0",
                            "Client-Sdk-Type": "rust",
                        },
                        timeout=30.0,
                    )
                    if resp.status_code != 200:
                        return SuiRpcResult(
                            False,
                            f"Key server '{srv.alias}' returned {resp.status_code}: {resp.text}",
                            None,
                        )
                    response_json = resp.json()
                except Exception as exc:
                    return SuiRpcResult(
                        False, f"HTTP error fetching key from {srv.url}: {exc}", None
                    )

                decryption_keys = response_json.get("decryption_keys", [])
                if not decryption_keys:
                    return SuiRpcResult(
                        False, f"No decryption keys in response from '{srv.alias}'", None
                    )

                verified = False
                for dk in decryption_keys:
                    raw_id = dk["id"]
                    full_id = bytes(raw_id) if isinstance(raw_id, list) else base64.b64decode(raw_id)
                    raw_ek = dk["encrypted_key"]
                    if isinstance(raw_ek, list):
                        encrypted_share = b"".join(base64.b64decode(s) for s in raw_ek)
                    else:
                        encrypted_share = base64.b64decode(raw_ek)
                    usk = credentials.decrypt_share(encrypted_share)
                    try:
                        verify_user_secret_key(usk, full_id, ibe_pk)
                        user_secret_keys.append((server_id_bytes, usk))
                        verified = True
                        break
                    except Exception:
                        continue
                if not verified:
                    return SuiRpcResult(
                        False,
                        f"USK verification failed for all keys from server '{srv.alias}'",
                        None,
                    )

                server_ibe_pks.append(ibe_pk)

        try:
            plaintext = seal_decrypt(
                encrypted_object.as_bytes(),
                user_secret_keys,
                public_keys=server_ibe_pks,
            )
        except Exception as exc:
            return SuiRpcResult(False, f"Decryption failed: {exc}", None)

        return SuiRpcResult(True, "", plaintext)
