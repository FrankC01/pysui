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

# -*- coding: utf-8 -*-


"""Keypair unit tests."""

import base64
import pytest

from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_types.address import address_from_keystring
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

TEST_ED25519_KEYSTRING = "AIIKwlBXko96i36aKTeHMYiWPDzNzQA6btkfK8f7uInJ3kX5ZqeoLqJZB2ZLhpj1xXHDlelzmej7yCca+ZGdAhY="
TEST_SECP256K1_KEYSTRING = "AQMm9+3O2Yn5KBWbwsRt33Gz6e6ankSeukxDFd9G30qSFQnSiMUHzIFGAASqu1PlQInM280Zae9JZMqYl+WzSnTS"
TEST_ED25519_ADDRESS = "0x83a299c2d0be351bdec7f509d16d5224075d0ab9"
TEST_SECP256K1_ADDRESS = "0xf5493a8ef4fbf1cbf0edcfdc37687fd6c2874f6c"
SIGN_INPUT_DATA = "APfrWX20DMtUWAvHxuv31tqBHogKNKnxuKA1QeB+wXGUx+Rp9/CGD9TzeazNhELCD2Y4o2VW5dL1juwzOUuEiAI9cjQi2P11jfUgBHa+Ah55U457R8w6ydbqSuIixhMm6w=="
# SECP_SIG = "3ka2oyct+ukiW65kEQBEFiVbhKRRwACxC6wbGBYjOlpltwqP5gdWildwJJoEAd8fwZqf+kufUWRsOkZFHr0LggA="
ED25_SIG = "FRS1Amac5cBHHD+HHtHRsmOnc7ytS59pGYiHrWb41XSxRLrtGxX7kvkaSB5IyxzXJNxKzdMMnBS28Jf/Oid1BQ=="


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


def test_edwards_signing() -> None:
    """Test signing."""
    edkp = keypair_from_keystring(TEST_ED25519_KEYSTRING)
    sig = edkp.private_key.sign(base64.b64decode(SIGN_INPUT_DATA))
    assert sig.signature == ED25_SIG


# def test_secp_signing() -> None:
#     """Test signing."""
#     edkp = keypair_from_keystring(TEST_SECP256K1_KEYSTRING)
#     sig = edkp.private_key.sign(base64.b64decode(SIGN_INPUT_DATA))
#     assert sig.signature == SECP_SIG


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
