"""Sui RPC Clients."""

from typing import Any
import httpx
from abstracts import Builder, SyncHttpRPC
from sui import SuiConfig


class SuiClient(SyncHttpRPC):
    """Sui Syncrhonous Client."""

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = httpx.Client()

    def execute(self, builder: Builder) -> Any:
        """Execute the builder construct."""
        return self._client.post(self.config.url, headers=builder.header, json=builder.data)
