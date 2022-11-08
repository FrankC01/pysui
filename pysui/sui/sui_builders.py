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


"""SUI Builders for RPC."""

from abc import abstractmethod
from enum import IntEnum
from typing import Type, Union
from ..abstracts import Builder, PublicKey, SignatureScheme
from .sui_types import (
    MovePackage,
    ObjectInfo,
    ObjectID,
    SuiString,
    SuiNumber,
    SuiTxBytes,
    SuiSignature,
    SuiArray,
    SuiMap,
    SuiAddress,
    SuiBaseType,
    TxEffectResult,
)


class SuiRequestType(IntEnum):
    """Key encoding scheme variations."""

    IMMEDIATERETURN = 0
    WAITFORTXCERT = 1
    WAITFOREFFECTSCERT = 2
    WAITFORLOCALEXECUTION = 3

    def as_str(self) -> str:
        """Get scheme as string."""
        if self is SuiRequestType.IMMEDIATERETURN:
            return "ImmediateReturn"
        if self is SuiRequestType.WAITFORTXCERT:
            return "WaitForTxCert"
        if self is SuiRequestType.WAITFOREFFECTSCERT:
            return "WaitForEffectsCert"
        if self is SuiRequestType.WAITFORLOCALEXECUTION:
            return "WaitForLocalExecution"
        raise TypeError(f"Unknown request type {self.name}")

    @property
    def request_type(self) -> str:
        """Satisfy transaction verification."""
        return self.as_str()


class SuiBaseBuilder(Builder):
    """
    Base Sui API Builder Class.

    Subclasses must identify public vars that are
    required by Sui RPC API.
    """

    def __init__(
        self, method: str, txn_required: bool, handler_cls: Type[SuiBaseType] = None, handler_func: str = None
    ) -> None:
        """Initialize Builder."""
        super().__init__()
        self._method = method
        self._txn_required = txn_required
        # Experimental
        self._handler_cls: Type[SuiBaseType] = handler_cls
        self._handler_func: str = handler_func

    def _pull_vars(self) -> list[SuiBaseType]:
        """Filter out private/protected var elements."""
        var_map = vars(self)
        return [val for key, val in var_map.items() if key[0] != "_"]

    @abstractmethod
    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()

    @property
    def params(self) -> list[SuiBaseType]:
        """Return parameters list."""
        return self._collect_parameters()

    @property
    def header(self) -> dict:
        """Return copy of the current header."""
        return self._header

    @property
    def method(self) -> str:
        """Return method."""
        return self._method

    @property
    def txn_required(self) -> bool:
        """Get transaction required flag."""
        return self._txn_required

    # Experimental
    def _has_return_handler_cls(self) -> bool:
        """Query presence of return handler."""
        return self._handler_cls is not None

    def _has_return_handler_func(self) -> bool:
        """Query presence of return handler."""
        return self._handler_func is not None

    # Experimental
    def handle_return(self, indata: dict) -> Union[dict, SuiBaseType]:
        """Handle the expected return."""
        if self._handler_cls and self._handler_func:
            return getattr(self._handler_cls, self._handler_func)(indata)
        if self._handler_cls and self._handler_func is None:
            return self._handler_cls(indata)
        if self._handler_cls is None and self._handler_func:
            return self._handler_func(indata)
        return indata


class _NativeTransactionBuilder(SuiBaseBuilder):
    """Builders for simple single parameter transactions."""

    def __init__(self, method: str, handler_cls: Type[SuiBaseType] = None, handler_func: str = None) -> None:
        """Initialize builder."""
        super().__init__(method, False, handler_cls, handler_func)


class GetObjectsOwnedByAddress(_NativeTransactionBuilder):
    """Fetch Objects for Address."""

    def __init__(self, address: SuiAddress = None) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObjectsOwnedByAddress")
        self.address: SuiAddress = address

    def set_address(self, address: SuiAddress) -> "GetObjectsOwnedByAddress":
        """Set the address to fetch objects owned by."""
        self.address = address
        return self

    def _collect_parameters(self) -> list[SuiAddress]:
        """Collect the call parameters."""
        return [self.address]


class GetObjectsOwnedByObject(_NativeTransactionBuilder):
    """Fetch Objects for Address."""

    def __init__(self, sui_object: ObjectInfo = None) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObjectsOwnedByObject")
        self.object_id = sui_object

    def set_object(self, sui_object: ObjectInfo) -> "GetObjectsOwnedByObject":
        """Set the object to fetch objects owned by."""
        self.object_id: ObjectInfo = sui_object
        return self

    def _collect_parameters(self) -> list[ObjectInfo]:
        """Collect the call parameters."""
        return [self.object_id]


class GetObject(_NativeTransactionBuilder):
    """Fetch Object detail for Object ID."""

    def __init__(self, sui_object: ObjectID = None) -> None:
        """Initialize Builder."""
        super().__init__("sui_getObject")
        self.object_id: ObjectID = sui_object

    def set_object(self, sui_object: ObjectID) -> "GetObjectsOwnedByObject":
        """Set the object to fetch objects owned by."""
        self.object_id: ObjectID = sui_object
        return self

    def _collect_parameters(self) -> list[ObjectInfo]:
        """Collect the call parameters."""
        return [self.object_id]


class GetRawPackage(_NativeTransactionBuilder):
    """Fetch package onject information."""

    def __init__(self, package_id: ObjectID = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getObject")
        self.object_id = package_id

    def set_object_id(self, package_id: ObjectID) -> "GetRawPackage":
        """Set the package object id to retrieve."""
        self.object_id = package_id
        return self

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.object_id]


class GetPackage(_NativeTransactionBuilder):
    """Fetch package definitions including modules and functions."""

    def __init__(self, package: ObjectID = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getNormalizedMoveModulesByPackage", handler_cls=MovePackage, handler_func="ingest_data")
        self.package: ObjectID = package

    def set_package(self, package: ObjectID) -> "GetPackage":
        """Set the package to retrieve."""
        self.package: ObjectID = package
        return self

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package]


class GetRpcAPI(_NativeTransactionBuilder):
    """Fetch the RPC API available for endpoint."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("rpc.discover")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return []


class GetCommittee(_NativeTransactionBuilder):
    """Fetch Committee Info."""

    def __init__(self, epoch: SuiNumber = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getCommitteeInfo")
        self.epoch: SuiNumber = epoch if epoch else SuiNumber(None)

    def set_epoch(self, epoch: SuiNumber) -> "GetCommittee":
        """Set epoch."""
        self.epoch = epoch
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.epoch]


class GetModuleEvents(_NativeTransactionBuilder):
    """Fetch Module Events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsByModule")
        self.package: ObjectID = None
        self.module: SuiString = None
        self.count: SuiNumber = None
        self.start_time: SuiNumber = None
        self.end_time: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "package":
                    self.package: ObjectID = value
                case "module":
                    self.module: SuiString = value if isinstance(value, SuiString) else SuiString(value)
                case "count":
                    self.count: SuiNumber = value
                case "start_time":
                    self.start_time: SuiNumber = value
                case "end_time":
                    self.end_time: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetStructEvents(_NativeTransactionBuilder):
    """Fetch Named Struct Events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsByMoveEventStructName")
        self.move_event_struct_name: SuiString = None
        self.count: SuiNumber = None
        self.start_time: SuiNumber = None
        self.end_time: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "move_event_struct_name":
                    self.move_event_struct_name: SuiString = value if isinstance(value, SuiString) else SuiString(value)
                case "count":
                    self.count: SuiNumber = value
                case "start_time":
                    self.start_time: SuiNumber = value
                case "end_time":
                    self.end_time: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetObjectEvents(_NativeTransactionBuilder):
    """Fetch Object Events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsByObject")
        self.object: ObjectID = None
        self.count: SuiNumber = None
        self.start_time: SuiNumber = None
        self.end_time: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "object":
                    self.object: ObjectID = value
                case "count":
                    self.count: SuiNumber = value
                case "start_time":
                    self.start_time: SuiNumber = value
                case "end_time":
                    self.end_time: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetRecipientEvents(_NativeTransactionBuilder):
    """Fetch Recipient Events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsByRecipient")
        self.recipient: SuiMap = None
        self.count: SuiNumber = None
        self.start_time: SuiNumber = None
        self.end_time: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "recipient":
                    self.recipient: SuiMap = SuiMap("AddressOwner", value)
                case "count":
                    self.count: SuiNumber = value
                case "start_time":
                    self.start_time: SuiNumber = value
                case "end_time":
                    self.end_time: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetSenderEvents(_NativeTransactionBuilder):
    """Fetch Sender Events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsBySender")
        self.sender: SuiAddress = None
        self.count: SuiNumber = None
        self.start_time: SuiNumber = None
        self.end_time: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "sender":
                    self.sender: SuiAddress = value
                case "count":
                    self.count: SuiNumber = value
                case "start_time":
                    self.start_time: SuiNumber = value
                case "end_time":
                    self.end_time: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTimeEvents(_NativeTransactionBuilder):
    """Fetch Time events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsByTimeRange")
        self.count: SuiNumber = None
        self.start_time: SuiNumber = None
        self.end_time: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "count":
                    self.count: SuiNumber = value
                case "start_time":
                    self.start_time: SuiNumber = value
                case "end_time":
                    self.end_time: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTxEvents(_NativeTransactionBuilder):
    """Fetch Transaction events Info."""

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEventsByTransaction")
        self.digest: SuiString = None
        self.count: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "digest":
                    self.digest: SuiString = value if isinstance(value, SuiString) else SuiString(value)
                case "count":
                    self.count: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTotalTxCount(_NativeTransactionBuilder):
    """Return the total number of transactions known to the server."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_getTotalTransactionNumber")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTx(_NativeTransactionBuilder):
    """Return information about a specific transaction."""

    def __init__(self, digest: SuiString = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getTransaction")
        self.digest: SuiString = digest if isinstance(digest, SuiString) else SuiString(digest)

    def set_digest(self, digest: SuiString) -> "GetTx":
        """Set digest var."""
        self.digest = digest if isinstance(digest, SuiString) else SuiString(digest)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.digest]


class ExecuteTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_executeTransaction", handler_cls=TxEffectResult, handler_func="from_dict")
        self.tx_bytes: SuiTxBytes = None
        self.sig_scheme: SignatureScheme = None
        self.signature: SuiSignature = None
        self.pub_key: PublicKey = None
        self.request_type: SuiRequestType = None

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes: SuiTxBytes = tbyteb64
        return self

    def set_sig_scheme(self, sig: SignatureScheme) -> "ExecuteTransaction":
        """Set the transaction base64 string."""
        self.sig_scheme: SignatureScheme = sig
        return self

    def set_signature(self, sigb64: SuiSignature) -> "ExecuteTransaction":
        """Set the signed transaction base64 string."""
        self.signature: SuiSignature = sigb64
        return self

    def set_pub_key(self, pubkey: PublicKey) -> "ExecuteTransaction":
        """Set the public key base64 string."""
        self.pub_key: PublicKey = pubkey
        return self

    def set_request_type(self, rtype: SuiRequestType) -> "ExecuteTransaction":
        """Set the request type for execution."""
        self.request_type: SuiRequestType = rtype
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class DryRunTransaction(_NativeTransactionBuilder):
    """Dry run a signed transaction to Sui."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_dryRunTransaction")
        self.tx_bytes: SuiTxBytes = None
        self.sig_scheme: SignatureScheme = None
        self.signature: SuiSignature = None
        self.pub_key: PublicKey = None

    def set_tx_bytes(self, tbyteb64: SuiTxBytes) -> "DryRunTransaction":
        """Set the transaction base64 string."""
        self.tx_bytes: SuiTxBytes = tbyteb64
        return self

    def set_sig_scheme(self, sig: SignatureScheme) -> "DryRunTransaction":
        """Set the transaction base64 string."""
        self.sig_scheme: SignatureScheme = sig
        return self

    def set_signature(self, sigb64: SuiSignature) -> "DryRunTransaction":
        """Set the signed transaction base64 string."""
        self.signature: SuiSignature = sigb64
        return self

    def set_pub_key(self, pubkey: PublicKey) -> "DryRunTransaction":
        """Set the public key base64 string."""
        self.pub_key: PublicKey = pubkey
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class _MoveCallTransactionBuilder(SuiBaseBuilder):
    """Builders that must be processed, signed then executed."""

    def __init__(self, method: str) -> None:
        """Initialize builder."""
        super().__init__(method, True)

    @property
    def authority(self) -> SuiAddress:
        """Fetch the authority."""
        if hasattr(self, "signer"):
            return getattr(self, "signer")
        if hasattr(self, "sender"):
            return getattr(self, "sender")
        raise ValueError(f"Object {self.__class__.__name__} has no authority property set")


class TransferObject(_MoveCallTransactionBuilder):
    """Transfers an object to another object owner."""

    transferobject_kwords: set[str] = {"signer", "object_id", "gas", "gas_budget", "recipient"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_transferObject")
        self.signer: SuiAddress = None
        self.object_id: ObjectID = None
        self.gas: ObjectID = None
        self.gas_budget: SuiNumber = None
        self.recipient: SuiAddress = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "object_id":
                    self.object_id: ObjectID = value
                case "gas":
                    self.gas: ObjectID = value
                case "gas_budget":
                    self.gas_budget = value
                case "recipient":
                    self.recipient = value
                case _:
                    raise ValueError(f"Unknown TransferObject bulder type {key}")

    def set_object_id(self, obj: ObjectID) -> "TransferObject":
        """Set the object to transfer."""
        self.object_id: ObjectID = obj
        return self

    def set_signer(self, address: SuiAddress) -> "TransferObject":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas(self, obj: ObjectID) -> "TransferObject":
        """Set sui object gas object."""
        self.gas: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "TransferObject":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_recipient(self, obj: SuiAddress) -> "TransferObject":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class TransferSui(_MoveCallTransactionBuilder):
    """Transfers Sui coin from one recipient to the other."""

    transfersui_kwords: set[str] = {"signer", "sui_object_id", "gas_budget", "recipient", "amount"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_transferSui")
        self.signer: SuiAddress = None
        self.sui_object_id: ObjectID = None
        self.gas_budget: SuiNumber = None
        self.recipient: SuiAddress = None
        self.amount: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer = value
                case "sui_object_id":
                    self.sui_object_id = value
                case "gas_budget":
                    self.gas_budget = value
                case "recipient":
                    self.recipient = value
                case "amount":
                    self.amount = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "TransferSui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_sui_object_id(self, obj: ObjectID) -> "TransferSui":
        """Set sui object gas object."""
        self.sui_object_id: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "TransferSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_recipient(self, obj: SuiAddress) -> "TransferSui":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def set_amount(self, obj: SuiNumber) -> "TransferSui":
        """Set the amount to transfer to recipient."""
        self.amount: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class Pay(_MoveCallTransactionBuilder):
    """Transfer, split and merge coins of any type (SUI coin 0x2::sui::SUI or otherwise)."""

    pay_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas", "gas_budget"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_pay")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiNumber] = None
        self.gas: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "input_coins":
                    self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](value)
                case "recipients":
                    self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](value)
                case "amounts":
                    self.amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](value)
                case "gas":
                    self.gas: ObjectID = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown Pay bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "Pay":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "Pay":
        """Set sui object gas object."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipients(self, obj: list[SuiAddress]) -> "Pay":
        """Set the addresses for the receivers."""
        self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](obj)
        return self

    def set_amounts(self, obj: list[SuiNumber]) -> "Pay":
        """Set the amount(s) to transfer to recipient."""
        self.amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](obj)
        return self

    def set_gas(self, obj: ObjectID) -> "Pay":
        """Set sui object gas object for paying transaction."""
        self.gas: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "Pay":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class PaySui(_MoveCallTransactionBuilder):
    """Transfer, split and merge SUI coins (0x2::sui::SUI) only."""

    pay_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas_budget"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_paySui")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiNumber] = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "input_coins":
                    self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](value)
                case "recipients":
                    self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](value)
                case "amounts":
                    self.amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](value)
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "PaySui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "PaySui":
        """Set sui object gas object."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipients(self, obj: list[SuiAddress]) -> "PaySui":
        """Set the addresses for the receivers."""
        self.recipients: SuiArray[SuiAddress] = SuiArray[SuiAddress](obj)
        return self

    def set_amounts(self, obj: list[SuiNumber]) -> "PaySui":
        """Set the amount(s) to transfer to recipient."""
        self.amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](obj)
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "PaySui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class PayAllSui(_MoveCallTransactionBuilder):
    """Transfer all coins of SUI coin type (0x2::sui::SUI) to a single recipient."""

    payall_kwords: set[str] = {"signer", "input_coins", "recipient", "gas_budget"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_payAllSui")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipient: SuiAddress = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "input_coins":
                    self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](value)
                case "recipient":
                    self.recipient: SuiAddress = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown PayAllSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "PayAllSui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_input_coins(self, obj: list[ObjectID]) -> "PayAllSui":
        """Set input coin array."""
        self.input_coins: SuiArray[ObjectID] = SuiArray[ObjectID](obj)
        return self

    def set_recipient(self, obj: SuiAddress) -> "PayAllSui":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "PayAllSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MergeCoin(_MoveCallTransactionBuilder):
    """Merge two coins together."""

    merge_kwords: set[str] = {"signer", "gas_object", "gas_budget", "primary_coin", "coin_to_merge"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_mergeCoins")
        self.signer: SuiAddress = None
        self.primary_coin: ObjectID = None
        self.coin_to_merge: ObjectID = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "gas_object":
                    self.gas_object: ObjectID = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case "primary_coin":
                    self.primary_coin: ObjectID = value
                case "coin_to_merge":
                    self.coin_to_merge: ObjectID = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "MergeCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "MergeCoin":
        """Set sui object gas object."""
        self.gas_object: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "MergeCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_coin_to_merge(self, obj: ObjectID) -> "MergeCoin":
        """Set the address for the receiver."""
        self.coin_to_merge: ObjectID = obj
        return self

    def set_primary_coin(self, obj: ObjectID) -> "MergeCoin":
        """Set the primary coin to merge into."""
        self.primary_coin: ObjectID = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class SplitCoin(_MoveCallTransactionBuilder):
    """Split a coin into a one or more new coins."""

    split_kwords: set[str] = {"signer", "gas_object", "gas_budget", "coin_object_id", "split_amounts"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_splitCoin")
        self.signer: SuiAddress = None
        self.coin_object_id: ObjectID = None
        self.split_amounts: SuiArray[SuiNumber] = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "gas_object":
                    self.gas_object: ObjectID = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case "split_amounts":
                    self.split_amounts = SuiArray[SuiNumber](value)
                case "coin_object_id":
                    self.coin_object_id: ObjectID = value
                case _:
                    raise ValueError(f"Unknown TransferSui bulder type {key}")

    def set_signer(self, address: SuiAddress) -> "SplitCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "SplitCoin":
        """Set sui object gas object."""
        self.gas_object: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "SplitCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def set_coin_object_id(self, obj: ObjectID) -> "SplitCoin":
        """Set the object ID for the coin being split."""
        self.coin_object_id: ObjectID = obj
        return self

    def set_split_amounts(self, obj: list[SuiNumber]) -> "SplitCoin":
        """Set the amounts to split the coin into."""
        self.split_amounts: SuiArray[SuiNumber] = SuiArray[SuiNumber](obj)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class BatchTransaction(_MoveCallTransactionBuilder):
    """Builder for submitting batch transactions."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_batchTransaction")
        raise NotImplementedError


class Publish(_MoveCallTransactionBuilder):
    """Builder for publishing SUI Move packages."""

    publish_kwords = {"sender", "compiled_modules", "gas", "gas_budget"}

    def __init__(self, **kwargs) -> None:
        """Initialize builder."""
        super().__init__("sui_publish")
        self.sender: SuiAddress = None
        self.compiled_modules: SuiArray[SuiString] = None
        self.gas: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "sender":
                    self.sender: SuiAddress = value
                case "compiled_modules":
                    self.compiled_modules: SuiArray[SuiString] = SuiArray[SuiString](value)
                case "gas":
                    self.gas: ObjectID = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown MoveCall bulder type {key}")

    def set_sender(self, obj: SuiAddress) -> "Publish":
        """Set the publisher address."""
        self.sender: SuiAddress = obj
        return self

    def set_compiled_modules(self, obj: SuiArray[SuiString]) -> "Publish":
        """Set the publishing package base64 modules string array."""
        self.compiled_modules: SuiArray[SuiString] = obj
        return self

    def set_gas_object(self, obj: ObjectID) -> "Publish":
        """Set sui object gas object."""
        self.gas: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "Publish":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MoveCall(_MoveCallTransactionBuilder):
    """Builder for making calls to SUI Move contracts."""

    move_kwords: set[str] = {
        "signer",
        "package",
        "module",
        "function",
        "types",
        "arguments",
        "gas_object",
        "gas_budget",
    }

    def __init__(self, **kwargs) -> None:
        """Initialize builder."""
        super().__init__("sui_moveCall")
        self.signer: SuiAddress = None
        self.package_object_id: ObjectID = None
        self.module: SuiString = None
        self.function: SuiString = None
        self.type_arguments: SuiArray[SuiString] = SuiArray[SuiString]([])
        self.arguments: SuiArray[SuiString] = SuiArray[SuiString]([])
        self.gas_object: ObjectID = None
        self.gas_budget: SuiNumber = None
        for key, value in kwargs.items():
            match key:
                case "signer":
                    self.signer: SuiAddress = value
                case "package":
                    self.package_object_id: ObjectID = value
                case "module":
                    self.module: SuiString = value
                case "function":
                    self.function: SuiString = value
                case "types":
                    self.type_arguments: SuiArray[SuiString] = SuiArray[SuiString](value)
                case "arguments":
                    self.arguments: SuiArray[SuiString] = SuiArray[SuiString](value)
                case "gas_object":
                    self.gas_object: ObjectID = value
                case "gas_budget":
                    self.gas_budget: SuiNumber = value
                case _:
                    raise ValueError(f"Unknown MoveCall bulder type {key}")

    def set_signer(self, obj: SuiAddress) -> "MoveCall":
        """Set signers address."""
        self.signer: SuiAddress = obj
        return self

    def set_module(self, obj: SuiString) -> "MoveCall":
        """Set sui move module name."""
        self.module: SuiString = obj
        return self

    def set_function(self, obj: SuiString) -> "MoveCall":
        """Set sui move function name."""
        self.function: SuiString = obj
        return self

    def set_types(self, obj: SuiArray[SuiString]) -> "MoveCall":
        """Set sui generic types (if any)."""
        self.type_arguments: SuiArray[SuiString] = obj
        return self

    def set_arguments(self, obj: SuiArray[SuiString]) -> "MoveCall":
        """Set sui move call arguments (if any)."""
        self.arguments: SuiArray[SuiString] = obj
        return self

    def set_gas_object(self, obj: ObjectID) -> "MoveCall":
        """Set sui object gas object."""
        self.gas_object: ObjectID = obj
        return self

    def set_gas_budget(self, obj: SuiNumber) -> "MoveCall":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiNumber = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()
