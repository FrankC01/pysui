#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui data classes for GraphQL results."""
from abc import ABC, abstractmethod

import dataclasses
from enum import IntEnum
from typing import Any, Optional, Union, Callable
import dataclasses_json
import json


def _fast_flat(in_dict: dict, out_dict: dict):
    """Flattens a nested dictionary."""

    for i_key, i_value in in_dict.items():
        if isinstance(i_value, dict):
            _fast_flat(i_value, out_dict)
        else:
            out_dict[i_key] = i_value


class PGQL_Type(ABC):
    """Base GraphQL to pysui data representation class."""

    @abstractmethod
    def from_query(self) -> "PGQL_Type":
        """Converts raw GraphQL result to dataclass type.

        :return: Object instance of implementing class
        :rtype: PGQL_Type
        """


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PagingCursor:
    """Static cursor controls used for paging results."""

    hasNextPage: bool = dataclasses.field(default=False)
    endCursor: Optional[str] = dataclasses.field(default_factory=str)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class NoopGQL(PGQL_Type):
    """Returned when no data received from GraphQL."""

    next_cursor: PagingCursor
    data: list

    @classmethod
    def from_query(self) -> "NoopGQL":
        return NoopGQL(PagingCursor(), [])


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ErrorGQL(PGQL_Type):
    """."""

    next_cursor: PagingCursor
    data: list
    errors: Any

    @classmethod
    def from_query(self, errors: Any) -> "ErrorGQL":
        return ErrorGQL(PagingCursor(), [], errors)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadDeletedGQL:
    """Return when object has been wrapped or deleted."""

    version: int
    object_id: str
    object_kind: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiObjectOwnedShared:
    """Collection of coin data objects."""

    obj_owner_kind: str
    initial_version: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiObjectOwnedAddress:
    """Collection of coin data objects."""

    obj_owner_kind: str
    address_id: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiObjectOwnedParent:
    """Collection of coin data objects."""

    obj_owner_kind: str
    parent_id: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiObjectOwnedImmutable:
    """Collection of coin data objects."""

    obj_owner_kind: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinObjectGQL(PGQL_Type):
    """Coin object representation class."""

    coin_type: str
    version: int
    object_digest: str
    balance: str
    previous_transaction: str
    # coin_owner: str
    has_public_transfer: bool
    coin_object_id: str
    object_owner: Union[
        SuiObjectOwnedAddress,
        SuiObjectOwnedParent,
        SuiObjectOwnedShared,
        SuiObjectOwnedImmutable,
    ]

    @property
    def object_id(self) -> str:
        """Get as object_id."""
        return self.coin_object_id

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectGQL":
        """From raw GraphQL result data."""
        ser_dict: dict[str, Union[str, int]] = {}
        owner = in_data.pop("owner")
        owner_kind = owner["obj_owner_kind"]
        _fast_flat(in_data, ser_dict)
        match owner_kind:
            case "AddressOwner":
                ser_dict["object_owner"] = SuiObjectOwnedAddress(
                    owner_kind, owner["owner"]["address_id"]
                )
            case "Shared":
                ser_dict["object_owner"] = SuiObjectOwnedShared.from_dict(owner)
            case "Parent":
                ser_dict["object_owner"] = SuiObjectOwnedParent(
                    owner_kind, owner["owner"]["parent_id"]
                )
            case "Immutable":
                ser_dict["object_owner"] = SuiObjectOwnedImmutable(owner_kind)
        # ser_dict = ser_dict | res_dict
        return clz.from_dict(ser_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinFromObjectsGQL(PGQL_Type):
    """Collection of sui coin from objects."""

    data: list[Union[SuiCoinObjectGQL, ObjectReadDeletedGQL]]

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinFromObjectsGQL":
        if in_data:
            ser_dict: dict = {}
            _fast_flat(in_data, ser_dict)
            mid_list: list[dict] = []
            for node in ser_dict["nodes"]:
                ser_dict: dict = {}
                _fast_flat(node, ser_dict)
                # If fetching by ID it may not exist
                if ser_dict.get("object_kind") == "HISTORICAL":
                    mid_list.append(ser_dict)
                elif ser_dict.get("object_kind") == "WRAPPED_OR_DELETED":
                    ser_dict.pop("amo")
                    mid_list.append(ObjectReadDeletedGQL.from_dict(ser_dict))
            return clz.from_dict({"data": mid_list})
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinObjectsGQL(PGQL_Type):
    """Collection of coin data objects."""

    data: list[SuiCoinObjectGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectsGQL":
        """Serializes query result to list of Sui gas coin objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'coin_objects'
        """
        # Get cursor
        in_data = in_data.pop("qres").pop("coins")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[SuiCoinObjectGQL] = [
            SuiCoinObjectGQL.from_query(i_coin) for i_coin in in_data["coin_objects"]
        ]
        return SuiCoinObjectsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiStakedCoinGQL:
    """Staked coin object."""

    poolId: str
    version: int
    has_public_transfer: bool
    principal: str
    estimated_reward: str
    activated: dict
    requested: dict
    status: str
    object_id: str
    object_digest: str
    object_owner: SuiObjectOwnedAddress

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiStakedCoinGQL":
        """Serializes query result to list of SuiStaked gas coin objects."""
        if len(in_data):
            owners_dict = in_data.pop("owner")
            if owners_dict["obj_owner_kind"] == "AddressOwner":
                owners_dict["address_id"] = owners_dict.pop("owner")["address_id"]
            else:
                raise ValueError(
                    f"{owners_dict['obj_owner_kind']} for StakedSui not supported"
                )
            in_data["object_owner"] = owners_dict
            return SuiStakedCoinGQL.from_dict(in_data)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiStakedCoinsGQL(PGQL_Type):
    """Collection of staked coin objects."""

    owner: str
    staked_coins: list[SuiStakedCoinGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiStakedCoinsGQL":
        """Serializes query result to list of Sui gas coin objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'coin_objects'
        """
        if len(in_data):
            in_data = in_data.pop("address")
            next_cursor = in_data["stakedSuis"].pop("cursor")
            staked_coins = [
                SuiStakedCoinGQL.from_query(x)
                for x in in_data["stakedSuis"].pop("staked_coin")
            ]
            return SuiStakedCoinsGQL.from_dict(
                {
                    "owner": in_data["address"],
                    "stakedCoins": staked_coins,
                    "nextCursor": next_cursor,
                }
            )
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadGQL(PGQL_Type):
    """Raw object representation class."""

    version: int  # Yes
    object_id: str  # Yes
    object_digest: str  # Yes
    previous_transaction_digest: str  # Yes
    object_kind: str  # Yes

    storage_rebate: str  # Yes
    bcs: str  # Yes

    object_owner: Union[
        SuiObjectOwnedAddress,
        SuiObjectOwnedParent,
        SuiObjectOwnedShared,
        SuiObjectOwnedImmutable,
    ]
    has_public_transfer: Optional[bool] = False  # Yes
    object_type: Optional[str] = None
    content: Optional[dict] = None
    owner_id: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectReadGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with nested dictionaries
        """
        in_data = in_data["object"] if "object" in in_data else in_data
        if in_data:
            res_dict: dict = {}

            owner = in_data.pop("owner")
            if owner:
                owner_kind = owner["obj_owner_kind"]
                if in_data.get("as_move_content"):
                    contents = in_data["as_move_content"]["as_object"].pop("content")
                else:
                    contents = None
                    if in_data.get("as_move_package"):
                        in_data.pop("as_move_package")
                        in_data["object_type"] = "Package"
                # Flatten
                _fast_flat(in_data, res_dict)
                # Reassign
                res_dict["content"] = contents
                match owner_kind:
                    case "AddressOwner":
                        res_dict["object_owner"] = SuiObjectOwnedAddress(
                            owner_kind, owner["owner"]["address_id"]
                        )
                    case "Shared":
                        res_dict["object_owner"] = SuiObjectOwnedShared.from_dict(owner)
                    case "Parent":
                        res_dict["object_owner"] = SuiObjectOwnedParent(
                            owner_kind, owner["owner"]["parent_id"]
                        )
                    case "Immutable":
                        res_dict["object_owner"] = SuiObjectOwnedImmutable(owner_kind)
                # Flatten dictionary
                return ObjectReadGQL.from_dict(res_dict)
            else:
                return ObjectReadDeletedGQL.from_dict(in_data)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadsGQL(PGQL_Type):
    """Collection of object data objects."""

    data: list[ObjectReadGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectReadsGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'objects_data'
        """
        in_data = in_data.pop("objects")
        # Get cursor
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[ObjectReadGQL] = [
            ObjectReadGQL.from_query(i_obj) for i_obj in in_data["objects_data"]
        ]
        return ObjectReadsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EventGQL(PGQL_Type):
    """Collection of event summaries."""

    package_id: str
    module_name: str
    event_type: str
    timestamp: str
    json: str
    sender: Optional[str]

    @classmethod
    def from_query(clz, in_data: dict) -> "EventGQL":
        """Serializes query result to list of Sui objects."""
        in_mod_id = in_data.pop("sendingModule")
        to_merge: dict = {}
        _fast_flat(in_mod_id, to_merge)
        in_data |= to_merge
        in_data["json"] = json.dumps(in_data["json"])
        in_data["event_type"] = in_data.pop("type")["event_type"]
        # in_data["sender"] = [x["address"] for x in in_data["sender"]]
        return EventGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EventsGQL(PGQL_Type):
    """Collection of event summaries."""

    data: list[EventGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "EventsGQL":
        """Serializes query result to list of Sui objects.
        The in_data is a dictionary with 2 keys: 'cursor' and 'events'
        """

        in_data = in_data.pop("events")
        # Get cursor
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[ObjectReadGQL] = [
            EventGQL.from_query(i_obj) for i_obj in in_data["events"]
        ]
        return EventsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TxBlockListGQL(PGQL_Type):
    """Checkpoint data representation."""

    data: list[str]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "TxBlockListGQL":
        """Serializes query result of tx blocks in checkpoint."""
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        dlist: list[str] = [t_digest["digest"] for t_digest in in_data["tx_digests"]]
        return TxBlockListGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointGQL(PGQL_Type):
    """Checkpoint data representation."""

    digest: str
    sequence_number: int
    timestamp: str
    networkTotalTransactions: int
    transaction_blocks: TxBlockListGQL
    previous_checkpoint_digest: Optional[str]

    @classmethod
    def from_query(clz, in_data: dict) -> "CheckpointGQL":
        """Serializes query result of tx blocks in checkpoint."""
        in_data = in_data.pop("checkpoint", in_data)
        in_data["transaction_blocks"] = TxBlockListGQL.from_query(
            in_data["transaction_blocks"]
        )
        return CheckpointGQL.from_dict(in_data)

    @classmethod
    def from_last_checkpoint(clz, in_data: dict) -> "CheckpointGQL":
        """Serializes query result of tx blocks in checkpoint."""
        in_data = in_data.pop("checkpoints", None)
        in_data = in_data["nodes"][0]
        in_data["transaction_blocks"] = TxBlockListGQL.from_query(
            in_data["transaction_blocks"]
        )
        return CheckpointGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointsGQL(PGQL_Type):
    """Collection of Checkpoint summaries."""

    data: list[CheckpointGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "CheckpointsGQL":
        """."""
        in_data = in_data.pop("checkpoints")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        ndata: list[CheckpointGQL] = [
            CheckpointGQL.from_query(i_cp) for i_cp in in_data["checkpoints"]
        ]
        return CheckpointsGQL(ndata, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BalanceGQL(PGQL_Type):
    """Balance representation class."""

    coin_type: str
    coin_object_count: int
    total_balance: str
    owner: Optional[str] = ""

    @classmethod
    def from_query(clz, in_data: dict) -> "BalanceGQL":
        """Serializes query result of balance.

        The in_data is a dictionary with nested dictionaries
        """
        res_dict: dict = {}
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        return BalanceGQL.from_dict(res_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BalancesGQL(PGQL_Type):
    """Collection of balance objects."""

    owner_address: str
    data: list[BalanceGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "BalancesGQL":
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'objects_data'
        """
        # Get result
        in_data = in_data["qres"] if "qres" in in_data else in_data
        # Get cursor
        owner = in_data.pop("owner_address")
        balances = in_data.pop("balances")
        ncurs: PagingCursor = PagingCursor.from_dict(balances["cursor"])
        dlist: list[BalanceGQL] = [
            BalanceGQL.from_query(i_obj) for i_obj in balances["type_balances"]
        ]
        return BalancesGQL(owner, dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinMetadataGQL(PGQL_Type):
    """Coin metadata result representation class."""

    decimals: Optional[int] = None
    name: Optional[str] = None
    symbol: Optional[str] = None
    description: Optional[str] = None
    supply: Optional[str] = None
    address: Optional[str] = None
    icon_url: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinMetadataGQL":
        """Serializes query result to Sui coin metadata object."""
        res_dict: dict = {}
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        return SuiCoinMetadataGQL.from_dict(res_dict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionResultGQL(PGQL_Type):
    """Transaction result representation class."""

    expiration: Union[dict, None]
    gas_input: dict
    effects: dict
    transaction_kind: str
    digest: Optional[str] = ""
    sender: Optional[dict] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionResultGQL":
        """."""
        if in_data.get("transactionBlock"):
            txblock = in_data.pop("transactionBlock")
            txblock["transaction_kind"] = txblock.pop("kind")["tx_kind"]
            return TransactionResultGQL.from_dict(txblock)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DryRunResultGQL(PGQL_Type):
    """DryRun result representation class."""

    transaction_block: TransactionResultGQL
    results: Optional[list[dict]]
    error: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "DryRunResultGQL":
        """."""
        if in_data:
            in_data = in_data.get("dryRun")
            if in_data:
                dr_err = in_data.pop("error")
                dr_res = in_data.pop("results")
                tblock = TransactionResultGQL.from_query(in_data)
                return DryRunResultGQL.from_dict(
                    {"error": dr_err, "results": dr_res, "transaction_block": tblock}
                )
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ExecutionResultGQL(PGQL_Type):
    """Execution result representation class."""

    status: str
    lamport_version: int
    digest: str
    errors: Optional[list[str]] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "ExecutionResultGQL":
        """."""
        if in_data:
            in_data = in_data.get("executeTransactionBlock")
            if in_data:
                fdict: dict = {}
                _fast_flat(in_data, fdict)
                return ExecutionResultGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSummaryGQL(PGQL_Type):
    digest: str
    status: str
    timestamp: str
    tx_kind: str
    errors: Optional[Any] = dataclasses.field(default_factory=list)

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionSummaryGQL":
        """."""
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        return TransactionSummaryGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSummariesGQL(PGQL_Type):
    """Transaction list of digest representation class."""

    data: list[TransactionSummaryGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionSummariesGQL":
        """."""
        in_data = in_data.pop("transactionBlocks")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])
        tsummary = [
            TransactionSummaryGQL.from_query(x) for x in in_data.pop("tx_blocks")
        ]
        return TransactionSummariesGQL(tsummary, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OwnedOrImmutableInputGQL:
    """ProgrammableTransactionBlock input class."""

    address: str
    version: int
    digest: str
    input_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SharedObjectInputGQL:
    """ProgrammableTransactionBlock input class."""

    address: str
    initial_shared_version: int
    mutable: bool
    input_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PureInputGQL:
    """ProgrammableTransactionBlock input class."""

    base64_bytes: str
    input_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ArgInputRefGQL:
    """ProgrammableTransactionBlock argument reference class."""

    input_index: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ArgResultRefGQL:
    """ProgrammableTransactionBlock argument reference class."""

    cmd: int
    result_index: Optional[int]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ArgGasCoinRefGQL:
    """ProgrammableTransactionBlock argument reference class."""

    gas_ref: Any


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionMoveCallGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    package: str
    module: str
    function_name: str
    arguments: list[Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]]
    tx_typename: str
    typeArguments: Optional[list[dict]]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactioTransferObjectslGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    inputs: list[Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]]
    address: Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]
    tx_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSplitCoinsGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    coin: Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]
    amounts: list[Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]]
    tx_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionMergeCoinsGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    coin: Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]
    coins: list[Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]]
    tx_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionPublishGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    modules: list[str]
    dependencies: list[str]
    tx_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionUpgradeGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    modules: list[str]
    dependencies: list[str]
    current_package: str
    upgrade_ticket: Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]
    tx_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionMakeMoveVecGQL:
    """ProgrammableTransactionBlock transaction representation class."""

    vector_type: dict
    elements: list[Union[ArgInputRefGQL, ArgResultRefGQL, ArgGasCoinRefGQL]]
    tx_typename: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ProgrammableTransactionBlockGQL:
    """ProgrammableTransactionBlock kind representation class."""

    inputs: list[Union[OwnedOrImmutableInputGQL, SharedObjectInputGQL, PureInputGQL]]
    transactions: list[
        Union[
            TransactionMoveCallGQL,
            TransactioTransferObjectslGQL,
            TransactionSplitCoinsGQL,
            TransactionMergeCoinsGQL,
            TransactionPublishGQL,
            TransactionUpgradeGQL,
            TransactionMakeMoveVecGQL,
        ]
    ]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ConsensusCommitPrologueTransactionGQL:
    """ConsensusCommitPrologueTransaction kind representation class."""

    epoch: dict
    consensus_round: int
    commit_timestamp: str
    consensus_commit_digest: Optional[str]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class GenesisTransactionGQL:
    """GenesisTransaction kind representation class."""

    objects: dict


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class AuthenticatorStateUpdateTransactionGQL:
    """AuthenticatorStateUpdateTransaction kind representation class."""

    epoch: dict
    consensus_round: int
    authenticator_obj_initial_shared_version: int
    new_active_jwks: dict


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class RandomnessStateUpdateTransactionGQL:
    """AuthenticatorStateUpdateTransaction kind representation class."""

    epoch: dict
    randomness_round: int
    random_bytes: str
    new_active_jwks: dict
    randomness_obj_initial_shared_version: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionKindGQL(PGQL_Type):
    """Transaction kind representation class."""

    digest: str
    timestamp: str
    transaction_kind: str
    kind: Union[
        ProgrammableTransactionBlockGQL,
        GenesisTransactionGQL,
        ConsensusCommitPrologueTransactionGQL,
    ]

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionKindGQL":
        """."""
        tx_block = in_data.get("transactionBlock") if in_data else None
        if tx_block:
            tx_type = tx_block["kind"].pop("tx_kind")
            tx_block["timestamp"] = tx_block.pop("effects")["timestamp"]
            tx_block["transaction_kind"] = tx_type
            match tx_type:
                case "ProgrammableTransactionBlock":
                    tx_block["kind"]["inputs"] = tx_block["kind"]["inputs"]["nodes"]
                    tx_block["kind"]["transactions"] = tx_block["kind"]["transactions"][
                        "nodes"
                    ]
                case "GenesisTransaction" | "ConsensusCommitPrologueTransaction":
                    pass
                case _:
                    raise ValueError(f"{tx_type} not handled in data model.")
            return TransactionKindGQL.from_dict(tx_block)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorGQL(PGQL_Type):
    """Validator representation class."""

    validator_name: str
    validator_address: str
    description: str
    project_url: str
    staking_pool_sui_balance: str
    pending_stake: str
    pending_pool_token_withdraw: str
    pending_total_sui_withdraw: str
    voting_power: int
    commission_rate: int
    next_epoch_stake: str
    gas_price: str
    next_epoch_gas_price: str
    commission_rate: str
    next_epoch_commission_rate: int
    at_risk: Optional[int]

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorGQL":
        """."""
        in_data["validatorAddress"] = in_data["address"]["validatorAddress"]
        return ValidatorGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorSetGQL(PGQL_Type):
    """ValidatorSet representation class."""

    total_stake: int
    validators: list[ValidatorGQL]
    pending_removals: Optional[list[int]]
    pending_active_validators_size: Optional[int]
    inactive_pools_size: Optional[int]
    validator_candidates_size: Optional[int]

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorSetGQL":
        """."""
        in_data["validators"] = [
            ValidatorGQL.from_query(v_obj)
            for v_obj in in_data["validators"]["validators"]
        ]
        return ValidatorSetGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ReferenceGasPriceGQL(PGQL_Type):
    """ReferenceGasPriceGQL representation class."""

    reference_gas_price: str

    @classmethod
    def from_query(clz, in_data: dict) -> "ReferenceGasPriceGQL":
        in_data = in_data.pop("epoch", in_data)
        return ReferenceGasPriceGQL.from_dict(in_data)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SystemStateSummaryGQL(PGQL_Type):
    """SuiSystemStateSummary representation class."""

    system_state_version: str
    total_transactions: int
    reference_gas_price: ReferenceGasPriceGQL
    system_parameters: dict
    validator_set: ValidatorSetGQL
    storage_fund: dict
    safe_mode: dict

    @classmethod
    def from_query(clz, in_data: dict) -> "SystemStateSummaryGQL":
        in_data = in_data.pop("qres", in_data)
        rgp = {"referenceGasPrice": in_data.pop("referenceGasPrice")}
        in_data["referenceGasPrice"] = ReferenceGasPriceGQL.from_query(rgp)
        in_data["validatorSet"] = ValidatorSetGQL.from_query(in_data["validatorSet"])
        return SystemStateSummaryGQL.from_dict(in_data)


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class TransactionConstraints:
    """Subset of Protocol Constraints."""

    protocol_version: Optional[int] = 0
    max_arguments: Optional[int] = 0
    max_input_objects: Optional[int] = 0
    max_num_transferred_move_object_ids: Optional[int] = 0
    max_programmable_tx_commands: Optional[int] = 0
    max_pure_argument_size: Optional[int] = 0
    max_tx_size_bytes: Optional[int] = 0
    max_type_argument_depth: Optional[int] = 0
    max_type_arguments: Optional[int] = 0
    max_tx_gas: Optional[int] = 0
    receive_objects: bool = False


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class KeyValue:
    """Generic map element."""

    key: str
    value: Union[bool, str, None]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ProtocolConfigGQL:
    """Sui ProtocolConfig representation."""

    protocolVersion: int
    configs: list[KeyValue]
    featureFlags: list[KeyValue]
    transaction_constraints: Optional[TransactionConstraints] = dataclasses.field(
        default_factory=TransactionConstraints
    )

    def _value_to_type(self, v: Any) -> Union[int, bool]:
        """."""
        if v:
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                if v.count("."):
                    return float(v)
                return int(v, base=0)
        return None

    def __post_init__(self):
        """."""
        # Convert configs key/val to dict of key/int
        cfg_dict: dict = {}
        cnst_dict: dict = self.transaction_constraints.to_dict()
        # Turn to key addressable dict
        for ckv in self.configs:
            cfg_dict[ckv.key] = self._value_to_type(ckv.value)

        # Fetch the constraint and replace self.constraints
        for cnst_key in cnst_dict.keys():
            if cnst_key in cfg_dict:
                cnst_dict[cnst_key] = cfg_dict[cnst_key]
        self.transaction_constraints = TransactionConstraints.from_dict(cnst_dict)
        self.transaction_constraints.protocol_version = self.protocolVersion

        # Set appropriate features
        feat_dict: dict = {k.key: k.value for k in self.featureFlags}
        self.transaction_constraints.receive_objects = feat_dict["receive_objects"]

    @classmethod
    def from_query(clz, in_data: dict) -> "ProtocolConfigGQL":
        return ProtocolConfigGQL.from_dict(in_data.pop("protocolConfig"))


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructureGQL:
    """Sui MoveStucture representation."""

    struct_name: str
    abilities: list[str]
    fields: list[dict]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveStructureGQL":
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            return MoveStructureGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructuresGQL:
    """Sui collection of MoveStuctures."""

    structures: list[MoveStructureGQL]
    next_cursor: Optional[PagingCursor]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveStructuresGQL":
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            _fast_flat(in_data, fdict)
            if "hasNextPage" in fdict:
                fdict["next_cursor"] = PagingCursor(
                    fdict.pop("hasNextPage"), fdict.pop("endCursor")
                )
            else:
                fdict["next_cursor"] = None
            fdict["structures"] = [
                MoveStructureGQL.from_query(x) for x in fdict["nodes"]
            ]
            return MoveStructuresGQL.from_dict(fdict)
            # return MoveStructuresGQL.from_dict(
            #     {"structures": [MoveStructureGQL.from_query(x) for x in fdict["nodes"]]}
            # )
        return NoopGQL.from_query()


class RefType(IntEnum):
    """."""

    NO_REF = 0
    REF = 1
    MUT_REF = 2

    @classmethod
    def from_ref(cls, rstr: str) -> "RefType":
        """."""
        return (
            RefType.REF
            if rstr == "&"
            else RefType.MUT_REF if rstr == "&mut" else RefType.NO_REF
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveTypeArg:
    """."""

    ref: RefType
    scalar_type: str

    @classmethod
    def from_str(cls, in_ref: str, in_type: str) -> "MoveTypeArg":
        """ "."""


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveScalarArg:
    """."""

    ref: RefType
    scalar_type: str

    @classmethod
    def from_str(cls, in_ref: str, in_type: str) -> "MoveScalarArg":
        """ "."""
        return cls(RefType.from_ref(in_ref), in_type)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveObjectRefArg:
    """."""

    ref_type: RefType
    type_package: str
    type_module: str
    type_struct: str
    type_params: list
    is_optional: bool
    is_receiving: bool
    has_type: bool

    @classmethod
    def from_body(cls, in_ref: str, in_type: dict) -> "MoveObjectRefArg":
        """ "."""
        ref_type: RefType = (
            in_ref if isinstance(in_ref, RefType) else RefType.from_ref(in_ref)
        )
        if in_type["type"] == "String" or in_type["type"] == "ID":
            return MoveScalarArg.from_str(in_ref, in_type["type"])
        ref_type: RefType = (
            in_ref if isinstance(in_ref, RefType) else RefType.from_ref(in_ref)
        )
        inner_type = in_type.get("typeParameters")
        has_type = bool(inner_type)
        inner_list = []

        if has_type:
            inner_list = []
            for inner_t in inner_type:
                if isinstance(inner_t, dict):
                    if "typeParameter" in inner_t:
                        inner_list.append(inner_t["typeParameter"])
                    else:
                        if "vector" in inner_t:
                            inner_list.append(
                                MoveVectorArg.from_body(ref_type, inner_t)
                            )
                        else:
                            inner_list.append(
                                MoveObjectRefArg.from_body(
                                    ref_type, inner_t["datatype"]
                                )
                            )
                else:
                    inner_list.append(MoveScalarArg.from_str("", inner_t))

        return cls(
            ref_type,
            in_type["package"],
            in_type["module"],
            in_type["type"],
            inner_list,
            in_type["type"] == "Option",
            in_type["type"] == "Receiving",
            has_type,
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveVectorArg:
    """."""

    ref: RefType
    vec_arg: Union[MoveScalarArg, MoveObjectRefArg]

    @classmethod
    def from_body(cls, in_ref: str, in_type: dict) -> "MoveVectorArg":
        """ "."""
        from_vec = in_type["vector"]
        return cls(
            RefType.from_ref(in_ref),
            (
                MoveScalarArg.from_str("", from_vec)
                if isinstance(from_vec, str)
                else MoveObjectRefArg.from_body("", from_vec["datatype"])
            ),
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveListArg:
    """."""

    ref: RefType
    list_arg: Union[MoveScalarArg, MoveObjectRefArg]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveWitnessArg:
    """."""

    ref: RefType

    @classmethod
    def from_body(cls, in_ref: str) -> "MoveWitnessArg":
        """."""
        return cls(
            RefType.from_ref(in_ref),
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveArgSummary:
    """."""

    type_parameters: list
    arg_list: list[
        Union[
            MoveScalarArg, MoveObjectRefArg, MoveTypeArg, MoveVectorArg, MoveWitnessArg
        ]
    ]
    returns: Optional[int] = None


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionGQL:
    """Sui MoveFunction representation."""

    function_name: str
    is_entry: bool
    visibility: str
    type_parameters: list
    parameters: list[dict]
    returns: Optional[list] = dataclasses.field(default_factory=list)

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveFunctionGQL":
        if in_data.get("object") or in_data.get("function_name"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            return MoveFunctionGQL.from_dict(fdict)
        return NoopGQL.from_query()

    def arg_summary(self) -> MoveArgSummary:
        """Summarize the function's arguments."""
        a_list: list = []
        for parm in self.parameters:
            sig = parm.get("signature")
            ref = sig.get("ref")
            body = sig.get("body")
            if "datatype" in body:
                if body.get("datatype")["type"] == "TxContext":
                    continue
                a_list.append(MoveObjectRefArg.from_body(ref, body.get("datatype")))
            elif "vector" in body:
                a_list.append(MoveVectorArg.from_body(ref, body))
            else:
                if (
                    isinstance(body, dict)
                    and len(body) == 1
                    and "typeParameter" in body
                ):
                    a_list.append(MoveWitnessArg.from_body(ref))
                else:
                    a_list.append(MoveScalarArg.from_str(ref, body))
        return MoveArgSummary(
            self.type_parameters, a_list, len(self.returns) if self.returns else None
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionsGQL:
    """Sui MoveFunction representation."""

    functions: list[MoveFunctionGQL]
    next_cursor: Optional[PagingCursor]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveFunctionsGQL":
        """."""
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            if fdict.get("nodes"):
                if "hasNextPage" in fdict:
                    fdict["next_cursor"] = PagingCursor(
                        fdict.pop("hasNextPage"), fdict.pop("endCursor")
                    )
                else:
                    fdict["next_cursor"] = None
                fdict["functions"] = [
                    MoveFunctionGQL.from_query(x) for x in fdict["nodes"]
                ]
                return MoveFunctionsGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveModuleGQL:
    """Sui MoveModule representation."""

    module_name: str
    module_structures: Union[MoveStructuresGQL, list]
    module_functions: Union[MoveFunctionsGQL, list]

    @classmethod
    def from_query(clz, in_data: dict) -> "MoveModuleGQL":
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            if "structure_list" in fdict:
                fdict["module_structures"] = []
            if "function_list" in fdict:
                fdict["module_functions"] = []
            fdict["module_structures"] = MoveStructuresGQL.from_query(
                {"nodes": fdict["module_structures"]}
            )
            fdict["module_functions"] = MoveFunctionsGQL.from_query(
                {"nodes": fdict["module_functions"]}
            )

            return MoveModuleGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MovePackageGQL:
    """Sui MovePackage representation."""

    package_id: str
    package_version: int
    modules: list[MoveModuleGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "MovePackageGQL":
        if in_data.get("object"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["next_cursor"] = PagingCursor(
                fdict.pop("hasNextPage"), fdict.pop("endCursor")
            )
            fdict["modules"] = [MoveModuleGQL.from_query(x) for x in fdict["nodes"]]
            fdict.pop("nodes")
            return MovePackageGQL.from_dict(fdict)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorFullGQL:
    """Sui ValidatorSet representation."""

    validator_name: str
    validator_address: str
    description: str
    imageUrl: str
    projectUrl: str
    stakingPoolSuiBalance: str
    stakingPoolActivationEpoch: int
    exchangeRatesSize: int
    rewardsPool: str
    poolTokenBalance: str
    pendingStake: str
    pendingTotalSuiWithdraw: str
    pendingPoolTokenWithdraw: str
    votingPower: int
    gasPrice: str
    commissionRate: int
    nextEpochStake: str
    nextEpochGasPrice: str
    nextEpochCommissionRate: 1200
    apy: int
    atRisk: Optional[int] = None
    operating_cap_address: Optional[str] = None
    exchange_rates_address: Optional[str] = None
    staking_pool_address: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorFullGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        if "operatingCap" in fdict:
            fdict["operating_cap_address"] = None
            fdict.pop("operatingCap")
        # if "exchangeRate" in fdict:
        #     fdict["exchange_rates_address"] = None
        #     fdict.pop("exchangeRate")
        return ValidatorFullGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorSetsGQL:
    """Sui ValidatorSet representation."""

    totalStake: str
    pendingRemovals: list
    pendingActiveValidatorsId: str
    pendingActiveValidatorsSize: int
    stakingPoolMappingsId: str
    inactivePoolsId: str
    validatorCandidatesId: str
    validatorCandidatesSize: int
    validators: list[ValidatorFullGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorSetsGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        fdict["next_cursor"] = PagingCursor(
            fdict.pop("hasNextPage"), fdict.pop("endCursor")
        )
        fdict["validators"] = [
            ValidatorFullGQL.from_query(x) for x in fdict["validators"]
        ]
        return ValidatorSetsGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorApyGQL:
    """Sui ValidatorApy representation."""

    name: str
    apy: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorApysGQL:
    """Sui ValidatorApy representation."""

    validators_apy: list[ValidatorApyGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorApysGQL":
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        fdict["next_cursor"] = PagingCursor(
            fdict.pop("hasNextPage"), fdict.pop("endCursor")
        )
        return ValidatorApysGQL.from_dict(fdict)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DynamicFieldGQL:
    """Sui Object's Dynamic Field representation."""

    name: dict
    field_kind: str
    field_data: dict


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DynamicFieldsGQL:
    """Sui Object's Dynamic Fields representation."""

    parent_object_id: str
    version: int
    next_cursor: PagingCursor
    dynamic_fields: list[DynamicFieldGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "DynamicFieldsGQL":
        if in_data.get("objects"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["next_cursor"] = PagingCursor(
                fdict.pop("hasNextPage"), fdict.pop("endCursor")
            )
            return DynamicFieldsGQL.from_dict(fdict)
        return NoopGQL.from_query()
