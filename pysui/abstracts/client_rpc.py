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

    @abstractmethod
    def is_ok(self) -> bool:
        """Return success indicator."""

    @abstractmethod
    def is_err(self) -> bool:
        """Return failure indicator."""

    @property
    @abstractmethod
    def result_data(self) -> Any:
        """Get result data."""

    @property
    @abstractmethod
    def result_string(self) -> str:
        """Get result data."""


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
    def execute(self, builder: Builder) -> RpcResult:
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
