"""Sui RPC Clients."""

from typing import Any
import httpx
from abstracts import Builder, SyncHttpRPC, RpcResult
from sui import SuiConfig


class SuiRpcResult(RpcResult):
    """Sui RpcResult."""

    def __init__(self, result_status: bool, result_fail_string: str, result_data: Any) -> None:
        """Initialize a new RpcResult."""
        super().__init__()
        self._success = result_status
        self._result_str = result_fail_string
        self._data = result_data

    @property
    def data(self) -> Any:
        """Get result data."""
        return self._data

    @property
    def result(self) -> Any:
        """Get result string."""
        return self._result_str


class SuiClient(SyncHttpRPC):
    """Sui Syncrhonous Client."""

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = httpx.Client()

    def execute(self, builder: Builder) -> Any:
        """Execute the builder construct."""
        return self._client.post(self.config.url, headers=builder.header, json=builder.data)
