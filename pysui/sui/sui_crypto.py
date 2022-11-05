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


"""Sui Crpto Utilities."""

import base64
import secp256k1
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder


from ..abstracts import KeyPair, PrivateKey, PublicKey, SignatureScheme
from .sui_excepts import SuiInvalidKeyPair, SuiInvalidKeystringLength
from .sui_constants import (
    SUI_KEYPAIR_LEN,
    ED25519_PUBLICKEY_BYTES_LEN,
    ED25519_PRIVATEKEY_BYTES_LEN,
    ED25519_KEYPAIR_BYTES_LEN,
    SECP256K1_KEYPAIR_BYTES_LEN,
    SECP256K1_PUBLICKEY_BYTES_LEN,
    SECP256K1_PRIVATEKEY_BYTES_LEN,
)
from .sui_types import SuiSignature, SuiAddress

# m / purpose' / coin_type' / account' / change / address_index
_DEFAULT_ED25519_PATH = "m/44'/784'/0'/0'/0'"

# Edwards Curve Keys


class SuiPublicKeyED25519(PublicKey):
    """A ED25519 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != ED25519_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {ED25519_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._verify_key = VerifyKey(self.to_b64(), encoder=Base64Encoder)

    @property
    def pub_key(self) -> str:
        """Return self as base64 encoded string."""
        return self.to_b64()


class SuiPrivateKeyED25519(PrivateKey):
    """A ED25519 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        dlen = len(indata)
        if dlen != ED25519_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {ED25519_PRIVATEKEY_BYTES_LEN} bytes, found {dlen}")
        super().__init__(SignatureScheme.ED25519, indata)
        self._signing_key = SigningKey(self.to_b64(), encoder=Base64Encoder)

    def sign(self, data: bytes) -> str:
        """ED25519 sign data bytes."""
        return SuiSignature(self._signing_key.sign(data, encoder=Base64Encoder).signature)


class SuiKeyPairED25519(KeyPair):
    """A SuiKey Pair."""

    def __init__(self, pub_key_bytes: bytes, priv_key_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        self._scheme = SignatureScheme.ED25519
        self._private_key = SuiPrivateKeyED25519(priv_key_bytes)
        self._public_key = SuiPublicKeyED25519(pub_key_bytes)

    @property
    def private_key(self) -> PrivateKey:
        """Return the Private Key."""
        return self._private_key

    @property
    def public_key(self) -> PublicKey:
        """Return the Public Key."""
        return self._public_key

    @property
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""
        return self._scheme

    def to_bytes(self) -> bytes:
        """Convert keypair to bytes."""
        all_bytes = self.scheme.to_bytes(1, "little") + self.public_key.key_bytes + self.private_key.key_bytes
        return all_bytes

    @classmethod
    def unique(cls) -> "SuiKeyPairED25519":
        """Generate a unique ED25519 keypair."""
        signer = SigningKey.generate()
        verifier = signer.verify_key
        bytes(verifier)
        return cls(bytes(verifier), bytes(signer))

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != SUI_KEYPAIR_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {SUI_KEYPAIR_LEN}")
        base_decode = base64.b64decode(indata)
        if base_decode[0] == SignatureScheme.ED25519:
            return SuiKeyPairED25519.from_bytes(base_decode[1:])
        raise SuiInvalidKeyPair("Scheme not ED25519")

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        if len(indata) != ED25519_KEYPAIR_BYTES_LEN:
            raise SuiInvalidKeyPair("Expect bytes len of 64")
        return SuiKeyPairED25519(indata[0:32], indata[32:])

    def __repr__(self) -> str:
        """To string."""
        return f"PubKey {self._public_key}, PrivKey {self._private_key}"


# Secp256


class SuiPublicKeySECP256K1(PublicKey):
    """A SECP256K1 Public Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize public key."""
        if len(indata) != SECP256K1_PUBLICKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Public Key expects {SECP256K1_PUBLICKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256K1, indata)
        self._verify_key = secp256k1.PublicKey(indata, raw=True)

    @property
    def pub_key(self) -> str:
        """Return self as base64 encoded string."""
        return self.to_b64()


class SuiPrivateKeySECP256K1(PrivateKey):
    """A SECP256K1 Private Key."""

    def __init__(self, indata: bytes) -> None:
        """Initialize private key."""
        if len(indata) != SECP256K1_PRIVATEKEY_BYTES_LEN:
            raise SuiInvalidKeyPair(f"Private Key expects {SECP256K1_PRIVATEKEY_BYTES_LEN} bytes, found {len(indata)}")
        super().__init__(SignatureScheme.SECP256K1, indata)
        self._signing_key = secp256k1.PrivateKey(indata, raw=True)

    def sign(self, data: bytes) -> str:
        """secp256k1 sign data bytes."""
        sig = self._signing_key.ecdsa_sign_recoverable(data)
        sig_sb, sig_si = self._signing_key.ecdsa_recoverable_serialize(sig)
        sig_ba = bytearray(sig_sb)
        sig_ba.append(sig_si)
        fsig = base64.b64encode(sig_ba).decode()
        return SuiSignature(fsig)


class SuiKeyPairSECP256K1(KeyPair):
    """A SuiKey Pair."""

    def __init__(self, pub_key_bytes: bytes, priv_key_bytes: bytes) -> None:
        """Init keypair with public and private byte array."""
        self._scheme = SignatureScheme.SECP256K1
        self._public_key = SuiPublicKeySECP256K1(pub_key_bytes)
        self._private_key = SuiPrivateKeySECP256K1(priv_key_bytes)

    @property
    def private_key(self) -> PrivateKey:
        """Return the Private Key."""
        return self._private_key

    @property
    def public_key(self) -> PublicKey:
        """Return the Public Key."""
        return self._public_key

    @property
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""
        return self._scheme

    def to_bytes(self) -> bytes:
        """Convert keypair to bytes."""
        all_bytes = self.scheme.to_bytes(1, "little") + self.public_key.key_bytes + self.private_key.key_bytes
        return all_bytes

    @classmethod
    def unique(cls) -> KeyPair:
        """Generate a unique secp256k1 keypair."""
        signer = secp256k1.PrivateKey()
        return cls(signer.pubkey.serialize(compressed=True), signer.private_key)

    @classmethod
    def from_b64(cls, indata: str) -> KeyPair:
        """Convert base64 string to keypair."""
        if len(indata) != SUI_KEYPAIR_LEN:
            raise SuiInvalidKeyPair(f"Expect str len of {SUI_KEYPAIR_LEN}")
        base_decode = base64.b64decode(indata)
        if base_decode[0] == SignatureScheme.SECP256K1:
            return SuiKeyPairED25519.from_bytes(base_decode[1:])
        raise SuiInvalidKeyPair("Scheme not SECP256K1")

    @classmethod
    def from_bytes(cls, indata: bytes) -> KeyPair:
        """Convert bytes to keypair."""
        if len(indata) != SECP256K1_KEYPAIR_BYTES_LEN:
            raise SuiInvalidKeyPair("Expect bytes len of 65")
        return SuiKeyPairSECP256K1(indata[0:33], indata[33:])

    def __repr__(self) -> str:
        """To string."""
        return f"PubKey {self._public_key}, PrivKey {self._private_key}"


# Utility functions


def keypair_from_keystring(keystring: str) -> KeyPair:
    """Derive keypair from address string."""
    if len(keystring) != SUI_KEYPAIR_LEN:
        raise SuiInvalidKeystringLength(len(keystring))
    addy_bytes = base64.b64decode(keystring)
    match addy_bytes[0]:
        case SignatureScheme.ED25519:
            return SuiKeyPairED25519.from_bytes(addy_bytes[1:])
        case SignatureScheme.SECP256K1:
            return SuiKeyPairSECP256K1.from_bytes(addy_bytes[1:])
    raise NotImplementedError


def create_new_keypair(keytype: SignatureScheme = SignatureScheme.ED25519) -> KeyPair:
    """Generate a new keypair."""
    match keytype:
        case SignatureScheme.ED25519:
            return SuiKeyPairED25519.unique()
        case SignatureScheme.SECP256K1:
            return SuiKeyPairSECP256K1.unique()
        case _:
            raise NotImplementedError


def create_new_address(keytype: SignatureScheme) -> tuple[KeyPair, SuiAddress]:
    """Create a new keypair and address for a key type."""
    new_kp = create_new_keypair(keytype)
    return (new_kp, SuiAddress.from_bytes(new_kp.to_bytes()))
