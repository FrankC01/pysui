"""Type Client Abstractions."""
from abc import ABC
from typing import Any


class AbstractType(ABC):
    """Base most abstraction."""

    def __init__(self, identifier: Any) -> None:
        """Initialize type."""
        self._value = identifier

    @property
    def identifier(self) -> Any:
        """Return underlying value."""
        return self._value

    @property
    def value(self) -> Any:
        """Return underlying value."""
        return self._value

    def __eq__(self, other: "AbstractType") -> bool:
        """Equality check."""
        return str(self) == str(other)

    def __hash__(self) -> int:
        """Hashability."""
        return hash(str(self))

    def __str__(self) -> str:
        """Convert value to string using formatting."""
        if isinstance(self._value, str):
            return self._value
        if isinstance(self._value, bytes):
            return self._value.decode()
        if isinstance(self._value, int):
            return str(self._value)
        if isinstance(self._value, AbstractType):
            return str(self._value)
        raise NotImplementedError
        # return self._value if isinstance(self._value, str) else self._value.decode()  # f"{self._value}"
