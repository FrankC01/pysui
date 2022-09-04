"""Abstraction for Types."""
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
