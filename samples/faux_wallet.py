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


"""Sui Wallet Facade."""


from numbers import Number
import json

from typing import Union
from pysui.abstracts import Builder, SignatureScheme
from pysui.sui import (
    SuiClient,
    SuiConfig,
    SuiRpcResult,
    GetCommittee,
    GetTotalTxCount,
    GetTx,
    # DryRunTransaction,
)

from pysui.sui.sui_crypto import SuiAddress

from pysui.sui.sui_types import (
    ObjectID,
    SuiGasDescriptor,
    SuiString,
    SuiInteger,
    SuiCoin,
    ObjectInfo,
    MoveDataDescriptor,
)


class SuiWallet:
    """Sui Wallet Example."""

    def __init__(self, config: SuiConfig) -> None:
        """Initialize from keystore path."""
        self._client = SuiClient(config)

    @property
    def current_address(self) -> SuiAddress:
        """Get the current address."""
        return self._client.config.active_address

    @property
    def addresses(self) -> list[str]:
        """Get all the addresses."""
        return self._client.config.addresses

    def execute(self, builder: Builder, dry_run: bool = False) -> SuiRpcResult:
        """Execute the builder."""
        return self._client.execute(builder, dry_run)

    def get_rpc_api_names(self) -> list[str]:
        """Fetch RCP API method names."""
        return self._client.rpc_api_names

    def get_rpc_api(self) -> dict:
        """Fetch RCP API descriptors."""
        return self._client.rpc_api

    def api_exists(self, api_name: str) -> bool:
        """Check if API supported in RPC host."""
        return self._client.api_exists(api_name)

    def create_new_keypair_and_address(self, sigscheme: SignatureScheme) -> str:
        """Create new keypair and address."""
        return self._client.config.create_new_keypair_and_address(sigscheme)

    def get_package(self, package_id: ObjectID) -> Union[SuiRpcResult, Exception]:
        """Get details of Sui package."""
        return self._client.get_package(package_id)

    def get_committee_info(self, epoch: SuiInteger) -> Union[SuiRpcResult, Exception]:
        """Get info of Sui committtee."""
        return self.execute(GetCommittee(epoch))

    def get_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get module events."""
        return self._client.get_events(**kwargs)

    def get_total_tx_count(self) -> Union[SuiRpcResult, Exception]:
        """Get total tx count."""
        return self.execute(GetTotalTxCount())

    def get_transaction(self, digest: SuiString) -> Union[SuiRpcResult, Exception]:
        """Get total tx count."""
        return self.execute(GetTx(digest))

    def get_txns(self, **kwargs) -> SuiRpcResult:
        """Get transaction information from query."""
        return self._client.get_txns(**kwargs)

    def transfer_sui(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer SUI coin from one account to another."""
        return self._client.transfer_sui_txn(**kwargs)

    def transfer_object(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer SUI Object from one account to another."""
        return self._client.transfer_object_txn(**kwargs)

    def pay_transfer(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer any coin type using Pay from one account to another."""
        return self._client.pay_txn(**kwargs)

    def pay_sui_transfer(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer SUI coin using Pay from one account to another."""
        return self._client.pay_sui_txn(**kwargs)

    def pay_all_sui_transfer(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer SUI coin using Pay from one account to another."""
        return self._client.pay_allsui_txn(**kwargs)

    def merge_coin(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Merge two coins together."""
        return self._client.merge_coin_txn(**kwargs)

    def split_coin(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Split coins into multiple."""
        return self._client.split_coin_txn(**kwargs)

    def move_call(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Call a SUI move contract function."""
        return self._client.move_call_txn(**kwargs)

    def publish_package(self, **kwargs: dict) -> SuiRpcResult:
        """Publish a sui package."""
        return self._client.publish_package_txn(**kwargs)

    def get_type_descriptor(self, claz: ObjectInfo, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get descriptors of claz type for address."""
        return self._client.get_address_object_descriptors(claz, address)

    def get_data_descriptors(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the objects descriptors."""
        return self.get_type_descriptor(MoveDataDescriptor, address)

    def get_gas_descriptors(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiGasDescriptor, address)

    def get_object(self, identifier: ObjectID) -> Union[SuiRpcResult, Exception]:
        """Get specific object by it's id."""
        return self._client.get_object(identifier)

    def _get_objects(self, descriptor_result: SuiRpcResult) -> Union[SuiRpcResult, Exception]:
        """Get the underlying data objects list."""
        if descriptor_result.is_ok():
            identities = [ids.identifier for ids in descriptor_result.result_data]
            return self._client.get_objects_for(identities)

    def get_objects(self, address: SuiAddress = None, claz: ObjectInfo = None) -> Union[SuiRpcResult, Exception]:
        """Get specific object by address/id."""
        return self._get_objects(self.get_type_descriptor(claz if claz else ObjectInfo, address))

    def data_objects(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the objects from descriptors."""
        return self._get_objects(self.get_data_descriptors(address))

    def gas_objects(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas objects."""
        return self._get_objects(self.get_gas_descriptors(address))

    def total_gas(self, coin_objects: list[SuiCoin]) -> Number:
        """Get the total of balances for SuiCoin type."""
        results = 0
        for cdesc in coin_objects:
            results = results + cdesc.balance
        return results
