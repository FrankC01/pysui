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


"""SUI Builders modules.

Defines RPC encapsulation of types and arguments for SUI RPC calls.
"""

from abc import abstractmethod
from enum import IntEnum
from typing import Any, Type, Union
from pysui.abstracts import Builder, PublicKey, SignatureScheme
from pysui.sui.sui_types import (
    CommitteeInfo,
    EventID,
    EventQueryEnvelope,
    MovePackage,
    ObjectInfo,
    ObjectRead,
    ObjectID,
    SuiBoolean,
    SuiString,
    SuiInteger,
    SuiTxBytes,
    SuiSignature,
    SuiArray,
    SuiGas,
    SuiMap,
    SuiAddress,
    SuiBaseType,
    TransactionQueryEnvelope,
    TxEffectResult,
)
import pysui.sui.sui_utils as sui_utils


class SuiRequestType(IntEnum):
    """SuiRequestType Defines the type of request being made when invoking `sui_executeTransaction`.

    :param IntEnum: Base enumeration type
    :type IntEnum: _type_
    :raises TypeError: _description_
    """

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
    """Base Sui API Builder Class.

    Subclasses must identify public vars that are
    required by Sui RPC API.
    """

    def __init__(
        self, method: str, txn_required: bool, handler_cls: Type[SuiBaseType] = None, handler_func: str = None
    ) -> None:
        """__init__ Initialize builder.

        :param method: The SUI RPC API method
        :type method: str
        :param txn_required: Indicate that this is a complex request or simple transaction
        :type txn_required: bool
        :param handler_cls: Designate factor class for receipt data, defaults to None
        :type handler_cls: Type[SuiBaseType], optional
        :param handler_func:
            Name of function (either on class or regular function) to convert receipt data, defaults to None
        :type handler_func: str, optional
        """
        super().__init__()
        self._method = method
        self._txn_required = txn_required
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
    """GetObjectsOwnedByAddress When executed, returns the list of objects owned by an address."""

    def __init__(self, address: SuiAddress = None) -> None:
        """__init__ Initializes builder with optional address to fetch objects for.

        :param address: A SuiAddress object whose identifier is used as parameter to RPC calls, defaults to None
        :type address: SuiAddress, optional
        """
        super().__init__("sui_getObjectsOwnedByAddress", handler_cls=ObjectInfo, handler_func="factory")
        self.address: SuiAddress = address

    def set_address(self, address: SuiAddress) -> "GetObjectsOwnedByAddress":
        """set_address Set the address whose objects you want to return.

        :param address: A SuiAddress object whose identifier is used as parameter to RPC calls
        :type address: SuiAddress
        :return: self
        :rtype: GetObjectsOwnedByAddress
        """
        self.address = address
        return self

    def _collect_parameters(self) -> list[SuiAddress]:
        """_collect_parameters Returns expected RPC parameters.

        :return: RPC expects a string representing a SUI address (e.g. 0x....)
        :rtype: list[SuiAddress]
        """
        return [self.address]


class GetObjectsOwnedByObject(_NativeTransactionBuilder):
    """GetObjectsOwnedByObject When executed, returns the list of objects owned by an object."""

    def __init__(self, sui_object: Any = None) -> None:
        """__init__ Initializes builder with ObjectID to fetch objects for.

        :param sui_object: An ObjectID or type that can be coerced to ObjectID, defaults to None
        :type sui_object: Any, optional
        """
        super().__init__("sui_getObjectsOwnedByObject")
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)

    def set_object_id(self, sui_object: Any) -> "GetObjectsOwnedByObject":
        """set_object_id Set the object to fetch objects owned by.

        :param sui_object: An ObjectID or type that can be coerced to ObjectID, defaults to None
        :type sui_object: Any
        :return: self
        :rtype: GetObjectsOwnedByObject
        """
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)
        return self

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.object_id]


class GetObject(_NativeTransactionBuilder):
    """GetObject When executed, return the object detailed information for a specified object."""

    def __init__(self, sui_object: Any = None) -> None:
        """__init__ Initializes builder.

        :param sui_object: Object identifier to fetch from chain, defaults to None
        :type sui_object: ObjectID, optional
        """
        super().__init__("sui_getObject", handler_cls=ObjectRead, handler_func="factory")
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)

    def set_object(self, sui_object: ObjectID) -> "GetObjectsOwnedByObject":
        """Set the object to fetch objects owned by."""
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)
        return self

    def _collect_parameters(self) -> list[ObjectInfo]:
        """Collect the call parameters."""
        return [self.object_id]


class GetPastObject(_NativeTransactionBuilder):
    """GetPastObject When executed, return the object information for a specified version.

    Note there is no software-level guarantee/SLA that objects with past versions can be retrieved by this API,
    even if the object and version exists/existed. The result may vary across nodes depending on their pruning
    policies.
    """

    def __init__(self, sui_object: Any, version: SuiInteger = None) -> None:
        """__init__ Initialize builder.

        :param sui_object: Object identifier to fetch from chain, defaults to None
        :type sui_object: ObjectID, optional
        :param version: Specific version sequence number being requested, defaults to None
        :type version: SuiInteger, optional
        """
        super().__init__("sui_tryGetPastObject", handler_cls=ObjectRead, handler_func="factory")
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)
        if version:
            self.version: SuiInteger = version if isinstance(version, SuiInteger) else SuiInteger(version)
        else:
            self.version: SuiInteger = SuiInteger(1)

    def set_object(self, sui_object: ObjectID) -> "GetPastObject":
        """Set the object to fetch objects owned by."""
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)
        return self

    def set_version(self, version: SuiInteger) -> "GetPastObject":
        """Set the object version."""
        self.version: SuiInteger = version
        return self

    def _collect_parameters(self) -> list[ObjectInfo]:
        """Collect the call parameters."""
        return [self.object_id, self.version]


class GetPackage(_NativeTransactionBuilder):
    """GetPackage When executed, return structured representations of all modules in the given package.

    :param _NativeTransactionBuilder: _description_
    :type _NativeTransactionBuilder: _type_
    """

    def __init__(self, package: ObjectID = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getNormalizedMoveModulesByPackage", handler_cls=MovePackage, handler_func="ingest_data")
        self.package: ObjectID = sui_utils.as_object_id(package)

    def set_package(self, package: ObjectID) -> "GetPackage":
        """Set the package ObjectID to be retrieved."""
        self.package: ObjectID = sui_utils.as_object_id(package)
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

    def __init__(self, epoch: SuiInteger = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getCommitteeInfo", handler_cls=CommitteeInfo, handler_func="factory")
        self.epoch: SuiInteger = epoch if epoch else SuiInteger(None)

    def set_epoch(self, epoch: SuiInteger) -> "GetCommittee":
        """Set epoch."""
        self.epoch = epoch
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.epoch]


# Event Query Types


class TransactionEventQuery(SuiMap):
    """Query events for Transaction."""

    def __init__(self, txid: str):
        """Initialize query parameter."""
        super().__init__("Transaction", txid)


class MoveModuleEventQuery(SuiMap):
    """Query events for Move Module."""

    def __init__(self, module: str, package: str) -> None:
        """Initialize query parameter."""
        sdict = {"module": module, "package": package}
        super().__init__("MoveModule", sdict)


class MoveEventQuery(SuiMap):
    """Query events for Move Event."""

    def __init__(self, struct: str):
        """Initialize query parameter."""
        super().__init__("MoveEvent", struct)


class EventTypeQuery(SuiMap):
    """Query events for Event types."""

    _evtype_set = {
        "MoveEvent",
        "Publish",
        "CoinBalanceChange",
        "EpochChange",
        "Checkpoint",
        "TransferObject",
        "MutateObject",
        "DeleteObject",
        "NewObject",
    }

    def __init__(self, event_type: str):
        """Initialize query parameter."""
        if event_type in self._evtype_set:
            super().__init__("EventType", event_type)
        else:
            raise ValueError(f"event_type: {event_type} not one of {self._evtype_set}")


class SenderEventQuery(SuiMap):
    """Query events for Sender address."""

    def __init__(self, sender: SuiAddress):
        """Initialize query parameter."""
        super().__init__("Sender", sender.value.value)


class RecipientEventQuery(SuiMap):
    """Query events for Recipient address."""

    def __init__(self, recipient: SuiAddress):
        """Initialize query parameter."""
        sdict = {"AddressOwner": recipient.value.value}
        super().__init__("Recipient", sdict)


class ObjectEventQuery(SuiMap):
    """Query events for Object id."""

    def __init__(self, object_id: ObjectID):
        """Initialize query parameter."""
        super().__init__("Object", object_id.value)


class TimeRangeEventQuery(SuiMap):
    """Query events for Time Range."""

    def __init__(self, start_time: SuiInteger, end_time: SuiInteger):
        """Initialize query parameter."""
        sdict = {"start_time": start_time.value, "end_time": end_time.value}
        super().__init__("TimeRange", sdict)


class GetEvents(_NativeTransactionBuilder):
    """Generalized event retrieval."""

    events_kwords = {"query", "cursor", "limit", "descending_order"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getEvents", handler_cls=EventQueryEnvelope, handler_func="from_dict")
        self.query: Union[SuiString, SuiMap] = None
        self.cursor: EventID = None
        self.limit: SuiInteger = None
        self.descending_order: SuiBoolean = False
        for hit in self.events_kwords & set(kwargs.keys()):
            setattr(self, hit, kwargs[hit])

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

    def __init__(self, digest: Union[SuiString, str] = None) -> None:
        """Initialize builder."""
        super().__init__("sui_getTransaction")
        self.digest: SuiString = digest if isinstance(digest, SuiString) else SuiString(digest)

    def set_digest(self, digest: Union[SuiString, str]) -> "GetTx":
        """Set digest var."""
        self.digest = digest if isinstance(digest, SuiString) else SuiString(digest)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.digest]


class GetTxsMoveFunction(SuiMap):
    """For GetTxns."""

    def __init__(self, package: str, function: str, module: str):
        """Initialize query params."""
        super().__init__("MoveFunction", {"package": package, "function": function, "module": module})


class GetTxsInputObject(SuiMap):
    """For GetTxns."""

    def __init__(self, object_id: str):
        """Initialize query params."""
        super().__init__("InputObject", object_id)


class GetTxsMutateObject(SuiMap):
    """For GetTxns."""

    def __init__(self, object_id: str):
        """Initialize query params."""
        super().__init__("MutatedObject", object_id)


class GetTxsFromAddress(SuiMap):
    """For GetTxns."""

    def __init__(self, address_id: str):
        """Initialize query params."""
        super().__init__("FromAddress", address_id)


class GetTxsToAddress(SuiMap):
    """For GetTxns."""

    def __init__(self, address_id: str):
        """Initialize query params."""
        super().__init__("ToAddress", address_id)


class GetTxs(_NativeTransactionBuilder):
    """Return information about a specific transaction."""

    txs_kwords = {"query", "cursor", "limit", "descending_order"}

    def __init__(self, **kwargs: dict) -> None:
        """Initialize builder."""
        super().__init__("sui_getTransactions", handler_cls=TransactionQueryEnvelope, handler_func="from_dict")
        self.query: Union[str, SuiMap] = None
        self.cursor: str = None
        self.limit: SuiInteger = None
        self.descending_order: SuiBoolean = False
        for hit in self.txs_kwords & set(kwargs.keys()):
            setattr(self, hit, kwargs[hit])

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class ExecuteTransaction(_NativeTransactionBuilder):
    """Submit a signed transaction to Sui."""

    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes = None,
        sig_scheme: SignatureScheme = None,
        signature: SuiSignature = None,
        pub_key: PublicKey = None,
        request_type: SuiRequestType = None,
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_executeTransaction", handler_cls=TxEffectResult, handler_func="from_dict")
        self.tx_bytes: SuiTxBytes = tx_bytes
        self.sig_scheme: SignatureScheme = sig_scheme
        self.signature: SuiSignature = signature
        self.pub_key: PublicKey = pub_key
        self.request_type: SuiRequestType = request_type

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

    def __init__(
        self,
        *,
        tx_bytes: SuiTxBytes = None,
        sig_scheme: SignatureScheme = None,
        signature: SuiSignature = None,
        pub_key: PublicKey = None,
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_dryRunTransaction")
        self.tx_bytes: SuiTxBytes = tx_bytes
        self.sig_scheme: SignatureScheme = sig_scheme
        self.signature: SuiSignature = signature
        self.pub_key: PublicKey = pub_key

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

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        object_id: ObjectID = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
        recipient: SuiAddress = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_transferObject")
        self.signer: SuiAddress = None
        self.object_id: ObjectID = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        self.recipient: SuiAddress = None
        for hit in self.transferobject_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_object_id(self, obj: ObjectID) -> "TransferObject":
        """Set the object to transfer."""
        self.object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_signer(self, address: SuiAddress) -> "TransferObject":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas(self, obj: ObjectID) -> "TransferObject":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "TransferObject":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
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

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        sui_object_id: ObjectID = None,
        gas_budget: SuiInteger = None,
        recipient: SuiAddress = None,
        amount: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_transferSui")
        self.signer: SuiAddress = None
        self.sui_object_id: ObjectID = None
        self.gas_budget: SuiInteger = None
        self.recipient: SuiAddress = None
        self.amount: SuiInteger = None
        for hit in self.transfersui_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "TransferSui":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_sui_object_id(self, obj: ObjectID) -> "TransferSui":
        """Set sui object gas object."""
        self.sui_object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "TransferSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_recipient(self, obj: SuiAddress) -> "TransferSui":
        """Set the address for the receiver."""
        self.recipient: SuiAddress = obj
        return self

    def set_amount(self, obj: SuiInteger) -> "TransferSui":
        """Set the amount to transfer to recipient."""
        self.amount: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class Pay(_MoveCallTransactionBuilder):
    """Transfer, split and merge coins of any type (SUI coin 0x2::sui::SUI or otherwise)."""

    pay_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas", "gas_budget"}
    _pay_array_keys: set[str] = {"input_coins", "recipients", "amounts"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        input_coins: SuiArray[ObjectID] = None,
        recipients: SuiArray[SuiAddress] = None,
        amounts: SuiArray[SuiInteger] = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_pay")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiInteger] = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.pay_kwords & set(inargs.keys()):
            if hit in self._pay_array_keys and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

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

    def set_amounts(self, obj: list[SuiInteger]) -> "Pay":
        """Set the amount(s) to transfer to recipient."""
        self.amounts: SuiArray[SuiInteger] = SuiArray[SuiInteger](obj)
        return self

    def set_gas(self, obj: ObjectID) -> "Pay":
        """Set sui object gas object for paying transaction."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "Pay":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class PaySui(_MoveCallTransactionBuilder):
    """Transfer, split and merge SUI coins (0x2::sui::SUI) only."""

    paysui_kwords: set[str] = {"signer", "input_coins", "recipients", "amounts", "gas_budget"}
    _paysui_array_keys: set[str] = {"input_coins", "recipients", "amounts"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        input_coins: SuiArray[ObjectID] = None,
        recipients: SuiArray[SuiAddress] = None,
        amounts: SuiArray[SuiInteger] = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_paySui")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipients: SuiArray[SuiAddress] = None
        self.amounts: SuiArray[SuiInteger] = None
        self.gas_budget: SuiInteger = None
        for hit in self.paysui_kwords & set(inargs.keys()):
            if hit in self._paysui_array_keys and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

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

    def set_amounts(self, obj: list[SuiInteger]) -> "PaySui":
        """Set the amount(s) to transfer to recipient."""
        self.amounts: SuiArray[SuiInteger] = SuiArray[SuiInteger](obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "PaySui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class PayAllSui(_MoveCallTransactionBuilder):
    """Transfer all coins of SUI coin type (0x2::sui::SUI) to a single recipient."""

    payallsui_kwords: set[str] = {"signer", "input_coins", "recipient", "gas_budget"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        input_coins: SuiArray[ObjectID] = None,
        recipient: SuiAddress = None,
        amounts: SuiArray[SuiInteger] = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_payAllSui")
        self.signer: SuiAddress = None
        self.input_coins: SuiArray[ObjectID] = None
        self.recipient: SuiAddress = None
        self.gas_budget: SuiInteger = None
        for hit in self.payallsui_kwords & set(inargs.keys()):
            if hit == "input_coins" and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

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

    def set_gas_budget(self, obj: SuiInteger) -> "PayAllSui":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MergeCoin(_MoveCallTransactionBuilder):
    """Merge two coins together."""

    merge_kwords: set[str] = {"signer", "gas_object", "gas_budget", "primary_coin", "coin_to_merge"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        primary_coin: ObjectID = None,
        coin_to_merge: ObjectID = None,
        gas_object: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_mergeCoins")
        self.signer: SuiAddress = None
        self.primary_coin: ObjectID = None
        self.coin_to_merge: ObjectID = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.merge_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "MergeCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "MergeCoin":
        """Set sui object gas object."""
        self.gas_object: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "MergeCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_coin_to_merge(self, obj: ObjectID) -> "MergeCoin":
        """Set the address for the receiver."""
        self.coin_to_merge: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_primary_coin(self, obj: ObjectID) -> "MergeCoin":
        """Set the primary coin to merge into."""
        self.primary_coin: ObjectID = sui_utils.as_object_id(obj)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class SplitCoin(_MoveCallTransactionBuilder):
    """Split a coin into a one or more new coins."""

    split_kwords: set[str] = {"signer", "gas_object", "gas_budget", "coin_object_id", "split_amounts"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        coin_object_id: ObjectID = None,
        split_amounts: SuiArray[SuiInteger] = None,
        gas_object: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_splitCoin")
        self.signer: SuiAddress = None
        self.coin_object_id: ObjectID = None
        self.split_amounts: SuiArray[SuiInteger] = None
        self.gas_object: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.split_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "SplitCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "SplitCoin":
        """Set sui object gas object."""
        self.gas_object: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "SplitCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_coin_object_id(self, obj: ObjectID) -> "SplitCoin":
        """Set the object ID for the coin being split."""
        self.coin_object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_split_amounts(self, obj: list[SuiInteger]) -> "SplitCoin":
        """Set the amounts to split the coin into."""
        self.split_amounts: SuiArray[SuiInteger] = SuiArray[SuiInteger](obj)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class SplitCoinEqually(_MoveCallTransactionBuilder):
    """Split a coin into a one or more new coins."""

    splite_kwords: set[str] = {"signer", "gas", "gas_budget", "coin_object_id", "split_count"}

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        coin_object_id: ObjectID = None,
        split_count: SuiInteger = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_splitCoinEqual")
        self.signer: SuiAddress = None
        self.coin_object_id: ObjectID = None
        self.split_count: SuiInteger = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.splite_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def set_signer(self, address: SuiAddress) -> "SplitCoin":
        """Set the gas owner signer."""
        self.signer: SuiAddress = address
        return self

    def set_gas_object(self, obj: ObjectID) -> "SplitCoin":
        """Set sui object gas object."""
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "SplitCoin":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def set_coin_object_id(self, obj: ObjectID) -> "SplitCoin":
        """Set the object ID for the coin being split."""
        self.coin_object_id: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_split_count(self, obj: SuiInteger) -> "SplitCoin":
        """Set the amounts to split the coin into."""
        self.split_count: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class BatchParameter(SuiMap):
    """Type for verifications."""

    @abstractmethod
    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""


class TransferObjectParams(BatchParameter):
    """For submitting transfer in a batch transaction."""

    def __init__(self, *, receiver: SuiAddress, transfer_object: SuiGas) -> None:
        """Initialize transfer properties."""
        self.receiver: SuiAddress = receiver
        self.transfer_object: SuiGas = transfer_object
        super().__init__("transferObjectRequestParams", {})

    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""
        out_dict = self.map["transferObjectRequestParams"]
        out_dict["recipient"] = self.receiver.address
        out_dict["objectId"] = self.transfer_object.identifier.value
        return self.map


class MoveCallRequestParams(BatchParameter):
    """For submitting transfer in a batch transaction."""

    def __init__(
        self,
        *,
        package_object: ObjectID,
        module_str: SuiString,
        function_str: SuiString,
        type_arguments: SuiArray[SuiString],
        arguments: SuiArray[SuiString],
    ):
        """__init__ Initialize parameters."""
        self.package_object_id: ObjectID = sui_utils.as_object_id(package_object)
        self.module: SuiString = module_str
        self.function: SuiString = function_str
        self.type_arguments: SuiArray[str] = SuiArray([x.value for x in type_arguments.array])
        self.arguments: SuiArray[str] = SuiArray([x.value for x in arguments.array])
        super().__init__("moveCallRequestParams", {})

    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""
        out_dict = self.map["moveCallRequestParams"]
        out_dict["arguments"] = self.arguments.array
        out_dict["function"] = self.function.value
        out_dict["module"] = self.module.value
        out_dict["packageObjectId"] = self.package_object_id.value
        out_dict["typeArguments"] = self.type_arguments.array
        return self.map


class BatchTransaction(_MoveCallTransactionBuilder):
    """Builder for submitting batch transactions."""

    def __init__(
        self, signer: SuiAddress, transaction_params: SuiArray[BatchParameter], gas: ObjectID, gas_budget: SuiInteger
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_batchTransaction")
        self.signer: SuiAddress = signer
        self.single_transaction_params = None
        self.gas: ObjectID = sui_utils.as_object_id(gas)
        self.gas_budget = gas_budget

        for item in transaction_params.array:
            if not isinstance(item, BatchParameter):
                raise ValueError(f"{item} is not of type BatchParameter")
        self.single_transaction_params = transaction_params

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        collection = []
        for item in self.single_transaction_params.array:
            collection.append(item.realize_parameters())
        self.single_transaction_params = SuiArray(collection)
        return self._pull_vars()


class Publish(_MoveCallTransactionBuilder):
    """Builder for publishing SUI Move packages."""

    publish_kwords = {"sender", "compiled_modules", "gas", "gas_budget"}

    def __init__(
        self,
        *,
        sender: SuiAddress = None,
        compiled_modules: SuiArray[SuiString] = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_publish")
        self.sender: SuiAddress = None
        self.compiled_modules: SuiArray[SuiString] = None
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.publish_kwords & set(inargs.keys()):
            if hit == "compiled_modules" and isinstance(inargs[hit], list):
                setattr(self, hit, SuiArray(inargs[hit]))
            else:
                setattr(self, hit, inargs[hit])

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
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "Publish":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class MoveCall(_MoveCallTransactionBuilder):
    """Builder for making calls to SUI Move contracts."""

    move_kwords: set[str] = {
        "signer",
        "package_object_id",
        "module",
        "function",
        "type_arguments",
        "arguments",
        "gas",
        "gas_budget",
    }
    _movecall_array_keys: set[str] = {
        "type_arguments",
        "arguments",
    }

    def __init__(
        self,
        *,
        signer: SuiAddress = None,
        package_object_id: ObjectID = None,
        module: SuiString = None,
        function: SuiString = None,
        type_arguments: SuiArray[SuiString] = None,
        arguments: SuiArray[SuiString] = None,
        gas: ObjectID = None,
        gas_budget: SuiInteger = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_moveCall")
        self.signer: SuiAddress = None
        self.package_object_id: ObjectID = None
        self.module: SuiString = None
        self.function: SuiString = None
        self.type_arguments: SuiArray[SuiString] = SuiArray[SuiString]([])
        self.arguments: SuiArray[SuiString] = SuiArray[SuiString]([])
        self.gas: ObjectID = None
        self.gas_budget: SuiInteger = None
        for hit in self.move_kwords & set(inargs.keys()):
            if hit in self._movecall_array_keys:
                if inargs[hit]:
                    setattr(self, hit, SuiArray(inargs[hit]))
                else:
                    setattr(self, hit, SuiArray([]))
            else:
                setattr(self, hit, inargs[hit])

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
        self.gas: ObjectID = sui_utils.as_object_id(obj)
        return self

    def set_gas_budget(self, obj: SuiInteger) -> "MoveCall":
        """Set the amount for transaction payment."""
        self.gas_budget: SuiInteger = obj
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()
