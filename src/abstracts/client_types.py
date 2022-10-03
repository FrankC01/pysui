"""Type Client Abstractions."""
from abc import ABC, abstractmethod
from numbers import Number
from typing import Any


class ClientAbstractScalarType(ABC):
    """Core scalar type."""

    def __init__(self, value: Any) -> None:
        """Initialize with identifier."""
        self._value = value

    def value(self) -> Any:
        """Return the self value."""
        return self._value

    def __str__(self) -> str:
        """Convert value to string using formatting."""
        return f"{self._value}"


class ClientAbstractClassType(ABC):
    """Core type that supports identification."""

    def __init__(self, identifier: ClientAbstractScalarType) -> None:
        """Initialize with identifier."""
        self._identifier = identifier

    @property
    def identifier(self) -> ClientAbstractScalarType:
        """Return the types identifer."""
        return self._identifier


class ClientObjectDescriptor(ClientAbstractClassType):
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


class ClientType(ClientAbstractClassType):
    """Base type abstraction."""

    @property
    @abstractmethod
    def data_type(self) -> str:
        """Return the data type."""

    @property
    @abstractmethod
    def type_signature(self) -> str:
        """Return the type signature."""

    @property
    @abstractmethod
    def has_public_transfer(self) -> bool:
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
