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


"""Sui RPC Clients."""

from json import JSONDecodeError
from typing import Any
import httpx
from abstracts import SyncHttpRPC, RpcResult
from sui import SuiConfig, GetRpcAPI, build_api_descriptors, SuiApi, SuiBaseBuilder
from sui.sui_txn_validator import validate_api
from sui.sui_excepts import SuiRpcApiNotAvailable


class SuiRpcResult(RpcResult):
    """Sui RpcResult."""

    def __init__(self, result_status: bool, result_string: str, result_data: Any = None) -> None:
        """Initialize a new RpcResult."""
        super().__init__()
        self._status: bool = result_status
        self._result_str: str = result_string
        self._data: Any = result_data

    def is_ok(self) -> bool:
        """Ease of use status."""
        return self._status is True

    def is_err(self) -> bool:
        """Ease of use status."""
        return self._status is True

    @property
    def result_data(self) -> Any:
        """Get result data."""
        return self._data

    @property
    def result_string(self) -> str:
        """Get result data."""
        return self._result_str


class SuiClient(SyncHttpRPC):
    """Sui Syncrhonous Client."""

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = httpx.Client()
        self._rpc_api = {}
        self._build_api_descriptors()

    def _generate_data_block(self, data_block: dict, method: str, params: list) -> dict:
        """Build the json data block for Rpc."""
        data_block["method"] = method
        data_block["params"] = params
        return data_block

    def _build_api_descriptors(self):
        """Fetch RPC method descrptors."""
        builder = GetRpcAPI()
        try:
            result = self._client.post(
                self.config.url,
                headers=builder.header,
                json=self._generate_data_block(builder.data_dict, builder.method, builder.params),
            ).json()
            self._rpc_api, self._schema_dict = build_api_descriptors(result)
        except JSONDecodeError as jexc:
            raise jexc
        except httpx.ReadTimeout as hexc:
            raise hexc

    def api_exists(self, api_name: str) -> bool:
        """Check if API supported in RPC host."""
        return api_name in self._rpc_api

    @property
    def rpc_api(self) -> dict:
        """Return entire dictionary of RPC API methods."""
        return self._rpc_api

    def _api_method(self, method_name: str) -> SuiApi:
        """Get the method definition."""

    def _argument_check(self, _api_method: SuiApi, builder: SuiBaseBuilder) -> SuiBaseBuilder:
        """Perform argument validations."""
        return builder

    def execute(self, builder: SuiBaseBuilder, print_json: bool = False) -> Any:
        """Execute the builder construct."""
        if not builder.method in self._rpc_api:
            raise SuiRpcApiNotAvailable(builder.method)
        parm_results = [y for x, y in validate_api(self._rpc_api[builder.method], builder)]
        jblock = self._generate_data_block(builder.data_dict, builder.method, parm_results)
        if print_json:
            print(f"jblock {jblock}")
        try:
            return SuiRpcResult(
                True,
                None,
                self._client.post(
                    self.config.url,
                    headers=builder.header,
                    json=jblock,
                ).json(),
            )
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except httpx.ReadTimeout as hexc:
            return SuiRpcResult(False, "HTTP read timeout error", vars(hexc))

    @property
    def rpc_api_names(self) -> list[str]:
        """Return names of RPC API methods."""
        return list(self._rpc_api.keys())
