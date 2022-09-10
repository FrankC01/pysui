"""KeyPair abstraction."""

from abc import ABC, abstractmethod
import base64
from typing import Any


class Key(ABC):
    """Base key abstract class."""

    def __init__(self, key_bytes: bytes) -> None:
        """Init with byte array."""
        self._bytes = key_bytes

    def to_b64(self) -> str:
        """Convert key bytes to base64."""
        return base64.b64encode(self._bytes)

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
    def from_b64(cls, indata: str) -> Any:
        """Convert base64 string to keypair."""

    @classmethod
    @abstractmethod
    def from_bytes(cls, indata: bytes) -> Any:
        """Convert bytes to keypair."""
