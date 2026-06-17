#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.zklogin_seal.zklogin_client."""

import pytest
from unittest.mock import MagicMock, patch

from pysui.zklogin_seal.zklogin_client import (
    ZkSession,
    ZkClaimKey,
    _SESSION_TOKEN,
)
from pysui.zklogin_seal._ext import _CRYPTO_AVAILABLE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(nonce: str = "test_nonce") -> ZkSession:
    mock_client = MagicMock()
    mock_client.salt = "12345678901234567890"
    return ZkSession(
        _token=_SESSION_TOKEN,
        client=mock_client,
        provider="google",
        epk_bytes=b"\x00" * 32,
        prv_bytes=b"\x00" * 32,
        nonce=nonce,
        max_epoch=100,
        randomness="randomness123",
        as_secp256r1=False,
    )


# ---------------------------------------------------------------------------
# ZkClaimKey
# ---------------------------------------------------------------------------

class TestZkClaimKey:
    def test_subject_is_sub(self):
        assert ZkClaimKey.SUBJECT == "sub"

    def test_audience_is_aud(self):
        assert ZkClaimKey.AUDIENCE == "aud"

    def test_is_str_subclass(self):
        assert isinstance(ZkClaimKey.SUBJECT, str)
        assert isinstance(ZkClaimKey.AUDIENCE, str)


# ---------------------------------------------------------------------------
# ZkSession instantiation
# ---------------------------------------------------------------------------

class TestZkSessionInstantiation:
    def test_direct_instantiation_raises_type_error(self):
        with pytest.raises(TypeError, match="ZkClient.session"):
            ZkSession(
                client=MagicMock(),
                provider="google",
                epk_bytes=b"\x00" * 32,
                prv_bytes=b"\x00" * 32,
                nonce="nonce",
                max_epoch=100,
                randomness="random",
                as_secp256r1=False,
            )

    def test_token_instantiation_succeeds(self):
        session = _make_session()
        assert session is not None
        assert session._nonce == "test_nonce"


# ---------------------------------------------------------------------------
# process_jwt claim selection (requires pysui-crypto)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _CRYPTO_AVAILABLE, reason="pysui-crypto not installed")
class TestProcessJwtClaimSelection:
    def test_invalid_key_claim_raises_value_error(self):
        session = _make_session(nonce="nonce123")
        with (
            patch("pysui.zklogin_seal.zklogin_client.extract_jwt_claims", return_value=("iss", "sub_val", "aud_val", "nonce123")),
            patch("pysui.zklogin_seal.zklogin_client.compute_address_seed", return_value=b"seed"),
            patch("pysui.zklogin_seal.zklogin_client.compute_zklogin_address", return_value="0xabc"),
        ):
            with pytest.raises(ValueError, match="key_claim_name must be ZkClaimKey"):
                session.process_jwt(jwt="fake.jwt", key_claim_name="email")

    def test_subject_claim_uses_sub_value(self):
        session = _make_session(nonce="nonce123")
        with (
            patch("pysui.zklogin_seal.zklogin_client.extract_jwt_claims", return_value=("iss", "sub_val", "aud_val", "nonce123")),
            patch("pysui.zklogin_seal.zklogin_client.compute_address_seed", return_value=b"seed") as mock_seed,
            patch("pysui.zklogin_seal.zklogin_client.compute_zklogin_address", return_value="0xabc"),
        ):
            session.process_jwt(jwt="fake.jwt", key_claim_name=ZkClaimKey.SUBJECT)
            assert mock_seed.call_args[0][1] == "sub_val"

    def test_audience_claim_uses_aud_value(self):
        session = _make_session(nonce="nonce123")
        with (
            patch("pysui.zklogin_seal.zklogin_client.extract_jwt_claims", return_value=("iss", "sub_val", "aud_val", "nonce123")),
            patch("pysui.zklogin_seal.zklogin_client.compute_address_seed", return_value=b"seed") as mock_seed,
            patch("pysui.zklogin_seal.zklogin_client.compute_zklogin_address", return_value="0xabc"),
        ):
            session.process_jwt(jwt="fake.jwt", key_claim_name=ZkClaimKey.AUDIENCE)
            assert mock_seed.call_args[0][1] == "aud_val"
