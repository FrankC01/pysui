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


"""Sui RPC Result and Synch and Asynch Clients Module."""

import asyncio
import json
import base64

from json import JSONDecodeError
from typing import Any, Union
from pkg_resources import packaging

import httpx
from pysui.abstracts import RpcResult, Provider
from pysui.sui.sui_types import (
    FaucetGasRequest,
    ObjectID,
    SuiArray,
    SuiMap,
    SuiInteger,
    SuiSignature,
    SuiString,
    SuiTxBytes,
    ObjectInfo,
    SuiAddress,
)
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_builders import (
    DryRunTransaction,
    GetPastObject,
    GetRpcAPI,
    SuiBaseBuilder,
    ExecuteTransaction,
    ExecuteSerializedTransaction,
    SuiRequestType,
    GetObjectsOwnedByAddress,
    GetObject,
    GetPackage,
    GetEvents,
    GetTxs,
    Pay,
    PaySui,
    PayAllSui,
    MergeCoin,
    SplitCoin,
    SplitCoinEqually,
    TransferObject,
    TransferSui,
    MoveCall,
    Publish,
)
from pysui.sui.sui_apidesc import build_api_descriptors
from pysui.sui.sui_txn_validator import validate_api
from pysui.sui.sui_excepts import SuiRpcApiNotAvailable


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


class SuiClient(_ClientMixin):
    """Sui Syncrhonous Client."""

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = httpx.Client(http2=True)
        self._build_api_descriptors()

    def _build_api_descriptors(self):
        """Fetch RPC method descrptors."""
        builder = GetRpcAPI()
        try:
            result = self._client.post(
                self.config.rpc_url,
                headers=builder.header,
                json=self._generate_data_block(builder.data_dict, builder.method, builder.params),
            ).json()
            self._rpc_version, self._rpc_api, self._schema_dict = build_api_descriptors(result)
            self.rpc_version_support()
        except JSONDecodeError as jexc:
            raise jexc
        except httpx.ReadTimeout as hexc:
            raise hexc

    def _execute(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        # Verify we have SUI RPC API for this
        if not builder.method in self._rpc_api:
            raise SuiRpcApiNotAvailable(builder.method)
        parm_results = [y for x, y in validate_api(self._rpc_api[builder.method], builder)]
        jblock = self._generate_data_block(builder.data_dict, builder.method, parm_results)
        # jout = json.dumps(jblock, indent=2)
        # print(f"{jout}")
        try:
            return SuiRpcResult(
                True,
                None,
                self._client.post(
                    self.config.rpc_url,
                    headers=builder.header,
                    json=jblock,
                    timeout=15,
                ).json(),
            )
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except httpx.ReadTimeout as hexc:
            return SuiRpcResult(False, "HTTP read timeout error", vars(hexc))

    def execute(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        if not builder.txn_required:
            result = self._execute(builder)
            if result.is_ok():
                if "error" in result.result_data:
                    return SuiRpcResult(False, result.result_data["error"], None)
                # print(result.result_data)
                return SuiRpcResult(True, None, builder.handle_return(result.result_data["result"]))
            return result
        return self._signed_execution(builder)

    def execute_no_sign(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Submit transaction and returns the signer and transaction bytes in the result_data as tuple."""
        if builder.txn_required:
            result = self._execute(builder)
            if result.is_ok():
                result = result.result_data
                if "error" in result:
                    return SuiRpcResult(False, result["error"]["message"], None)
                result = SuiRpcResult(True, None, (builder.authority, SuiTxBytes(result["result"]["txBytes"])))
            return result
        return SuiRpcResult(False, "execute_no_sign is used only with transaction types")

    def sign_and_submit(self, signer: SuiAddress, tx_bytes: SuiTxBytes) -> Union[SuiRpcResult, Exception]:
        """sign_and_submit Signs the transaction bytes from previous submission, signs and executes.

        :param signer: Signer for transaction. Should be the same from original transaction
        :type signer: SuiAddress
        :param tx_bytes: Transaction bytes from previous submission
        :type tx_bytes: SuiTxBytes
        :return: Result from execution
        :rtype: Union[SuiRpcResult, Exception]
        """
        kpair = self.config.keypair_for_address(signer)
        if self.version_at_least(0, 18, 0):
            sig = kpair.private_key.sign(base64.b64decode(tx_bytes.tx_bytes))
            compound = [kpair.scheme.value] + list(base64.b64decode(sig.value)) + list(kpair.public_key.key_bytes)
            sig = base64.b64encode(bytearray(compound))
            builder = ExecuteSerializedTransaction(
                tx_bytes=tx_bytes,
                signature=SuiSignature(sig),
                request_type=self.request_type,
            )
        else:
            builder = ExecuteTransaction(
                tx_bytes=tx_bytes,
                sig_scheme=kpair.scheme,
                signature=kpair.private_key.sign(base64.b64decode(tx_bytes.tx_bytes)),
                pub_key=kpair.public_key,
                request_type=self.request_type,
            )
        result = self._execute(builder)
        if result.is_ok():
            if "error" in result.result_data:
                return SuiRpcResult(False, result.result_data["error"]["message"], None)
            # print(json.dumps(result.result_data["result"], indent=2))
            result = SuiRpcResult(True, None, builder.handle_return(result.result_data["result"]))
        return result

    def dry_run(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Submit transaction than sui_dryRunTransaction only."""
        if builder.txn_required:
            result = self.execute_no_sign(builder)
            if result.is_ok():
                _, tx_bytes = result.result_data
                result = self.execute(DryRunTransaction(tx_bytes=tx_bytes))
            return result
        return SuiRpcResult(False, "dry_run is used only with transaction types")

    def _signed_execution(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Subit base transaction, sign valid result and execute."""
        result = self.execute_no_sign(builder)
        if result.is_ok():
            result = self.sign_and_submit(*result.result_data)
        return result

    # Build and execute convenience methods

    def get_gas_from_faucet(self, for_address: SuiAddress = None) -> Any:
        """get_gas_from_faucet Gets gas from SUI faucet.

        **Note**: This is only for devnet, testnet and local usage.
        :param for_address: Address to transfer faucet gas to, defaults to None
        :type for_address: SuiAddress, optional
        :return: _description_
        :rtype: Any
        """
        for_address = for_address or self.config.active_address
        try:
            result = self._client.post(
                self.config.faucet_url,
                headers=GetObjectsOwnedByAddress(for_address).header,
                json={"FixedAmountRequest": {"recipient": f"{for_address}"}},
            ).json()
            if result["error"] is None:
                return SuiRpcResult(True, None, FaucetGasRequest.from_dict(result))
            return SuiRpcResult(False, result["error"])
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except httpx.ReadTimeout as hexc:
            return SuiRpcResult(False, "HTTP read timeout error", vars(hexc))
        except TypeError as texc:
            return SuiRpcResult(False, "Type error", vars(texc))

    def get_address_object_descriptors(
        self, claz: ObjectInfo = None, address: SuiAddress = None
    ) -> Union[SuiRpcResult, Exception]:
        """get_address_object_descriptors Get object descriptors for address.

        :param claz: Class type to filter result on. If None then ObjectInfo types will be returned
        :type claz: ObjectInfo
        :param address: The address of which is being queried. If None then currrent `active_address` is used
        :type address: SuiAddress
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: A list of ObjectInfo objects
        :rtype: SuiRpcResult
        """
        claz = claz if claz else ObjectInfo
        builder = GetObjectsOwnedByAddress(address if address else self.config.active_address)
        result = self.execute(builder)
        if result.is_ok():
            result = result.result_data
            type_descriptors = []
            for sui_objdesc in result:
                if isinstance(sui_objdesc, claz):
                    type_descriptors.append(sui_objdesc)
            return SuiRpcResult(True, None, type_descriptors)
        return result

    def get_object(self, identifier: ObjectID, version: SuiInteger = None) -> Union[SuiRpcResult, Exception]:
        """get_object Get specific object by it's identifier and version if provided.

        :param identifier: The object identifier of object to fetch
        :type identifier: ObjectID
        :param version: The objects version sequence number, defaults to None
        :type version: SuiInteger, optional
        :return: The objeect's ObjectRead data
        :rtype: Union[SuiRpcResult, Exception]
        """
        return self.execute(GetObject(identifier) if version is None else GetPastObject(identifier, version))

    def get_objects_for(self, identifiers: list[ObjectID]) -> Union[SuiRpcResult, Exception]:
        """get_objects_for Get objects for the list of identifiers.

        :param identifiers: The list of ObjectID's being queried.
        :type identifiers: list
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: A list of object data
        :rtype: SuiRpcResult
        """
        obj_types = []
        for identity in identifiers:
            result = self.get_object(identity)
            if result.is_ok():
                obj_types.append(result.result_data)
            else:
                return result
        return SuiRpcResult(True, None, obj_types)

    def get_package(self, package_id: ObjectID) -> Union[SuiRpcResult, Exception]:
        """get_package Get details of Sui package.

        :param package_id: The ObjectID of object being queried.
        :type package_id: ObjectID
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: The package detail data
        :rtype: SuiRpcResult
        """
        result = self.execute(GetPackage(package=package_id))
        return result

    def get_events(self, *, query: SuiMap, cursor: str, limit: int, descending_order: bool) -> SuiRpcResult:
        """get_events `sui_getEvents` API.

        :param query: The event query type map.
        :type query: SuiMap
        :param cursor: _description_
        :type cursor: str
        :param limit: _description_
        :type limit: int
        :param descending_order: _description_
        :type descending_order: bool
        :return: API call result
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(GetEvents(**inargs))

    def get_txns(self, *, query: SuiMap, cursor: str, limit: int, descending_order: bool) -> SuiRpcResult:
        """get_txns `sui_getTransactions` API.

        :param query: The transaction query type map.
        :type query: SuiMap
        :param cursor: _description_
        :type cursor: str
        :param limit: _description_
        :type limit: int
        :param descending_order: _description_
        :type descending_order: bool
        :return: API call result
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(GetTxs(**inargs))

    def pay_txn(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipients: SuiArray[SuiAddress],
        amounts: SuiArray[SuiInteger],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """pay_txn From the input Coin<T> coins, pay receipients the amounts for each.

        :param signer: **Required**: Signer address for transaction and owner of the input_coins
        :type signer: SuiAddress
        :param input_coins: **Required**: Array of 1 or more input coin Coin<T> ObjectIDs,
            including the coin for gas payment
        :type input_coins: SuiArray[ObjectID]
        :param recipients: **Required**: Array of recipient addresses of coins being paid to.
            The length of this array must be the same as amounts
        :type recipients: SuiArray[SuiAddress]
        :param amounts: **Required**: The amounts to be transferred to recipients, following the same order
        :type amounts: SuiArray[SuiInteger]
        :param gas: **Required**: Gas object ObjectID to be used to pay for this transaction
        :type gas: ObjectID
        :param gas_budget: **Required**: Amount of gas to pay for transaction (taken from first of input coins)
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(Pay(**inargs))

    def pay_sui_txn(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipients: SuiArray[SuiAddress],
        amounts: SuiArray[SuiInteger],
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """pay_sui_txn From the input Sui Gas coins, pay receipients the amounts for each.

        :param signer: **Required**: Signer address for transaction and owner of the input_coins
        :type signer: SuiAddress
        :param input_coins: **Required**: Array of 1 or more input coin Sui Gas ObjectIDs,
            including the coin for gas payment
        :type input_coins: SuiArray[ObjectID]
        :param recipients: **Required**: Array of recipient addresses of coins being paid to.
            The length of this array must be the same as amounts
        :type recipients: SuiArray[SuiAddress]
        :param amounts: **Required**: The amounts to be transferred to recipients, following the same order
        :type amounts: SuiArray[SuiInteger]
        :param gas_budget: **Required**: Amount of gas to pay for transaction (taken from first of input coins)
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(PaySui(**inargs))

    def pay_allsui_txn(
        self, *, signer: SuiAddress, input_coins: SuiArray[ObjectID], recipient: SuiAddress, gas_budget: SuiInteger
    ) -> SuiRpcResult:
        """pay_allsui_txn Send all input coins to recipient.

        :param signer: **Required**: Signer address for transaction and owner of the input_coins
        :type signer: SuiAddress
        :param input_coins: **Required**: Array of 1 or more input Sui Gas ObjectIDs
        :type input_coins: SuiArray
        :param recipient: **Required**: Recipient address of coins being paid to
        :type recipient: SuiAddress
        :param gas_budget: **Required**: Amount of gas to pay for transaction (taken from first of input coins)
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(PayAllSui(**inargs))

    def transfer_sui_txn(
        self,
        *,
        signer: SuiAddress,
        sui_object_id: ObjectID,
        gas_budget: SuiInteger,
        recipient: SuiAddress,
        amount: SuiInteger,
    ) -> SuiRpcResult:
        """transfer_sui_txn invokes `sui_transferSui` API.

        :param signer: _description_
        :type signer: SuiAddress
        :param sui_object_id: _description_
        :type sui_object_id: ObjectID
        :param gas_budget: _description_
        :type gas_budget: SuiInteger
        :param recipient: _description_
        :type recipient: SuiAddress
        :param amount: _description_
        :type amount: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(TransferSui(**inargs))

    def transfer_object_txn(
        self,
        *,
        signer: SuiAddress,
        object_id: ObjectID,
        gas: ObjectID,
        gas_budget: SuiInteger,
        recipient: SuiAddress,
    ) -> SuiRpcResult:
        """transfer_object_txn invokes `sui_transferObject` API.

        :param signer: Transaction signer and owner of object_id
        :type signer: SuiAddress
        :param object_id: The object being transferred
        :type object_id: ObjectID
        :param gas: The gas ObjectID that transaction fees will come from
        :type gas: ObjectID
        :param gas_budget: The gas budget to use in validating transaction payment
        :type gas_budget: SuiInteger
        :param recipient: The receiving party SuiAddress
        :type recipient: SuiAddress
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(TransferObject(**inargs))

    def merge_coin_txn(
        self,
        *,
        signer: SuiAddress,
        primary_coin: ObjectID,
        coin_to_merge: ObjectID,
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """merge_coin_txn invokes `sui_mergeCoin` API.

        :param signer: Transaction signer and owner of primary and coin being merged
        :type signer: SuiAddress
        :param primary_coin: the coin object to merge into, this coin will remain after the transaction
        :type primary_coin: ObjectID
        :param coin_to_merge: the coin object to be merged, this coin will be destroyed,
            the balance will be added to `primary_coin`
        :type coin_to_merge: ObjectID
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(MergeCoin(**inargs))

    def split_coin_txn(
        self,
        *,
        signer: SuiAddress,
        coin_object_id: ObjectID,
        split_amounts: SuiArray[SuiInteger],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """split_coin_txn invokes `sui_splitCoin` API.

        :param signer: Transaction signer and owner of coin being split
        :type signer: SuiAddress
        :param coin_object_id: the coin object to be spilt
        :type coin_object_id: ObjectID
        :param split_amounts: the amounts to split out from the coin
        :type split_amounts: SuiArray[SuiInteger]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(SplitCoin(**inargs))

    def split_coin_equally_txn(
        self,
        *,
        signer: SuiAddress,
        coin_object_id: ObjectID,
        split_count: SuiInteger,
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """split_coin_equally_txn invokes `sui_splitCoinEqual` API.

        :param signer: Transaction signer and owner of coin being split
        :type signer: SuiAddress
        :param coin_object_id: the coin object to be spilt
        :type coin_object_id: ObjectID
        :param split_count: The count of coins to distribute evenly from coin_object_id
        :type split_count: SuiInteger
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(SplitCoinEqually(**inargs))

    def move_call_txn(
        self,
        *,
        signer: SuiAddress,
        package_object_id: ObjectID,
        module: SuiString,
        function: SuiString,
        type_arguments: SuiArray[SuiString],
        arguments: SuiArray[SuiString],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """move_call_txn invokes `sui_moveCall` API.

        :param signer: Transaction signer
        :type signer: SuiAddress
        :param package_object_id: the Move package ID
        :type package_object_id: ObjectID
        :param module: The Sui Move module name.
        :type module: SuiString
        :param function: The Sui Move function name
        :type function: SuiString
        :param type_arguments: The type arguments, if any, of the Sui Move function
        :type type_arguments: SuiArray[SuiString]
        :param arguments: The arguments to be passed into the Sui Move function
        :type arguments: SuiArray[SuiString]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(MoveCall(**inargs))

    def publish_package_txn(
        self,
        sender: SuiAddress,
        compiled_modules: SuiArray[SuiString],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """publish_package_txn invokes `sui_publish` API.

        :param sender: the transaction signer's Sui address
        :type sender: SuiAddress
        :param compiled_modules: the compiled bytes of a sui move package
        :type compiled_modules: SuiArray[SuiString]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return self.execute(Publish(**inargs))


class SuiAsynchClient(_ClientMixin):
    """Sui Asyncrhonous Client."""

    def __init__(self, config: SuiConfig) -> None:
        """Client initializer."""
        super().__init__(config)
        self._client = httpx.AsyncClient(http2=True)
        self._rpc_api = {}
        self._schema_dict = {}
        self._build_api_descriptors()

    def _build_api_descriptors(self) -> None:
        """Fetch RPC method descrptors."""
        builder = GetRpcAPI()

        with httpx.Client(http2=True) as client:
            result = client.post(
                self.config.rpc_url,
                headers=builder.header,
                json=self._generate_data_block(builder.data_dict, builder.method, builder.params),
            )
        self._rpc_version, self._rpc_api, self._schema_dict = build_api_descriptors(result.json())
        self.rpc_version_support()

    async def _execute(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        parm_results = [y for x, y in validate_api(self._rpc_api[builder.method], builder)]
        jblock = self._generate_data_block(builder.data_dict, builder.method, parm_results)
        # jout = json.dumps(jblock, indent=2)
        # print(f"{jout}")
        try:
            result = await self._client.post(
                self.config.rpc_url,
                headers=builder.header,
                json=jblock,
            )
            return SuiRpcResult(
                True,
                None,
                result.json(),
            )
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except httpx.ReadTimeout as hexc:
            return SuiRpcResult(False, "HTTP read timeout error", vars(hexc))

    async def execute(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        if not builder.txn_required:
            result = await self._execute(builder)
            if result.is_ok():
                if "error" in result.result_data:
                    return SuiRpcResult(False, result.result_data["error"], None)
                # print(result.result_data)
                return SuiRpcResult(True, None, builder.handle_return(result.result_data["result"]))
            return result
        return await self._signed_execution(builder)

    async def execute_no_sign(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Submit transaction and returns the signer and transaction bytes in the result_data as tuple."""
        if builder.txn_required:
            result = await self._execute(builder)
            if result.is_ok():
                result = result.result_data
                if "error" in result:
                    return SuiRpcResult(False, result["error"]["message"], None)
                result = SuiRpcResult(True, None, (builder.authority, SuiTxBytes(result["result"]["txBytes"])))
            return result
        return SuiRpcResult(False, "execute_no_sign is used only with transaction types")

    async def sign_and_submit(self, signer: SuiAddress, tx_bytes: SuiTxBytes) -> Union[SuiRpcResult, Exception]:
        """sign_and_submit Signs the transaction bytes from previous submission, signs and executes.

        :param signer: Signer for transaction. Should be the same from original transaction
        :type signer: SuiAddress
        :param tx_bytes: Transaction bytes from previous submission
        :type tx_bytes: SuiTxBytes
        :return: Result from execution
        :rtype: Union[SuiRpcResult, Exception]
        """
        kpair = self.config.keypair_for_address(signer)
        kpair = self.config.keypair_for_address(signer)
        if self.version_at_least(0, 18, 0):
            sig = kpair.private_key.sign(base64.b64decode(tx_bytes.tx_bytes))
            compound = [kpair.scheme.value] + list(base64.b64decode(sig.value)) + list(kpair.public_key.key_bytes)
            sig = base64.b64encode(bytearray(compound))
            builder = ExecuteSerializedTransaction(
                tx_bytes=tx_bytes,
                signature=SuiSignature(sig),
                request_type=self.request_type,
            )
        else:
            builder = ExecuteTransaction(
                tx_bytes=tx_bytes,
                sig_scheme=kpair.scheme,
                signature=kpair.private_key.sign(base64.b64decode(tx_bytes.tx_bytes)),
                pub_key=kpair.public_key,
                request_type=self.request_type,
            )
        result = await self._execute(builder)
        if result.is_ok():
            if "error" in result.result_data:
                return SuiRpcResult(False, result.result_data["error"]["message"], None)
            # print(json.dumps(result.result_data["result"], indent=2))
            result = SuiRpcResult(True, None, builder.handle_return(result.result_data["result"]))
        return result

    async def dry_run(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Submit transaction than sui_dryRunTransaction only."""
        if builder.txn_required:
            result = await self.execute_no_sign(builder)
            if result.is_ok():
                _, tx_bytes = result.result_data
                result = await self.execute(DryRunTransaction(tx_bytes=tx_bytes))
            return result
        return SuiRpcResult(False, "dry_run is used only with transaction types")

    async def _signed_execution(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Subit base transaction, sign valid result and execute."""
        result = await self.execute_no_sign(builder)
        if result.is_ok():
            result = await self.sign_and_submit(*result.result_data)
        return result

    # Build and execute convenience methods

    async def get_gas_from_faucet(self, for_address: SuiAddress = None) -> Any:
        """get_gas_from_faucet Gets gas from SUI faucet.

        **Note**: This is only for devnet, testnet and local usage.
        :param for_address: Address to transfer faucet gas to, defaults to None
        :type for_address: SuiAddress, optional
        :return: _description_
        :rtype: Any
        """
        for_address = for_address or self.config.active_address
        try:
            result = await self._client.post(
                self.config.faucet_url,
                headers=GetObjectsOwnedByAddress(for_address).header,
                json={"FixedAmountRequest": {"recipient": f"{for_address}"}},
            )
            result = result.json()
            if result["error"] is None:
                return SuiRpcResult(True, None, FaucetGasRequest.from_dict(result))
            return SuiRpcResult(False, result["error"])
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except httpx.ReadTimeout as hexc:
            return SuiRpcResult(False, "HTTP read timeout error", vars(hexc))
        except TypeError as texc:
            return SuiRpcResult(False, "Type error", vars(texc))

    async def get_address_object_descriptors(
        self, claz: ObjectInfo = None, address: SuiAddress = None
    ) -> Union[SuiRpcResult, Exception]:
        """get_address_object_descriptors Get object descriptors for address.

        :param claz: Class type to filter result on. If None then ObjectInfo types will be returned
        :type claz: ObjectInfo
        :param address: The address of which is being queried. If None then currrent `active_address` is used
        :type address: SuiAddress
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: A list of ObjectInfo objects
        :rtype: SuiRpcResult
        """
        claz = claz if claz else ObjectInfo
        builder = GetObjectsOwnedByAddress(address if address else self.config.active_address)
        result = await self.execute(builder)
        if result.is_ok():
            result = result.result_data
            type_descriptors = []
            for sui_objdesc in result:
                if isinstance(sui_objdesc, claz):
                    type_descriptors.append(sui_objdesc)
            return SuiRpcResult(True, None, type_descriptors)
        return result

    async def get_object(self, identifier: ObjectID, version: SuiInteger = None) -> Union[SuiRpcResult, Exception]:
        """get_object Get specific object by it's identifier and version if provided.

        :param identifier: The object identifier of object to fetch
        :type identifier: ObjectID
        :param version: The objects version sequence number, defaults to None
        :type version: SuiInteger, optional
        :return: The objeect's ObjectRead data
        :rtype: Union[SuiRpcResult, Exception]
        """
        return await self.execute(GetObject(identifier) if version is None else GetPastObject(identifier, version))

    async def get_objects_for(self, identifiers: list[ObjectID]) -> Union[SuiRpcResult, Exception]:
        """get_objects_for Get objects for the list of identifiers.

        :param identifiers: The list of ObjectID's being queried.
        :type identifiers: list
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: A list of object data
        :rtype: SuiRpcResult
        """
        obj_types = []
        for identity in identifiers:
            result = await self.get_object(identity)
            if result.is_ok():
                obj_types.append(result.result_data)
            else:
                return result
        return SuiRpcResult(True, None, obj_types)

    async def get_package(self, package_id: ObjectID) -> Union[SuiRpcResult, Exception]:
        """get_package Get details of Sui package.

        :param package_id: The ObjectID of object being queried.
        :type package_id: ObjectID
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: The package detail data
        :rtype: SuiRpcResult
        """
        result = await self.execute(GetPackage(package=package_id))
        return result

    async def get_events(self, *, query: SuiMap, cursor: str, limit: int, descending_order: bool) -> SuiRpcResult:
        """get_events `sui_getEvents` API.

        :param query: The event query type map.
        :type query: SuiMap
        :param cursor: _description_
        :type cursor: str
        :param limit: _description_
        :type limit: int
        :param descending_order: _description_
        :type descending_order: bool
        :return: API call result
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(GetEvents(**inargs))

    async def get_txns(self, *, query: SuiMap, cursor: str, limit: int, descending_order: bool) -> SuiRpcResult:
        """get_txns `sui_getTransactions` API.

        :param query: The transaction query type map.
        :type query: SuiMap
        :param cursor: _description_
        :type cursor: str
        :param limit: _description_
        :type limit: int
        :param descending_order: _description_
        :type descending_order: bool
        :return: API call result
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(GetTxs(**inargs))

    async def pay_txn(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipients: SuiArray[SuiAddress],
        amounts: SuiArray[SuiInteger],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """pay_txn From the input Coin<T> coins, pay receipients the amounts for each.

        :param signer: **Required**: Signer address for transaction and owner of the input_coins
        :type signer: SuiAddress
        :param input_coins: **Required**: Array of 1 or more input coin Coin<T> ObjectIDs,
            including the coin for gas payment
        :type input_coins: SuiArray[ObjectID]
        :param recipients: **Required**: Array of recipient addresses of coins being paid to.
            The length of this array must be the same as amounts
        :type recipients: SuiArray[SuiAddress]
        :param amounts: **Required**: The amounts to be transferred to recipients, following the same order
        :type amounts: SuiArray[SuiInteger]
        :param gas: **Required**: Gas object ObjectID to be used to pay for this transaction
        :type gas: ObjectID
        :param gas_budget: **Required**: Amount of gas to pay for transaction (taken from first of input coins)
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(Pay(**inargs))

    async def pay_sui_txn(
        self,
        *,
        signer: SuiAddress,
        input_coins: SuiArray[ObjectID],
        recipients: SuiArray[SuiAddress],
        amounts: SuiArray[SuiInteger],
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """pay_sui_txn From the input Sui Gas coins, pay receipients the amounts for each.

        :param signer: **Required**: Signer address for transaction and owner of the input_coins
        :type signer: SuiAddress
        :param input_coins: **Required**: Array of 1 or more input coin Sui Gas ObjectIDs,
            including the coin for gas payment
        :type input_coins: SuiArray[ObjectID]
        :param recipients: **Required**: Array of recipient addresses of coins being paid to.
            The length of this array must be the same as amounts
        :type recipients: SuiArray[SuiAddress]
        :param amounts: **Required**: The amounts to be transferred to recipients, following the same order
        :type amounts: SuiArray[SuiInteger]
        :param gas_budget: **Required**: Amount of gas to pay for transaction (taken from first of input coins)
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(PaySui(**inargs))

    async def pay_allsui_txn(
        self, *, signer: SuiAddress, input_coins: SuiArray[ObjectID], recipient: SuiAddress, gas_budget: SuiInteger
    ) -> SuiRpcResult:
        """pay_allsui_txn Send all input coins to recipient.

        :param signer: **Required**: Signer address for transaction and owner of the input_coins
        :type signer: SuiAddress
        :param input_coins: **Required**: Array of 1 or more input Sui Gas ObjectIDs
        :type input_coins: SuiArray
        :param recipient: **Required**: Recipient address of coins being paid to
        :type recipient: SuiAddress
        :param gas_budget: **Required**: Amount of gas to pay for transaction (taken from first of input coins)
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(PayAllSui(**inargs))

    async def transfer_sui_txn(
        self,
        *,
        signer: SuiAddress,
        sui_object_id: ObjectID,
        gas_budget: SuiInteger,
        recipient: SuiAddress,
        amount: SuiInteger,
    ) -> SuiRpcResult:
        """transfer_sui_txn invokes `sui_transferSui` API.

        :param signer: _description_
        :type signer: SuiAddress
        :param sui_object_id: _description_
        :type sui_object_id: ObjectID
        :param gas_budget: _description_
        :type gas_budget: SuiInteger
        :param recipient: _description_
        :type recipient: SuiAddress
        :param amount: _description_
        :type amount: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(TransferSui(**inargs))

    async def transfer_object_txn(
        self,
        *,
        signer: SuiAddress,
        object_id: ObjectID,
        gas: ObjectID,
        gas_budget: SuiInteger,
        recipient: SuiAddress,
    ) -> SuiRpcResult:
        """transfer_object_txn invokes `sui_transferObject` API.

        :param signer: Transaction signer and owner of object_id
        :type signer: SuiAddress
        :param object_id: The object being transferred
        :type object_id: ObjectID
        :param gas: The gas ObjectID that transaction fees will come from
        :type gas: ObjectID
        :param gas_budget: The gas budget to use in validating transaction payment
        :type gas_budget: SuiInteger
        :param recipient: The receiving party SuiAddress
        :type recipient: SuiAddress
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(TransferObject(**inargs))

    async def merge_coin_txn(
        self,
        *,
        signer: SuiAddress,
        primary_coin: ObjectID,
        coin_to_merge: ObjectID,
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """merge_coin_txn invokes `sui_mergeCoin` API.

        :param signer: Transaction signer and owner of primary and coin being merged
        :type signer: SuiAddress
        :param primary_coin: the coin object to merge into, this coin will remain after the transaction
        :type primary_coin: ObjectID
        :param coin_to_merge: the coin object to be merged, this coin will be destroyed,
            the balance will be added to `primary_coin`
        :type coin_to_merge: ObjectID
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(MergeCoin(**inargs))

    async def split_coin_txn(
        self,
        *,
        signer: SuiAddress,
        coin_object_id: ObjectID,
        split_amounts: SuiArray[SuiInteger],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """split_coin_txn invokes `sui_splitCoin` API.

        :param signer: Transaction signer and owner of coin being split
        :type signer: SuiAddress
        :param coin_object_id: the coin object to be spilt
        :type coin_object_id: ObjectID
        :param split_amounts: the amounts to split out from the coin
        :type split_amounts: SuiArray[SuiInteger]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(SplitCoin(**inargs))

    async def split_coin_equally_txn(
        self,
        *,
        signer: SuiAddress,
        coin_object_id: ObjectID,
        split_count: SuiInteger,
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """split_coin_equally_txn invokes `sui_splitCoinEqual` API.

        :param signer: Transaction signer and owner of coin being split
        :type signer: SuiAddress
        :param coin_object_id: the coin object to be spilt
        :type coin_object_id: ObjectID
        :param split_count: The count of coins to distribute evenly from coin_object_id
        :type split_count: SuiInteger
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(SplitCoinEqually(**inargs))

    async def move_call_txn(
        self,
        *,
        signer: SuiAddress,
        package_object_id: ObjectID,
        module: SuiString,
        function: SuiString,
        type_arguments: SuiArray[SuiString],
        arguments: SuiArray[SuiString],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """move_call_txn invokes `sui_moveCall` API.

        :param signer: Transaction signer
        :type signer: SuiAddress
        :param package_object_id: the Move package ID
        :type package_object_id: ObjectID
        :param module: The Sui Move module name.
        :type module: SuiString
        :param function: The Sui Move function name
        :type function: SuiString
        :param type_arguments: The type arguments, if any, of the Sui Move function
        :type type_arguments: SuiArray[SuiString]
        :param arguments: The arguments to be passed into the Sui Move function
        :type arguments: SuiArray[SuiString]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(MoveCall(**inargs))

    async def publish_package_txn(
        self,
        sender: SuiAddress,
        compiled_modules: SuiArray[SuiString],
        gas: ObjectID,
        gas_budget: SuiInteger,
    ) -> SuiRpcResult:
        """publish_package_txn invokes `sui_publish` API.

        :param sender: the transaction signer's Sui address
        :type sender: SuiAddress
        :param compiled_modules: the compiled bytes of a sui move package
        :type compiled_modules: SuiArray[SuiString]
        :param gas: gas object to be used in this transaction
        :type gas: ObjectID
        :param gas_budget: the gas budget, the transaction will fail if the gas cost exceed the budget
        :type gas_budget: SuiInteger
        :return: Result of the transaction
        :rtype: SuiRpcResult
        """
        inargs: dict = locals().copy()
        inargs.pop("self")
        return await self.execute(Publish(**inargs))
