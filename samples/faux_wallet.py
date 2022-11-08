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
import os
import json

from typing import Union
from pysui.abstracts import Builder, SignatureScheme
from pysui.sui import (
    SuiClient,
    SuiConfig,
    SuiRpcResult,
    SuiBaseBuilder,
    GetObjectsOwnedByAddress,
    GetObject,
    GetRawPackage,
    GetPackage,
    GetCommittee,
    GetModuleEvents,
    GetStructEvents,
    GetObjectEvents,
    GetRecipientEvents,
    GetSenderEvents,
    GetTimeEvents,
    GetTxEvents,
    GetTotalTxCount,
    GetTx,
    TransferSui,
    TransferObject,
    Pay,
    PaySui,
    PayAllSui,
    MergeCoin,
    SplitCoin,
    MoveCall,
    Publish,
    # DryRunTransaction,
)

from pysui.sui.sui_crypto import SuiAddress

from pysui.sui.sui_types import (
    ObjectID,
    SuiNativeCoinDescriptor,
    SuiString,
    SuiNumber,
    SuiGasType,
    ObjectInfo,
    SuiNftDescriptor,
    SuiDataDescriptor,
    from_object_descriptor,
    from_object_type,
)


class SuiWallet:
    """Sui Wallet Example."""

    def __init__(self, config: SuiConfig) -> None:
        """Initialize from keystore path."""
        if os.path.exists(config.keystore_file):
            self._keypairs = {}
            self._addresses = {}
            self._address_keypair = {}
            self._client = SuiClient(config)

    @property
    def current_address(self) -> SuiAddress:
        """Get the current address."""
        return self._client.config.active_address

    def set_current_address(self, address: SuiAddress) -> SuiAddress:
        """Change up the active address."""
        if address.address in self._addresses:
            old = self._client.config.set_active_address(address)
            return old
        raise ValueError(f"Address {address.address} not recognized.")

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
        result = self.execute(GetPackage(package_id))
        # if result.is_ok():
        #     result = result.result_data
        #     if "error" in result:
        #         return SuiRpcResult(False, f"{result['error']}")
        #     return SuiRpcResult(True, None, json.dumps(result["result"], indent=2))
        return result

    def get_committee_info(self, epoch: SuiNumber) -> Union[SuiRpcResult, Exception]:
        """Get info of Sui committtee."""
        result = self.execute(GetCommittee(epoch))
        if result.is_ok():
            result = result.result_data
            if "error" in result:
                return SuiRpcResult(False, f"{result['error']}")
            return SuiRpcResult(True, None, json.dumps(result, indent=2))
        return result

    def _get_events(self, cls: SuiBaseBuilder, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get events."""
        result = self.execute(cls(**kwargs))
        if result.is_ok():
            result = result.result_data
            if "error" in result:
                return SuiRpcResult(False, f"{result['error']}")
            return SuiRpcResult(True, None, json.dumps(result, indent=2))
        return result

    def get_module_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get module events."""
        return self._get_events(GetModuleEvents, **kwargs)

    def get_struct_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get struct events."""
        return self._get_events(GetStructEvents, **kwargs)

    def get_object_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get object events."""
        return self._get_events(GetObjectEvents, **kwargs)

    def get_recipient_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get recipient events."""
        return self._get_events(GetRecipientEvents, **kwargs)

    def get_sender_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get sender events."""
        return self._get_events(GetSenderEvents, **kwargs)

    def get_time_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get time events."""
        return self._get_events(GetTimeEvents, **kwargs)

    def get_tx_events(self, **kwargs: dict) -> Union[SuiRpcResult, Exception]:
        """Get transaction events."""
        return self._get_events(GetTxEvents, **kwargs)

    def get_total_tx_count(self) -> Union[SuiRpcResult, Exception]:
        """Get total tx count."""
        return self.execute(GetTotalTxCount())

    def get_transaction(self, digest: SuiString) -> Union[SuiRpcResult, Exception]:
        """Get total tx count."""
        return self.execute(GetTx(digest))

    def get_package_object(self, package_id: ObjectID) -> Union[SuiRpcResult, Exception]:
        """Get details of Sui package."""
        result = self.execute(GetRawPackage(package_id))
        if result.is_ok():
            result = result.result_data
            if result["result"]["status"] != "Exists":
                if result["result"]["status"] == "Exists":
                    return SuiRpcResult(False, f"Package id {package_id} {result['result']['status']}")
                return SuiRpcResult(False, f"Package id {package_id} is Deleted")
            if result["result"]["details"]["data"]["dataType"] == "package":
                return SuiRpcResult(True, None, from_object_type(result["result"]["details"]))
            return SuiRpcResult(False, f"ID: {package_id} is a move object, not a package")
        return result

    def transfer_sui(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer SUI coin from one account to another."""
        kword_set = set(kwargs.keys())
        if kword_set == TransferSui.transfersui_kwords:
            return self.execute(TransferSui(**kwargs))
        missing = TransferSui.transfersui_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def transfer_object(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer SUI Object from one account to another."""
        kword_set = set(kwargs.keys())
        if kword_set == TransferObject.transferobject_kwords:
            return self.execute(TransferObject(**kwargs))
        missing = TransferObject.transferobject_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def pay_transfer(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer coin using Pay from one account to another."""
        kword_set = set(kwargs.keys())
        if kword_set == Pay.pay_kwords:
            return self.execute(Pay(**kwargs))
        missing = Pay.pay_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def pay_sui_transfer(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer coin using Pay from one account to another."""
        kword_set = set(kwargs.keys())
        if kword_set == PaySui.pay_kwords:
            return self.execute(PaySui(**kwargs))
        missing = PaySui.pay_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def pay_all_sui_transfer(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Transfer coin using Pay from one account to another."""
        kword_set = set(kwargs.keys())
        if kword_set == PayAllSui.payall_kwords:
            return self.execute(PayAllSui(**kwargs))
        missing = PayAllSui.payall_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def merge_coin(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Merge two coins together."""
        kword_set = set(kwargs.keys())
        if kword_set == MergeCoin.merge_kwords:
            return self.execute(MergeCoin(**kwargs))
        missing = MergeCoin.merge_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def split_coin(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Split coins into multiple."""
        kword_set = set(kwargs.keys())
        if kword_set == SplitCoin.split_kwords:
            return self.execute(SplitCoin(**kwargs))
        missing = SplitCoin.split_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def move_call(
        self,
        **kwargs: dict,
    ) -> SuiRpcResult:
        """Call a SUI move contract function."""
        kword_set = set(kwargs.keys())
        if kword_set == MoveCall.move_kwords:
            return self.execute(MoveCall(**kwargs))
        missing = MoveCall.move_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def publish_package(self, **kwargs: dict) -> SuiRpcResult:
        """Publish a sui package."""
        kword_set = set(kwargs.keys())
        if kword_set == Publish.publish_kwords:
            return self.execute(Publish(**kwargs))
        missing = Publish.publish_kwords - kword_set
        raise ValueError(f"Missing {missing}")

    def get_type_descriptor(self, claz: ObjectInfo, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get descriptors of claz type for address."""
        builder = GetObjectsOwnedByAddress().set_address(address if address else self.current_address)
        result = self.execute(builder)
        if result.is_ok():
            result = result.result_data
            type_descriptors = []
            # if "error" in result:
            #     raise SuiRpcApiError(result["error"])
            # for sui_objdesc in result["result"]:
            for sui_objdesc in result:
                sui_type = from_object_descriptor(sui_objdesc)
                if isinstance(sui_type, claz):
                    type_descriptors.append(sui_type)
            return SuiRpcResult(True, None, type_descriptors)
        return result

    def get_data_descriptors(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the objects descriptors."""
        return self.get_type_descriptor(SuiDataDescriptor, address)

    def get_gas_descriptors(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiNativeCoinDescriptor, address)

    def get_nft_descriptors(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas object descriptors."""
        return self.get_type_descriptor(SuiNftDescriptor, address)

    def get_object(self, identifier: ObjectID) -> Union[SuiRpcResult, Exception]:
        """Get specific object by it's id."""
        result = self.execute(GetObject().set_object(identifier))
        if result.is_ok():
            result = result.result_data
            if result["status"] != "Exists":
                return SuiRpcResult(False, f"Object {identifier} {result['status']}", None)
            return SuiRpcResult(True, None, from_object_type(result["details"]))
        return result

    def _get_objects(self, descriptor_result: SuiRpcResult):
        """Get the underlying data objects list."""
        if descriptor_result.is_ok():
            obj_types = []
            for cdesc in descriptor_result.result_data:
                result = self.execute(GetObject().set_object(cdesc.identifier))
                if result.is_ok():
                    result = result.result_data
                    if result["status"] != "Exists":
                        return SuiRpcResult(False, f"Object {cdesc.identifier} {result['status']}", None)
                    data_object = from_object_type(result["details"])
                    obj_types.append(data_object)
                else:
                    return result
            return SuiRpcResult(True, None, obj_types)
        return descriptor_result

    def get_objects(self, address: SuiAddress = None, claz: ObjectInfo = None) -> Union[SuiRpcResult, Exception]:
        """Get specific object by address/id."""
        return self._get_objects(self.get_type_descriptor(claz if claz else ObjectInfo, address))

    def data_objects(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the objects from descriptors."""
        return self._get_objects(self.get_data_descriptors(address))

    def nft_objects(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the nft objects from descriptors."""
        return self._get_objects(self.get_nft_descriptors(address))

    def gas_objects(self, address: SuiAddress = None) -> Union[SuiRpcResult, Exception]:
        """Get the gas objects."""
        return self._get_objects(self.get_gas_descriptors(address))

    def total_gas(self, gas_objects: list[SuiGasType]) -> Number:
        """Get the total gas for wallet."""
        results = 0
        for cdesc in gas_objects:
            results = results + cdesc.balance
        return results
