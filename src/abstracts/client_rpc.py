"""RPC Client Abstractions."""

from abc import ABC, abstractmethod
from typing import Any
from abstracts import ClientConfiguration


class Builder(ABC):
    """Builder for RPC Calls."""

    _data = {"jsonrpc": "2.0", "id": 1}
    _header = {"Content-Type": "application/json"}

    def __init__(self):
        """Initialize abstract Builder."""

    @property
    def data_dict(self) -> dict:
        """Return the data."""
        return self._data.copy()

    @property
    def header(self) -> dict:
        """Return the header."""
        return self._header.copy()

    @property
    @abstractmethod
    def txn_required(self) -> bool:
        """Return the transaction required flag."""

    @property
    @abstractmethod
    def method(self) -> str:
        """Return method."""


class RpcResult(ABC):
    """Rpc Result for call returns."""

    def __init__(self) -> None:
        """Initialize Result."""
        self._success = True

    @property
    def succeeded(self) -> bool:
        """Return success indicator."""
        return self._success

    @property
    def failed(self) -> bool:
        """Return failure indicator."""
        return not self.succeeded


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
