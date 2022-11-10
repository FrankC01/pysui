#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-


"""RPC Client Abstractions."""

from abc import ABC, abstractmethod
from typing import Any
from .client_config import ClientConfiguration


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
        """Return transaction required flag."""

    @property
    @abstractmethod
    def method(self) -> str:
        """Return RPC API method name."""


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


class Provider(ABC):
    """Generic provider state."""

    def __init__(self, config: ClientConfiguration) -> None:
        """Initialize Base Client."""
        self._config = config

    @property
    def config(self) -> ClientConfiguration:
        """Return the client configuration."""
        return self._config


class SyncHttpRPC(Provider):
    """Synchronous HTTP RPC Client."""

    @abstractmethod
    def execute(self, builder: Builder) -> RpcResult:
        """Execute builder content."""


class AsyncHttpRPC(Provider):
    """Asynchronous HTTP RPC Client."""

    @abstractmethod
    async def execute(self, builder: Builder) -> RpcResult:
        """Execute builder content."""
