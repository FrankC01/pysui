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
# pylint: disable=too-many-instance-attributes, too-many-public-methods, line-too-long

"""Sui Synchronous RPC Client module."""

from typing import Any, Union
from json import JSONDecodeError
import httpx
from pysui.sui.sui_clients.common import _ClientMixin, SuiRpcResult
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiTxBytes, SuiString
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_txresults.single_tx import FaucetGasRequest, ObjectInfo
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_builders.base_builder import SuiBaseBuilder, SuiRequestType
from pysui.sui.sui_builders.get_builders import (
    GetCoinTypeBalance,
    GetCoins,
    GetPastObject,
    GetObjectsOwnedByAddress,
    GetObject,
    GetPackage,
    GetEvents,
    GetTxs,
)
from pysui.sui.sui_builders.exec_builders import (
    DryRunTransaction,
    ExecuteTransaction,
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


class SuiClient(_ClientMixin):
    """Sui Syncrhonous Client."""

    def __init__(self, config: SuiConfig, request_type: SuiRequestType = SuiRequestType.WAITFORLOCALEXECUTION) -> None:
        """Client initializer."""
        super().__init__(config, request_type)
        self._client = httpx.Client(http2=True, timeout=30.0)
        self._build_api_descriptors()

    @property
    def is_synchronous(self) -> bool:
        """Return whether client is syncrhonous (True) or not (False)."""
        return True

    def _execute(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        # Validate builder and send request
        try:
            result = self._client.post(
                self.config.rpc_url,
                headers=builder.header,
                json=self._validate_builder(builder),
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
        _recovery_id = 0
        kpair = self.config.keypair_for_address(signer)

        def _inner_sign(recovery_id: int) -> SuiRpcResult:
            builder = ExecuteTransaction(
                tx_bytes=tx_bytes,
                signature=kpair.new_sign_secure(tx_bytes.tx_bytes, recovery_id),
                request_type=self.request_type,
            )
            result = self._execute(builder)
            if result.is_ok() and "error" not in result.result_data:
                # print(result.result_data["result"])
                result = SuiRpcResult(True, None, builder.handle_return(result.result_data["result"]))
            elif "error" in result.result_data:
                msg = result.result_data["error"]["message"]
                if msg == _ClientMixin._SIGNATURE_ERROR and recovery_id > 0:
                    result = SuiRpcResult(False, msg)
                elif msg == _ClientMixin._SIGNATURE_ERROR and recovery_id < 1:
                    result = _inner_sign(recovery_id + 1)
                else:
                    result = SuiRpcResult(False, msg)
            return result

        return _inner_sign(_recovery_id)

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

    def _get_coins_for_type(
        self, address: SuiAddress, coin_type: SuiString = SuiString("0x2::sui::SUI")
    ) -> SuiRpcResult:
        """_get_coins_for_type Returns all the coins of type for an address.

        :param address: The address to fetch coins of coin_type for
        :type address: SuiAddress
        :param coin_type: Fully qualified type names for the coin (e.g., 0x168da5bf1f48dafc111b0a488fa454aca95e0b5e::usdc::USDC),
        defaults to SuiString("0x2::sui::SUI")
        :type coin_type: SuiString, optional
        :return: If successful, result contains an array of coins objects of coin_type found
        :rtype: SuiRpcResult
        """
        result = self.execute(GetCoinTypeBalance(owner=address, coin_type=coin_type))
        if result.is_ok():
            limit = SuiInteger(result.result_data.coin_object_count)
            result = self.execute(GetCoins(owner=address, coin_type=coin_type, limit=limit))
        return result

    def get_gas(self, address: SuiAddress = None) -> SuiRpcResult:
        """get_gas Retrieves SUI gas coin objects for address.

        :param address: If None, active_address will be used, defaults to None
        :type address: SuiAddress, optional
        :return: If successful, result contains an array of SUI gas objects found
        :rtype: SuiRpcResult
        """
        address = address or self.config.active_address
        return self._get_coins_for_type(address)

    def get_coin(
        self,
        coin_type: SuiString,
        address: SuiAddress = None,
    ) -> SuiRpcResult:
        """get_coin Retrieves objects of coin_type for address.

        :param coin_type: Fully qualified type names for the coin (e.g., 0x168da5bf1f48dafc111b0a488fa454aca95e0b5e::usdc::USDC)
        :type coin_type: SuiString
        :param address: If None, active_address will be used, defaults to None
        :type address: SuiAddress, optional
        :return: If successful, result contains an array of coins objects of coin_type found
        :rtype: SuiRpcResult
        """
        address = address or self.config.active_address
        return self._get_coins_for_type(address, coin_type)

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
