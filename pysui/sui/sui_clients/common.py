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

"""Sui Client common classes module."""

from typing import Any
from pkg_resources import packaging
from pysui.abstracts import RpcResult, Provider
from pysui.sui.sui_builders.base_builder import SuiRequestType
from pysui.sui.sui_config import SuiConfig


class SuiRpcResult(RpcResult):
    """Sui RpcResult.

    Captures information returned from simple and complex RPC API calls
    """

    def __init__(self, result_status: bool, result_string: str, result_data: Any = None) -> None:
        """__init__ SuiRpcResult constructor.

        :param result_status: bool indicating success (True) or not (False)
        :type result_status: bool
        :param result_string: Any string, typically to capture a failure of a call
        :type result_string: str
        :param result_data: If success, contains data realized by RPC result, defaults to None
        :type result_data: Any, optional
        """
        super().__init__()
        self._status: bool = result_status
        self._result_str: str = result_string
        self._data: Any = result_data

    def is_ok(self) -> bool:
        """Ease of use status."""
        return self._status

    def is_err(self) -> bool:
        """Ease of use status."""
        return not self._status

    @property
    def result_data(self) -> Any:
        """Get result data."""
        return self._data

    @property
    def result_string(self) -> str:
        """Get result string."""
        return self._result_str


class _ClientMixin(Provider):
    """Abstract Mix-in.

    Inherited by both Synch and Async clients to ensure
    constructor consistency as well as utility functions
    """

    _RPC_MINIMAL_VERSION: int = 17

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = None
        self._rpc_api = {}
        self._schema_dict = {}
        self._rpc_version: str = None
        self._request_type = SuiRequestType.WAITFORLOCALEXECUTION

    @property
    def rpc_version(self) -> str:
        """Return the version string."""
        return self._rpc_version

    @property
    def request_type(self) -> SuiRequestType:
        """Return the transaction execution request type."""
        return self._request_type

    @request_type.setter
    def set_request_type(self, rqtype: SuiRequestType) -> None:
        """Sets the transaction execution request type."""
        self._request_type = rqtype

    @property
    def rpc_api(self) -> dict:
        """Return entire dictionary of RPC API methods."""
        return self._rpc_api

    @property
    def rpc_api_names(self) -> list[str]:
        """Return names of RPC API methods."""
        return list(self._rpc_api.keys())

    def api_exists(self, api_name: str) -> bool:
        """Check if API supported in RPC host."""
        return api_name in self._rpc_api

    def rpc_version_support(self) -> None:
        """rpc_version_support Validats minimal version supported.

        :raises RuntimeError: If RPC API version less than provided
        """
        if int(self._rpc_version.split(".")[1]) < self._RPC_MINIMAL_VERSION:
            raise RuntimeError(f"Requires minimum version '0.{self._RPC_MINIMAL_VERSION}.x found {self._rpc_version}")

    def version_at_least(self, majver: int, minver: int, bldver: int) -> bool:
        """Check if minor version is greater than or equal to."""
        tpa = packaging.version.parse(".".join([str(majver), str(minver), str(bldver)]))
        rpa = packaging.version.parse(self.rpc_version)
        if rpa >= tpa:
            return True
        return False

    def _generate_data_block(self, data_block: dict, method: str, params: list) -> dict:
        """Build the json data block for Rpc."""
        data_block["method"] = method
        data_block["params"] = params
        return data_block
