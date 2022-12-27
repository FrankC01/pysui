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

"""Sui Builders: Simple sui_getXXX calls."""

from typing import Any, Union
from pysui.abstracts.client_types import SuiBaseType
from pysui.sui.sui_builders.base_builder import _NativeTransactionBuilder
from pysui.sui.sui_types.scalars import SuiString, SuiInteger, ObjectID, SuiNullType, SuiBoolean, SuiTransactionDigest
from pysui.sui.sui_types.collections import SuiMap, EventID
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_txresults.single_tx import (
    SuiCoinMetadata,
    CoinBalances,
    SuiCoinObjects,
    SuiSystemState,
    ObjectInfo,
    ObjectRead,
    CommitteeInfo,
    SuiTxnAuthSigners,
)
from pysui.sui.sui_txresults.complex_tx import EventQueryEnvelope, TransactionQueryEnvelope
from pysui.sui.sui_txresults.package_meta import (
    SuiMovePackage,
    SuiMoveModule,
    SuiMoveFunction,
    SuiMoveStruct,
    SuiMoveFunctionArgumentTypes,
)

from pysui.sui import sui_utils


class GetCoinMetaData(_NativeTransactionBuilder):
    """GetCoinMetaData returns meta data for a specific `coin_type`."""

    def __init__(self, *, coin_type: SuiString = None) -> None:
        """."""
        super().__init__("sui_getCoinMetadata", handler_cls=SuiCoinMetadata, handler_func="from_dict")
        self.coin_type = coin_type if isinstance(coin_type, SuiString) else SuiString(coin_type)

    def set_coin_type(self, coin_type: SuiString) -> "GetCoinMetaData":
        """."""
        self.coin_type = coin_type if isinstance(coin_type, SuiString) else SuiString(coin_type)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """_collect_parameters Returns expected RPC parameters.

        :return: RPC expects a string representing a coin type signature (e.g. 0x2::sui::SUI)
        :rtype: list[SuiAddress]
        """
        return [self.coin_type]


class GetCoinTypeBalance(_NativeTransactionBuilder):
    """GetCoinTypeBalance Return the total coin balance for each coin type."""

    def __init__(self, *, owner: SuiAddress, coin_type: SuiString):
        """__init__ Initializes builder with address and coin type to fetch balances for.

        :param owner: the owner's Sui address
        :type owner: SuiAddress
        :param coin_type: fully qualified type names for the coin (e.g., 0x2::sui::SUI)
        :type coin_type: SuiString
        """
        super().__init__("sui_getBalance", handler_cls=CoinBalances, handler_func="ingest_data")
        self.owner = None
        self.coin_type = None
        self.set_owner(owner)
        self.set_coin_type(coin_type)

    def set_owner(self, owner: SuiAddress) -> "GetCoinTypeBalance":
        """Set the owner property."""
        if isinstance(owner, SuiAddress):
            self.owner = owner
            return self
        raise ValueError(f"{owner} is not of type SuiAddress")

    def set_coin_type(self, coin_type: SuiString) -> "GetCoinTypeBalance":
        """Set the coin_type property."""
        if isinstance(coin_type, SuiString):
            self.coin_type = coin_type
            return self
        if isinstance(coin_type, str):
            self.coin_type = SuiString(coin_type)
            return self
        raise ValueError(f"{coin_type} is not of type SuiString")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """_collect_parameters Returns expected RPC parameters."""
        return [self.owner, self.coin_type]


class GetCoins(_NativeTransactionBuilder):
    """Return the list of Coin objects owned by an address."""

    def __init__(
        self,
        *,
        owner: SuiAddress,
        coin_type: SuiString,
        limit: SuiInteger,
        cursor: ObjectID = None,
    ):
        """__init__ Initialize builder with address,coin_type, page limits and cursor.

        :param owner: the coin owner's Sui address
        :type owner: SuiAddress
        :param coin_type: fully qualified type names for the coin (e.g., 0x2::sui::SUI)
        :type coin_type: SuiString
        :param limit: maximum number of items per page
        :type limit: SuiInteger
        :param cursor: Optional ObjectID as the starting item in returned page, defaults to None
        :type cursor: ObjectID, optional
        """
        super().__init__("sui_getCoins", handler_cls=SuiCoinObjects, handler_func="from_dict")
        self.set_limit(limit)
        self.cursor = cursor if cursor else SuiNullType()
        self.set_owner(owner)
        self.set_coin_type(coin_type)

    def set_owner(self, owner: SuiAddress) -> "GetCoinTypeBalance":
        """Set the owner property."""
        if isinstance(owner, SuiAddress):
            self.owner = owner
            return self
        raise ValueError(f"{owner} is not of type SuiAddress")

    def set_coin_type(self, coin_type: SuiString) -> "GetCoinTypeBalance":
        """Set the coin_type property."""
        if isinstance(coin_type, SuiString):
            self.coin_type = coin_type
            return self
        if isinstance(coin_type, str):
            self.coin_type = SuiString(coin_type)
            return self
        raise ValueError(f"{coin_type} is not of type SuiString")

    def set_limit(self, limit: Union[int, SuiInteger]) -> "GetCoins":
        """Sets the maximum values returned on the result page."""
        if isinstance(limit, SuiInteger):
            self.limit = limit
            return self
        if isinstance(limit, int):
            self.limit = SuiInteger(limit)
            return self
        raise ValueError(f"{limit} is not of type SuiInteger")

    def set_cursor(self, cursor: ObjectID) -> "GetCoins":
        """Optional ObjectID (of sample ``coin_type``)."""
        self.cursor = cursor
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """_collect_parameters Returns expected RPC parameters."""
        return [self.owner, self.coin_type, self.cursor, self.limit]


class GetSuiSystemState(_NativeTransactionBuilder):
    """Return the SUI system state."""

    def __init__(self):
        """__init__ Initializes builder."""
        super().__init__("sui_getSuiSystemState", handler_cls=SuiSystemState, handler_func="from_dict")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """_collect_parameters Returns expected RPC parameters."""
        return []


class GetTotalSupply(_NativeTransactionBuilder):
    """Return the total supply for a given coin type (eg. 0x2::sui::SUI)."""

    def __init__(
        self,
        *,
        coin_type: SuiString,
    ):
        """__init__ Initializes builder."""
        super().__init__("sui_getTotalSupply")
        self.coin_type = None
        self.set_coin_type(coin_type)

    def set_coin_type(self, coin_type: SuiString) -> "GetTotalSupply":
        """Set the coin_type property."""
        if isinstance(coin_type, SuiString):
            self.coin_type = coin_type
            return self
        if isinstance(coin_type, str):
            self.coin_type = SuiString(coin_type)
            return self
        raise ValueError(f"{coin_type} is not of type SuiString")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """_collect_parameters Returns expected RPC parameters."""
        return [self.coin_type]


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

    def __init__(self, sui_object: Any, version: SuiInteger) -> None:
        """__init__ Initialize builder.

        :param sui_object: Object identifier to fetch from chain, defaults to None
        :type sui_object: ObjectID, optional
        :param version: Specific version sequence number being requested, defaults to None
        :type version: SuiInteger, optional
        """
        super().__init__("sui_tryGetPastObject", handler_cls=ObjectRead, handler_func="factory")
        self.object_id: ObjectID = sui_utils.as_object_id(sui_object)
        self.version: SuiInteger = version if isinstance(version, SuiInteger) else SuiInteger(version)

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
    """GetPackage When executed, return structured representations of all modules in the given package."""

    def __init__(self, *, package: ObjectID) -> None:
        """__init__ Initialize GetPackage object.

        :param package: ObjectID of package to query, defaults to None
        :type package: ObjectID, optional
        """
        super().__init__(
            "sui_getNormalizedMoveModulesByPackage", handler_cls=SuiMovePackage, handler_func="ingest_data"
        )
        self.package: ObjectID = sui_utils.as_object_id(package)

    def set_package(self, package: ObjectID) -> "GetPackage":
        """Set the package ObjectID to be retrieved."""
        self.package: ObjectID = sui_utils.as_object_id(package)
        return self

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package]


class GetModule(_NativeTransactionBuilder):
    """GetModule When executed, returns the structural representation of a module.

    Includes general Module informationn as well as structure and function definitions.
    """

    def __init__(self, *, package: ObjectID, module_name: SuiString) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module_name: Name of module from package to fetch
        :type module_name: SuiString
        """
        super().__init__("sui_getNormalizedMoveModule", handler_cls=SuiMoveModule, handler_func="ingest_data")
        self.package: ObjectID = sui_utils.as_object_id(package)
        self.module_name: SuiString = module_name

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package, self.module_name]


class GetFunction(_NativeTransactionBuilder):
    """GetFunction When executed, returns the structural representation of a module's function.

    Includes general function arguments and return type definitions.
    """

    def __init__(self, *, package: ObjectID, module_name: SuiString, function_name: SuiString) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module_name: Name of module from package containing function_name to fetch
        :type module_name: SuiString
        :param function_name: Name of module from package to fetch
        :type function_name: SuiString
        """
        super().__init__("sui_getNormalizedMoveFunction", handler_cls=SuiMoveFunction, handler_func="ingest_data")
        self.package: ObjectID = sui_utils.as_object_id(package)
        self.module_name: SuiString = module_name
        self.function_name: SuiString = function_name

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package, self.module_name, self.function_name]


class GetFunctionArgs(_NativeTransactionBuilder):
    """GetFunction When executed, returns the argument types of a Move function."""

    def __init__(self, *, package: ObjectID, module: SuiString, function: SuiString) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module: Name of module from package containing function_name to fetch
        :type module: SuiString
        :param function: Name of module's function to fetch arguments for
        :type function: SuiString
        """
        super().__init__(
            "sui_getMoveFunctionArgTypes", handler_cls=SuiMoveFunctionArgumentTypes, handler_func="ingest_data"
        )
        self.package: ObjectID = sui_utils.as_object_id(package)
        self.module: SuiString = module
        self.function: SuiString = function

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package, self.module, self.function]


class GetStructure(_NativeTransactionBuilder):
    """GetStructure When executed, returns a module's structure representation."""

    def __init__(self, *, package: ObjectID, module_name: SuiString, structure_name: SuiString) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module_name: Name of module from package containing function_name to fetch
        :type module_name: SuiString
        :param structure_name: Name of structure from structure to fetch
        :type structure_name: SuiString
        """
        super().__init__("sui_getNormalizedMoveStruct", handler_cls=SuiMoveStruct, handler_func="ingest_data")
        self.package: ObjectID = sui_utils.as_object_id(package)
        self.module_name: SuiString = module_name
        self.structure_name: SuiString = structure_name

    def _collect_parameters(self) -> list[ObjectID]:
        """Collect the call parameters."""
        return [self.package, self.module_name, self.structure_name]


class GetRpcAPI(_NativeTransactionBuilder):
    """GetRpcAPI When executed, returns full list of SUI node RPC API supported."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("rpc.discover")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return []


class GetCommittee(_NativeTransactionBuilder):
    """GetCommittee When executed, returns information on committee (collection of nodes)."""

    def __init__(self, epoch: SuiInteger = None) -> None:
        """__init__ GetCommitttee Builder initializer.

        :param epoch: Epoch to return state of committee from, defaults to None
        :type epoch: SuiInteger, optional
        """
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
    """GetEvents When executed, return list of events for a specified query criteria."""

    events_kwords = {"query", "cursor", "limit", "descending_order"}

    def __init__(
        self,
        *,
        query: Union[SuiString, SuiMap] = None,
        cursor: EventID = None,
        limit: Union[SuiInteger, SuiNullType] = None,
        descending_order: SuiBoolean = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_getEvents", handler_cls=EventQueryEnvelope, handler_func="from_dict")
        self.query: Union[SuiString, SuiMap] = None
        self.cursor: EventID = None
        self.limit: Union[SuiInteger, SuiNullType] = None
        self.descending_order: SuiBoolean = False
        for hit in self.events_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTotalTxCount(_NativeTransactionBuilder):
    """GetTotalTxCount When executed, return the total number of transactions known to the server."""

    def __init__(self) -> None:
        """Initialize builder."""
        super().__init__("sui_getTotalTransactionNumber")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTx(_NativeTransactionBuilder):
    """GetTx When executed, return the transaction response object."""

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

    def __init__(
        self,
        *,
        query: Union[str, SuiMap] = None,
        curser: str = None,
        limit: SuiInteger = None,
        descending_order: SuiBoolean = None,
    ) -> None:
        """Initialize builder."""
        inargs = locals().copy()
        super().__init__("sui_getTransactions", handler_cls=TransactionQueryEnvelope, handler_func="from_dict")
        self.query: Union[str, SuiMap] = None
        self.cursor: str = None
        self.limit: SuiInteger = None
        self.descending_order: SuiBoolean = False
        for hit in self.txs_kwords & set(inargs.keys()):
            setattr(self, hit, inargs[hit])

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()


class GetTransactionsInRange(_NativeTransactionBuilder):
    """Return list of transaction digests within the queried range."""

    def __init__(
        self,
        *,
        start: SuiInteger,
        end: SuiInteger,
    ) -> None:
        """Initialize builder."""
        super().__init__("sui_getTransactionsInRange")
        self.start = None
        self.end = None
        self.set_start(start)
        self.set_end(end)

    def set_start(self, start: SuiInteger) -> "GetTransactionsInRange":
        """."""
        if isinstance(start, SuiInteger):
            self.start = start
            return self
        if isinstance(start, int):
            self.start = SuiInteger(start)
            return self
        raise ValueError(f"{start} is not an integer type.")

    def set_end(self, end: SuiInteger) -> "GetTransactionsInRange":
        """."""
        if isinstance(end, SuiInteger):
            self.end = end
            return self
        if isinstance(end, int):
            self.end = SuiInteger(end)
            return self
        raise ValueError(f"{end} is not an integer type.")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.start, self.end]


class GetTxAuthSignatures(_NativeTransactionBuilder):
    """Fetch transaction authorized signatures public keys."""

    def __init__(self, *, txn_digest: SuiTransactionDigest = None):
        """__init__ When executed, returns the authorizers public keys array.

        :param txn_digest: Base58 transaction digest, defaults to None
        :type txn_digest: SuiTransactionDigest, optional
        """
        super().__init__("sui_getTransactionAuthSigners", handler_cls=SuiTxnAuthSigners, handler_func="from_dict")
        self.digest = txn_digest

    def set_txn_digest(self, txn_digest: SuiTransactionDigest) -> "GetTxAuthSignatures":
        """Sets the transaciotn digest."""
        self.digest = txn_digest if isinstance(txn_digest, SuiTransactionDigest) else SuiTransactionDigest(txn_digest)
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return [self.digest]
