#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Keypair unit tests."""

import base64
import pytest

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_types import address_from_keystring
from pysui.sui.sui_crypto import (
    SuiPublicKeyED25519,
    SuiPrivateKeyED25519,
    SuiPublicKeySECP256K1,
    SuiPrivateKeySECP256K1,
    keypair_from_keystring,
    create_new_address,
)
from pysui.sui.sui_constants import (
    SUI_KEYPAIR_LEN,
    ED25519_PRIVATEKEY_BYTES_LEN,
    ED25519_PUBLICKEY_BYTES_LEN,
    SECP256K1_PRIVATEKEY_BYTES_LEN,
    SECP256K1_PUBLICKEY_BYTES_LEN,
)

TEST_ED25519_KEYSTRING = "APLkwzgb263XFdZB2CloxMz4z2h4pP2m7C5y1ef56MTaHnSr41donGv0yAIhYgWc6DJUdoWE4ZTF020YAOQ9tyw="
TEST_SECP256K1_KEYSTRING = "AQLjRaEVn1AOwAy3IKIzhrPXwBKSrD7QHfrI0k7GnDidv3y11eFD+gwe2A86VG6y4S8dpK2FGC68MZ6Y7fB4FFpb"
TEST_ED25519_ADDRESS = "0x2e8c9bb1260d44fd5ba4c5ddde10bb13b47067f8"
TEST_SECP256K1_ADDRESS = "0xb2ca232ea8fec377ded6048c933b73ce97c842a8"


def test_ed25519_pass() -> None:
    """Test conversion from Sui keystring to ED25519."""
    assert len(TEST_ED25519_KEYSTRING) == SUI_KEYPAIR_LEN
    test_bytes = base64.b64decode(TEST_ED25519_KEYSTRING)
    assert test_bytes[0] == SignatureScheme.ED25519
    test_pubbytes = test_bytes[1:33]
    assert len(test_pubbytes) == ED25519_PUBLICKEY_BYTES_LEN
    test_prvbytes = test_bytes[33:]
    assert len(test_prvbytes) == ED25519_PRIVATEKEY_BYTES_LEN
    sui_pubkey = SuiPublicKeyED25519(test_pubbytes)
    assert sui_pubkey is not None
    assert test_pubbytes == sui_pubkey.key_bytes
    assert len(sui_pubkey.key_bytes) == ED25519_PUBLICKEY_BYTES_LEN
    sui_privkey = SuiPrivateKeyED25519(test_prvbytes)
    assert sui_privkey is not None
    assert test_prvbytes == sui_privkey.key_bytes
    kpair = keypair_from_keystring(TEST_ED25519_KEYSTRING)
    assert kpair is not None


def test_secp256k1_pass() -> None:
    """Test conversion from Sui keystring to ED25519."""
    assert len(TEST_SECP256K1_KEYSTRING) == SUI_KEYPAIR_LEN
    test_bytes = base64.b64decode(TEST_SECP256K1_KEYSTRING)
    assert test_bytes[0] == SignatureScheme.SECP256K1
    test_pubbytes = test_bytes[1:34]
    assert len(test_pubbytes) == SECP256K1_PUBLICKEY_BYTES_LEN
    test_prvbytes = test_bytes[34:]
    assert len(test_prvbytes) == SECP256K1_PRIVATEKEY_BYTES_LEN
    sui_pubkey = SuiPublicKeySECP256K1(test_pubbytes)
    assert sui_pubkey is not None
    assert test_pubbytes == sui_pubkey.key_bytes
    assert len(sui_pubkey.key_bytes) == SECP256K1_PUBLICKEY_BYTES_LEN
    sui_privkey = SuiPrivateKeySECP256K1(test_prvbytes)
    assert sui_privkey is not None
    assert test_prvbytes == sui_privkey.key_bytes
    kpair = keypair_from_keystring(TEST_SECP256K1_KEYSTRING)
    assert kpair is not None


def test_ed25519_address_pass() -> None:
    """Test conversion from keystring to address."""
    suiaddress = address_from_keystring(TEST_ED25519_KEYSTRING)
    assert suiaddress is not None
    assert TEST_ED25519_ADDRESS == str(suiaddress.identifier)


def test_new_ed25519_address_pass() -> None:
    """Test new address generation for ED25519."""
    suiaddress = create_new_address(SignatureScheme.ED25519)
    assert suiaddress is not None


def test_new_secp256k1_address_pass() -> None:
    """Test new address generation for secp256k1."""
    suiaddress = create_new_address(SignatureScheme.SECP256K1)
    assert suiaddress is not None


def test_secp256k1_address_pass() -> None:
    """Test conversion from keystring to address."""
    suiaddress = address_from_keystring(TEST_SECP256K1_KEYSTRING)
    assert suiaddress is not None
    assert TEST_SECP256K1_ADDRESS == str(suiaddress.identifier)


@pytest.mark.xfail(raises=Exception)
def test_ed25519_address_length_fail() -> None:
    """Test string length error."""
    _suiaddress = address_from_keystring("ThisWillFail")


@pytest.mark.xfail(raises=Exception)
def test_ed25519_address_content_fail() -> None:
    """Test string length error."""
    decoded = list(base64.b64decode(TEST_ED25519_KEYSTRING))
    # Not a valid scheme
    decoded[0] = 2
    _suiaddress = address_from_keystring(base64.b64encode(bytes(decoded)))
