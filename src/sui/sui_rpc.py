"""Sui RPC Clients."""

from typing import Any
import httpx
from abstracts import Builder, SyncHttpRPC
from sui import SuiConfig


class BaseBuilder(Builder):
    """Base Builder Class."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__()
        self.__params = []
        self._method = ""

    @property
    def _params(self) -> list[str]:
        return self.__params

    def add_parameter(self, param: str) -> Any:
        """Append a parameter to end."""
        self.__params.append(param)
        return self

    @property
    def data(self) -> dict:
        """Return copy of the current data state."""
        dcopy = self._data.copy()
        dcopy["params"] = self._params
        return dcopy

    @property
    def header(self) -> dict:
        """Return copy of the current header."""
        return self._header.copy()

    @property
    def method(self) -> str:
        """Inspect method."""
        return self._method


class BuildObjectsForAddress(BaseBuilder):
    """Build Fetch Objects for Address."""

    def __init__(self) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = "sui_getObjectsOwnedByAddress"

    @property
    def data(self) -> dict:
        """Overload data return with method."""
        scopy = super().data
        scopy["method"] = self.method
        return scopy


class SuiClient(SyncHttpRPC):
    """Sui Syncrhonous Client."""

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = httpx.Client()

    def execute(self, builder: Builder) -> Any:
        """Execute the builder construct."""
        return self._client.post(self.config.url, headers=builder.header, json=builder.data)
