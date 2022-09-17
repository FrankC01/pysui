"""Keypair unit tests."""

import base64
import pytest

from src.abstracts.client_keypair import SignatureScheme
from src.sui.sui_crypto import (
    SuiPublicKeyED25519,
    SuiPrivateKeyED25519,
    keypair_from_b64address,
    address_from_keystring,
)
from src.sui.sui_types import B64_ADDRESS_LEN, ED25519_KEY_BYTES_LEN

TEST_KEYSTRING = "APLkwzgb263XFdZB2CloxMz4z2h4pP2m7C5y1ef56MTaHnSr41donGv0yAIhYgWc6DJUdoWE4ZTF020YAOQ9tyw="
TEST_KNOWN_ADDRESS = "0x2e8c9bb1260d44fd5ba4c5ddde10bb13b47067f8"


def test_ed25519_pass() -> None:
    """Test conversion from Sui keystring to ED25519."""
    assert len(TEST_KEYSTRING) == B64_ADDRESS_LEN
    test_bytes = base64.b64decode(TEST_KEYSTRING)
    assert test_bytes[0] == SignatureScheme.ED25519
    test_pubbytes = test_bytes[1:33]
    assert len(test_pubbytes) == ED25519_KEY_BYTES_LEN
    test_prvbytes = test_bytes[33:]
    assert len(test_prvbytes) == ED25519_KEY_BYTES_LEN
    sui_pubkey = SuiPublicKeyED25519(test_pubbytes)
    assert sui_pubkey is not None
    assert test_pubbytes == sui_pubkey.key_bytes
    assert len(sui_pubkey.key_bytes) == ED25519_KEY_BYTES_LEN
    sui_privkey = SuiPrivateKeyED25519(test_prvbytes)
    assert sui_privkey is not None
    assert test_prvbytes == sui_privkey.key_bytes
    kpair = keypair_from_b64address(TEST_KEYSTRING)
    assert kpair is not None


def test_ed25519_address_pass() -> None:
    """Test conversion from keystring to address."""
    suiaddress = address_from_keystring(TEST_KEYSTRING)
    assert suiaddress is not None
    assert TEST_KNOWN_ADDRESS == suiaddress.address


@pytest.mark.xfail(raises=Exception)
def test_ed25519_address_length_fail() -> None:
    """Test string length error"""
    _suiaddress = address_from_keystring("ThisWillFail")


@pytest.mark.xfail(raises=Exception)
def test_ed25519_address_content_fail() -> None:
    """Test string length error"""
    decoded = list(base64.b64decode(TEST_KEYSTRING))
    # Not a valid scheme
    decoded[0] = 2
    _suiaddress = address_from_keystring(base64.b64encode(bytes(decoded)))
