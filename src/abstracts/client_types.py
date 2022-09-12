"""Type Client Abstractions."""
from abc import ABC, abstractmethod
from numbers import Number


class ClientObjectDescriptor(ABC):
    """Base type descriptor abstraction."""

    @property
    @abstractmethod
    def identifer(self) -> str:
        """Return the types identifer."""

    @property
    @abstractmethod
    def version(self) -> Number:
        """Return the types version."""

    @property
    @abstractmethod
    def owner(self) -> str:
        """Return the types instance owner."""

    @property
    @abstractmethod
    def type_signature(self) -> str:
        """Return the types type."""


class ClientType(ABC):
    """Base type abstraction."""

    @property
    @abstractmethod
    def identifer(self) -> str:
        """Return the type identifer."""

    @property
    @abstractmethod
    def data_type(self) -> str:
        """Return the data type."""

    @property
    @abstractmethod
    def type_signature(self) -> str:
        """Return the type type."""

    @property
    @abstractmethod
    def is_transferable(self) -> bool:
        """Return the types type."""
