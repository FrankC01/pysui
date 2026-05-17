#    Copyright Frank V. Castellucci
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

import sys
from dataclasses import dataclass
from typing import Any
from pysui.abstracts import RpcResult
from pysui.sui.sui_txresults.complex_tx import TransactionBytes
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.scalars import SuiTxBytes


class SuiRpcResult(RpcResult):
    """Sui RpcResult.

    Captures information returned from simple and complex RPC API calls
    """

    def __init__(
        self, result_status: bool, result_string: str, result_data: Any = None
    ) -> None:
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


@dataclass
class PreExecutionResult:
    """Results of pre-execution transaction submission."""

    authority_address: SuiAddress
    pre_transaction_result: TransactionBytes

    @property
    def tx_bytes(self) -> SuiTxBytes:
        """tx_bytes return the tx_byte string as a SuiTxBytes.

        :return: tx_bytes in TransactionBytes as SuiTxBytes
        :rtype: SuiSignature
        """
        return SuiTxBytes(self.pre_transaction_result.tx_bytes)


def pysui_default_handler(result: SuiRpcResult) -> Any:
    """pysui_default_handler Out of box SuiRpcResult error handler.

    Exits the application!!!

    :param result: The result from calling Sui RPC API
    :type result: SuiRpcResult
    :return: The data from call if valid
    :rtype: Any
    """
    if result and result.is_ok():
        return result.result_data
    print(f"Error in result: {result.result_string}")
    sys.exit(-1)


def handle_result(from_cmd: SuiRpcResult, handler=pysui_default_handler) -> Any:
    """handle_result Returns value from invoking handler.

    :param from_cmd: The result from calling Sui RPC API
    :type from_cmd: SuiRpcResult
    :param handler: The result handler function, defaults to pysui_default_handler
    :type handler: Function, optional
    :return: Result from handler
    :rtype: Any
    """
    assert callable(handler), "Invalid 'handler' argument"
    assert isinstance(from_cmd, SuiRpcResult), "Invalid 'from_command' return"
    return handler(from_cmd)
