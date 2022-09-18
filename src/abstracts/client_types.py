"""Type Client Abstractions."""
from abc import ABC, abstractmethod
from numbers import Number


class ClientAbstractType(ABC):
    """Core type that supports identification."""

    def __init__(self, identifier: str) -> None:
        """Initialize with identifier."""
        self._identifier = identifier

    @property
    def identifer(self) -> str:
        """Return the types identifer."""
        return self._identifier


class ClientObjectDescriptor(ClientAbstractType):
    """Base type descriptor abstraction."""

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


class ClientType(ClientAbstractType):
    """Base type abstraction."""

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


class ClientFunction(ABC):
    """Base function abstraction."""


class ClientModule(ABC):
    """Base module abstraction."""

    @property
    @abstractmethod
    def functions(self) -> list[ClientFunction]:
        """Return the modules functions."""


class ClientPackage(ABC):
    """Base package abstraction."""

    def __init__(self) -> None:
        """Initialize package."""
        self._modules = []

    @property
    def modules(self) -> list[ClientModule]:
        """Return the package's modules."""
        return self._modules
