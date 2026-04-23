#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui data classes for GraphQL results."""
from abc import ABC, abstractmethod

import base64
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

    @classmethod
    @abstractmethod
    def from_query(cls, in_data: Any = None) -> "PGQL_Type":
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
    def from_query(self) -> "NoopGQL":  # type: ignore[override]
        return NoopGQL(PagingCursor(), [])


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ErrorGQL(PGQL_Type):
    """."""

    next_cursor: PagingCursor
    data: list
    errors: Any

    @classmethod
    def from_query(self, errors: Any) -> "ErrorGQL":  # type: ignore[override]
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
    has_public_transfer: bool
    coin_object_id: str
    object_owner: Union[
        SuiObjectOwnedAddress,
        SuiObjectOwnedShared,
        SuiObjectOwnedParent,
        SuiObjectOwnedImmutable,
    ]
    previous_transaction: Optional[str] = dataclasses.field(default="")

    @property
    def object_id(self) -> str:
        """Get as object_id."""
        return self.coin_object_id

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectGQL":  # type: ignore[override]
        """From raw GraphQL result data."""
        ser_dict: dict[str, Any] = {}
        owner = in_data.pop("owner")
        owner_kind = owner["obj_owner_kind"]
        _fast_flat(in_data, ser_dict)
        match owner_kind:
            case "AddressOwner":
                ser_dict["object_owner"] = SuiObjectOwnedAddress(
                    owner_kind, owner["address_id"]["address"]
                )
            case "Shared":
                ser_dict["object_owner"] = SuiObjectOwnedShared.from_dict(owner)  # type: ignore[attr-defined]
            case "ObjectOwner":
                ser_dict["object_owner"] = SuiObjectOwnedParent(
                    owner_kind, owner["parent_id"]["address"]
                )
            case "Immutable":
                ser_dict["object_owner"] = SuiObjectOwnedImmutable(owner_kind)
        # ser_dict = ser_dict | res_dict
        return clz.from_dict(ser_dict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinFromObjectsGQL(PGQL_Type):
    """Collection of sui coin from objects."""

    data: list[Union[SuiCoinObjectGQL, ObjectReadDeletedGQL]]
    next_cursor: Optional[PagingCursor] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[SuiCoinFromObjectsGQL, NoopGQL]":  # type: ignore[override]
        if in_data:
            ser_dict: dict = {}
            _fast_flat(in_data, ser_dict)
            mid_list: list[Any] = []
            for node in ser_dict["multiGetObjects"]:
                ser_coin_dict: dict = node["asMoveObject"]
                mid_list.append(SuiCoinObjectGQL.from_query(ser_coin_dict))
                # _fast_flat(node, ser_dict)
                # If fetching by ID it may not exist
                # if (
                #     ser_coin_dict.get("status") == "HISTORICAL"
                #     or ser_coin_dict.get("status") == "INDEXED"
                # ):
                #     mid_list.append(SuiCoinObjectGQL.from_query(ser_coin_dict))
                # elif ser_coin_dict.get("status") == "WRAPPED_OR_DELETED":
                #     # ser_coin_dict.pop("amo")
                #     mid_list.append(ObjectReadDeletedGQL.from_dict(ser_coin_dict))  # type: ignore[attr-defined]
            return clz.from_dict({"data": mid_list, "next_cursor": None})  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinObjectsGQL(PGQL_Type):
    """Collection of coin data objects."""

    data: list[SuiCoinObjectGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectsGQL":  # type: ignore[override]
        """Serializes query result to list of Sui gas coin objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'coin_objects'
        """
        # Get cursor
        in_data = in_data.pop("qres").pop("coins")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])  # type: ignore[attr-defined]
        dlist: list[SuiCoinObjectGQL] = []
        for i_coin in in_data["coin_objects"]:
            dlist.append(SuiCoinObjectGQL.from_query(i_coin))
        return SuiCoinObjectsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiCoinObjectSummaryGQL(PGQL_Type):
    """Summary information on sui coin."""

    coin_object_id: str
    object_digest: str
    version: int
    balance: str

    @property
    def object_id(self) -> str:
        """Get as object_id."""
        return self.coin_object_id

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiCoinObjectSummaryGQL":  # type: ignore[override]
        """Serializes query result to sui coin summary."""
        ser_dict: dict = {}
        _fast_flat(in_data, ser_dict)
        ser_dict.pop("id")
        return clz.from_dict(ser_dict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiStakedCoinGQL:
    """Staked coin object."""

    coin_type: str
    version: int
    object_digest: str
    has_public_transfer: bool
    coin_object_id: str
    pool_id: str
    principal: str
    stake_activation_epoch: str
    object_owner: Union[
        SuiObjectOwnedAddress,
        SuiObjectOwnedShared,
        SuiObjectOwnedParent,
        SuiObjectOwnedImmutable,
    ]
    previous_transaction: Optional[str] = dataclasses.field(default="")

    @property
    def object_id(self) -> str:
        """Get as object_id."""
        return self.coin_object_id

    @classmethod
    def from_query(clz, in_data: dict) -> "SuiStakedCoinGQL":  # type: ignore[override]
        """From raw GraphQL result data."""
        ser_dict: dict[str, Any] = {}
        owner = in_data.pop("owner")
        owner_kind = owner["obj_owner_kind"]
        _fast_flat(in_data, ser_dict)
        match owner_kind:
            case "AddressOwner":
                ser_dict["object_owner"] = SuiObjectOwnedAddress(
                    owner_kind, owner["address_id"]["address"]
                )
            case "Shared":
                ser_dict["object_owner"] = SuiObjectOwnedShared.from_dict(owner)  # type: ignore[attr-defined]
            case "ObjectOwner":
                ser_dict["object_owner"] = SuiObjectOwnedParent(
                    owner_kind, owner["parent_id"]["address"]
                )
            case "Immutable":
                ser_dict["object_owner"] = SuiObjectOwnedImmutable(owner_kind)
        # ser_dict = ser_dict | res_dict
        return clz.from_dict(ser_dict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BasicCurrentEpochInfoGQL(PGQL_Type):
    """Basic info from current epoch."""

    epoch_id: int
    reference_gas_price: int
    start_timestamp: str
    end_timestampt: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[BasicCurrentEpochInfoGQL, NoopGQL]":  # type: ignore[override]
        """."""
        if in_data:
            in_data = in_data.pop("epoch")
            return BasicCurrentEpochInfoGQL.from_dict(in_data)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class SuiStakedCoinsGQL(PGQL_Type):
    """Collection of staked coin objects."""

    staked_coins: list[SuiStakedCoinGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[SuiStakedCoinsGQL, NoopGQL]":  # type: ignore[override]
        """Serializes query result to list of Sui gas coin objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'coin_objects'
        """
        if len(in_data):
            in_data = in_data.pop("objects")
            next_cursor = in_data.pop("cursor")
            staked_coins = [
                SuiStakedCoinGQL.from_query(x.get("asMoveObject"))
                for x in in_data.pop("staked_coin")
            ]
            return SuiStakedCoinsGQL.from_dict(  # type: ignore[attr-defined]
                {
                    # "owner": in_data["address"],
                    "stakedCoins": staked_coins,
                    "nextCursor": next_cursor,
                }
            )
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectContentBCS(PGQL_Type):
    """Raw object content BCS string."""

    address: str  # Yes
    bcs: str
    previous_transaction_digest: Optional[str] = None

    def as_bytes(self) -> bytes:
        """Convert BCS to bytes"""
        return base64.b64decode(self.bcs)

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectContentBCS":  # type: ignore[override]
        """."""
        to_merge: dict = {}
        _fast_flat(in_data, to_merge)
        return clz.from_dict(to_merge)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectsContentBCS(PGQL_Type):
    """Raw object content BCS string."""

    objects_data: list[ObjectContentBCS]

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[ObjectsContentBCS, NoopGQL]":  # type: ignore[override]
        """."""
        if len(in_data):
            objs = [ObjectContentBCS.from_query(x) for x in in_data["multiGetObjects"]]
            return clz(objs)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadGQL(PGQL_Type):
    """Raw object representation class."""

    version: int  # Yes
    object_id: str  # Yes
    object_digest: str  # Yes

    storage_rebate: str  # Yes
    bcs: str  # Yes

    object_owner: Union[
        SuiObjectOwnedAddress,
        SuiObjectOwnedShared,
        SuiObjectOwnedParent,
        SuiObjectOwnedImmutable,
    ]

    has_public_transfer: Optional[bool] = False  # Yes
    object_type: Optional[str] = None
    content: Optional[dict] = None
    owner_id: Optional[str] = None
    previous_transaction_digest: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[ObjectReadGQL, NoopGQL]":  # type: ignore[override]
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
                            owner_kind, owner["address_id"]["address"]
                        )
                    case "Shared":
                        res_dict["object_owner"] = SuiObjectOwnedShared.from_dict(owner)  # type: ignore[attr-defined]
                    case "ObjectOwner":
                        res_dict["object_owner"] = SuiObjectOwnedParent(
                            owner_kind, owner["parent_id"]["address"]
                        )
                    case "Immutable":
                        res_dict["object_owner"] = SuiObjectOwnedImmutable(owner_kind)
                # Flatten dictionary
                return ObjectReadGQL.from_dict(res_dict)  # type: ignore[attr-defined]
            else:
                return ObjectReadDeletedGQL.from_dict(in_data)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectReadsGQL(PGQL_Type):
    """Collection of object data objects."""

    data: list[ObjectReadGQL]
    next_cursor: Optional[PagingCursor] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectReadsGQL":  # type: ignore[override]
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with either 'multiGetObjects:list' and no cursor
        or 'objects:list' with cursor
        """
        if mgo := in_data.get("multiGetObjects"):
            dlist: list[Any] = [
                ObjectReadGQL.from_query(i_obj) for i_obj in mgo
            ]
            return ObjectReadsGQL(dlist)
        else:
            obj_mbase = in_data.pop("objects")
            ncurs: PagingCursor = PagingCursor.from_dict(obj_mbase["cursor"])  # type: ignore[attr-defined]
            dlist = [
                ObjectReadGQL.from_query(i_obj) for i_obj in obj_mbase["objects_data"]
            ]
            return ObjectReadsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectVersionReadsGQL(PGQL_Type):
    """Collection of object data objects."""

    data: list[ObjectReadGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectVersionReadsGQL":  # type: ignore[override]
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'objects_data'
        """
        in_data = in_data.pop("multiGetObjects")
        # Get cursor
        dlist: list[Any] = [
            ObjectReadGQL.from_query(i_obj) for i_obj in in_data
        ]
        return ObjectVersionReadsGQL(dlist)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EventGQL(PGQL_Type):
    """Collection of event summaries."""

    package_id: str
    module_name: str
    timestamp: str
    json: str
    sender: Optional[dict]

    @classmethod
    def from_query(clz, in_data: dict) -> "EventGQL":  # type: ignore[override]
        """Serializes query result to list of Sui objects."""
        in_mod_id = in_data.pop("transactionModule")
        to_merge: dict = {}
        _fast_flat(in_mod_id, to_merge)
        in_data |= to_merge
        in_data["json"] = json.dumps(in_data["contents"]["json"])
        return EventGQL.from_dict(in_data)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EventsGQL(PGQL_Type):
    """Collection of event summaries."""

    data: list[EventGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "EventsGQL":  # type: ignore[override]
        """Serializes query result to list of Sui objects.
        The in_data is a dictionary with 2 keys: 'cursor' and 'events'
        """

        in_data = in_data.pop("events")
        # Get cursor
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])  # type: ignore[attr-defined]
        dlist: list[EventGQL] = [
            EventGQL.from_query(i_obj) for i_obj in in_data["events"]  # type: ignore[misc]
        ]
        return EventsGQL(dlist, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TxBlockListGQL(PGQL_Type):
    """Checkpoint data representation."""

    data: list[str]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "TxBlockListGQL":  # type: ignore[override]
        """Serializes query result of tx blocks in checkpoint."""
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])  # type: ignore[attr-defined]
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
    def from_query(clz, in_data: dict) -> "CheckpointGQL":  # type: ignore[override]
        """Serializes query result of tx blocks in checkpoint."""
        in_data = in_data.pop("checkpoint", in_data)
        in_data["transaction_blocks"] = TxBlockListGQL.from_query(
            in_data["transaction_blocks"]
        )
        return CheckpointGQL.from_dict(in_data)  # type: ignore[attr-defined]

    @classmethod
    def from_last_checkpoint(clz, in_data: dict) -> "CheckpointGQL":
        """Serializes query result of tx blocks in checkpoint."""
        in_data = in_data.pop("checkpoints", None)
        in_data = in_data["nodes"][0]
        in_data["transaction_blocks"] = TxBlockListGQL.from_query(
            in_data["transaction_blocks"]
        )
        return CheckpointGQL.from_dict(in_data)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class CheckpointsGQL(PGQL_Type):
    """Collection of Checkpoint summaries."""

    data: list[CheckpointGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "CheckpointsGQL":  # type: ignore[override]
        """."""
        in_data = in_data.pop("checkpoints")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])  # type: ignore[attr-defined]
        ndata: list[CheckpointGQL] = [
            CheckpointGQL.from_query(i_cp) for i_cp in in_data["checkpoints"]
        ]
        return CheckpointsGQL(ndata, ncurs)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BalanceGQL(PGQL_Type):
    """Balance representation class."""

    coin_type: str
    address_balance: int
    coin_balance: int
    total_balance: int

    @classmethod
    def from_query(clz, in_data: dict) -> "BalanceGQL":  # type: ignore[override]
        """Serializes query result of balance.

        The in_data is a dictionary with nested dictionaries
        """
        # Flatten dictionary
        res_dict: dict = {}
        _fast_flat(in_data, res_dict)
        res_dict["addressBalance"] = int(res_dict["addressBalance"])
        res_dict["coinBalance"] = int(res_dict["coinBalance"])
        res_dict["totalBalance"] = int(res_dict["totalBalance"])
        return BalanceGQL.from_dict(res_dict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class AddressBalanceGQL(PGQL_Type):
    """Single coin type address balance."""

    balance: BalanceGQL

    @classmethod
    def from_query(clz, in_data: dict) -> "AddressBalanceGQL":  # type: ignore[override]
        """."""
        bal_ref: dict = {"balance": BalanceGQL.from_query(in_data.pop("address"))}
        return AddressBalanceGQL.from_dict(bal_ref)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class BalancesGQL(PGQL_Type):
    """Collection of balance objects."""

    owner_address: str
    data: list[BalanceGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "BalancesGQL":  # type: ignore[override]
        """Serializes query result to list of Sui objects.

        The in_data is a dictionary with 2 keys: 'cursor' and 'objects_data'
        """
        # Get result
        in_data = in_data["qres"] if "qres" in in_data else in_data
        # Get cursor
        owner = in_data.pop("owner_address")
        balances = in_data.pop("balances")
        ncurs: PagingCursor = PagingCursor.from_dict(balances["cursor"])  # type: ignore[attr-defined]
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
    def from_query(clz, in_data: dict) -> "SuiCoinMetadataGQL":  # type: ignore[override]
        """Serializes query result to Sui coin metadata object."""
        res_dict: dict = {}
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        return SuiCoinMetadataGQL.from_dict(res_dict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectContent:
    has_public_transfer: bool
    content: dict
    object_type: str

    # "as_object": {
    #     "content": {
    #         "id": "0x1407ced9cc7127d642abaf789f0b81c5a519832367fbd641bfe2e4fc8d48b3c3",
    #         "balance": {"value": "1247706815"},
    #     },
    #     "object_type_repr": {
    #         "object_type": "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"
    #     },
    # },
    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectContent":  # type: ignore[override]
        res_dict: dict = {}
        content = in_data["as_object"].pop("content")
        # Flatten dictionary
        _fast_flat(in_data, res_dict)
        res_dict["content"] = content
        return clz.from_dict(res_dict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectState:
    bcs: str
    version: int
    object_digest: str
    object_id: str
    owner: dict
    storage_rebate: str
    prior_transaction: dict

    as_move_content: Optional[ObjectContent] = None
    as_move_package: Optional[dict] = None

    def is_package(self) -> bool:
        return bool(self.as_move_package)

    def is_object(self) -> bool:
        return bool(self.as_move_content)

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectState":  # type: ignore[override]
        if obj_cont := in_data.get("as_move_content"):
            in_data["as_move_content"] = ObjectContent.from_query(obj_cont)
        return clz.from_dict(in_data)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectChange:
    address: str
    deleted: bool
    created: bool
    input_state: Optional[ObjectState]
    output_state: Optional[ObjectState]

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectChange":  # type: ignore[override]
        if ist := in_data.get("input_state"):
            in_data["input_state"] = ObjectState.from_query(ist)
        if ost := in_data.get("output_state"):
            in_data["output_state"] = ObjectState.from_query(ost)
        return clz.from_dict(in_data)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ObjectChanges:
    nodes: list[ObjectChange]

    @classmethod
    def from_query(clz, in_data: dict) -> "ObjectChanges":  # type: ignore[override]
        """."""
        in_data["nodes"] = [ObjectChange.from_query(x) for x in in_data["nodes"]]
        return clz.from_dict(in_data)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionResultGQL(PGQL_Type):
    """Transaction result representation class."""

    expiration: Union[dict, None]
    gas_input: dict
    effects: dict
    transaction_kind: str
    signatures: Optional[list[str]] = None
    digest: Optional[str] = ""
    sender: Optional[dict] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[TransactionResultGQL, NoopGQL]":  # type: ignore[override]
        """."""
        if in_data.get("transaction"):
            txblock = in_data.pop("transaction")
            txblock["transaction_kind"] = txblock.pop("kind")["tx_kind"]
            return TransactionResultGQL.from_dict(txblock)  # type: ignore[attr-defined]
        return NoopGQL.from_query()

    def object_changes(self) -> ObjectChanges:
        """Return data structured object changes."""
        return ObjectChanges.from_query(self.effects["objectChanges"])


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DryRunResultTransactionGQL(PGQL_Type):
    """Dry Run relevant Transaction details"""

    status: str

    gas_effects: dict
    balance_changes: dict
    object_changes: ObjectChanges
    events: Optional[dict] = None
    timestamp: Optional[str] = None
    execution_error: Optional[dict] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[DryRunResultTransactionGQL, NoopGQL]":  # type: ignore[override]
        """."""
        if tx_data := in_data.get("transactionBlock"):
            # tx_data["transaction_kind"] = tx_data.pop("kind")["tx_kind"]
            tx_data["objectChanges"] = ObjectChanges.from_query(
                tx_data["objectChanges"]
            )
            return clz.from_dict(tx_data)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class DryRunResultGQL(PGQL_Type):
    """DryRun result representation class."""

    transaction_block: DryRunResultTransactionGQL
    results: Optional[list[dict]] = None
    # error: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[DryRunResultGQL, NoopGQL]":  # type: ignore[override]
        """."""
        if in_data:
            in_data = in_data.get("dryRun")  # type: ignore[assignment]
            if in_data:
                # dr_err = in_data.pop("error")
                dr_res = in_data.pop("results")
                tblock = DryRunResultTransactionGQL.from_query(in_data)
                return DryRunResultGQL.from_dict(  # type: ignore[attr-defined]
                    {"results": dr_res, "transaction_block": tblock}
                )
        return NoopGQL.from_query()


#: Alias for DryRunResultGQL; use this with SimulateTransaction / SimulateTransactionKind.
SimulateResultGQL = DryRunResultGQL


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ExecutionResultGQL(PGQL_Type):
    """Execution result representation class."""

    status: str

    lamport_version: int
    digest: str
    bcs: str
    effects_bcs: str
    execution_error: Optional[dict] = None
    errors: Optional[list[str]] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[ExecutionResultGQL, NoopGQL]":  # type: ignore[override]
        """."""
        if in_data:
            in_data = in_data.get("executeTransaction")  # type: ignore[assignment]
            if in_data:
                ex_err = in_data["effects"].pop("execution_errors")
                fdict: dict = {}
                _fast_flat(in_data, fdict)
                fdict["execution_error"] = ex_err
                return ExecutionResultGQL.from_dict(fdict)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSummaryGQL(PGQL_Type):
    digest: str
    signatures: list[str]
    status: str
    timestamp: str
    tx_kind: str
    errors: Optional[Any] = dataclasses.field(default_factory=list)

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionSummaryGQL":  # type: ignore[override]
        """."""
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        return TransactionSummaryGQL.from_dict(fdict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class TransactionSummariesGQL(PGQL_Type):
    """Transaction list of digest representation class."""

    data: list[TransactionSummaryGQL]
    next_cursor: PagingCursor

    @classmethod
    def from_query(clz, in_data: dict) -> "TransactionSummariesGQL":  # type: ignore[override]
        """."""
        in_data = in_data.pop("transactions")
        ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])  # type: ignore[attr-defined]
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
class ReceivingInputGQL:
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
    typeArguments: Optional[list[dict]] = None


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

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[ProgrammableTransactionBlockGQL, NoopGQL]":  # type: ignore[override]
        ins_list: list = []
        cmd_list: list = []
        router = {
            "TransferObjectsCommand": TransactioTransferObjectslGQL,
            "SplitCoinsCommand": TransactionSplitCoinsGQL,
            "MergeCoinsCommand": TransactionMergeCoinsGQL,
            "PublishCommand": TransactionPublishGQL,
            "UpgradeCommand": TransactionUpgradeGQL,
            "MakeMoveVecCommand": TransactionMakeMoveVecGQL,
        }
        if in_data:
            for ins in in_data["inputs"]:
                match ins["input_typename"]:
                    case "OwnedOrImmutable":
                        in_dict = ins["object"]
                        in_dict["input_typename"] = ins["input_typename"]
                        ins_list.append(OwnedOrImmutableInputGQL.from_dict(in_dict))  # type: ignore[attr-defined]
                    case "Receiving":
                        in_dict = ins["object"]
                        in_dict["input_typename"] = ins["input_typename"]
                        ins_list.append(ReceivingInputGQL.from_dict(in_dict))  # type: ignore[attr-defined]
                    case "SharedInput":
                        ins_list.append(SharedObjectInputGQL.from_dict(ins))  # type: ignore[attr-defined]
                    case "Pure":
                        ins_list.append(PureInputGQL.from_dict(ins))  # type: ignore[attr-defined]
            for cmds in in_data["transactions"]:
                cmd_name = cmds["tx_typename"]
                match cmd_name:
                    case "MoveCallCommand":
                        mvc_dict = {
                            "package": cmds["function"]["module"]["package"]["address"],
                            "module": cmds["function"]["module"]["name"],
                            "function_name": cmds["function"]["name"],
                            "arguments": cmds["arguments"],
                            "tx_typename": cmd_name,
                        }
                        cmd_list.append(TransactionMoveCallGQL.from_dict(mvc_dict))  # type: ignore[attr-defined]
                    case _:
                        if c_clz := router.get(cmds["tx_typename"]):
                            cmd_list.append(c_clz.from_dict(cmds))  # type: ignore[attr-defined]
                        else:
                            raise ValueError(f"Not handling {cmd_name}")

            return clz(ins_list, cmd_list)

        return NoopGQL.from_query()


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
    def from_query(clz, in_data: dict) -> "Union[TransactionKindGQL, NoopGQL]":  # type: ignore[override]
        """."""
        tx_block = in_data.get("transaction") if in_data else None
        if tx_block:
            tx_type = tx_block["kind"].pop("tx_kind")
            tx_block["timestamp"] = tx_block.pop("effects")["timestamp"]
            tx_block["transaction_kind"] = tx_type
            match tx_type:
                case "ProgrammableTransaction":
                    tx_block["kind"] = ProgrammableTransactionBlockGQL.from_query(
                        {
                            "inputs": tx_block["kind"]["inputs"]["nodes"],
                            "transactions": tx_block["kind"]["commands"]["nodes"],
                        }
                    )
                case "GenesisTransaction" | "ConsensusCommitPrologueTransaction":
                    pass
                case _:
                    raise ValueError(f"{tx_type} not handled in data model.")
            return TransactionKindGQL.from_dict(tx_block)  # type: ignore[attr-defined]
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
    commission_rate: str  # type: ignore[no-redef]
    next_epoch_commission_rate: int

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorGQL":  # type: ignore[override]
        """."""
        return ValidatorGQL.from_dict(in_data)  # type: ignore[attr-defined]


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
    def from_query(clz, in_data: dict) -> "Union[ValidatorSetGQL, NoopGQL]":  # type: ignore[override]
        """."""
        if i_val := in_data.pop("activeValidators"):
            in_data["validators"] = [
                ValidatorGQL.from_query(v_obj) for v_obj in i_val["validators"]
            ]
            return ValidatorSetGQL.from_dict(in_data)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ReferenceGasPriceGQL(PGQL_Type):
    """ReferenceGasPriceGQL representation class."""

    reference_gas_price: str

    @classmethod
    def from_query(clz, in_data: dict) -> "ReferenceGasPriceGQL":  # type: ignore[override]
        in_data = in_data.pop("epoch", in_data)
        return ReferenceGasPriceGQL.from_dict(in_data)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class EpochGQL(PGQL_Type):
    """Epoch data representation class."""

    epoch_id: int
    start_timestamp: str
    end_timestamp: Optional[str] = None
    reference_gas_price: Optional[str] = None
    total_checkpoints: Optional[int] = None
    total_transactions: Optional[int] = None
    total_gas_fees: Optional[str] = None
    total_stake_rewards: Optional[str] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[EpochGQL, NoopGQL]":  # type: ignore[override]
        """Serializes query result to EpochGQL."""
        if in_data:
            in_data = in_data.pop("epoch", in_data)
            if in_data:
                return EpochGQL.from_dict(in_data)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PackageVersionGQL:
    """Single package version entry."""

    package_id: str
    version: int
    digest: Optional[str] = None


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class PackageVersionsGQL(PGQL_Type):
    """Collection of package versions."""

    versions: list[PackageVersionGQL]
    next_cursor: Optional[PagingCursor] = None

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[PackageVersionsGQL, NoopGQL]":  # type: ignore[override]
        """Serializes query result to PackageVersionsGQL."""
        if in_data:
            in_data = in_data.pop("packageVersions", in_data)
            if in_data:
                ncurs: PagingCursor = PagingCursor.from_dict(in_data["cursor"])  # type: ignore[attr-defined]
                versions: list[PackageVersionGQL] = [
                    PackageVersionGQL(
                        package_id=v["address"],
                        version=v["version"],
                        digest=v.get("digest"),
                    )
                    for v in in_data["versions"]
                ]
                return PackageVersionsGQL(versions=versions, next_cursor=ncurs)
        return NoopGQL.from_query()


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
    def from_query(clz, in_data: dict) -> "SystemStateSummaryGQL":  # type: ignore[override]
        in_data = in_data.pop("qres", in_data)
        rgp = {"referenceGasPrice": in_data.pop("referenceGasPrice")}
        in_data["referenceGasPrice"] = ReferenceGasPriceGQL.from_query(rgp)
        in_data["validatorSet"] = ValidatorSetGQL.from_query(in_data["validatorSet"])
        return SystemStateSummaryGQL.from_dict(in_data)  # type: ignore[attr-defined]


# Re-exported from sui_common for backwards compatibility.
# New code should import from pysui.sui.sui_common.sui_txn_types directly.
from pysui.sui.sui_common.sui_txn_types import TransactionConstraints


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

    def _value_to_type(self, v: Any) -> Any:
        """."""
        if v:
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                if v == "true" or v == "false":
                    return v
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
        self.transaction_constraints = TransactionConstraints.from_dict(cnst_dict)  # type: ignore[attr-defined]
        self.transaction_constraints.protocol_version = self.protocolVersion

        # Set appropriate features
        feat_dict: dict = {k.key: k.value for k in self.featureFlags}
        # Receive objects
        self.transaction_constraints.receive_objects = feat_dict.get(
            "receive_objects", False
        )
        # Use account balance for gas payments
        self.transaction_constraints.enable_address_balance_gas_payments = (
            feat_dict.get("enable_address_balance_gas_payments", False)
        )

    @classmethod
    def from_query(clz, in_data: dict) -> "ProtocolConfigGQL":  # type: ignore[override]
        return ProtocolConfigGQL.from_dict(in_data.pop("protocolConfigs"))  # type: ignore[attr-defined]


# ── OpenMoveType dataclasses — schema-faithful representation ─────────────────


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveScalarBodyGQL:
    """A primitive scalar type body: 'u8', 'bool', 'address', etc."""

    scalar_type: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveVectorBodyGQL:
    """A vector type body: { vector: body }."""

    inner: Union[OpenMoveScalarBodyGQL, "OpenMoveVectorBodyGQL", "OpenMoveDatatypeBodyGQL", "OpenMoveTypeParamBodyGQL"]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveDatatypeBodyGQL:
    """A named datatype body: { datatype: { package, module, type, typeParameters } }."""

    package: str
    module: str
    type_name: str
    type_parameters: list[Union[OpenMoveScalarBodyGQL, OpenMoveVectorBodyGQL, "OpenMoveDatatypeBodyGQL", "OpenMoveTypeParamBodyGQL"]]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveTypeParamBodyGQL:
    """A generic type parameter reference: { typeParameter: N }."""

    index: int


def _body_from_dict(raw: Any) -> Union[OpenMoveScalarBodyGQL, OpenMoveVectorBodyGQL, OpenMoveDatatypeBodyGQL, OpenMoveTypeParamBodyGQL]:
    """Recursively deserialize an OpenMoveTypeSignatureBody from raw JSON."""
    if isinstance(raw, str):
        return OpenMoveScalarBodyGQL(scalar_type=raw)
    if "vector" in raw:
        return OpenMoveVectorBodyGQL(inner=_body_from_dict(raw["vector"]))
    if "datatype" in raw:
        dt = raw["datatype"]
        return OpenMoveDatatypeBodyGQL(
            package=dt["package"],
            module=dt["module"],
            type_name=dt["type"],
            type_parameters=[_body_from_dict(p) for p in dt.get("typeParameters", [])],
        )
    if "typeParameter" in raw:
        return OpenMoveTypeParamBodyGQL(index=raw["typeParameter"])
    raise ValueError(f"Unrecognised OpenMoveTypeSignatureBody: {raw}")


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveTypeSignatureGQL:
    """Decoded OpenMoveTypeSignature scalar: { ref, body }."""

    ref: Optional[str]
    body: Union[OpenMoveScalarBodyGQL, OpenMoveVectorBodyGQL, OpenMoveDatatypeBodyGQL, OpenMoveTypeParamBodyGQL]

    @classmethod
    def from_query(cls, raw: dict) -> "OpenMoveTypeSignatureGQL":
        """Deserialize an OpenMoveTypeSignature scalar dict.

        :param raw: dict with optional ``ref`` ("&" or "&mut") and required ``body``
            (an OpenMoveTypeSignatureBody — scalar string, vector dict, datatype dict,
            or typeParameter dict).
        :returns: Fully constructed ``OpenMoveTypeSignatureGQL`` with decoded body variant.
        :raises KeyError: if ``body`` is absent.
        :raises ValueError: if ``body`` shape is not recognised.
        """
        return cls(ref=raw.get("ref"), body=_body_from_dict(raw["body"]))


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class OpenMoveTypeGQL:
    """OpenMoveType: a type with its recursive signature and display repr."""

    signature: OpenMoveTypeSignatureGQL
    repr: str

    @classmethod
    def from_query(cls, raw: dict) -> "OpenMoveTypeGQL":
        """Deserialize an OpenMoveType wire dict.

        :param raw: dict with keys ``signature`` (OpenMoveTypeSignature scalar dict)
            and ``repr`` (human-readable type string).
        :returns: Fully constructed ``OpenMoveTypeGQL`` with decoded signature and body.
        :raises KeyError: if ``signature`` is absent.
        :raises ValueError: if the signature body shape is not recognised.
        """
        return cls(
            signature=OpenMoveTypeSignatureGQL.from_query(raw["signature"]),
            repr=raw.get("repr", ""),
        )


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFieldGQL:
    """A named field in a Move struct or enum variant."""

    name: Optional[str]
    type_: Optional[OpenMoveTypeGQL]

    @classmethod
    def from_query(cls, raw: dict) -> "MoveFieldGQL":
        """Deserialize a MoveField wire dict.

        :param raw: dict with optional ``name`` (field name string) and optional
            ``type`` (OpenMoveType wire dict).
        :returns: ``MoveFieldGQL`` with name and decoded type signature, or ``None``
            for type if absent.
        :raises ValueError: if the type body shape is not recognised.
        """
        type_raw = raw.get("type")
        return cls(
            name=raw.get("name"),
            type_=OpenMoveTypeGQL.from_query(type_raw) if type_raw else None,
        )


# ── Move metadata dataclasses ─────────────────────────────────────────────────


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveEnumVariantGQL:
    """Sui MoveEnum variant representation."""

    variant_name: str
    fields: list[MoveFieldGQL]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveEnumGQL:
    """Sui MoveEnum representation."""

    enum_name: str
    abilities: list[str]
    variants: list[MoveEnumVariantGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[MoveEnumGQL, NoopGQL]":  # type: ignore[override]
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["variants"] = [
                MoveEnumVariantGQL(
                    variant_name=v["variant_name"],
                    fields=[MoveFieldGQL.from_query(f) for f in v.get("fields", [])],
                )
                for v in fdict.get("variants", [])
            ]
            return MoveEnumGQL.from_dict(fdict)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructureGQL:
    """Sui MoveStucture representation."""

    struct_name: str
    abilities: list[str]
    fields: list[MoveFieldGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[MoveStructureGQL, NoopGQL]":  # type: ignore[override]
        if in_data:
            in_data = in_data.get("object", in_data)
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["fields"] = [MoveFieldGQL.from_query(f) for f in fdict.get("fields", [])]
            return MoveStructureGQL.from_dict(fdict)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


class MoveDataTypeGQL:
    @classmethod
    def from_query(clz, in_data: dict) -> Union[MoveStructureGQL, MoveEnumGQL, NoopGQL]:  # type: ignore[override]
        """."""
        if in_data:
            dtype = in_data["object"]["asMovePackage"]["module"]
            if dtype.get("struct"):
                return MoveStructureGQL.from_query(in_data)
            dtype = dtype["datatype"]
            if dtype.get("asMoveStruct"):
                if dtype.get("asMoveEnum"):
                    dtype.pop("asMoveEnum")
                return MoveStructureGQL.from_query(in_data)
            else:
                if dtype.get("asMoveStruct"):
                    dtype.pop("asMoveStruct")
                return MoveEnumGQL.from_query(in_data)
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveStructuresGQL:
    """Sui collection of MoveStuctures."""

    structures: list[MoveStructureGQL]
    next_cursor: Optional[PagingCursor]

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[MoveStructuresGQL, NoopGQL]":  # type: ignore[override]
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
            return MoveStructuresGQL.from_dict(fdict)  # type: ignore[attr-defined]
            # return MoveStructuresGQL.from_dict(  # type: ignore[attr-defined]
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
        reftype = RefType.NO_REF
        if rstr:
            if rstr in ["&mut", "MUTABLE"]:
                reftype = RefType.MUT_REF
            elif rstr in ["&", "IMMUTABLE"]:
                reftype = RefType.REF
        return reftype


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveParameterArg:
    """."""

    type_index: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveTypeArg:
    """."""

    ref: RefType
    scalar_type: str

    @classmethod
    def from_str(cls, in_ref: str, in_type: str) -> "MoveTypeArg":
        """ "."""
        return cls(RefType.from_ref(in_ref), in_type)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveScalarArg:
    """."""

    ref: RefType
    scalar_type: str
    optional: Optional[bool] = False

    @classmethod
    def from_str(cls, in_ref: str, in_type: str) -> "MoveScalarArg":
        """ "."""
        return cls(RefType.from_ref(in_ref), in_type)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveAnyArg:
    """."""

    ref: RefType


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
    def from_body(cls, in_ref: Union[str, "RefType", None], in_type: dict) -> "MoveObjectRefArg":
        """."""
        ref_type: RefType = (
            in_ref if isinstance(in_ref, RefType) else RefType.from_ref(in_ref)  # type: ignore[arg-type]
        )
        if in_type["type"] == "String" or in_type["type"] == "ID":
            return MoveScalarArg.from_str(in_ref, in_type["type"])  # type: ignore[return-value, arg-type]
        inner_type = in_type.get("typeParameters")
        has_type = bool(inner_type)
        inner_list: list[Any] = []

        if has_type:
            inner_list = []
            for inner_t in inner_type:  # type: ignore[union-attr]
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
    vec_arg: Union["MoveVectorArg", MoveScalarArg, MoveObjectRefArg, MoveAnyArg]

    @classmethod
    def from_body(cls, in_ref: Union[str, "RefType", None], in_type: dict) -> "MoveVectorArg":
        """ "."""
        from_vec: dict = in_type["vector"]
        if not isinstance(from_vec, str):
            if ivec := from_vec.get("vector"):
                if isinstance(ivec, dict) and ivec.get("vector"):
                    return cls(
                        RefType.from_ref(in_ref), cls.from_body(in_ref, from_vec)  # type: ignore[arg-type]
                    )
                else:
                    from_vec = ivec
            else:
                key, value = next(iter(from_vec.items()))
                if key == "datatype":
                    return cls(
                        RefType.from_ref(in_ref),  # type: ignore[arg-type]
                        MoveObjectRefArg.from_body(None, value),
                    )
                elif (
                    len(from_vec) == 1
                    and key == "typeParameter"
                    and isinstance(value, int)
                ):
                    return cls(
                        RefType.from_ref(in_ref),  # type: ignore[arg-type]
                        MoveAnyArg(RefType.from_ref("")),
                    )
                else:
                    raise ValueError(f"Can't resolve {from_vec}")
        return cls(
            RefType.from_ref(in_ref),  # type: ignore[arg-type]
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
            MoveScalarArg,
            MoveObjectRefArg,
            MoveTypeArg,
            MoveVectorArg,
            MoveWitnessArg,
            MoveAnyArg,
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
    parameters: list[OpenMoveTypeGQL]
    returns: list[OpenMoveTypeGQL] = dataclasses.field(default_factory=list)

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[MoveFunctionGQL, NoopGQL]":  # type: ignore[override]
        if in_data.get("object") or in_data.get("function_name") or in_data.get("functionName"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            params = [OpenMoveTypeGQL.from_query(p) for p in fdict.get("parameters", [])]
            # Skip TxContext parameters at any position
            filtered_params = [
                p for p in params
                if not (
                    isinstance(p.signature.body, OpenMoveDatatypeBodyGQL)
                    and p.signature.body.type_name == "TxContext"
                )
            ]
            returns = [OpenMoveTypeGQL.from_query(r) for r in fdict.get("returns", [])]
            return MoveFunctionGQL(
                function_name=fdict.get("functionName", ""),
                is_entry=fdict.get("isEntry", False),
                visibility=fdict.get("visibility", ""),
                type_parameters=fdict.get("typeParameters", []),
                parameters=filtered_params,
                returns=returns,
            )
        return NoopGQL.from_query()

    def arg_summary(self) -> list["OpenMoveTypeGQL"]:
        """Deprecated — use parameters directly."""
        import warnings
        warnings.warn(
            "arg_summary() is deprecated; use parameters (list[OpenMoveTypeGQL]) directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.parameters


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveFunctionsGQL:
    """Sui MoveFunction representation."""

    functions: list[MoveFunctionGQL]
    next_cursor: Optional[PagingCursor]

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[MoveFunctionsGQL, NoopGQL]":  # type: ignore[override]
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
                return MoveFunctionsGQL.from_dict(fdict)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class MoveModuleGQL:
    """Sui MoveModule representation."""

    module_name: str
    module_structures: Union[MoveStructuresGQL, list]
    module_functions: Union[MoveFunctionsGQL, list]

    @classmethod
    def from_query(clz, in_data: dict) -> "Union[MoveModuleGQL, NoopGQL]":  # type: ignore[override]
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

            return MoveModuleGQL.from_dict(fdict)  # type: ignore[attr-defined]
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
    def from_query(clz, in_data: dict) -> "Union[MovePackageGQL, NoopGQL]":  # type: ignore[override]
        if in_data.get("object"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["next_cursor"] = PagingCursor(
                fdict.pop("hasNextPage"), fdict.pop("endCursor")
            )
            fdict["modules"] = [MoveModuleGQL.from_query(x) for x in fdict["nodes"]]
            fdict.pop("nodes")
            return MovePackageGQL.from_dict(fdict)  # type: ignore[attr-defined]
        return NoopGQL.from_query()


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorExchangeRateGQL:
    identifier: str
    pool_token_amount: str | None = None
    sui_amount: str | None = None

    @classmethod
    def from_query(clz, name: str, in_data: dict) -> "ValidatorExchangeRateGQL":  # type: ignore[override]
        idict = {"identifier": name}
        if in_data:
            idict = idict | in_data["value"]["json"]
        return clz.from_dict(idict)  # type: ignore[attr-defined]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorExchangeRatesGQL:
    """Sui Validator Exchange Rates List"""

    exchange_rates: list[ValidatorExchangeRateGQL]

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorExchangeRatesGQL":  # type: ignore[override]
        in_data = in_data.pop("address")
        ex_list: list[ValidatorExchangeRateGQL] = []
        for key, value in in_data.items():
            ex_list.append(ValidatorExchangeRateGQL.from_query(key, value))
        return clz(ex_list)


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclasses.dataclass
class ValidatorFullGQL:
    """Sui ValidatorSet representation."""

    validator_name: str
    validator_address: str
    description: str
    exchangeRateTableAddress: str
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
    nextEpochCommissionRate: int
    atRisk: int

    @classmethod
    def from_query(clz, in_data: dict) -> "ValidatorFullGQL":  # type: ignore[override]
        fdict: dict = {}
        _fast_flat(in_data, fdict)
        return ValidatorFullGQL.from_dict(fdict)  # type: ignore[attr-defined]


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
    def from_query(clz, in_data: dict) -> "ValidatorSetsGQL":  # type: ignore[override]
        fdict: dict = {}
        cursor: PagingCursor = PagingCursor.from_dict(  # type: ignore[attr-defined]
            in_data["epoch"]["validatorSet"]["activeValidators"].pop("cursor")
        )
        _fast_flat(in_data, fdict)
        fdict["validators"] = [
            ValidatorFullGQL.from_query(x) for x in fdict["validators"]
        ]
        fdict["next_cursor"] = cursor

        return ValidatorSetsGQL.from_dict(fdict)  # type: ignore[attr-defined]


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
    def from_query(clz, in_data: dict) -> "Union[DynamicFieldsGQL, NoopGQL]":  # type: ignore[override]
        if in_data.get("object"):
            fdict: dict = {}
            _fast_flat(in_data, fdict)
            fdict["next_cursor"] = PagingCursor(
                fdict.pop("hasNextPage"), fdict.pop("endCursor")
            )
            return DynamicFieldsGQL.from_dict(fdict)  # type: ignore[attr-defined]
        return NoopGQL.from_query()
