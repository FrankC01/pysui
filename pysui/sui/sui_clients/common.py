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

import os
import sys
import json
from dataclasses import dataclass
from abc import abstractmethod
from typing import Any, Optional, Union, Callable
import httpx
from deprecated.sphinx import versionchanged, versionadded
from pysui.abstracts import RpcResult, Provider
from pysui.abstracts.client_keypair import KeyPair
from pysui.sui.sui_builders.base_builder import SuiBaseBuilder, SuiRequestType
from pysui.sui.sui_builders.exec_builders import (
    _MoveCallTransactionBuilder,
    ExecuteTransaction,
)
from pysui.sui.sui_builders.get_builders import (
    GetProtocolConfig,
    GetReferenceGasPrice,
    GetRpcAPI,
)
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_apidesc import build_api_descriptors
from pysui.sui.sui_constants import PYSUI_RPC_VERSION
from pysui.sui.sui_txn_validator import validate_api
from pysui.sui.sui_excepts import (
    SuiException,
    SuiRpcApiNotAvailable,
    SuiNotComplexTransaction,
)
from pysui.sui.sui_txresults.complex_tx import TransactionBytes
from pysui.sui.sui_txresults.single_tx import ProtocolConfig
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import SuiArray
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


class ClientMixin(Provider):
    """Abstract Mix-in.

    Inherited by both Synch and Async clients to ensure
    constructor consistency as well as utility functions
    """

    _RPC_MINIMAL_VERSION: str = "1.36.0"
    _RPC_REQUIRED_VERSION: str = "1.42.0"

    @versionchanged(
        version="0.26.1",
        reason="Added bool flag indicating state of underlying transport",
    )
    @versionchanged(
        version="0.28.0",
        reason="Added ProtcolConfig pre-fetch.",
    )
    def __init__(
        self,
        config: SuiConfig,
        request_type: SuiRequestType = SuiRequestType.WAITFORLOCALEXECUTION,
    ) -> None:
        """Client initializer."""
        super().__init__(config)
        self._transport_open: bool = True
        self._client = None
        self._gas_price: int = None
        self._rpc_api: dict = {}
        self._schema_dict: dict = {}
        self._rpc_version: str = None
        self._request_type: SuiRequestType = request_type
        self._protocol: ProtocolConfig = None

    @versionchanged(
        version="0.28.0",
        reason="Renamed for semantics added fetching current protocol",
    )
    def _fetch_common_descriptors(self) -> None:
        """Fetch RPC method descrptors."""
        builder_rpc_api = GetRpcAPI()
        builder_gas_price = GetReferenceGasPrice()
        builder_protocol = GetProtocolConfig()

        with httpx.Client(http2=True) as client:
            rpc_api_result = client.post(
                self.config.rpc_url,
                headers=builder_rpc_api.header,
                json=self._generate_data_block(
                    builder_rpc_api.data_dict,
                    builder_rpc_api.method,
                    builder_rpc_api.params,
                ),
            )
            rpc_gas_result = client.post(
                self.config.rpc_url,
                headers=builder_gas_price.header,
                json=self._generate_data_block(
                    builder_gas_price.data_dict,
                    builder_gas_price.method,
                    builder_gas_price.params,
                ),
            )
            rpc_protocol_result = client.post(
                self.config.rpc_url,
                headers=builder_protocol.header,
                json=self._generate_data_block(
                    builder_protocol.data_dict,
                    builder_protocol.method,
                    [],
                ),
            )
            self._protocol = ProtocolConfig.loader(rpc_protocol_result.json()["result"])
            self._gas_price = rpc_gas_result.json()["result"]

        (
            self._rpc_version,
            self._rpc_api,
            self._schema_dict,
        ) = build_api_descriptors(rpc_api_result.json())
        self.rpc_version_support()
        os.environ[PYSUI_RPC_VERSION] = self._rpc_version

    def _generate_data_block(self, data_block: dict, method: str, params: list) -> dict:
        """Build the json data block for Rpc."""
        data_block["method"] = method
        data_block["params"] = params
        return data_block

    @versionchanged(version="0.24.0", reason="Moved from list to dict for RPC params")
    def _validate_builder(
        self, builder: SuiBaseBuilder
    ) -> Union[dict, SuiRpcApiNotAvailable]:
        """Validate SUI RPC API field alignment."""
        if not builder.method in self._rpc_api:
            raise SuiRpcApiNotAvailable(builder.method)
        parm_results = validate_api(self._rpc_api[builder.method], builder)
        # parm_results = [y for x, y in validate_api(self._rpc_api[builder.method], builder)]
        jblock = self._generate_data_block(
            builder.data_dict, builder.method, parm_results
        )
        # print(f"{json.dumps(jblock, indent=2)}")

        return jblock

    @versionadded(
        version="0.26.1",
        reason="Added to support transport state information.",
    )
    @property
    def transport_open(self) -> bool:
        """Returns true/false on state of transport."""
        return self._transport_open

    @property
    @abstractmethod
    def is_synchronous(self) -> bool:
        """Return whether client is syncrhonous (True) or not (False)."""

    @property
    def current_gas_price(self) -> int:
        """Returns session gas price."""
        return int(self._gas_price)

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

    @versionadded(
        version="0.26.1", reason="Support closing underlying client transport."
    )
    @abstractmethod
    def close(self) -> None:
        """Abstract method to close transport."""

    def rpc_version_support(self) -> None:
        """rpc_version_support Validates minimal version supported.

        :raises RuntimeError: If RPC API version less than minimal support
        """
        rpa = [int(x) for x in self.rpc_version.split(".")]
        mpa = [int(x) for x in self._RPC_MINIMAL_VERSION.split(".")]
        ipa = [int(x) for x in self._RPC_REQUIRED_VERSION.split(".")]
        # If the running version is greater than most recent supported by pysui
        if rpa >= ipa:
            pass
        # If the running version is less than the minimum supported by pysui
        elif rpa < mpa:
            raise RuntimeError(
                f"Requires minimum version '{self._RPC_MINIMAL_VERSION} found {self._rpc_version}"
            )
        # If the running version is less than the most recent supported by pysui
        elif rpa < ipa:
            print(
                f"Host RPC version is {self.rpc_version} and is backward compatible with code built for {self._RPC_REQUIRED_VERSION}."
            )

    def version_at_least(self, majver: int, minver: int, bldver: int) -> bool:
        """Check if minor version is greater than or equal to."""
        tpa = [majver, minver, bldver]
        rpa = [int(x) for x in self.rpc_version.split(".")]
        if rpa >= tpa:
            return True
        return False

    def sign_for_execution(
        self,
        tx_bytes: SuiTxBytes,
        builder: _MoveCallTransactionBuilder,
        signers: Optional[SuiArray[SuiAddress]] = None,
    ) -> Union[ExecuteTransaction, SuiException, ValueError]:
        """sign_for_execution Sets up a TransactioBlock Execution builder.

        :param tx_bytes: Transaction bytes from transaction method submission.
        :type tx_bytes: SuiTxBytes
        :param builder: The builder reflecting the transaction method called.
        :type builder: _MoveCallTransactionBuilder
        :param signers: Additional signers, defaults to None
        :type signers: Optional[SuiArray[SuiAddress]], optional
        :raises SuiNotComplexTransaction: If builder is simple type
        :return: An ExecuteTransaction builder
        :rtype: Union[ExecuteTransaction, SuiException, ValueError]
        """
        if not builder.txn_required:
            raise SuiNotComplexTransaction(builder.__class__.__name__)
        # Gather keypairs for signing
        signers_list: list[KeyPair] = []
        base_signer = builder.authority
        signers_list.append(self.config.keypair_for_address(base_signer))
        if signers:
            for other_address in signers.array:
                signers_list.append(self.config.keypair_for_address(other_address))
        # Iterate and return signatures list
        total_signed = SuiArray(
            [kpair.new_sign_secure(tx_bytes.tx_bytes) for kpair in signers_list]
        )
        return ExecuteTransaction(
            tx_bytes=tx_bytes,
            signatures=total_signed,
            request_type=self.request_type,
        )

    # Protocol properties
    @versionadded(version="0.28.0", reason="Connection specific ProtcolConfig.")
    @property
    def protocol(self) -> ProtocolConfig:
        """Return the raw protocol config in place for the connection."""
        return self._protocol

    @versionadded(version="0.29.0", reason="Added constraint for RPC sfetches.")
    @property
    def max_gets(self) -> int:
        """Return maximum getXXX values (either cursored types or multiget types)."""
        return 50
