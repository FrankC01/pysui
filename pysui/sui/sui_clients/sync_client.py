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

"""Sui Synchronous RPC Client module."""

import logging
from typing import Any, Optional, Union
from json import JSONDecodeError
import ssl
import httpx
from deprecated.sphinx import versionchanged, versionadded, deprecated
from pysui import (
    PreExecutionResult,
    SuiRpcResult,
    handle_result,
    ObjectID,
    SuiAddress,
    SuiConfig,
)
from pysui.sui.sui_clients.common import ClientMixin
from pysui.sui.sui_constants import (
    TESTNET_FAUCET_STATUS_URLV1,
    DEVNET_FAUCET_STATUS_URLV1,
)

from pysui.sui.sui_crypto import MultiSig, SuiPublicKey
from pysui.sui.sui_types.scalars import (
    SuiInteger,
    SuiSignature,
    SuiTxBytes,
    SuiString,
)
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_txresults.single_tx import (
    FaucetGasRequest,
    ObjectReadPage,
    SuiCoinObjects,
)
from pysui.sui.sui_builders.base_builder import SuiBaseBuilder, SuiRequestType
from pysui.sui.sui_builders.get_builders import (
    GetCoinTypeBalance,
    GetCoins,
    GetMultipleObjects,
    GetPastObject,
    GetObjectsOwnedByAddress,
    GetObject,
    GetPackage,
    QueryEvents,
)
from pysui.sui.sui_builders.exec_builders import (
    DryRunTransaction,
    ExecuteTransaction,
)
from pysui.sui.sui_utils import partition

# Standard library logging setup
logger = logging.getLogger("pysui.sync_client")
if not logging.getLogger().handlers:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


class SuiClient(ClientMixin):
    """Sui Syncrhonous Client."""

    @versionchanged(version="0.28.0", reason="Added logging")
    def __init__(
        self,
        config: SuiConfig,
        request_type: SuiRequestType = SuiRequestType.WAITFORLOCALEXECUTION,
    ) -> None:
        """Client initializer."""
        super().__init__(config, request_type)
        self._client = httpx.Client(
            http2=True,
            timeout=120.0,
            verify=ssl.SSLContext(ssl.PROTOCOL_SSLv23),
        )
        self._fetch_common_descriptors()
        logger.info(f"Initialized synchronous client for {config.rpc_url}")

    @property
    def is_synchronous(self) -> bool:
        """Return whether client is syncrhonous (True) or not (False)."""
        return True

    @versionchanged(version="0.28.0", reason="Consolidated exception handling.")
    def _execute(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        # Validate builder and send request
        vres = self._validate_builder(builder)
        # print(vres)
        try:
            result = self._client.post(
                self.config.rpc_url,
                headers=builder.header,
                json=vres,
            )
            return SuiRpcResult(
                True,
                None,
                result.json(),
            )
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except (
            httpx.HTTPError,
            httpx.InvalidURL,
            httpx.CookieConflict,
        ) as hexc:
            return SuiRpcResult(
                False, f"HTTPX error: {hexc.__class__.__name__}", vars(hexc)
            )

    def execute(
        self,
        builder: SuiBaseBuilder,
        additional_signatures: SuiArray[SuiAddress] = None,
    ) -> Union[SuiRpcResult, Exception]:
        """Execute the builder construct."""
        if not builder.txn_required:
            result = self._execute(builder)
            if result.is_ok():
                if "error" in result.result_data:
                    return SuiRpcResult(False, result.result_data["error"], None)
                # print(result.result_data)
                return SuiRpcResult(
                    True,
                    None,
                    builder.handle_return(result.result_data["result"]),
                )
            return result
        return self._multi_signed_execution(builder, additional_signatures)

    def execute_no_sign(
        self, builder: SuiBaseBuilder
    ) -> Union[SuiRpcResult, Exception]:
        """Submit transaction and returns the signer and transaction bytes in the result_data as tuple."""
        if builder.txn_required:
            result = self._execute(builder)
            if result.is_ok():
                result = result.result_data
                if "error" in result:
                    return SuiRpcResult(False, result["error"]["message"], None)
                result = SuiRpcResult(
                    True,
                    None,
                    PreExecutionResult(
                        builder.authority,
                        builder.handle_return(result["result"]),
                    ),
                )
            return result
        return SuiRpcResult(
            False, "execute_no_sign is used only with transaction types"
        )

    @versionchanged(version="0.16.1", reason="Support sponsored transaction signing.")
    def execute_with_multisig(
        self,
        builder: SuiBaseBuilder,
        multi_sig: MultiSig,
        pub_keys: list[SuiPublicKey],
        signers: Optional[SuiArray[SuiAddress]] = None,
    ) -> Union[SuiRpcResult, Exception]:
        """execute_with_multisig Executes a transaction, signing with MultiSig."""
        if builder.txn_required:
            result = self.execute_no_sign(builder)
            if result.is_ok():
                tx_bytes = result.result_data.tx_bytes
                new_sig = multi_sig.sign(tx_bytes, pub_keys)
                if isinstance(new_sig, SuiSignature):
                    sig_array = [new_sig]
                    if signers:
                        sig_array.extend(
                            [kpair.new_sign_secure(tx_bytes) for kpair in signers.array]
                        )
                    exec_tx = ExecuteTransaction(
                        tx_bytes=tx_bytes,
                        signatures=SuiArray(sig_array),
                        request_type=SuiRequestType.WAITFORLOCALEXECUTION,
                    )
                    return self.execute(exec_tx)
                return SuiRpcResult(False, f"Signing error code {new_sig}")
            return result
        return self._execute(builder)

    def sign_and_submit(
        self,
        signer: SuiAddress,
        tx_bytes: SuiTxBytes,
        additional_signatures: SuiArray[SuiAddress] = None,
    ) -> Union[SuiRpcResult, Exception]:
        """sign_and_submit Signs the transaction bytes from previous submission, signs and executes.

        :param signer: Signer for transaction. Should be the same from original transaction
        :type signer: SuiAddress
        :param tx_bytes: Transaction bytes from previous submission
        :type tx_bytes: SuiTxBytes
        :param additional_signatures: Array of additional signatures to sign with, defaults to None
        :type additional_signatures: SuiArray[SuiAddress], optional
        :return: Result of execution
        :rtype: Union[SuiRpcResult, Exception]
        """
        signers_list = []
        signers_list.append(self.config.keypair_for_address(signer))
        if additional_signatures:
            for addy in additional_signatures.array:
                signers_list.append(self.config.keypair_for_address(addy))
        builder = ExecuteTransaction(
            tx_bytes=tx_bytes,
            signatures=SuiArray(
                [kpair.new_sign_secure(tx_bytes.tx_bytes) for kpair in signers_list]
            ),
            request_type=self.request_type,
        )
        result = self._execute(builder)
        if result.is_ok() and "error" not in result.result_data:
            # print(result.result_data["result"])
            result = SuiRpcResult(
                True, None, builder.handle_return(result.result_data["result"])
            )
        return result

    def dry_run(self, builder: SuiBaseBuilder) -> Union[SuiRpcResult, Exception]:
        """Submit transaction than sui_dryRunTransaction only."""
        if builder.txn_required:
            result = self.execute_no_sign(builder)
            if result.is_ok():
                result = self.execute(
                    DryRunTransaction(tx_bytes=result.result_data.tx_bytes)
                )
            return result
        return SuiRpcResult(False, "dry_run is used only with transaction types")

    def _multi_signed_execution(
        self,
        builder: SuiBaseBuilder,
        additional_signers: SuiArray[SuiAddress] = None,
    ) -> Union[SuiRpcResult, Exception]:
        """."""
        result = self.execute_no_sign(builder)
        if result.is_ok():
            exec_builder = self.sign_for_execution(
                result.result_data.tx_bytes, builder, additional_signers
            )
            result = self._execute(exec_builder)
            if result.is_ok() and "error" not in result.result_data:
                # print(result.result_data["result"])
                result = SuiRpcResult(
                    True,
                    None,
                    exec_builder.handle_return(result.result_data["result"]),
                )
            else:
                result = SuiRpcResult(False, result.result_data["error"])
        return result

    # Build and execute convenience methods

    @versionchanged(
        version="0.28.0",
        reason="Support for > RPC provider limits of coin objects for owner.",
    )
    def _get_coins_for_type(
        self,
        *,
        address: SuiAddress,
        coin_type: SuiString = SuiString("0x2::sui::SUI"),
        fetch_all: Optional[bool] = False,
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
            limit: int = result.result_data.coin_object_count
            builder = GetCoins(owner=address, coin_type=coin_type)
            if limit > self.max_gets and fetch_all:
                accumer: list = []
                gasses = handle_result(self.execute(builder))
                accumer.extend(gasses.data)
                while gasses.next_cursor:
                    builder.cursor = gasses.next_cursor
                    gasses = handle_result(self.execute(builder))
                    accumer.extend(gasses.data)
                result = SuiRpcResult(
                    True,
                    "",
                    SuiCoinObjects.from_dict({"data": accumer, "next_cursor": None}),
                )
            # if < 50 or > 50 and fetch_all false
            # legacy behavior
            else:
                result = self.execute(builder)
        return result

    @versionadded(
        version="0.26.1",
        reason="Implement closing underlying httpx transport.",
    )
    def close(self):
        """Closes the httpx transport connection.

        Does not usually need to be called but put in place as part of commingling with websocket activity.
        """
        self._client.close()
        self._transport_open = False

    @versionchanged(
        version="0.28.0",
        reason="Added fetch_all as currently limited by RPC providers results",
    )
    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
    def get_gas(
        self, address: SuiAddress = None, fetch_all: Optional[bool] = False
    ) -> SuiRpcResult:
        """get_gas Retrieves SUI gas coin objects for address.

        :param address: If None, active_address will be used, defaults to None
        :type address: SuiAddress, optional
        :param fetch_all: Flag indicating to fetch all coins, defaults to False
            Max coins are set by RPC Provider (currently 50 for Sui MystenLab providers)
        :type fetch_all: Optional[bool], optional
        :return: If successful, result contains an array of SUI gas objects found
        :rtype: SuiRpcResult
        """
        address = address or self.config.active_address
        return self._get_coins_for_type(address=address, fetch_all=fetch_all)

    @versionchanged(
        version="0.28.0",
        reason="Added fetch_all as currently limited by RPC providers results",
    )
    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
    def get_coin(
        self,
        coin_type: SuiString,
        address: SuiAddress = None,
        fetch_all: Optional[bool] = False,
    ) -> SuiRpcResult:
        """get_coin Retrieves objects of coin_type for address.

        :param coin_type: Fully qualified type names for the coin (e.g., 0x168da5bf1f48dafc111b0a488fa454aca95e0b5e::usdc::USDC)
        :type coin_type: SuiString
        :param address: If None, active_address will be used, defaults to None
        :type address: SuiAddress, optional
        :param fetch_all: Flag indicating to fetch all coins, defaults to False
            Max coins are set by RPC Provider (currently 50 for Sui MystenLab providers)
        :type fetch_all: Optional[bool], optional
        :return: If successful, result contains an array of coins objects of coin_type found
        :rtype: SuiRpcResult
        """
        address = address or self.config.active_address
        return self._get_coins_for_type(
            address=address, coin_type=coin_type, fetch_all=fetch_all
        )

    @versionchanged(
        version="0.34.0",
        reason="Added faucet check. Will fail gracefull setting SuiRpcResult",
    )
    def get_gas_from_faucet(self, for_address: SuiAddress = None) -> Any:
        """get_gas_from_faucet Gets gas from SUI faucet.

        **Note**: This is only for devnet, testnet and local usage.
        :param for_address: Address to transfer faucet gas to, defaults to None
        :type for_address: SuiAddress, optional
        :return: _description_
        :rtype: Any
        """
        for_address = for_address or self.config.active_address

        def _faucet_status(furl: str, task_id: str) -> SuiRpcResult:
            while True:
                result = self._client.get(
                    furl + task_id,
                ).json()
                if result["error"]:
                    return SuiRpcResult(False, f"Error on status for task {task_id}")
                elif result["status"]["status"] == "SUCCEEDED":
                    return SuiRpcResult(
                        True,
                        None,
                        FaucetGasRequest.from_dict(
                            {
                                "transferred_gas_objects": result["status"][
                                    "transferred_gas_objects"
                                ]["sent"]
                            }
                        ),
                    )
                elif result["status"]["status"] == "INPROGRESS":
                    pass
                else:
                    return SuiRpcResult(False, result)

        try:
            if self.config.faucet_url:
                s1 = self._client.post(
                    self.config.faucet_url,
                    headers=GetObjectsOwnedByAddress(for_address).header,
                    json={"FixedAmountRequest": {"recipient": f"{for_address}"}},
                )
                # If exhausted requests
                if s1.status_code == 429:
                    return SuiRpcResult(False, s1.reason_phrase)
                result = s1.json()
                if result["error"] is None:
                    faucet_status = (
                        DEVNET_FAUCET_STATUS_URLV1
                        if self.config.environment == "devnet"
                        else TESTNET_FAUCET_STATUS_URLV1
                    )
                    return _faucet_status(faucet_status, result["task"])
                return SuiRpcResult(False, result["error"])
            else:
                return SuiRpcResult(False, "Faucet not enabled for this configuration.")
        except JSONDecodeError as jexc:
            return SuiRpcResult(False, f"JSON Decoder Error {jexc.msg}", vars(jexc))
        except httpx.ReadTimeout as hexc:
            return SuiRpcResult(False, "HTTP read timeout error", vars(hexc))
        except TypeError as texc:
            return SuiRpcResult(False, "Type error", vars(texc))

    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
    def get_object(
        self, identifier: ObjectID, version: SuiInteger = None
    ) -> Union[SuiRpcResult, Exception]:
        """get_object Get specific object by it's identifier and version if provided.

        :param identifier: The object identifier of object to fetch
        :type identifier: ObjectID
        :param version: The objects version sequence number, defaults to None
        :type version: SuiInteger, optional
        :return: The objeect's ObjectRead data
        :rtype: Union[SuiRpcResult, Exception]
        """
        return self.execute(
            GetObject(object_id=identifier)
            if version is None
            else GetPastObject(identifier, version)
        )

    @versionchanged(
        version="0.28.0",
        reason="Added fetch_all as currently limited by RPC providers results",
    )
    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
    def get_objects(
        self,
        address: SuiAddress = None,
        fetch_all: Optional[bool] = False,
    ) -> Union[SuiRpcResult, Exception]:
        """get_objects Returns objects owned by address.

        :param address: Address to object ownership, defaults to None
            Will use active-address if None
        :type address: SuiAddress, optional
        :param fetch_all: Flag indicating to fetch all objects, defaults to False
            Max objects are set by RPC Provider (currently 50 for Sui MystenLab providers)
        :type fetch_all: Optional[bool], optional
        :return: list of owned objects
        :rtype: Union[SuiRpcResult,Exception]
        """
        builder = GetObjectsOwnedByAddress(
            address if address else self.config.active_address
        )
        result = self.execute(builder)
        if result.is_ok():
            if result.result_data.next_cursor and fetch_all:
                objects = result.result_data
                accumer: list = []
                accumer.extend(objects.data)
                while objects.next_cursor and objects.has_next_page:
                    builder.cursor = objects.next_cursor
                    objects = handle_result(self.execute(builder))
                    accumer.extend(objects.data)
                objread_page = ObjectReadPage.from_dict(
                    {
                        "data": [],
                        "has_next_page": False,
                        "next_cursor": None,
                    }
                )
                objread_page.data = accumer
                result = SuiRpcResult(True, "", objread_page)
        return result

    @versionchanged(
        version="0.29.0",
        reason="Handles large identifier list",
    )
    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
    def get_objects_for(
        self, identifiers: list[ObjectID]
    ) -> Union[SuiRpcResult, Exception]:
        """get_objects_for Get objects for the list of identifiers.

        :param identifiers: The list of ObjectID's being queried.
        :type identifiers: list
        :raises: :class:`SuiException`: if returned from `self.execute`

        :returns: A list of object data
        :rtype: SuiRpcResult
        """
        # Revert to new multiOp
        builder = GetMultipleObjects(object_ids=[])
        # Handle large list
        if len(identifiers) > self.max_gets:
            accum: list = []
            for chunk in list(partition(identifiers, self.max_gets)):
                builder.object_ids = chunk
                accum.extend(handle_result(self.execute(builder)))
            result = SuiRpcResult(True, None, accum)
        else:
            builder.object_ids = identifiers
            result = self.execute(builder)

        return result

    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
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

    @deprecated(version="0.53.0", reason="Transition to GraphQL QueryNode")
    def get_events(
        self,
        *,
        query: SuiMap,
        cursor: str = "",
        limit: int = 50,
        descending_order: bool = True,
    ) -> SuiRpcResult:
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
        return self.execute(QueryEvents(**inargs))
