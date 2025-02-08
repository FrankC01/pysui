#    Copyright Frank V. Castellucci
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


"""KeyPair abstraction."""

from abc import ABC, abstractmethod
import base64
from enum import IntEnum
from typing import Union
from pysui.abstracts import AbstractType


class SignatureScheme(IntEnum):
    """Key encoding scheme variations."""

    ED25519 = 0
    SECP256K1 = 1
    SECP256R1 = 2
    MULTISIG = 3
    BLS12381 = 4
    ZKLOGINAUTHENTICATOR = 5

    def as_str(self) -> str:
        """Get scheme as string."""
        if self is SignatureScheme.ED25519:
            return self.name
        if self is SignatureScheme.SECP256K1:
            return "Secp256k1"
        if self is SignatureScheme.SECP256R1:
            return "Secp256r1"
        if self is SignatureScheme.MULTISIG:
            return "MultiSig"
        if self is SignatureScheme.BLS12381:
            return "Bls12381"
        if self is SignatureScheme.ZKLOGINAUTHENTICATOR:
            return "ZkLoginAuthenticator"
        raise TypeError(f"Unknown scheme {self.name}")

    @property
    def sig_scheme(self) -> str:
        """As signature scheme string."""
        return self.as_str()


class Key(ABC):
    """Base key abstract class."""

    def __init__(self, scheme: SignatureScheme, key_bytes: bytes) -> None:
        """Init with byte array."""
        self._keybytes = key_bytes
        self._scheme = scheme

    @property
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""
        return self._scheme

    @property
    def key_bytes(self) -> bytes:
        """Get the keys bytes."""
        return self._keybytes

    def to_b64(self) -> str:
        """Convert key bytes to base64."""
        return base64.b64encode(self.key_bytes).decode()

    def __repr__(self) -> str:
        """To string."""
        return f"{self.to_b64()}"


class PublicKey(Key):
    """PublicKey construct."""

    def scheme_and_key(self) -> bytes:
        """scheme_and_key returns bytes of key scheme + pubkey bytes.

        :return: pubkey bytes with scheme value prefix
        :rtype: bytes
        """
        return self.scheme.value.to_bytes(1, "little") + self.key_bytes

    @abstractmethod
    def serialize(self) -> str:
        """Serialize public key to base64 keystring."""

    @classmethod
    @abstractmethod
    def from_serialized(cls, indata: str) -> "PublicKey":
        """Convert base64 string to public key."""


class PrivateKey(Key):
    """PrivateKey construct."""

    @abstractmethod
    def sign_secure(self, tx_data: str) -> list:
        """Sign data securely, returning signature."""


class KeyPair(ABC):
    """KeyPair construct."""

    @property
    @abstractmethod
    def scheme(self) -> SignatureScheme:
        """Get the keys scheme."""

    @property
    @abstractmethod
    def public_key(self) -> Union[PublicKey, None]:
        """Get the keypair public key."""

    @property
    @abstractmethod
    def private_key(self) -> Union[PrivateKey, None]:
        """Get the keypair private key."""

    @abstractmethod
    def new_sign_secure(self, tx_data: str) -> Union[AbstractType, str]:
        """Sign transactions securley."""

    @abstractmethod
    def sign_personal_message(self, message: str) -> str:
        """Sign arbitrary base64 encoded message with intent, returning a base64 signed personal message."""

    @abstractmethod
    def verify_signature(self, message: str, signature: str) -> bool:
        """Verify message with signature, returning true/false."""

    @classmethod
    @abstractmethod
    def from_b64(cls, indata: str) -> "KeyPair":
        """Convert base64 string to keypair."""

    @classmethod
    @abstractmethod
    def from_bech32(cls, indata: str) -> "KeyPair":
        """Convert bech32 encoded string to keypair."""

    @classmethod
    @abstractmethod
    def from_bytes(cls, indata: bytes) -> "KeyPair":
        """Convert bytes to keypair."""

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Convert keypair to encoded bytes."""

    @abstractmethod
    def to_bech32(self) -> str:
        """Convert keypair private key to bech32 format."""

    @abstractmethod
    def serialize(self) -> str:
        """Serialize to platform keystring for persist."""

    def to_b64(self) -> str:
        """Convert full key bytes (priv and pub) to base64."""
        return base64.b64encode(self.to_bytes()).decode()
