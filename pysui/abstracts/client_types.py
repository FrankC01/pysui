"""Type Client Abstractions."""
from abc import ABC
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
