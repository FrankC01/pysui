"""Keypair unit tests."""

import base64

from src.abstracts.client_keypair import SignatureScheme
from src.sui.sui_crypto import (
    B64_ADDRESS_LEN,
    ED25519_KEY_BYTES_LEN,
    SuiPublicKeyED25519,
    SuiPrivateKeyED25519,
    keypair_from_b64address,
)
from src.sui import parse_keystring_to_address


def test_ed25519_pass() -> None:
    """Test conversion from Sui keystring to ED25519."""
    test_b64 = "APLkwzgb263XFdZB2CloxMz4z2h4pP2m7C5y1ef56MTaHnSr41donGv0yAIhYgWc6DJUdoWE4ZTF020YAOQ9tyw="
    assert len(test_b64) == B64_ADDRESS_LEN
    test_bytes = base64.b64decode(test_b64)
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
    kpair = keypair_from_b64address(test_b64)
    assert kpair is not None


def test_ed25519_address_pass() -> None:
    """Test conversion from keystring to address."""
    knwnaddy = "0x2e8c9bb1260d44fd5ba4c5ddde10bb13b47067f8"
    keystring = "APLkwzgb263XFdZB2CloxMz4z2h4pP2m7C5y1ef56MTaHnSr41donGv0yAIhYgWc6DJUdoWE4ZTF020YAOQ9tyw="
    suiaddress = parse_keystring_to_address(keystring)
    assert suiaddress is not None
    assert knwnaddy == suiaddress.address
