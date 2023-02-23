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
    SuiPublicKeySECP256R1,
    SuiPrivateKeySECP256R1,
    keypair_from_keystring,
    create_new_address,
)
from pysui.sui.sui_constants import (
    SUI_KEYPAIR_LEN,
    ED25519_PRIVATEKEY_BYTES_LEN,
    ED25519_PUBLICKEY_BYTES_LEN,
    SECP256K1_PRIVATEKEY_BYTES_LEN,
    SECP256K1_PUBLICKEY_BYTES_LEN,
    SECP256R1_PRIVATEKEY_BYTES_LEN,
    SECP256R1_PUBLICKEY_BYTES_LEN,
)

# pylint: disable=line-too-long
TEST_ED25519_KEYSTRING = "AFGIonkZWixFTVrcNVBh3vGwqCXA2zKwDzpuANkBFWUN"
TEST_SECP256K1_KEYSTRING = "AT4Be0JOKSRRs0BEZFwH756JEpBjzA9DwG/fJrv/W1Cn"
TEST_SECP256R1_KEYSTRING = "AqPmvgC0d98+QsB9W2TumfztXyyxN3FxiTCBf3Fbd3Mg"

TEST_ED25519_ADDRESS = "0xe58c532315dced9d08fcb9c3aab16eac0d7fbc5f"
TEST_SECP256K1_ADDRESS = "0x49611f06b7e59d09bdc72d2947f6a01cbc9b9480"
TEST_SECP256R1_ADDRESS = "0x69fac8d4fb598485d21fd1c599cabfbd07437651"

PAY_FROM_ED25519 = "AAYBLF99r3B6NVs1mOPEqaewM/vckDYKCQAAAAAAACCwIxopOMvtF9OcOqIMQgIAfYbccf+U4zJZ3xO0JlRsMUlhHwa35Z0JvcctKUf2oBy8m5SA5YxTIxXc7Z0I/LnDqrFurA1/vF8sX32vcHo1WzWY48Spp7Az+9yQNgoJAAAAAAAAILAjGik4y+0X05w6ogxCAgB9htxx/5TjMlnfE7QmVGwxAQAAAAAAAAAsAQAAAAAAAA=="
PAY_FROM_SECP256K1 = "AAYBLF99r3B6NVs1mOPEqaewM/vckDYKCQAAAAAAACCwIxopOMvtF9OcOqIMQgIAfYbccf+U4zJZ3xO0JlRsMWn6yNT7WYSF0h/RxZnKv70HQ3ZRSWEfBrflnQm9xy0pR/agHLyblIAsX32vcHo1WzWY48Spp7Az+9yQNgoJAAAAAAAAILAjGik4y+0X05w6ogxCAgB9htxx/5TjMlnfE7QmVGwxAQAAAAAAAAAsAQAAAAAAAA=="
PAY_FROM_SECP256R1 = "AAYBLF99r3B6NVs1mOPEqaewM/vckDYKCQAAAAAAACCwIxopOMvtF9OcOqIMQgIAfYbccf+U4zJZ3xO0JlRsMdqhBX9gEEU85ylRDw2BEOnLszSTafrI1PtZhIXSH9HFmcq/vQdDdlEsX32vcHo1WzWY48Spp7Az+9yQNgoJAAAAAAAAILAjGik4y+0X05w6ogxCAgB9htxx/5TjMlnfE7QmVGwxAQAAAAAAAAAsAQAAAAAAAA=="

ED25_SIG = "ALRkZf8rF/Fms9dKWD21YtZKCz93clj/zIlu3EA13QGUJSEMyr3CzjeEyogbCUfFoJyX4H92oUHEILhVypEYBwLOCfvqghldQd/4nAs/0nKZgjGNJD4f9rL0KVolPoPhng=="
K1_SIG = "ARXVT1zs/azj1ks6wo2G/cs3pSVdQ+13Lhiuqj2/EYCzExKT9YhFPbHflfCeOqjb6yRmKpLRs3aVNtWzriSJ8sQCP/S98MO1Nlcw8ClVtJW4KzLJXzRm+X7vu5/sl33yziY="
R1_SIG = "Aj3ePiwI34Q1h1Oiulq4WI4p4UrpL2av7M3bZcPKTFaIndaiS9K0y9QuGvf5VLlOl/2KIvq/FDIaLjGf/x8Fun4Dv49dV+NohQCZEk8eU+iO5Ameo8dggMPVCmFZt8lI9iM="


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


def test_secp256r1_pass() -> None:
    """Test conversion from Sui keystring to ED25519."""
    assert len(TEST_SECP256R1_KEYSTRING) == SUI_KEYPAIR_LEN
    test_bytes = base64.b64decode(TEST_SECP256R1_KEYSTRING)
    assert test_bytes[0] == SignatureScheme.SECP256R1
    test_kpair = keypair_from_keystring(TEST_SECP256R1_KEYSTRING)
    test_pubbytes = test_kpair.to_bytes()[1:34]
    assert len(test_pubbytes) == SECP256R1_PUBLICKEY_BYTES_LEN
    test_prvbytes = test_kpair.to_bytes()[34:]
    assert len(test_prvbytes) == SECP256R1_PRIVATEKEY_BYTES_LEN
    sui_pubkey = SuiPublicKeySECP256R1(test_pubbytes)
    assert sui_pubkey is not None
    assert test_pubbytes == sui_pubkey.key_bytes
    assert len(sui_pubkey.key_bytes) == SECP256R1_PUBLICKEY_BYTES_LEN
    sui_privkey = SuiPrivateKeySECP256R1(test_prvbytes)
    assert sui_privkey is not None
    assert test_prvbytes == sui_privkey.key_bytes
    kpair = keypair_from_keystring(TEST_SECP256R1_KEYSTRING)
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


def test_secp256r1_address_pass() -> None:
    """Test conversion from keystring to address."""
    suiaddress = address_from_keystring(TEST_SECP256R1_KEYSTRING)
    assert suiaddress is not None
    assert TEST_SECP256R1_ADDRESS == str(suiaddress.identifier)


def test_edwards_signing() -> None:
    """Test signing."""
    edkp = keypair_from_keystring(TEST_ED25519_KEYSTRING)
    sig = edkp.new_sign_secure(PAY_FROM_ED25519)
    assert sig.signature == ED25_SIG


def test_secp256k1_signing() -> None:
    """Test signing."""
    edkp = keypair_from_keystring(TEST_SECP256K1_KEYSTRING)
    sig = edkp.new_sign_secure(PAY_FROM_SECP256K1)
    assert sig.signature == K1_SIG


def test_secp256r1_signing() -> None:
    """Test signing."""
    edkp = keypair_from_keystring(TEST_SECP256R1_KEYSTRING)
    sig = edkp.new_sign_secure(PAY_FROM_SECP256R1)
    assert sig.signature == R1_SIG


@pytest.mark.xfail(raises=Exception)
def test_ed25519_address_length_fail() -> None:
    """Test string length error."""
    _suiaddress = address_from_keystring("ThisWillFail")
