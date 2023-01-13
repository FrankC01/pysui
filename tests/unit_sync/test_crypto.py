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

# pylint: disable=line-too-long
TEST_ED25519_KEYSTRING = "ABxuKTPmP1+iOSJckBNBj0G4sRYC3ys8mRT9/zrIkrSB"
TEST_SECP256K1_KEYSTRING = "AVvk7nnAaMwJYk+pnVfpU57nLjGkxZdXVzU1BAzIH5lk"
TEST_ED25519_ADDRESS = "0x4cb2a458bcdea8593b261b2d90d0ec73053ca4de"
TEST_SECP256K1_ADDRESS = "0x7c7a86b564d5db0c5837191bd17980b2fb9934db"
SIGN_INPUT_DATA = "APfrWX20DMtUWAvHxuv31tqBHogKNKnxuKA1QeB+wXGUx+Rp9/CGD9TzeazNhELCD2Y4o2VW5dL1juwzOUuEiAI9cjQi2P11jfUgBHa+Ah55U457R8w6ydbqSuIixhMm6w=="
# SECP_SIG = "3ka2oyct+ukiW65kEQBEFiVbhKRRwACxC6wbGBYjOlpltwqP5gdWildwJJoEAd8fwZqf+kufUWRsOkZFHr0LggA="
ED25_SIG = "AKGcSh7lGP9vlPNRiy0lDkuB4I+0Q/LI/Gas/fqqNzF6e6pHpX7blwel0amSPXsO26M0YoUOxa+Bk5y7XXE9DA3GqXCOqPyrn6E/hmbypfgU/5VbAKu0HvOH5CPXtw52rA=="


def test_ed25519_pass() -> None:
    """Test conversion from Sui keystring to ED25519."""
    assert len(TEST_ED25519_KEYSTRING) == SUI_KEYPAIR_LEN
    test_bytes = base64.b64decode(TEST_ED25519_KEYSTRING)
    assert test_bytes[0] == SignatureScheme.ED25519
    test_kpair = keypair_from_keystring(TEST_ED25519_KEYSTRING)
    test_pubbytes = test_kpair.to_bytes()[1:33]
    assert len(test_pubbytes) == ED25519_PUBLICKEY_BYTES_LEN
    test_prvbytes = test_kpair.to_bytes()[33:]
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
    test_kpair = keypair_from_keystring(TEST_SECP256K1_KEYSTRING)
    test_pubbytes = test_kpair.to_bytes()[1:34]
    assert len(test_pubbytes) == SECP256K1_PUBLICKEY_BYTES_LEN
    test_prvbytes = test_kpair.to_bytes()[34:]
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
    sig = edkp.new_sign_secure(TEST_ED25519_KEYSTRING)
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
