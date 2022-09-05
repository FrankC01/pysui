"""RPC Client Abstractions."""

from abc import ABC, abstractmethod
from typing import Any
from abstracts import ClientConfiguration


class Builder(ABC):
    """Builder for RPC Calls."""

    def __init__(self):
        """Default Builder Initializer."""
        self._data = {"jsonrpc": "2.0", "id": 1}
        self._header = {"Content-Type": "application/json"}

    @property
    @abstractmethod
    def data(self) -> dict:
        """Return the current data."""

    @property
    @abstractmethod
    def header(self) -> dict:
        """Return the current header."""


class SyncHttpRPC(ABC):
    """Synchronous HTTP RPC Client."""

    def __init__(self, config: ClientConfiguration) -> None:
        """Initialize Base Client."""
        self._config = config

    @property
    def config(self) -> ClientConfiguration:
        """Return the client configuration."""
        return self._config

    @abstractmethod
    def execute(self, builder: Builder) -> Any:
        """Execute builder content."""


class AsyncHttpRPC(ABC):
    """Asynchronous HTTP RPC Client."""

    def __init__(self, config: ClientConfiguration) -> None:
        """Initialize Base Client."""
        self._config = config

    @property
    def config(self) -> ClientConfiguration:
        """Return the client configuration."""
        return self._config
