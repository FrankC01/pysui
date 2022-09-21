"""Sui RPC Clients."""

from typing import Any
import httpx
from abstracts import Builder, SyncHttpRPC, RpcResult
from sui import SuiConfig, GetRpcAPI, from_json_api
from sui.sui_excepts import SuiRpcApiNotAvailable


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
        self._rpc_api = {}
        self._build_api_descriptors()

    def _build_api_descriptors(self):
        """Fetch RPC method descrptors."""
        builder = GetRpcAPI()
        result = self._client.post(self.config.url, headers=builder.header, json=builder.data).json()
        # result = self.execute(GetRpcAPI()).json()
        if isinstance(result["result"], dict) and "methods" in result["result"]:
            for rpc_api in result["result"]["methods"]:
                self._rpc_api[rpc_api["name"]] = from_json_api(rpc_api)

    def api_exists(self, api_name: str) -> bool:
        """Check if API supported in RPC host."""
        return api_name in self._rpc_api

    def execute(self, builder: Builder) -> Any:
        """Execute the builder construct."""
        if self.api_exists(builder.method):
            return self._client.post(self.config.url, headers=builder.header, json=builder.data)
        raise SuiRpcApiNotAvailable(builder.method)

    @property
    def rpc_api_names(self) -> list[str]:
        """Return names of RPC API methods."""
        return list(self._rpc_api.keys())

    @property
    def rpc_api(self) -> dict:
        """Return names of RPC API methods."""
        return self._rpc_api
