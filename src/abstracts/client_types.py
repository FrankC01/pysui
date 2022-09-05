"""Type Client Abstractions."""
from abc import ABC, abstractmethod


class ClientType(ABC):
    """Base type abstraction."""

    @property
    @abstractmethod
    def identifer(self):
        """Return the types identifer."""

    @property
    @abstractmethod
    def version(self):
        """Return the types version."""

    @property
    @abstractmethod
    def owner(self):
        """Return the types instance owner."""

    @property
    @abstractmethod
    def type_signature(self):
        """Return the types type."""
