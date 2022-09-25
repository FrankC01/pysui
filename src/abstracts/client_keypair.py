"""KeyPair abstraction."""

from abc import ABC, abstractmethod
import base64
from enum import IntEnum


class SignatureScheme(IntEnum):
    """Key encoding scheme variations."""

    ED25519 = 0
    SECP256K1 = 1


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


class PrivateKey(Key):
    """PrivateKey construct."""


class PublicKey(Key):
    """PublicKey construct."""


class KeyPair(ABC):
    """KeyPair construct."""

    @classmethod
    @abstractmethod
    def from_b64(cls, indata: str) -> "KeyPair":
        """Convert base64 string to keypair."""

    @classmethod
    @abstractmethod
    def from_bytes(cls, indata: bytes) -> "KeyPair":
        """Convert bytes to keypair."""

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Convert keypair to encoded bytes."""

    def to_b64(self) -> str:
        """Convert key bytes to base64."""
        return base64.b64encode(self.to_bytes()).decode()
