#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-#

"""QueryNode generators."""

from typing import Any, Optional, Callable, Union
import base64
import datetime
import warnings
from deprecated.sphinx import versionadded, versionchanged, deprecated
from gql import gql, GraphQLRequest
from gql.dsl import (
    DSLQuery,
    dsl_gql,
    DSLSchema,
    DSLMetaField,
    DSLInlineFragment,
    DSLMutation,
)

import betterproto2
from pysui.sui.sui_pgql.pgql_clients import PGQL_QueryNode, PGQL_NoOp
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_fragments as frag
from pysui.sui.sui_pgql.pgql_validators import TypeValidator
from pysui.sui.sui_bcs.bcs import TransactionKind
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_grpc.pgrpc_requests as _rn
import pysui.sui.sui_bcs.sui_system_bcs as sui_system_bcs
from pysui.sui.sui_types.scalars import SuiU64


class GetCoinMetaData(PGQL_QueryNode):
    """GetCoinMetaData returns meta data for a specific `coin_type`."""

    def __init__(self, *, coin_type: Optional[str] = "0x2::sui::SUI") -> None:
        """QueryNode initializer.

        :param coin_type: The specific coin type string, defaults to "0x2::sui::SUI"
        :type coin_type: str, optional
        """
        self.coin_type = coin_type

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build the GraphQLRequest."""
        qres = schema.Query.coinMetadata(coinType=self.coin_type).select(
            schema.CoinMetadata.decimals,
            schema.CoinMetadata.name,
            schema.CoinMetadata.symbol,
            schema.CoinMetadata.description,
            schema.CoinMetadata.iconUrl,
            schema.CoinMetadata.supply,
            schema.CoinMetadata.address,
        )
        return dsl_gql(DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinMetadataGQL]:
        """Return the serialization to SuiCoinMetadataGQL function."""
        return pgql_type.SuiCoinMetadataGQL.from_query


class GetAddressCoinBalance(PGQL_QueryNode):
    """GetAddressCoinBalance Returns an addresses balance for specific coin type.

    The resulting total balance is the sum of the `address` balance and any coin balances of `coin_type`.
    """

    def __init__(self, *, owner: str, coin_type: Optional[str] = "0x2::sui::SUI"):
        """__init__ _summary_

        :param owner: Address holding balances
        :type owner: str
        :param coin_type: _description_, defaults to "0x2::sui::SUI"
        :type coin_type: _type_, optional
        """
        self.owner = owner
        self.coin_type = coin_type

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        _QUERY = """
            {
            address(address:"OWNER") {
                balance(coinType: "COIN_TYPE") {
                            coinType {
                                coinType:repr
                            }
                            addressBalance
                            coinBalance
                            totalBalance
                        }
                    } 
            }           
        """
        _QUERY = _QUERY.replace("OWNER", self.owner).replace(
            "COIN_TYPE", self.coin_type or ""
        )
        return gql(_QUERY)

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.AddressBalanceGQL]:
        """Return the serializer to BalancesGQL function."""
        return pgql_type.AddressBalanceGQL.from_query


@deprecated(
    version="0.97.0",
    reason="Use new GetAddressCoinBalances query instead supporting Sui address balances.",
)
class GetAllCoinBalances(PGQL_QueryNode):
    """GetAllCoins Returns the total coin balances, for all coin types, for owner.

    This is different from legacy Builder as only a list of coin type summaries are returned.
    You take the coin_type from any list member and call...
    """

    def __init__(
        self, *, owner: str, next_page: Optional[pgql_type.PagingCursor] = None
    ):
        """QueryNode initializer.

        :param owner: the owner's Sui address
        :type owner: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.owner = owner
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.address(address=self.owner).alias("qres")
        balance_connection = schema.Address.balances
        if self.next_page:
            balance_connection(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor()

        balance_connection.select(
            cursor=schema.BalanceConnection.pageInfo.select(pg_cursor.fragment(schema)),
            type_balances=schema.BalanceConnection.nodes.select(
                schema.Balance.totalBalance,
                schema.Balance.coinType.select(coin_type=schema.MoveType.repr),
            ),
        )
        qres.select(owner_address=schema.Address.address, balances=balance_connection)

        return dsl_gql(pg_cursor.fragment(schema), DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.BalancesGQL]:
        """Return the serializer to BalancesGQL function."""
        return pgql_type.BalancesGQL.from_query


class GetAddressCoinBalances(PGQL_QueryNode):
    """GetAddressCoinBlances Returns the address and total coin balance, for all coin types of for owner.

    This is different from legacy Builder as only a list of coin type summaries are returned.
    """

    def __init__(
        self, *, owner: str, next_page: Optional[pgql_type.PagingCursor] = None
    ):
        """QueryNode initializer.

        :param owner: the owner's Sui address
        :type owner: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.owner = owner
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.address(address=self.owner).alias("qres")
        balance_connection = schema.Address.balances
        if self.next_page:
            balance_connection(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor()

        balance_connection.select(
            cursor=schema.BalanceConnection.pageInfo.select(pg_cursor.fragment(schema)),
            type_balances=schema.BalanceConnection.nodes.select(
                schema.Balance.addressBalance,
                schema.Balance.coinBalance,
                schema.Balance.totalBalance,
                schema.Balance.coinType.select(coin_type=schema.MoveType.repr),
            ),
        )
        qres.select(owner_address=schema.Address.address, balances=balance_connection)

        return dsl_gql(pg_cursor.fragment(schema), DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.BalancesGQL]:
        """Return the serializer to BalancesGQL function."""
        return pgql_type.BalancesGQL.from_query


@versionchanged(version="0.93.0", reason="owner argument now ignored")
class GetCoinSummary(PGQL_QueryNode):
    """GetCoinSummary Returns balance,digest and version"""

    def __init__(self, *, owner: str | None = None, coin_id: str):
        """Set up."""
        # self.owner = owner
        self.coin_id = coin_id

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""

        _QUERY = """
            {
            object(address:"COIN_ID") {
                coin_object_id:address
                object_digest:digest
                version
                asMoveObject {
                    contents {
                        json
                        }
                    }
                
                }            
            }
        """
        _QUERY = _QUERY.replace("COIN_ID", self.coin_id)
        return gql(_QUERY)

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinObjectSummaryGQL]:
        """Return summary serialized to data object."""
        return pgql_type.SuiCoinObjectSummaryGQL.from_query


class GetCoinSummarySC(GetCoinSummary):
    """SC variant: encode_fn maps GQL object response to GetObjectResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetObjectResponse]:
        """Return deserializer producing GetObjectResponse from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.GetObjectResponse:
            obj = in_data.get("object", {})
            flat: dict = {}
            pgql_type._fast_flat(obj, flat)
            balance = None
            if "asMoveObject" in obj and "contents" in obj["asMoveObject"]:
                contents = obj["asMoveObject"]["contents"].get("json")
                if contents and isinstance(contents, dict):
                    balance = contents.get("balance")
            return sui_prot.GetObjectResponse(
                object=sui_prot.Object(
                    object_id=flat.get("address"),
                    version=int(flat.get("version", 0)),
                    digest=flat.get("digest"),
                    balance=int(balance) if balance else None,
                )
            )

        return _encode


class GetCoins(PGQL_QueryNode):
    """GetCoins Returns all Coin objects of a specific type for owner."""

    def __init__(
        self,
        *,
        owner: str,
        coin_type: Optional[str] = "0x2::coin::Coin<0x2::sui::SUI>",
        next_page: Optional[pgql_type.PagingCursor] = None,
    ):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param coin_type: The fully qualified coin type to use in filtering, defaults to "0x2::coin::Coin<0x2::sui::SUI>"
        :type coin_type: str, optional
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.owner = owner
        self.coin_type = coin_type
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.address(address=self.owner).alias("qres")
        coin_connection = schema.Address.objects(filter={"type": self.coin_type}).alias(
            "coins"
        )
        if self.next_page:
            coin_connection(after=self.next_page.endCursor)

        std_coin = frag.StandardCoin()
        pg_cursor = frag.PageCursor()

        coin_connection.select(std_coin.fragment(schema))
        qres.select(coin_connection)
        return dsl_gql(
            std_coin.fragment(schema),
            pg_cursor.fragment(schema),
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinObjectsGQL]:
        """Return the serializer to SuiCoinObjectsGQL function."""
        return pgql_type.SuiCoinObjectsGQL.from_query


@versionadded(version="0.99.0", reason="Convenience alias for GetCoins with SUI coin type.")
class GetGas(GetCoins):
    """GetGas Returns all SUI gas coin objects owned by an address.

    Convenience subclass of GetCoins with coin_type fixed to ``0x2::coin::Coin<0x2::sui::SUI>``.
    """

    def __init__(
        self,
        *,
        owner: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """__init__ Initialize GetGas object.

        :param owner: Owner's Sui address
        :type owner: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        super().__init__(
            owner=owner,
            coin_type="0x2::coin::Coin<0x2::sui::SUI>",
            next_page=next_page,
        )


class GetLatestSuiSystemState(PGQL_QueryNode):
    """GetLatestSuiSystemState return the latest known SUI system state."""

    def __init__(self) -> None:
        """QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest using BCS system-state path."""
        qres = schema.Query.epoch.select(
            schema.Epoch.systemState.select(
                schema.MoveValue.bcs
            )
        )
        return dsl_gql(DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SystemStateSummaryGQL]:
        """Return the serializer to SystemStateSummaryGQL function."""
        return pgql_type.SystemStateSummaryGQL.from_query


class GetObject(PGQL_QueryNode):
    """Returns a specific object's data."""

    def __init__(self, *, object_id: str):
        """QueryNode initializer.

        :param object_id: The object id hex string with 0x prefix
        :type object_id: str
        """
        self.object_id = TypeValidator.check_object_id(object_id)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest"""
        std_object = frag.StandardObject()
        base_object = frag.BaseObject()
        return dsl_gql(
            std_object.fragment(schema),
            base_object.fragment(schema),
            DSLQuery(
                object=schema.Query.object(address=self.object_id).select(
                    std_object.fragment(schema),
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadGQL]:
        """Return the serializer to ObjectReadGQL function."""
        return pgql_type.ObjectReadGQL.from_query  # type: ignore[return-value]


class GetObjectsForType(PGQL_QueryNode):
    """GetObjectsForType Returnns all objects of a specific type."""

    def __init__(
        self,
        *,
        object_type: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ):
        """QueryNode initializer

        :param object_type: The fully qualified type (i.e. `"0x2::coin::Coin<0x2::sui::SUI>"`)
        :type object_type: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.object_type = object_type
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        std_object = frag.StandardObject().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)

        if self.next_page:
            obj_connection = schema.Query.objects(
                filter={"type": self.object_type}, after=self.next_page.endCursor
            )
        else:
            obj_connection = schema.Query.objects(
                filter={"type": self.object_type}
            ).select(
                cursor=schema.ObjectConnection.pageInfo.select(pg_cursor),
                objects_data=schema.ObjectConnection.nodes.select(std_object),
            )

        return dsl_gql(pg_cursor, std_object, base_object, DSLQuery(obj_connection))

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadsGQL]:
        """Return the serializer to ObjectReadsGQL function."""
        return pgql_type.ObjectReadsGQL.from_query


class GetObjectsForTypeSC(GetObjectsForType):
    """SC variant: encode_fn maps GQL objects response to ListOwnedObjectsResponse proto."""

    def __init__(
        self,
        *,
        owner: str,
        object_type: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ):
        """QueryNode initializer with owner filter.

        :param owner: Owner's Sui address
        :type owner: str
        :param object_type: The fully qualified type (i.e. `"0x2::coin::Coin<0x2::sui::SUI>"`)
        :type object_type: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.owner = owner
        self.object_type = object_type
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest with owner and type filters."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        std_object = frag.StandardObject().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)

        if self.next_page:
            obj_connection = schema.Query.objects(
                filter={"owner": self.owner, "type": self.object_type},
                after=self.next_page.endCursor,
            )
        else:
            obj_connection = schema.Query.objects(
                filter={"owner": self.owner, "type": self.object_type}
            ).select(
                cursor=schema.ObjectConnection.pageInfo.select(pg_cursor),
                objects_data=schema.ObjectConnection.nodes.select(std_object),
            )

        return dsl_gql(pg_cursor, std_object, base_object, DSLQuery(obj_connection))

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL objects dict."""

        def _encode(in_data: dict) -> sui_prot.ListOwnedObjectsResponse:
            qres = in_data.get("qres", in_data)
            cursor = qres.get("pageInfo", {})
            objects_data = qres.get("objects_data", [])
            objects: list[sui_prot.Object] = []
            for obj in objects_data:
                flat: dict = {}
                pgql_type._fast_flat(obj, flat)
                objects.append(
                    sui_prot.Object(
                        object_id=flat.get("address"),
                        version=int(flat.get("version", 0)),
                        digest=flat.get("digest"),
                        object_type=flat.get("objectType"),
                    )
                )
            end_cursor: str | None = cursor.get("endCursor")
            next_page_token: bytes | None = (
                end_cursor.encode()
                if cursor.get("hasNextPage") and end_cursor
                else None
            )
            return sui_prot.ListOwnedObjectsResponse(
                objects=objects, next_page_token=next_page_token
            )

        return _encode


@versionchanged(
    version="0.85.0", reason="Added status and previous transaction digest."
)
class GetObjectContent(PGQL_QueryNode):
    """Returns a specific object's content BCS string."""

    def __init__(self, *, object_id: str):
        """QueryNode initializer.

        :param object_id: The object id hex string with 0x prefix
        :type object_id: str
        """
        self.object_id = TypeValidator.check_object_id(object_id)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest"""
        return dsl_gql(
            DSLQuery(
                object=schema.Query.object(address=self.object_id).select(
                    schema.Object.address,
                    schema.Object.asMoveObject.select(
                        schema.MoveObject.contents.select(
                            schema.MoveValue.bcs,
                        )
                    ),
                    prior_transaction=schema.Object.previousTransaction.select(
                        previous_transaction_digest=schema.Transaction.digest
                    ),
                ),
            )
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectContentBCS]:
        """Return the serializer to ObjectReadGQL function."""
        return pgql_type.ObjectContentBCS.from_query


class GetObjectContentSC(GetObjectContent):
    """SC variant: encode_fn maps GQL object content response to GetObjectResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetObjectResponse]:
        """Return deserializer producing GetObjectResponse from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.GetObjectResponse:
            obj = in_data.get("object", {})
            flat: dict = {}
            pgql_type._fast_flat(obj, flat)
            bcs_content = None
            if "asMoveObject" in obj and "contents" in obj["asMoveObject"]:
                bcs_bytes = obj["asMoveObject"]["contents"].get("bcs")
                if bcs_bytes:
                    bcs_content = sui_prot.Bcs(value=bytes.fromhex(bcs_bytes[2:]))
            return sui_prot.GetObjectResponse(
                object=sui_prot.Object(
                    object_id=flat.get("address"),
                    version=int(flat.get("version", 0)),
                    digest=flat.get("digest"),
                    previous_transaction=flat.get("previousTransaction"),
                    contents=bcs_content,
                )
            )

        return _encode


@versionchanged(
    version="0.85.0", reason="Added status and previous transaction digest."
)
class GetMultipleObjectContent(PGQL_QueryNode):
    """Returns a specific object's content BCS string."""

    def __init__(
        self,
        *,
        object_ids: list[str],
    ):
        """QueryNode initializer.

        :param object_id: The object id hex string with 0x prefix
        :type object_id: str
        """
        self.object_ids = [TypeValidator.check_object_id(x) for x in object_ids]

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest"""
        obj_ids = [{"address": cid} for cid in self.object_ids]
        object_content = schema.Query.multiGetObjects(keys=obj_ids).select(
            schema.Object.address,
            schema.Object.asMoveObject.select(
                schema.MoveObject.contents.select(
                    schema.MoveValue.bcs,
                )
            ),
            prior_transaction=schema.Object.previousTransaction.select(
                previous_transaction_digest=schema.Transaction.digest
            ),
        )
        return dsl_gql(
            DSLQuery(object_content),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectsContentBCS]:
        """Return the serializer to ObjectsContentBCS function."""
        return pgql_type.ObjectsContentBCS.from_query  # type: ignore[return-value]


class GetMultipleObjectContentSC(GetMultipleObjectContent):
    """SC variant: encode_fn maps GQL objects content response to BatchGetObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.BatchGetObjectsResponse]:
        """Return deserializer producing BatchGetObjectsResponse from GQL objects dict."""

        def _encode(in_data: dict) -> sui_prot.BatchGetObjectsResponse:
            objects_data = in_data if isinstance(in_data, list) else [in_data]
            objects: list[sui_prot.Object] = []
            for obj in objects_data:
                flat: dict = {}
                pgql_type._fast_flat(obj, flat)
                bcs_content = None
                if "asMoveObject" in obj and "contents" in obj["asMoveObject"]:
                    bcs_bytes = obj["asMoveObject"]["contents"].get("bcs")
                    if bcs_bytes:
                        bcs_content = sui_prot.Bcs(value=bytes.fromhex(bcs_bytes[2:]))
                objects.append(
                    sui_prot.Object(
                        object_id=flat.get("address"),
                        version=int(flat.get("version", 0)),
                        digest=flat.get("digest"),
                        previous_transaction=flat.get("previousTransaction"),
                        contents=bcs_content,
                    )
                )
            return sui_prot.BatchGetObjectsResponse(objects=objects)

        return _encode


class GetObjectsOwnedByAddress(PGQL_QueryNode):
    """Returns data for all objects by owner."""

    def __init__(
        self, *, owner: str, next_page: Optional[pgql_type.PagingCursor] = None
    ):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.owner = owner
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.objects(filter={"owner": self.owner})
        if self.next_page:
            qres(after=self.next_page.endCursor)

        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)
        qres.select(
            cursor=schema.ObjectConnection.pageInfo.select(pg_cursor),
            objects_data=schema.ObjectConnection.nodes.select(std_object),
        )

        return dsl_gql(
            pg_cursor,
            std_object,
            base_object,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadsGQL]:
        """Return the serializer to ObjectReadsGQL function."""
        return pgql_type.ObjectReadsGQL.from_query


@versionchanged(
    version="0.82.0", reason="Fixes https://github.com/FrankC01/pysui/issues/292"
)
@versionchanged(
    version="0.84.0", reason="Reference https://github.com/FrankC01/pysui/issues/297"
)
@versionchanged(version="0.91.0", reason="Paging no longer supported")
class GetMultipleGasObjects(PGQL_QueryNode):
    """Return basic Sui gas represnetation for each coin_id string."""

    def __init__(
        self,
        *,
        coin_object_ids: list[str],
    ):
        """QueryNode initializer.

        :param coin_object_ids: list of object ids to fetch
        :type coin_object_ids: list[str]
        :param next_page: Ignored
        :type next_page: Ignored
        """
        self.coin_ids: list[str] = TypeValidator.check_object_ids(coin_object_ids)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""

        std_coin = frag.BaseSuiObjectForCoin().fragment(schema)
        coin_ids = [{"address": cid} for cid in self.coin_ids]
        qres = schema.Query.multiGetObjects(keys=coin_ids)
        qres.select(std_coin)

        return dsl_gql(
            std_coin,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinFromObjectsGQL]:
        """Return the serializer to SuiCoinFromObjectsGQL function."""
        return pgql_type.SuiCoinFromObjectsGQL.from_query  # type: ignore[return-value]


@versionchanged(version="0.91.0", reason="Paging no longer supported")
class GetMultipleObjects(PGQL_QueryNode):
    """Returns object data for list of object ids."""

    def __init__(
        self,
        *,
        object_ids: list[str],
    ):
        """QueryNode initializer.

        :param object_ids: List of Sui object_ids hex string prefixed with 0x
        :type object_ids: list[str]
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.object_ids = TypeValidator.check_object_ids(object_ids)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        obj_ids = [{"address": cid} for cid in self.object_ids]
        qres = schema.Query.multiGetObjects(keys=obj_ids)

        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        qres.select(std_object)

        return dsl_gql(
            std_object,
            base_object,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadsGQL]:
        """Return the serializer to ObjectReadsGQL function."""
        return pgql_type.ObjectReadsGQL.from_query


class _GetMultipleObjectsResolvedSC(GetMultipleObjects):
    """Internal GQL variant: encode_fn normalizes multiGetObjects → list[ObjectCacheEntry].

    Used by _FetchObjectsForResolution. Not for external use.
    """

    @staticmethod
    def encode_fn() -> Callable[[dict], list]:
        """Return deserializer producing list[ObjectCacheEntry] from multiGetObjects response."""
        from pysui.sui.sui_common.executors.cache import ObjectCacheEntry as _OCE

        def _encode(in_data: dict) -> list:
            reads = pgql_type.ObjectReadsGQL.from_query(in_data)
            entries: list[_OCE] = []
            for obj in reads.data:
                if not isinstance(obj, pgql_type.ObjectReadGQL):
                    continue
                ow = obj.object_owner
                owner_str = None
                shared_v = None
                if isinstance(ow, pgql_type.SuiObjectOwnedAddress):
                    owner_str = ow.address_id
                elif isinstance(ow, pgql_type.SuiObjectOwnedShared):
                    shared_v = str(ow.initial_version)
                entries.append(_OCE(
                    objectId=obj.object_id,
                    version=str(obj.version),
                    digest=obj.object_digest,
                    owner=owner_str,
                    initialSharedVersion=shared_v,
                ))
            return entries

        return _encode


class GetPastObject(PGQL_QueryNode):
    """Returns a specific objects version data."""

    def __init__(self, *, object_id: str, version: int):
        """QueryNode initializer

        :param object_id: The Sui object_id hex string with 0x prefix
        :type object_id: str
        :param version: The version of the object to fetch.
        :type version: int
        """
        self.object_id = TypeValidator.check_object_id(object_id)
        self.version = version

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)

        return dsl_gql(
            std_object,
            base_object,
            DSLQuery(
                object=schema.Query.object(
                    address=self.object_id, version=self.version
                ).select(
                    std_object,
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadGQL]:
        """Return the serializer to ObjectReadGQL function."""
        return pgql_type.ObjectReadGQL.from_query  # type: ignore[return-value]


@versionadded(version="0.76.0", reason="Sui 1.40.0 introduced")
@versionchanged(
    version="0.91.0",
    reason="GraphQL beta changed object_id to address in dictionary argument",
)
class GetMultipleVersionedObjects(PGQL_QueryNode):
    """GetMultipleVersionedObjects When executed, return the object information for a specified version.

    Note there is no software-level guarantee/SLA that objects with past versions can be retrieved by this API,
    even if the object and version exists/existed. The result may vary across nodes depending on their pruning
    policies.
    """

    def __init__(self, *, for_versions: list[dict[str, int]]):
        """QueryNode initializer to fetch past object information for a list of object keys.

        Where each ``dict`` entry must have the following keys::

            {
                "address": str,  # Object id
                "version": int   # Version to fetch
            }

        :param for_versions: The list of object and version dictionaries
        :type for_versions: list[dict]
        """

        self.version_list = for_versions

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)

        return dsl_gql(
            std_object,
            base_object,
            # pg_cursor,
            DSLQuery(
                schema.Query.multiGetObjects(keys=self.version_list).select(
                    std_object,
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectVersionReadsGQL]:
        """Return the serializer to ObjectReadsGQL function."""
        return pgql_type.ObjectVersionReadsGQL.from_query


@versionchanged(
    version="0.91.0", reason="Name MoveValue dropped 'data', using json instead"
)
class GetDynamicFields(PGQL_QueryNode):
    """GetDynamicFields when executed, returns the list of dynamic field objects owned by an object."""

    def __init__(
        self,
        *,
        object_id: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """QueryNode initializer to featch dynamic fields.

        :param object_id: The object id that holds dynamic fields
        :type object_id: str
        :param next_page: A paging directive, defaults to None
        :type next_page: Optional[pgql_type.PagingCursor], optional
        """
        self.object_id = object_id
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Return a query for dynamic fields."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp
        qres = schema.Query.object(address=self.object_id)
        qres = qres.select(
            schema.Object.address.alias("parent_object_id"), schema.Object.version
        )
        dfield_connection = schema.Object.dynamicFields
        if self.next_page:
            dfield_connection(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor().fragment(schema)
        dfield_connection.select(
            cursor=schema.DynamicFieldConnection.pageInfo.select(pg_cursor),
            dynamic_fields=schema.DynamicFieldConnection.nodes.select(
                schema.DynamicField.name.select(
                    name_type=schema.MoveValue.type.select(
                        name_layout=schema.MoveType.layout,
                    ),
                    name_data=schema.MoveValue.json,
                ),
                field_kind=DSLMetaField("__typename"),
                field_data=schema.DynamicField.value.select(
                    DSLInlineFragment()
                    .on(schema.MoveObject)
                    .select(
                        schema.MoveObject.address,
                        schema.MoveObject.version,
                        schema.MoveObject.digest,
                        data_kind=DSLMetaField("__typename"),
                    ),
                    DSLInlineFragment()
                    .on(schema.MoveValue)
                    .select(
                        object_type=schema.MoveValue.type.select(
                            schema.MoveType.layout
                        ),
                        data_kind=DSLMetaField("__typename"),
                    ),
                ),
            ),
        )
        return dsl_gql(
            pg_cursor,
            DSLQuery(qres.select(dfield_connection)),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.DynamicFieldsGQL]:
        """Return the serializer to DynamicFieldsGQL function."""
        return pgql_type.DynamicFieldsGQL.from_query  # type: ignore[return-value]


@versionchanged(version="0.91.0", reason="Event filter parms changed in GraphQL Beta")
class GetEvents(PGQL_QueryNode):
    """GetEvents When executed, return list of events for the filter choice."""

    def __init__(
        self,
        *,
        event_filter: dict,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """QueryNode initializer to query chain events of type defined by event_filter.

        Choose one key/value pair from the following options::

            {"afterCheckpoint": int}
            {"atCheckpoint": int}
            {"beforeCheckpoint": int}
            {"sender": "SOME_SUI_ACCOUNT"}
            {"module": "FULLY_QUALIFIED_MODULE"}
            {"type": "FULLY_QUALIFIED_EVENT_TYPE"}

        Example::

            {"type": "0x3::validator::StakingRequestEvent"}

        :param event_filter: Filter key/values aligned to Sui GraphQL schema's EventFilter
        :type event_filter: dict
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """

        self.event_filter = event_filter
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        pg_cursor = frag.PageCursor()
        std_event = frag.StandardEvent()
        qres = schema.Query.events(filter=self.event_filter)
        if self.next_page:
            qres(after=self.next_page.endCursor)

        qres.select(
            cursor=schema.EventConnection.pageInfo.select(pg_cursor.fragment(schema)),
            events=schema.EventConnection.nodes.select(std_event.fragment(schema)),
        )
        return dsl_gql(
            pg_cursor.fragment(schema), std_event.fragment(schema), DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.EventsGQL]:
        """Return the serializer to EventsGQL function."""
        return pgql_type.EventsGQL.from_query


@versionchanged(version="0.91.0", reason="GraphQL Beta changes to fields.")
class GetTx(PGQL_QueryNode):
    """GetTx When executed, return the transaction response object."""

    def __init__(self, *, digest: str) -> None:
        """QueryNode initializer to fetch a transaction by digest id.

        :param digest: The transaction digest to fetch
        :type digest: str
        """
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Builds the GQL GraphQLRequest

        :return: The transaction query GraphQLRequest for specific digest
        :rtype: GraphQLRequest
        """
        std_txn = frag.StandardTransaction().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.transaction(digest=self.digest)
        qres.select(std_txn)
        return dsl_gql(
            std_txn,
            tx_effects,
            base_object,
            std_object,
            gas_cost,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.TransactionResultGQL], None]:
        """Return the serializer to TransactionResultGQL function."""
        return pgql_type.TransactionResultGQL.from_query  # type: ignore[return-value]


class GetMultipleTx(PGQL_QueryNode):
    """GetTxs returns multiple transaction summaries and is controlled by filters and paging."""

    def __init__(
        self, *, next_page: Optional[pgql_type.PagingCursor] = None, **qfilter
    ) -> None:
        """QueryNode initializer to fetch multiple transactions by filter parameters.

        :param next_page: Pagination curosr, defaults to None
        :type next_page: Optional[pgql_type.PagingCursor], optional
        :param qfilter: 0 or more TransactionBlockFilter key/value to apply to criteria
        :rtype qfilter: dict
        """
        self.next_page = next_page
        self.qfilter = qfilter

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Builds the GQL GraphQLRequest

        :return: The transactions query GraphQLRequest
        :rtype: GraphQLRequest
        """
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.transactions(filter=self.qfilter)
        if self.next_page:
            qres(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor().fragment(schema)
        qres.select(
            cursor=schema.TransactionConnection.pageInfo.select(pg_cursor),
            tx_blocks=schema.TransactionConnection.nodes.select(
                schema.Transaction.digest,
                schema.Transaction.kind.select(
                    DSLMetaField("__typename").alias("tx_kind")
                ),
                schema.Transaction.signatures.select(
                    schema.UserSignature.signatureBytes
                ),
                schema.Transaction.effects.select(
                    schema.TransactionEffects.status,
                    schema.TransactionEffects.timestamp,
                    schema.TransactionEffects.executionError.select(
                        schema.ExecutionError.abortCode,
                        schema.ExecutionError.sourceLineNumber,
                        schema.ExecutionError.instructionOffset,
                        schema.ExecutionError.identifier,
                        schema.ExecutionError.constant,
                        schema.ExecutionError.message,
                    ),
                ),
            ),
        )
        return dsl_gql(
            pg_cursor,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.TransactionSummariesGQL], None]:
        """Return the serializer to TransactionSummariesGQL function."""
        return pgql_type.TransactionSummariesGQL.from_query


class GetFilteredTx(PGQL_QueryNode):
    """GetTxs returns all transactions with TransactionBlockFilter set and is controlled by paging."""

    def __init__(
        self, *, tx_filter: dict, next_page: Optional[pgql_type.PagingCursor] = None
    ) -> None:
        """QueryNode initializer.

        :param tx_filter: TransactionBlockFilter dict
        :type tx_filter: dict
        :param next_page: _description_, defaults to None
        :type next_page: Optional[pgql_type.PagingCursor], optional
        """
        self.next_page = next_page
        self.filter = tx_filter

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Builds the GQL GraphQLRequest

        :return: The transactions query GraphQLRequest
        :rtype: GraphQLRequest
        """
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.transactions(filter=self.filter)
        if self.next_page:
            qres(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor().fragment(schema)

        qres.select(
            cursor=schema.TransactionConnection.pageInfo.select(pg_cursor),
            tx_blocks=schema.TransactionConnection.nodes.select(
                schema.Transaction.digest,
                schema.Transaction.signatures.select(
                    schema.UserSignature.signatureBytes
                ),
                schema.Transaction.kind.select(tx_kind=DSLMetaField("__typename")),
                schema.Transaction.effects.select(
                    schema.TransactionEffects.status,
                    schema.TransactionEffects.timestamp,
                    schema.TransactionEffects.executionError.select(
                        schema.ExecutionError.abortCode,
                        schema.ExecutionError.sourceLineNumber,
                        schema.ExecutionError.instructionOffset,
                        schema.ExecutionError.identifier,
                        schema.ExecutionError.constant,
                        schema.ExecutionError.message,
                    ),
                ),
            ),
        )
        return dsl_gql(
            pg_cursor,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.TransactionSummariesGQL], None]:
        """Return the serializer to TransactionSummariesGQL function."""
        return pgql_type.TransactionSummariesGQL.from_query


class GetMultipleTransactions(PGQL_QueryNode):
    """GetMultipleTransactions returns multiple transactions by digest list."""

    def __init__(self, *, digests: list[str]) -> None:
        """QueryNode initializer to fetch multiple transactions by digests.

        :param digests: List of transaction digests to fetch
        :type digests: list[str]
        """
        self.digests = digests

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Builds the GQL GraphQLRequest

        :return: The transactions query GraphQLRequest for specific digests
        :rtype: GraphQLRequest
        """
        std_txn = frag.StandardTransaction().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.multiGetTransactions(keys=self.digests)
        qres.select(std_txn)
        return dsl_gql(
            std_txn,
            tx_effects,
            base_object,
            std_object,
            gas_cost,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.TransactionSummariesGQL]:
        """Return the serializer to TransactionSummariesGQL function."""
        return pgql_type.TransactionSummariesGQL.from_query


class GetTxKind(PGQL_QueryNode):
    """Gets details of Transaction kind."""

    def __init__(self, digest: str):
        """QueryNode initializer."""
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Builds the GQL GraphQLRequest

        :return: The transaction query GraphQLRequest for specific digest
        :rtype: GraphQLRequest
        """
        tx_kind = frag.StandardTransactionKind().fragment(schema)
        prg_kind = frag.ProgrammableTxKind().fragment(schema)
        ccp_kind = frag.ConsensusCommitPrologueKind().fragment(schema)
        qres = schema.Query.transaction(digest=self.digest)
        qres.select(
            # qres=schema.Query.transaction(digest=self.digest).select(
            schema.Transaction.digest,
            schema.Transaction.effects.select(schema.TransactionEffects.timestamp),
            tx_kind,
            # )
        )
        return dsl_gql(
            prg_kind,
            tx_kind,
            ccp_kind,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.TransactionKindGQL], None]:
        """Return the serializer to TransactionKindGQL function."""
        return pgql_type.TransactionKindGQL.from_query  # type: ignore[return-value]


class GetTransactionSC(GetTx):
    """SC variant: maps GQL transaction query to ExecutedTransaction proto."""

    def __init__(self, *, digest: str) -> None:
        """QueryNode initializer."""
        super().__init__(digest=digest)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build transaction query with metadata + BCS fields. Kind decoded from BCS."""
        tx_effects = frag.StandardTxEffects().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.transaction(digest=self.digest)
        qres.select(
            schema.Transaction.digest,
            schema.Transaction.signatures.select(schema.UserSignature.signatureBytes),
            schema.Transaction.sender.select(
                submitter_address=schema.Address.address
            ),
            schema.Transaction.expiration.select(schema.Epoch.epochId),
            schema.Transaction.gasInput.select(
                transaction_budget=schema.GasInput.gasBudget,
                price=schema.GasInput.gasPrice,
                sponsor=schema.GasInput.gasSponsor.select(
                    sponsor_address=schema.Address.address
                ),
                sponsor_pay_with=schema.GasInput.gasPayment.select(
                    gas_objects=schema.ObjectConnection.nodes.select(base_object)
                ),
            ),
            schema.Transaction.effects.select(
                tx_effects,
                schema.TransactionEffects.effectsBcs,
            ),
            schema.Transaction.transactionBcs,
        )
        return dsl_gql(
            tx_effects,
            base_object,
            std_object,
            gas_cost,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], "sui_prot.ExecutedTransaction | None"]:
        """Return encoder mapping GQL transaction dict to ExecutedTransaction proto."""

        def _encode(in_data: dict) -> "sui_prot.ExecutedTransaction | None":
            return _encode_executed_tx(in_data.get("transaction"))

        return _encode


class GetTransactionsSC(GetMultipleTransactions):
    """SC variant: maps GQL multi-transaction query to list[ExecutedTransaction | None]."""

    def __init__(self, *, digests: list[str]) -> None:
        """QueryNode initializer."""
        super().__init__(digests=digests)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build multi-transaction query with metadata + BCS fields. Kind decoded from BCS."""
        tx_effects = frag.StandardTxEffects().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.multiGetTransactions(keys=self.digests)
        qres.select(
            schema.Transaction.digest,
            schema.Transaction.signatures.select(schema.UserSignature.signatureBytes),
            schema.Transaction.sender.select(
                submitter_address=schema.Address.address
            ),
            schema.Transaction.expiration.select(schema.Epoch.epochId),
            schema.Transaction.gasInput.select(
                transaction_budget=schema.GasInput.gasBudget,
                price=schema.GasInput.gasPrice,
                sponsor=schema.GasInput.gasSponsor.select(
                    sponsor_address=schema.Address.address
                ),
                sponsor_pay_with=schema.GasInput.gasPayment.select(
                    gas_objects=schema.ObjectConnection.nodes.select(base_object)
                ),
            ),
            schema.Transaction.effects.select(
                tx_effects,
                schema.TransactionEffects.effectsBcs,
            ),
            schema.Transaction.transactionBcs,
        )
        return dsl_gql(
            tx_effects,
            base_object,
            std_object,
            gas_cost,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], "list[sui_prot.ExecutedTransaction | None]"]:
        """Return encoder mapping GQL multi-transaction dict to list of ExecutedTransaction protos."""

        def _encode(in_data: dict) -> "list[sui_prot.ExecutedTransaction | None]":
            tx_list = in_data.get("multiGetTransactions") or []
            return [_encode_executed_tx(tx) for tx in tx_list]

        return _encode


class GetTransactionKindSC(GetTxKind):
    """SC variant: maps GQL transaction kind query to TransactionKind proto."""

    def __init__(self, digest: str) -> None:
        """QueryNode initializer."""
        super().__init__(digest=digest)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Minimal kind query: fetch only __typename to stay under the 300-node limit."""
        qres = schema.Query.transaction(digest=self.digest).alias("transaction")
        qres.select(
            schema.Transaction.kind.select(
                tx_kind=DSLMetaField("__typename"),
            )
        )
        return dsl_gql(DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], "sui_prot.TransactionKind | None"]:
        """Return encoder mapping GQL transaction kind dict to TransactionKind proto."""

        def _encode(in_data: dict) -> "sui_prot.TransactionKind | None":
            tx_block = in_data.get("transaction")
            if not tx_block:
                return None
            kind_dict = tx_block.get("kind") or {}
            return _encode_tx_kind(kind_dict)

        return _encode


class GetDelegatedStakes(PGQL_QueryNode):
    """GetDelegatedStakes return all [StakedSui] coins for owner."""

    def __init__(self, owner: str, next_page: Optional[pgql_type.PagingCursor] = None):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param next_page: _description_, defaults to None
        :type next_page: Optional[pgql_type.PagingCursor], optional
        """
        self.owner = owner
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        if self.next_page:
            qres = schema.Query.objects(
                after=self.next_page.endCursor,
                filter={"owner": self.owner, "type": "0x3::staking_pool::StakedSui"},
            )
        else:
            qres = schema.Query.objects(
                filter={"owner": self.owner, "type": "0x3::staking_pool::StakedSui"}
            )
        # Build fragment
        pg_cursor = frag.PageCursor().fragment(schema)
        bs_coin = frag.BaseSuiObjectForCoin().fragment(schema)
        qres.select(
            cursor=schema.ObjectConnection.pageInfo.select(pg_cursor),
            staked_coin=schema.ObjectConnection.nodes.select(bs_coin),
        )
        return dsl_gql(pg_cursor, bs_coin, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.SuiStakedCoinsGQL], None]:
        """Return the serializer to SuiStakedCoinsGQL function."""
        return pgql_type.SuiStakedCoinsGQL.from_query  # type: ignore[return-value]


class GetBasicCurrentEpochInfo(PGQL_QueryNode):
    """GetBasicCurrentEpochInfo minimal current Epoch information."""

    def __init__(self):
        """."""

    def as_document_node(self, schema):
        """Build GraphQL DSL request."""
        _QUERY = """
            {  
            epoch {
                epochId
                referenceGasPrice
                startTimestamp
                endTimestamp
            }
            }            
        """
        return gql(_QUERY)

    @staticmethod
    def encode_fn() -> (
        Union[Callable[[dict], pgql_type.BasicCurrentEpochInfoGQL], None]
    ):
        """Return the serializer to SuiStakedCoinsGQL function."""
        return pgql_type.BasicCurrentEpochInfoGQL.from_query  # type: ignore[return-value]


@versionadded(version="0.99.0", reason="Full epoch query by ID or current epoch.")
class GetEpoch(PGQL_QueryNode):
    """GetEpoch Returns epoch information by epoch ID, or the current epoch if no ID is given."""

    def __init__(self, *, epoch_id: Optional[int] = None) -> None:
        """__init__ Initialize GetEpoch object.

        :param epoch_id: The epoch sequence number to fetch; omit or pass None for the current epoch
        :type epoch_id: Optional[int]
        """
        self.epoch_id = epoch_id

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        qres = schema.Query.epoch
        if self.epoch_id is not None:
            qres(epochId=self.epoch_id)
        qres.select(
            schema.Epoch.epochId,
            schema.Epoch.startTimestamp,
            schema.Epoch.endTimestamp,
            schema.Epoch.referenceGasPrice,
            schema.Epoch.totalCheckpoints,
            schema.Epoch.totalTransactions,
            schema.Epoch.totalGasFees,
            schema.Epoch.totalStakeRewards,
        )
        return dsl_gql(DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.EpochGQL], None]:
        """Return the serialization function for EpochGQL."""
        return pgql_type.EpochGQL.from_query  # type: ignore[return-value]


class GetLatestCheckpointSequence(PGQL_QueryNode):
    """GetLatestCheckpointSequence return the sequence number of the latest checkpoint that has been executed."""

    def __init__(self):
        """__init__ QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        std_checkpoint = frag.StandardCheckpoint().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)
        qres = schema.Query.checkpoints(last=1).select(
            schema.CheckpointConnection.nodes.select(std_checkpoint)
        )
        return dsl_gql(pg_cursor, std_checkpoint, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.CheckpointGQL], None]:
        """Return the serializer to CheckpointGQL function."""
        return pgql_type.CheckpointGQL.from_last_checkpoint


class GetCheckpointBySequence(PGQL_QueryNode):
    """GetCheckpoint return a checkpoint for cp_id."""

    def __init__(self, *, sequence_number: int):
        """__init__ QueryNode initializer.

        :param sequence_number: Checkpoint sequence number
        :type cp_seq: int
        """
        self.sequence_number = sequence_number

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        std_checkpoint = frag.StandardCheckpoint()
        pg_cursor = frag.PageCursor()
        qres = schema.Query.checkpoint(sequenceNumber=self.sequence_number).select(
            std_checkpoint.fragment(schema)
        )
        return dsl_gql(
            pg_cursor.fragment(schema), std_checkpoint.fragment(schema), DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.CheckpointGQL], None]:
        """Return the serializer to CheckpointGQL function."""
        return pgql_type.CheckpointGQL.from_query


class GetCheckpoints(PGQL_QueryNode):
    """GetCheckpoints return paginated list of checkpoints."""

    def __init__(self, *, next_page: Optional[pgql_type.PagingCursor] = None):
        """QueryNode initializer."""
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.checkpoints
        if self.next_page:
            qres(after=self.next_page.endCursor)

        std_checkpoint = frag.StandardCheckpoint()
        pg_cursor = frag.PageCursor()
        qres.select(
            cursor=schema.CheckpointConnection.pageInfo.select(
                pg_cursor.fragment(schema)
            ),
            checkpoints=schema.CheckpointConnection.nodes.select(
                std_checkpoint.fragment(schema)
            ),
        )
        return dsl_gql(
            pg_cursor.fragment(schema), std_checkpoint.fragment(schema), DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.CheckpointsGQL], None]:
        """Return the serializer to CheckpointsGQL function."""
        return pgql_type.CheckpointsGQL.from_query


class GetProtocolConfig(PGQL_QueryNode):
    """Return the protocol config table for the given version number or current."""

    def __init__(self, *, version: Optional[int] = None):
        """QueryNode initializer

        :param version: The protocol version to retreive, defaults to None (current)
        :type version: Optional[int]
        """
        self.version = version

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        std_prot_cfg = frag.StandardProtocolConfig().fragment(schema)
        if self.version is not None:
            qres = schema.Query.protocolConfigs(version=self.version).select(std_prot_cfg)
        else:
            qres = schema.Query.protocolConfigs().select(std_prot_cfg)
        return dsl_gql(std_prot_cfg, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ProtocolConfigGQL], None]:
        """Return the serialization function for ProtocolConfig."""
        return pgql_type.ProtocolConfigGQL.from_query


class GetProtocolConfigSC(GetProtocolConfig):
    """SC variant: encode_fn maps GQL protocol config response to ProtocolConfig proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ProtocolConfig]:
        """Return deserializer producing ProtocolConfig from GQL protocolConfigs dict."""

        def _encode(in_data: dict) -> sui_prot.ProtocolConfig:
            prot_cfg = in_data.get("protocolConfigs", {})
            feature_flags: dict[str, bool] = {}
            attributes: dict[str, str] = {}

            if "featureFlags" in prot_cfg:
                for flag in prot_cfg["featureFlags"]:
                    if isinstance(flag, dict) and "key" in flag and "value" in flag:
                        feature_flags[flag["key"]] = flag["value"]

            if "configs" in prot_cfg:
                for cfg in prot_cfg["configs"]:
                    if isinstance(cfg, dict) and "key" in cfg and "value" in cfg:
                        attributes[cfg["key"]] = str(cfg["value"])

            return sui_prot.ProtocolConfig(
                protocol_version=int(prot_cfg.get("protocolVersion", 0)),
                feature_flags=feature_flags,
                attributes=attributes,
            )

        return _encode


class GetReferenceGasPrice(PGQL_QueryNode):
    """GetReferenceGasPrice return the reference gas price for the network."""

    def __init__(self):
        """QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        return dsl_gql(
            DSLQuery(schema.Query.epoch.select(schema.Epoch.referenceGasPrice))
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ReferenceGasPriceGQL], None]:
        """Return the serialization function for ReferenceGasPrice."""
        return pgql_type.ReferenceGasPriceGQL.from_query


# TODO: Need object rep
# Renamed from Builder NameServiceAddress
class GetNameServiceAddress(PGQL_QueryNode):
    """Return the resolved name service name for a Sui address."""

    def __init__(self, *, name: str):
        """__init__ QueryNode initializer."""
        self.name = name

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        return dsl_gql(
            DSLQuery(
                schema.Query.suinsName(address=self.name).select(
                    schema.Address.defaultSuinsName
                )
            )
        )


# TODO: Need object rep
# Renamed from Builder NameServiceName
class GetNameServiceNames(PGQL_QueryNode):
    """Return the default Suins Name given and address."""

    def __init__(
        self,
        *,
        owner: str,
    ):
        """QueryNode initializer."""
        self.owner = owner

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        return dsl_gql(
            DSLQuery(
                schema.Query.address(address=self.owner).select(
                    primary_ns=schema.Address.defaultSuinsName,
                    additional_ns=schema.Address.suinsRegistrations.select(
                        schema.SuinsRegistrationConnection.nodes.select(
                            schema.SuinsRegistration.defaultSuinsName
                        )
                    ),
                )
            )
        )


class GetCurrentValidators(PGQL_QueryNode):
    """Return the set of validators from the current Epoch."""

    def __init__(self, next_page: pgql_type.PagingCursor | None = None):
        """QueryNode initializer."""
        self.pager = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest using BCS validator content path with paging."""
        if self.pager and not self.pager.hasNextPage:
            return PGQL_NoOp
        pg_cursor = frag.PageCursor().fragment(schema)
        if self.pager:
            active_vals = schema.ValidatorSet.activeValidators(after=self.pager.endCursor)
        else:
            active_vals = schema.ValidatorSet.activeValidators
        qres = schema.Query.epoch.select(
            schema.Epoch.validatorSet.select(
                active_vals.select(
                    schema.ValidatorConnection.pageInfo.select(pg_cursor).alias("cursor"),
                    schema.ValidatorConnection.nodes.select(
                        schema.Validator.contents.select(
                            schema.MoveValue.bcs
                        )
                    ),
                )
            )
        )
        return dsl_gql(pg_cursor, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ValidatorSetsGQL], None]:
        """Return the serialization function for ValidatorSetsGQL."""
        return pgql_type.ValidatorSetsGQL.from_query


class GetValidatorExchangeRates(PGQL_QueryNode):
    """Returns the exchange rate dynamic fields by Epoch (base64 BCS u64 encoded)."""

    def __init__(self, *, validator_exchange_address: str, epoch_ids: list[int]):
        """QueryNode initializer."""
        self.exchange_address = validator_exchange_address
        self.epoch_ids = epoch_ids

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        if not self.epoch_ids or not isinstance(self.epoch_ids[0], int):
            raise ValueError(
                f"Expected list of ints for epoch_ids found {self.epoch_ids}"
            )
        qres = schema.Query.address(address=self.exchange_address)
        for eint in self.epoch_ids:
            name = base64.b64encode(SuiU64(eint).to_bytes()).decode()
            tag = "EPOCH_" + str(eint)
            qres.select(
                schema.Address.dynamicField(name={"bcs": name, "type": "u64"})
                .select(
                    schema.DynamicField.value.select(
                        DSLInlineFragment()
                        .on(schema.MoveValue)
                        .select(schema.MoveValue.json)
                    )
                )
                .alias(tag)
            )
        return dsl_gql(DSLQuery(qres))

    @staticmethod
    def encode_fn() -> (
        Union[Callable[[dict], pgql_type.ValidatorExchangeRatesGQL], None]
    ):
        """Return the serialization function for ValidatorExchangeRatesGQL."""
        return pgql_type.ValidatorExchangeRatesGQL.from_query


class GetStructure(PGQL_QueryNode):
    """GetStructure When executed, returns a module's structure representation."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        structure_name: str,
    ) -> None:
        """QueryNode initializer.

        :param package: object_id of package to query
        :type package: str
        :param module_name: Name of module from package containing the structure_name to fetch
        :type module_name: str
        :param structure_name: Name of structure to fetch
        :type structure_name: str
        """
        self.package = package
        self.module = module_name
        self.struct = structure_name

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        struc = frag.MoveStructure()

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(
                    schema.MoveModule.struct(name=self.struct).select(
                        struc.fragment(schema)
                    )
                )
            )
        )
        return dsl_gql(struc.fragment(schema), DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveDataTypeGQL], None]:
        """Return the serialization function for MoveDataType."""
        return pgql_type.MoveDataTypeGQL.from_query  # type: ignore[return-value]


class GetMoveDataType(PGQL_QueryNode):
    """GetMoveDataType When executed, returns a module's structure or enum representation."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        data_type_name: str,
    ) -> None:
        """QueryNode initializer.

        :param package: object_id of package to query
        :type package: str
        :param module_name: Name of module from package containing the structure_name to fetch
        :type module_name: str
        :param data_type_name: Name of structure or enum to fetch
        :type data_type_name: str
        """
        self.package = package
        self.module = module_name
        self.data_type_name = data_type_name

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        struc = frag.MoveStructure().fragment(schema)
        enum = frag.MoveEnum().fragment(schema)

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(
                    schema.MoveModule.datatype(name=self.data_type_name).select(
                        schema.MoveDatatype.asMoveStruct.select(struc),
                        schema.MoveDatatype.asMoveEnum.select(enum),
                    )
                )
            )
        )
        return dsl_gql(struc, enum, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveDataTypeGQL], None]:
        """Return the serialization function for MoveDataType."""
        return pgql_type.MoveDataTypeGQL.from_query  # type: ignore[return-value]


class GetStructures(PGQL_QueryNode):
    """GetStructures When executed, returns all of a module's structures."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """QueryNode initializer.

        :param package: object_id of package to query
        :type package: str
        :param module_name: Name of module from package containing structures to fetch
        :type module_name: str
        """
        self.package = package
        self.module = module_name
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp
        elif self.next_page:
            struct_q = schema.MoveModule.structs(after=self.next_page.endCursor)
        else:
            struct_q = schema.MoveModule.structs

        struc = frag.MoveStructure().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(
                    struct_q.select(
                        schema.MoveStructConnection.pageInfo.select(pg_cursor).alias(
                            "cursor"
                        ),
                        schema.MoveStructConnection.nodes.select(struc),
                    )
                )
            )
        )
        return dsl_gql(struc, pg_cursor, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveStructuresGQL], None]:
        """Return the serialization function for ReferenceGasPrice."""
        return pgql_type.MoveStructuresGQL.from_query  # type: ignore[return-value]


class GetFunction(PGQL_QueryNode):
    """GetFunction When executed, returns a module's function information."""

    def __init__(self, *, package: str, module_name: str, function_name: str) -> None:
        """QueryNode initializer.

        :param package: object_id of package to query
        :type package: str
        :param module_name: Name of module from package containing the function to fetch
        :type module_name: str
        :param function_name: Name of function in the module to fetch
        :type module_name: str
        """
        self.package = package
        self.module = module_name
        self.function = function_name

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        func = frag.MoveFunction().fragment(schema)

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(
                    schema.MoveModule.function(name=self.function).select(func)
                )
            )
        )
        return dsl_gql(func, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveFunctionGQL], None]:
        """Return the serialization function for ReferenceGasPrice."""
        return pgql_type.MoveFunctionGQL.from_query  # type: ignore[return-value]


class GetFunctions(PGQL_QueryNode):
    """GetFunctions When executed, returns all module's functions information."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """QueryNode initializer.

        :param package: object_id of package to query
        :type package: str
        :param module_name: Name of module from package containing the function to fetch
        :type module_name: str
        """
        self.package = package
        self.module = module_name
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp
        elif self.next_page:
            func_q = schema.MoveModule.functions(after=self.next_page.endCursor)
        else:
            func_q = schema.MoveModule.functions

        func = frag.MoveFunction().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)
        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(
                    func_q.select(
                        schema.MoveFunctionConnection.pageInfo.select(pg_cursor).alias(
                            "cursor"
                        ),
                        schema.MoveFunctionConnection.nodes.select(func),
                    )
                )
            )
        )
        return dsl_gql(func, pg_cursor, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveFunctionsGQL], None]:
        """Return the serialization function for ReferenceGasPrice."""
        return pgql_type.MoveFunctionsGQL.from_query  # type: ignore[return-value]


class GetModule(PGQL_QueryNode):
    """GetModule When executed, returns the structural representation of a module.

    Includes general Module informationn as well as structure and function definitions.
    """

    def __init__(self, *, package: str, module_name: str) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module_name: Name of module from package to fetch
        :type module_name: SuiString
        """
        self.package = package
        self.module = module_name

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        func = frag.MoveFunction().fragment(schema)
        struc = frag.MoveStructure().fragment(schema)
        mod = frag.MoveModule().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(mod)
            )
        )
        return dsl_gql(
            pg_cursor,
            func,
            struc,
            mod,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveModuleGQL], None]:
        """Return the serialization MoveModule."""
        return pgql_type.MoveModuleGQL.from_query  # type: ignore[return-value]


class GetPackage(PGQL_QueryNode):
    """GetPackage When executed, return structured representations of the package."""

    def __init__(
        self, *, package: str, next_page: Optional[pgql_type.PagingCursor] = None
    ) -> None:
        """__init__ Initialize GetPackage object."""
        self.package = package
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp
        elif self.next_page:
            mod_q = schema.MovePackage.modules(after=self.next_page.endCursor)
        else:
            mod_q = schema.MovePackage.modules
        pg_cursor = frag.PageCursor().fragment(schema)
        func = frag.MoveFunction().fragment(schema)
        struc = frag.MoveStructure().fragment(schema)
        mod = frag.MoveModule().fragment(schema)

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.address.alias("package_id"),
                schema.MovePackage.version.alias("package_version"),
                mod_q.select(
                    schema.MoveModuleConnection.pageInfo.select(pg_cursor).alias(
                        "cursor"
                    ),
                    schema.MoveModuleConnection.nodes.select(mod),
                ),
            )
        )
        return dsl_gql(
            pg_cursor,
            func,
            struc,
            mod,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.MovePackageGQL], None]:
        """Return the serialization MovePackage."""
        return pgql_type.MovePackageGQL.from_query  # type: ignore[return-value]


@versionadded(version="0.99.0", reason="List all versions of a Move package by address.")
class GetPackageVersions(PGQL_QueryNode):
    """GetPackageVersions Returns all versions of a Move package sharing the same original ID."""

    def __init__(
        self,
        *,
        package_address: str,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """__init__ Initialize GetPackageVersions object.

        :param package_address: The storage address of any version of the package
        :type package_address: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.package_address = package_address
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        pg_cursor = frag.PageCursor()
        qres = schema.Query.packageVersions(address=self.package_address)
        if self.next_page:
            qres(after=self.next_page.endCursor)
        qres.select(
            cursor=schema.MovePackageConnection.pageInfo.select(
                pg_cursor.fragment(schema)
            ),
            versions=schema.MovePackageConnection.nodes.select(
                schema.MovePackage.address,
                schema.MovePackage.version,
                schema.MovePackage.digest,
            ),
        )
        return dsl_gql(pg_cursor.fragment(schema), DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.PackageVersionsGQL], None]:
        """Return the serialization function for PackageVersionsGQL."""
        return pgql_type.PackageVersionsGQL.from_query  # type: ignore[return-value]


@versionchanged(
    version="0.91.0", reason="tx_bytestr arg now requires bcs.TransactionKind"
)
@versionchanged(version="0.92.0", reason="Sui GraphQL requires sender set in tx_meta.")
@versionchanged(version="0.93.0", reason="tx_bytestr arg changed to tx_kind.")
@versionchanged(version="0.95.0", reason="Enabled ``skip_checks`` and ``do_gas_selection``")
class DryRunTransactionKind(PGQL_QueryNode):
    """DryRunTransactionKind query node."""

    def __init__(
        self,
        *,
        tx_kind: TransactionKind,
        tx_meta: dict,
        skip_checks: Optional[bool] = True,
        do_gas_selection: Optional[bool] = False,
    ) -> None:
        """__init__ Initialize DryRunTransactionKind object.

        BREAKING CHANGE: ``tx_meta`` expects a dictionary with one or more of the following keys::

            {
                "sender": str,            # Sui address of the sender (REQUIRED)
                "epoch_expiration": int,  # Epoch after which the tx won't be signed
                # NOT IMPLEMENTED YET (ignored):
                "gasPrice": int,          # Gas price (defaults to reference gas price)
                "gasObjects": [{"address": str, "version": int, "digest": str}],
                "gasBudget": int,         # Defaults to max gas budget
                "gasSponsor": str,        # Sponsor address, defaults to sender
            }

        """
        warnings.warn(
            "DryRunTransactionKind is deprecated; use SimulateTransactionKind instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        assert isinstance(tx_kind, TransactionKind)
        self.tx_data: TransactionKind = tx_kind
        self.transaction: sui_prot.Transaction = None
        self.tx_meta = tx_meta
        self.tx_skipchecks = skip_checks
        self.tx_do_gas_selection = do_gas_selection

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""

        prgrm_txn = self.tx_data.value
        inputs: list[sui_prot.Input] = []
        cmds: list[sui_prot.Command] = []
        trx_exp = None
        for input in prgrm_txn.Inputs:
            if input.enum_name == "Pure":
                inputs.append(
                    sui_prot.Input(
                        kind=sui_prot.InputInputKind.PURE, pure=bytes(input.value)
                    )
                )
            elif input.enum_name == "Object":
                oarg = input.value
                inputs.append(oarg.value.to_grpc_input(oarg.enum_name))
            elif input.enum_name == "FundsWithdrawal":
                inputs.append(input.value.to_grpc_input())

        for cmd in prgrm_txn.Command:
            cmds.append(cmd.value.to_grpc_command())
        self.transaction = sui_prot.Transaction(
            kind=sui_prot.TransactionKind(
                programmable_transaction=sui_prot.ProgrammableTransaction(
                    inputs=inputs, commands=cmds
                )
            ),
            expiration=trx_exp,
        )
        if self.tx_meta and (is_sender := self.tx_meta.get("sender")):
            self.transaction.sender = is_sender
            if txn_expires_after := self.tx_meta.get("epoch_expiration"):
                trx_exp = sui_prot.TransactionExpiration(
                    kind=sui_prot.TransactionExpirationTransactionExpirationKind.EPOCH,
                    epoch=txn_expires_after,
                )
                self.transaction.expiration = txn_expires_after
        else:
            raise ValueError("Requires 'sender' set in tx_meta dict")

        base_obj = frag.BaseObject().fragment(schema)
        standard_obj = frag.StandardObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)

        qres = (
            schema.Query.simulateTransaction(
                transaction=self.transaction.to_dict(casing=betterproto2.Casing.SNAKE),
                checksEnabled=self.tx_skipchecks,
                doGasSelection=self.tx_do_gas_selection,
            )
            .alias("dryRun")
            .select(
                # schema.SimulationResult.error,
                results=schema.SimulationResult.outputs.select(
                    schema.CommandResult.returnValues.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.type.select(schema.MoveType.repr),
                            schema.MoveValue.bcs,
                        ),
                    )
                ),
                transactionBlock=schema.SimulationResult.effects.select(tx_effects),
            )
        )
        return dsl_gql(
            base_obj,
            standard_obj,
            gas_cost,
            tx_effects,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.DryRunResultGQL], None]:
        """Return the serialization MovePackage."""
        return pgql_type.DryRunResultGQL.from_query  # type: ignore[return-value]


@versionchanged(version="0.95.0", reason="Enabled ``skip_checks`` and ``do_gas_selection``")
class DryRunTransaction(PGQL_QueryNode):
    """DryRunTransaction query node."""

    def __init__(
        self,
        *,
        tx_bytestr: bytes | str,
        skip_checks: Optional[bool] = True,
        do_gas_selection: Optional[bool] = False,
    ) -> None:
        """__init__ Initialize the dry run query.

        :param tx_bytestr: Either the serialized bytes of a bcs TransactionData or base64 string of same
        :type tx_bytestr: bytes | str
        """
        warnings.warn(
            "DryRunTransaction is deprecated; use SimulateTransaction instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.tx_data = tx_bytestr
        transaction = (
            tx_bytestr
            if isinstance(tx_bytestr, bytes)
            else base64.b64decode(tx_bytestr)
        )
        self.transaction = sui_prot.Transaction(
            bcs=(sui_prot.Bcs(value=transaction, name="Transaction"))
        )
        self.tx_skipchecks = skip_checks
        self.tx_do_gas_selection = do_gas_selection

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        base_obj = frag.BaseObject().fragment(schema)
        standard_obj = frag.StandardObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)

        qres = (
            schema.Query.simulateTransaction(
                transaction=self.transaction.to_dict(casing=betterproto2.Casing.SNAKE),
                checksEnabled=self.tx_skipchecks,
                doGasSelection=self.tx_do_gas_selection,
            )
            .alias("dryRun")
            .select(
                # schema.SimulationResult.error,
                results=schema.SimulationResult.outputs.select(
                    schema.CommandResult.returnValues.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.type.select(schema.MoveType.repr),
                            schema.MoveValue.bcs,
                        ),
                    )
                ),
                transactionBlock=schema.SimulationResult.effects.select(tx_effects),
            )
        )
        return dsl_gql(
            base_obj,
            standard_obj,
            gas_cost,
            tx_effects,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.DryRunResultGQL], None]:
        """Return the serialization MovePackage."""
        return pgql_type.DryRunResultGQL.from_query  # type: ignore[return-value]


@versionadded(version="0.99.0", reason="Replaces deprecated DryRunTransactionKind.")
class SimulateTransactionKind(PGQL_QueryNode):
    """SimulateTransactionKind query node.

    Simulates a transaction using a TransactionKind (programmable transaction), returning
    execution effects without committing to the chain.
    """

    def __init__(
        self,
        *,
        tx_kind: TransactionKind,
        tx_meta: dict,
        skip_checks: Optional[bool] = True,
        do_gas_selection: Optional[bool] = False,
    ) -> None:
        """__init__ Initialize SimulateTransactionKind object.

        :param tx_kind: The programmable TransactionKind BCS object
        :type tx_kind: TransactionKind
        :param tx_meta: Dict with at minimum ``sender`` (str Sui address). Optional keys:
            ``epoch_expiration`` (int), ``gasPrice``, ``gasObjects``, ``gasBudget``, ``gasSponsor``
        :type tx_meta: dict
        :param skip_checks: Whether to skip transaction checks, defaults to True
        :type skip_checks: Optional[bool]
        :param do_gas_selection: Whether to perform gas selection, defaults to False
        :type do_gas_selection: Optional[bool]
        """
        assert isinstance(tx_kind, TransactionKind)
        self.tx_data: TransactionKind = tx_kind
        self.transaction: sui_prot.Transaction = None
        self.tx_meta = tx_meta
        self.tx_skipchecks = skip_checks
        self.tx_do_gas_selection = do_gas_selection

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""

        prgrm_txn = self.tx_data.value
        inputs: list[sui_prot.Input] = []
        cmds: list[sui_prot.Command] = []
        trx_exp = None
        for input in prgrm_txn.Inputs:
            if input.enum_name == "Pure":
                inputs.append(
                    sui_prot.Input(
                        kind=sui_prot.InputInputKind.PURE, pure=bytes(input.value)
                    )
                )
            elif input.enum_name == "Object":
                oarg = input.value
                inputs.append(oarg.value.to_grpc_input(oarg.enum_name))
            elif input.enum_name == "FundsWithdrawal":
                inputs.append(input.value.to_grpc_input())

        for cmd in prgrm_txn.Command:
            cmds.append(cmd.value.to_grpc_command())
        self.transaction = sui_prot.Transaction(
            kind=sui_prot.TransactionKind(
                programmable_transaction=sui_prot.ProgrammableTransaction(
                    inputs=inputs, commands=cmds
                )
            ),
            expiration=trx_exp,
        )
        if self.tx_meta and (is_sender := self.tx_meta.get("sender")):
            self.transaction.sender = is_sender
            if txn_expires_after := self.tx_meta.get("epoch_expiration"):
                trx_exp = sui_prot.TransactionExpiration(
                    kind=sui_prot.TransactionExpirationTransactionExpirationKind.EPOCH,
                    epoch=txn_expires_after,
                )
                self.transaction.expiration = txn_expires_after
        else:
            raise ValueError("Requires 'sender' set in tx_meta dict")

        base_obj = frag.BaseObject().fragment(schema)
        standard_obj = frag.StandardObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)

        qres = (
            schema.Query.simulateTransaction(
                transaction=self.transaction.to_dict(casing=betterproto2.Casing.SNAKE),
                checksEnabled=self.tx_skipchecks,
                doGasSelection=self.tx_do_gas_selection,
            )
            .alias("dryRun")
            .select(
                results=schema.SimulationResult.outputs.select(
                    schema.CommandResult.returnValues.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.type.select(schema.MoveType.repr),
                            schema.MoveValue.bcs,
                        ),
                    )
                ),
                transactionBlock=schema.SimulationResult.effects.select(tx_effects),
            )
        )
        return dsl_gql(
            base_obj,
            standard_obj,
            gas_cost,
            tx_effects,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.DryRunResultGQL], None]:
        """Return the serialization function."""
        return pgql_type.DryRunResultGQL.from_query  # type: ignore[return-value]


class SimulateTransactionKindSC(SimulateTransactionKind):
    """SC variant: encode_fn normalizes GQL simulate response to canonical SimulateTransactionResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.SimulateTransactionResponse]:
        """Return encoder that maps GQL dryRun result to SimulateTransactionResponse."""

        def _encode(in_data: dict) -> sui_prot.SimulateTransactionResponse:
            dry_run = in_data.get("dryRun") or {}
            tx_block = dry_run.get("transactionBlock") or {}
            gas_effects = tx_block.get("gasEffects") or {}
            summary = gas_effects.get("gasSummary") or {}
            return sui_prot.SimulateTransactionResponse(
                transaction=sui_prot.ExecutedTransaction(
                    effects=sui_prot.TransactionEffects(
                        gas_used=sui_prot.GasCostSummary(
                            computation_cost=int(summary.get("computationCost") or 0),
                            storage_cost=int(summary.get("storageCost") or 0),
                            storage_rebate=int(summary.get("storageRebate") or 0),
                        )
                    )
                )
            )

        return _encode


@versionadded(version="0.99.0", reason="Replaces deprecated DryRunTransaction.")
class SimulateTransaction(PGQL_QueryNode):
    """SimulateTransaction query node.

    Simulates a fully serialized transaction (BCS bytes or base64 string), returning
    execution effects without committing to the chain.
    """

    def __init__(
        self,
        *,
        tx_bytestr: bytes | str,
        skip_checks: Optional[bool] = True,
        do_gas_selection: Optional[bool] = False,
    ) -> None:
        """__init__ Initialize the SimulateTransaction query.

        :param tx_bytestr: Serialized BCS bytes of a TransactionData, or base64 string of same
        :type tx_bytestr: bytes | str
        :param skip_checks: Whether to skip transaction checks, defaults to True
        :type skip_checks: Optional[bool]
        :param do_gas_selection: Whether to perform gas selection, defaults to False
        :type do_gas_selection: Optional[bool]
        """
        self.tx_data = tx_bytestr
        transaction = (
            tx_bytestr
            if isinstance(tx_bytestr, bytes)
            else base64.b64decode(tx_bytestr)
        )
        self.transaction = sui_prot.Transaction(
            bcs=(sui_prot.Bcs(value=transaction, name="Transaction"))
        )
        self.tx_skipchecks = skip_checks
        self.tx_do_gas_selection = do_gas_selection

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        base_obj = frag.BaseObject().fragment(schema)
        standard_obj = frag.StandardObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)

        qres = (
            schema.Query.simulateTransaction(
                transaction=self.transaction.to_dict(casing=betterproto2.Casing.SNAKE),
                checksEnabled=self.tx_skipchecks,
                doGasSelection=self.tx_do_gas_selection,
            )
            .alias("dryRun")
            .select(
                results=schema.SimulationResult.outputs.select(
                    schema.CommandResult.returnValues.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.type.select(schema.MoveType.repr),
                            schema.MoveValue.bcs,
                        ),
                    )
                ),
                transactionBlock=schema.SimulationResult.effects.select(tx_effects),
            )
        )
        return dsl_gql(
            base_obj,
            standard_obj,
            gas_cost,
            tx_effects,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.DryRunResultGQL], None]:
        """Return the serialization function."""
        return pgql_type.DryRunResultGQL.from_query  # type: ignore[return-value]


class ExecuteTransaction(PGQL_QueryNode):
    """."""

    def __init__(self, *, tx_bytestr: str, sig_array: list[str]) -> None:
        """__init__ Initialize ExecuteTransaction object."""
        self.tx_data: str = tx_bytestr
        self.sigs: list[str] = sig_array

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""

        qres = schema.Mutation.executeTransaction(
            transactionDataBcs=self.tx_data, signatures=self.sigs
        ).select(
            # schema.ExecutionResult.errors,
            schema.ExecutionResult.effects.select(
                schema.TransactionEffects.status,
                schema.TransactionEffects.lamportVersion,
                schema.TransactionEffects.digest,
                schema.TransactionEffects.transaction.select(
                    bcs=schema.Transaction.transactionBcs
                ),
                effects_bcs=schema.TransactionEffects.effectsBcs,
                execution_errors=schema.TransactionEffects.executionError.select(
                    schema.ExecutionError.abortCode,
                    schema.ExecutionError.sourceLineNumber,
                    schema.ExecutionError.instructionOffset,
                    schema.ExecutionError.identifier,
                    schema.ExecutionError.constant,
                    schema.ExecutionError.message,
                ),
            ),
        )
        return dsl_gql(DSLMutation(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ExecutionResultGQL], None]:
        """Return the serialization Execution result function."""
        return pgql_type.ExecutionResultGQL.from_query  # type: ignore[return-value]


class ExecuteTransactionSC(ExecuteTransaction):
    """SC variant: adds objectChanges to execute mutation; encode_fn maps to ExecuteTransactionResponse proto."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Execute mutation extended with objectChanges and effectsBcs for proto mapping."""
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)

        qres = schema.Mutation.executeTransaction(
            transactionDataBcs=self.tx_data, signatures=self.sigs
        ).select(
            schema.ExecutionResult.effects.select(
                schema.TransactionEffects.status,
                schema.TransactionEffects.digest,
                effects_bcs=schema.TransactionEffects.effectsBcs,
                object_changes=schema.TransactionEffects.objectChanges.select(
                    schema.ObjectChangeConnection.nodes.select(
                        address=schema.ObjectChange.address,
                        created=schema.ObjectChange.idCreated,
                        input_state=schema.ObjectChange.inputState.select(std_object),
                        output_state=schema.ObjectChange.outputState.select(std_object),
                    )
                ),
            ),
        )
        return dsl_gql(base_object, std_object, DSLMutation(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], "sui_prot.ExecuteTransactionResponse"]:
        """Return encoder mapping GQL executeTransaction to ExecuteTransactionResponse proto."""

        def _encode(in_data: dict) -> "sui_prot.ExecuteTransactionResponse":
            raw = in_data.get("executeTransaction") or {}
            effects = raw.get("effects") or {}

            status_str = effects.get("status")
            exec_status = (
                sui_prot.ExecutionStatus(success=(status_str == "SUCCESS"))
                if status_str else None
            )

            digest = effects.get("digest")

            effects_bcs_b64: str | None = effects.get("effects_bcs")
            effects_bcs_proto = (
                sui_prot.Bcs(value=base64.b64decode(effects_bcs_b64))
                if effects_bcs_b64 else None
            )

            nodes = (effects.get("object_changes") or {}).get("nodes") or []
            changed_objects: list[sui_prot.ChangedObject] = []
            for node in nodes:
                obj_id = node.get("address")
                created = node.get("created", False)
                in_state = (
                    sui_prot.ChangedObjectInputObjectState.DOES_NOT_EXIST
                    if created
                    else sui_prot.ChangedObjectInputObjectState.EXISTS
                )
                out = node.get("output_state") or {}
                if out.get("as_move_package"):
                    obj_type = "package"
                else:
                    mc = out.get("as_move_content") or {}
                    obj = mc.get("as_object") or {}
                    type_repr = obj.get("object_type_repr") or {}
                    obj_type = type_repr.get("object_type")
                changed_objects.append(
                    sui_prot.ChangedObject(
                        object_id=obj_id,
                        input_state=in_state,
                        object_type=obj_type,
                    )
                )

            return sui_prot.ExecuteTransactionResponse(
                transaction=sui_prot.ExecutedTransaction(
                    digest=digest,
                    effects=sui_prot.TransactionEffects(
                        bcs=effects_bcs_proto,
                        status=exec_status,
                        changed_objects=changed_objects,
                    ),
                )
            )

        return _encode


# ---------------------------------------------------------------------------
# SC siblings — these subclasses inherit as_document_node() unchanged and
# override encode_fn() to return gRPC proto instances instead of GQL types.
# Used by SuiCommand subclasses that dispatch over both GQL and gRPC.
# ---------------------------------------------------------------------------


class GetCoinMetaDataSC(GetCoinMetaData):
    """SC variant: encode_fn maps GQL coinMetadata response to GetCoinInfoResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetCoinInfoResponse]:
        """Return deserializer producing GetCoinInfoResponse from GQL coinMetadata dict."""

        def _encode(in_data: dict) -> sui_prot.GetCoinInfoResponse:
            flat: dict = {}
            pgql_type._fast_flat(in_data, flat)
            return sui_prot.GetCoinInfoResponse(
                metadata=sui_prot.CoinMetadata(
                    id=flat.get("address"),
                    decimals=flat.get("decimals"),
                    name=flat.get("name"),
                    symbol=flat.get("symbol"),
                    description=flat.get("description"),
                    icon_url=flat.get("iconUrl"),
                )
            )

        return _encode


class GetAddressCoinBalanceSC(GetAddressCoinBalance):
    """SC variant: encode_fn maps GQL address.balance response to GetBalanceResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetBalanceResponse]:
        """Return deserializer producing GetBalanceResponse from GQL address balance dict."""

        def _encode(in_data: dict) -> sui_prot.GetBalanceResponse:
            flat: dict = {}
            pgql_type._fast_flat(in_data["address"]["balance"], flat)
            return sui_prot.GetBalanceResponse(
                balance=sui_prot.Balance(
                    coin_type=flat.get("coinType"),
                    balance=int(flat["totalBalance"]),
                    address_balance=int(flat["addressBalance"]),
                    coin_balance=int(flat["coinBalance"]),
                )
            )

        return _encode


class GetAddressCoinBalancesSC(GetAddressCoinBalances):
    """SC variant: encode_fn maps GQL address.balances response to ListBalancesResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListBalancesResponse]:
        """Return deserializer producing ListBalancesResponse from GQL balances dict."""

        def _encode(in_data: dict) -> sui_prot.ListBalancesResponse:
            qres = in_data.get("qres", in_data)
            balances_raw = qres["balances"]
            cursor = balances_raw["cursor"]
            balances: list[sui_prot.Balance] = []
            for item in balances_raw["type_balances"]:
                flat: dict = {}
                pgql_type._fast_flat(item, flat)
                balances.append(
                    sui_prot.Balance(
                        coin_type=flat.get("coin_type"),
                        balance=int(flat["totalBalance"]),
                        address_balance=int(flat["addressBalance"]),
                        coin_balance=int(flat["coinBalance"]),
                    )
                )
            end_cursor: str | None = cursor.get("endCursor")
            next_page_token: bytes | None = (
                end_cursor.encode()
                if cursor.get("hasNextPage") and end_cursor
                else None
            )
            return sui_prot.ListBalancesResponse(
                balances=balances, next_page_token=next_page_token
            )

        return _encode


class GetEpochSC(GetEpoch):
    """SC variant: encode_fn maps GQL epoch response to GetEpochResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetEpochResponse]:
        """Return deserializer producing GetEpochResponse from GQL epoch dict."""

        def _encode(in_data: dict) -> sui_prot.GetEpochResponse:
            epoch_data = in_data.pop("epoch", in_data) if in_data else {}
            start_ts: str | None = epoch_data.get("startTimestamp")
            end_ts: str | None = epoch_data.get("endTimestamp")
            rgp: str | None = epoch_data.get("referenceGasPrice")
            return sui_prot.GetEpochResponse(
                epoch=sui_prot.Epoch(
                    epoch=epoch_data.get("epochId"),
                    reference_gas_price=int(rgp) if rgp else None,
                    start=_parse_gql_datetime(start_ts),
                    end=_parse_gql_datetime(end_ts),
                )
            )

        return _encode


class GetBasicCurrentEpochInfoSC(GetBasicCurrentEpochInfo):
    """SC variant: encode_fn maps GQL basic epoch response to Epoch proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.Epoch]:
        """Return deserializer producing Epoch proto from GQL basic epoch dict."""

        def _encode(in_data: dict) -> sui_prot.Epoch:
            epoch_data = in_data.pop("epoch", in_data) if in_data else {}
            start_ts: str | None = epoch_data.get("startTimestamp")
            end_ts: str | None = epoch_data.get("endTimestamp")
            rgp: str | None = epoch_data.get("referenceGasPrice")
            return sui_prot.Epoch(
                epoch=epoch_data.get("epochId"),
                reference_gas_price=int(rgp) if rgp else None,
                start=_parse_gql_datetime(start_ts),
                end=_parse_gql_datetime(end_ts),
            )

        return _encode


class GetPackageVersionsSC(GetPackageVersions):
    """SC variant: encode_fn maps GQL packageVersions response to ListPackageVersionsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListPackageVersionsResponse]:
        """Return deserializer producing ListPackageVersionsResponse from GQL package versions dict."""

        def _encode(in_data: dict) -> sui_prot.ListPackageVersionsResponse:
            pkg_data = in_data.pop("packageVersions", in_data) if in_data else {}
            cursor = pkg_data.get("cursor", {})
            end_cursor: str | None = cursor.get("endCursor")
            versions = [
                sui_prot.PackageVersion(package_id=v["address"], version=v["version"])
                for v in pkg_data.get("versions", [])
            ]
            next_page_token: bytes | None = (
                end_cursor.encode()
                if cursor.get("hasNextPage") and end_cursor
                else None
            )
            return sui_prot.ListPackageVersionsResponse(
                versions=versions, next_page_token=next_page_token
            )

        return _encode


class GetNameServiceAddressSC(GetNameServiceAddress):
    """SC variant: encode_fn maps GQL suinsName response to LookupNameResponse proto.

    Overrides as_document_node to also select Address.address (parent only selects
    defaultSuinsName, which is insufficient to populate NameRecord.target_address).
    """

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request selecting both address and name fields."""
        return dsl_gql(
            DSLQuery(
                schema.Query.suinsName(address=self.name).select(
                    schema.Address.address,
                    schema.Address.defaultSuinsName,
                )
            )
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.LookupNameResponse]:
        """Return deserializer producing LookupNameResponse from GQL suinsName dict."""

        def _encode(in_data: dict) -> sui_prot.LookupNameResponse:
            ns_data = in_data.get("suinsName", in_data)
            if not ns_data:
                return sui_prot.LookupNameResponse()
            return sui_prot.LookupNameResponse(
                record=sui_prot.NameRecord(
                    name=ns_data.get("defaultSuinsName"),
                    target_address=ns_data.get("address"),
                )
            )

        return _encode


class GetNameServiceNamesSC(GetNameServiceNames):
    """SC variant: encode_fn maps GQL address response to ReverseLookupNameResponse proto.

    Overrides as_document_node to use clean field selection without aliases and
    to also select Address.address for populating NameRecord.target_address.
    Returns empty response when the address has no SuiNS name registered.
    """

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request selecting address and default SuiNS name."""
        return dsl_gql(
            DSLQuery(
                schema.Query.address(address=self.owner).select(
                    schema.Address.address,
                    schema.Address.defaultSuinsName,
                )
            )
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ReverseLookupNameResponse]:
        """Return deserializer producing ReverseLookupNameResponse from GQL address dict."""

        def _encode(in_data: dict) -> sui_prot.ReverseLookupNameResponse:
            addr_data = in_data.get("address", in_data)
            if not addr_data:
                return sui_prot.ReverseLookupNameResponse()
            name: str | None = addr_data.get("defaultSuinsName")
            if name is None:
                return sui_prot.ReverseLookupNameResponse()
            return sui_prot.ReverseLookupNameResponse(
                record=sui_prot.NameRecord(
                    name=name,
                    target_address=addr_data.get("address"),
                )
            )

        return _encode


# ---------------------------------------------------------------------------
# SC sibling helpers — Steps 1-6
# ---------------------------------------------------------------------------

_GQL_ABILITY_MAP: dict[str, "sui_prot.Ability"] = {
    "COPY": sui_prot.Ability.COPY,
    "DROP": sui_prot.Ability.DROP,
    "STORE": sui_prot.Ability.STORE,
    "KEY": sui_prot.Ability.KEY,
}

_GQL_VIS_MAP: dict[str, "sui_prot.FunctionDescriptorVisibility"] = {
    "Private": sui_prot.FunctionDescriptorVisibility.PRIVATE,
    "Public": sui_prot.FunctionDescriptorVisibility.PUBLIC,
    "Friend": sui_prot.FunctionDescriptorVisibility.FRIEND,
}

_GQL_SCALAR_MAP: dict[str, "sui_prot.OpenSignatureBodyType"] = {
    "address": sui_prot.OpenSignatureBodyType.ADDRESS,
    "bool": sui_prot.OpenSignatureBodyType.BOOL,
    "u8": sui_prot.OpenSignatureBodyType.U8,
    "u16": sui_prot.OpenSignatureBodyType.U16,
    "u32": sui_prot.OpenSignatureBodyType.U32,
    "u64": sui_prot.OpenSignatureBodyType.U64,
    "u128": sui_prot.OpenSignatureBodyType.U128,
    "u256": sui_prot.OpenSignatureBodyType.U256,
}


def _is_tx_context_sig(sig_dict: dict) -> bool:
    """Return True if sig_dict represents a TxContext parameter."""
    body = sig_dict.get("body", {})
    if isinstance(body, dict) and "datatype" in body:
        return body["datatype"].get("type") == "TxContext"
    return False


def _owner_from_inline_frag(owner_dict: Optional[dict]) -> Optional[sui_prot.Owner]:
    """Map a StandardObject owner inline-fragment dict to an Owner proto."""
    if not owner_dict:
        return None
    kind_str = owner_dict.get("obj_owner_kind")
    if kind_str == "AddressOwner":
        addr_id = owner_dict.get("address_id", {})
        return sui_prot.Owner(
            kind=sui_prot.OwnerOwnerKind.ADDRESS,
            address=addr_id.get("address") if isinstance(addr_id, dict) else None,
        )
    if kind_str == "ObjectOwner":
        parent_id = owner_dict.get("parent_id", {})
        return sui_prot.Owner(
            kind=sui_prot.OwnerOwnerKind.OBJECT,
            address=parent_id.get("address") if isinstance(parent_id, dict) else None,
        )
    if kind_str == "Shared":
        return sui_prot.Owner(
            kind=sui_prot.OwnerOwnerKind.SHARED,
            version=owner_dict.get("initial_version"),
        )
    if kind_str == "Immutable":
        return sui_prot.Owner(kind=sui_prot.OwnerOwnerKind.IMMUTABLE)
    return None


def _gql_sig_body_to_proto(body: Any) -> sui_prot.OpenSignatureBody:
    """Recursively map a GQL signature body to OpenSignatureBody proto."""
    if isinstance(body, str):
        body_type = _GQL_SCALAR_MAP.get(body)
        if body_type is None:
            raise ValueError(f"_gql_sig_body_to_proto: unrecognized scalar type '{body}'")
        return sui_prot.OpenSignatureBody(type=body_type)
    if isinstance(body, dict):
        if "vector" in body:
            return sui_prot.OpenSignatureBody(
                type=sui_prot.OpenSignatureBodyType.VECTOR,
                type_parameter_instantiation=[_gql_sig_body_to_proto(body["vector"])],
            )
        if "datatype" in body:
            dt = body["datatype"]
            type_name = f"{dt['package']}::{dt['module']}::{dt['type']}"
            type_params = [_gql_sig_body_to_proto(p) for p in dt.get("typeParameters", [])]
            return sui_prot.OpenSignatureBody(
                type=sui_prot.OpenSignatureBodyType.DATATYPE,
                type_name=type_name,
                type_parameter_instantiation=type_params,
            )
        if "typeParameter" in body:
            return sui_prot.OpenSignatureBody(
                type=sui_prot.OpenSignatureBodyType.TYPE_PARAMETER,
                type_parameter=int(body["typeParameter"]),
            )
    raise ValueError(f"_gql_sig_body_to_proto: unrecognized body shape {body!r}")


def _gql_sig_to_proto_open_sig(sig_dict: dict) -> sui_prot.OpenSignature:
    """Map a GQL OpenMoveType.signature dict to an OpenSignature proto."""
    ref = sig_dict.get("ref")
    if ref == "&":
        reference: Optional[sui_prot.OpenSignatureReference] = sui_prot.OpenSignatureReference.IMMUTABLE
    elif ref == "&mut":
        reference = sui_prot.OpenSignatureReference.MUTABLE
    else:
        reference = None
    return sui_prot.OpenSignature(
        reference=reference,
        body=_gql_sig_body_to_proto(sig_dict.get("body", {})),
    )


def _encode_object_from_raw(obj_dict: dict) -> sui_prot.Object:
    """Map a StandardObject raw GQL dict to an Object proto."""
    if not obj_dict:
        return sui_prot.Object()
    bcs_str: Optional[str] = obj_dict.get("bcs")
    object_bcs = sui_prot.Bcs(value=base64.b64decode(bcs_str)) if bcs_str else None
    owner = _owner_from_inline_frag(obj_dict.get("owner"))
    prior_tx = obj_dict.get("prior_transaction") or {}
    prev_tx: Optional[str] = prior_tx.get("previous_transaction_digest") if isinstance(prior_tx, dict) else None
    object_type: Optional[str] = None
    has_public_transfer: Optional[bool] = None
    as_move_content = obj_dict.get("as_move_content")
    if isinstance(as_move_content, dict):
        has_public_transfer = as_move_content.get("has_public_transfer")
        as_object = as_move_content.get("as_object") or {}
        if isinstance(as_object, dict):
            obj_type_repr = as_object.get("object_type_repr") or {}
            if isinstance(obj_type_repr, dict):
                object_type = obj_type_repr.get("object_type")
    sr = obj_dict.get("storage_rebate")
    return sui_prot.Object(
        object_id=obj_dict.get("object_id"),
        version=int(obj_dict.get("version") or 0),
        digest=obj_dict.get("object_digest"),
        owner=owner,
        object_type=object_type,
        has_public_transfer=has_public_transfer,
        bcs=object_bcs,
        previous_transaction=prev_tx,
        storage_rebate=int(sr) if sr is not None else None,
    )


def _encode_coin_from_move_obj(mo_dict: dict) -> sui_prot.Object:
    """Map a MoveObject-level GQL dict (coin or staked coin node) to an Object proto."""
    if not mo_dict:
        return sui_prot.Object()
    owner = _owner_from_inline_frag(mo_dict.get("owner"))
    prev_tx_info = mo_dict.get("previousTransaction") or {}
    prev_tx: Optional[str] = prev_tx_info.get("previous_transaction") if isinstance(prev_tx_info, dict) else None
    contents = mo_dict.get("contents") or {}
    coin_type: Optional[str] = None
    balance_raw = None
    if isinstance(contents, dict):
        coin_type = (contents.get("type") or {}).get("coin_type")
        coin_json = contents.get("json") or {}
        if isinstance(coin_json, dict):
            balance_raw = coin_json.get("balance")
    return sui_prot.Object(
        object_id=mo_dict.get("coin_object_id"),
        version=int(mo_dict.get("version") or 0),
        digest=mo_dict.get("object_digest"),
        owner=owner,
        object_type=coin_type,
        has_public_transfer=mo_dict.get("hasPublicTransfer"),
        previous_transaction=prev_tx,
        balance=int(balance_raw) if balance_raw is not None else None,
    )


def _encode_coins_list(in_data) -> sui_prot.ListOwnedObjectsResponse:
    """Shared encoder for GetCoinsSC and GetGasSC.

    Accepts either a raw GQL response dict (single-page path) or a list of coin
    dicts (SC auto-paging path where all pages are pre-accumulated by the client).
    """
    if isinstance(in_data, list):
        objects: list[sui_prot.Object] = [_encode_coin_from_move_obj(c) for c in in_data]
        return sui_prot.ListOwnedObjectsResponse(objects=objects, next_page_token=None)
    qres = in_data.get("qres", in_data)
    coins = qres.get("coins", {}) if isinstance(qres, dict) else {}
    cursor = coins.get("cursor", {}) if isinstance(coins, dict) else {}
    coin_objects = coins.get("coin_objects", []) if isinstance(coins, dict) else []
    objects = [_encode_coin_from_move_obj(c) for c in coin_objects]
    end_cursor: Optional[str] = cursor.get("endCursor") if isinstance(cursor, dict) else None
    next_page_token: Optional[bytes] = (
        end_cursor.encode()
        if isinstance(cursor, dict) and cursor.get("hasNextPage") and end_cursor
        else None
    )
    return sui_prot.ListOwnedObjectsResponse(objects=objects, next_page_token=next_page_token)


def _encode_checkpoint_from_raw(cp_dict: dict) -> sui_prot.GetCheckpointResponse:
    """Map a StandardCheckpoint raw GQL dict to GetCheckpointResponse proto."""
    if not cp_dict:
        return sui_prot.GetCheckpointResponse()
    ts_str: Optional[str] = cp_dict.get("timestamp")
    ts: Optional[datetime.datetime] = None
    if ts_str:
        try:
            ts = _parse_gql_datetime(ts_str)
        except ValueError:
            pass
    seq = cp_dict.get("sequenceNumber")
    net_txns = cp_dict.get("networkTotalTransactions")
    return sui_prot.GetCheckpointResponse(
        checkpoint=sui_prot.Checkpoint(
            sequence_number=int(seq) if seq is not None else None,
            digest=cp_dict.get("digest"),
            summary=sui_prot.CheckpointSummary(
                sequence_number=int(seq) if seq is not None else None,
                digest=cp_dict.get("digest"),
                total_network_transactions=int(net_txns) if net_txns is not None else None,
                previous_digest=cp_dict.get("previousCheckpointDigest"),
                timestamp=ts,
            ),
        )
    )


def _fields_to_descriptors(fields_list: list) -> list:
    """Map GQL field dicts to FieldDescriptor protos."""
    result = []
    for i, f in enumerate(fields_list):
        sig_container = f.get("field_type") or {}
        sig_dict = sig_container.get("signature") or {} if isinstance(sig_container, dict) else {}
        body = sig_dict.get("body") if isinstance(sig_dict, dict) else None
        field_type = _gql_sig_body_to_proto(body) if body is not None else None
        result.append(sui_prot.FieldDescriptor(
            name=f.get("field_name"),
            position=i,
            type=field_type,
        ))
    return result


def _struct_to_datatype(
    struct_dict: dict,
    defining_id: str,
    module_name: str,
) -> sui_prot.DatatypeDescriptor:
    """Map a MoveStruct raw dict to a DatatypeDescriptor proto."""
    name = struct_dict.get("struct_name", "")
    abilities = [_GQL_ABILITY_MAP[a] for a in struct_dict.get("abilities", []) if a in _GQL_ABILITY_MAP]
    type_params = [
        sui_prot.TypeParameter(
            constraints=[_GQL_ABILITY_MAP[c] for c in tp.get("constraints", []) if c in _GQL_ABILITY_MAP],
            is_phantom=bool(tp.get("isPhantom", False)),
        )
        for tp in struct_dict.get("typeParameters", [])
        if isinstance(tp, dict)
    ]
    fields = _fields_to_descriptors(struct_dict.get("fields", []))
    return sui_prot.DatatypeDescriptor(
        type_name=f"{defining_id}::{module_name}::{name}",
        defining_id=defining_id,
        module=module_name,
        name=name,
        abilities=abilities,
        type_parameters=type_params,
        kind=sui_prot.DatatypeDescriptorDatatypeKind.STRUCT,
        fields=fields,
    )


def _enum_to_datatype(
    enum_dict: dict,
    defining_id: str,
    module_name: str,
) -> sui_prot.DatatypeDescriptor:
    """Map a MoveEnum raw dict to a DatatypeDescriptor proto."""
    name = enum_dict.get("enum_name", "")
    abilities = [_GQL_ABILITY_MAP[a] for a in enum_dict.get("abilities", []) if a in _GQL_ABILITY_MAP]
    type_params = [
        sui_prot.TypeParameter(
            constraints=[_GQL_ABILITY_MAP[c] for c in tp.get("constraints", []) if c in _GQL_ABILITY_MAP],
            is_phantom=bool(tp.get("isPhantom", False)),
        )
        for tp in enum_dict.get("typeParameters", [])
        if isinstance(tp, dict)
    ]
    variants = [
        sui_prot.VariantDescriptor(
            name=v.get("variant_name"),
            position=i,
            fields=_fields_to_descriptors(v.get("fields", [])),
        )
        for i, v in enumerate(enum_dict.get("variants", []))
        if isinstance(v, dict)
    ]
    return sui_prot.DatatypeDescriptor(
        type_name=f"{defining_id}::{module_name}::{name}",
        defining_id=defining_id,
        module=module_name,
        name=name,
        abilities=abilities,
        type_parameters=type_params,
        kind=sui_prot.DatatypeDescriptorDatatypeKind.ENUM,
        variants=variants,
    )


def _func_to_descriptor(func_dict: dict) -> sui_prot.FunctionDescriptor:
    """Map a MoveFunction raw dict to a FunctionDescriptor proto."""
    name = func_dict.get("function_name", "")
    vis_str = func_dict.get("visibility", "Private")
    visibility = _GQL_VIS_MAP.get(vis_str, sui_prot.FunctionDescriptorVisibility.PRIVATE)
    is_entry = bool(func_dict.get("isEntry", False))
    type_params = [
        sui_prot.TypeParameter(
            constraints=[_GQL_ABILITY_MAP[c] for c in tp.get("constraints", []) if c in _GQL_ABILITY_MAP],
            is_phantom=False,
        )
        for tp in func_dict.get("typeParameters", [])
        if isinstance(tp, dict)
    ]
    raw_params = func_dict.get("parameters", [])
    parameters = [
        _gql_sig_to_proto_open_sig(p["signature"])
        for p in raw_params
        if isinstance(p, dict) and "signature" in p and not _is_tx_context_sig(p["signature"])
    ]
    returns = [
        _gql_sig_to_proto_open_sig(r["signature"])
        for r in func_dict.get("returns", [])
        if isinstance(r, dict) and "signature" in r
    ]
    return sui_prot.FunctionDescriptor(
        name=name,
        visibility=visibility,
        is_entry=is_entry,
        type_parameters=type_params,
        parameters=parameters,
        returns=returns,
    )


def _module_raw_to_proto(mod_dict: dict, package_id: str) -> sui_prot.Module:
    """Map a MoveModule raw GQL dict to a Module proto."""
    module_name = mod_dict.get("module_name", "")
    struct_list_data = mod_dict.get("structure_list") or {}
    func_list_data = mod_dict.get("function_list") or {}
    module_structures = struct_list_data.get("module_structures", []) if isinstance(struct_list_data, dict) else []
    module_functions = func_list_data.get("module_functions", []) if isinstance(func_list_data, dict) else []
    datatypes = [_struct_to_datatype(s, package_id, module_name) for s in module_structures if isinstance(s, dict)]
    functions = [_func_to_descriptor(f) for f in module_functions if isinstance(f, dict)]
    return sui_prot.Module(
        name=module_name,
        datatypes=datatypes,
        functions=functions,
    )


# ---------------------------------------------------------------------------
# Step 1 — Simple GQL SC siblings
# ---------------------------------------------------------------------------


class GetObjectSC(GetObject):
    """SC variant: encode_fn maps GQL object response to Object proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.Object]:
        """Return deserializer producing Object from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.Object:
            obj_dict = in_data.get("object") or {}
            return _encode_object_from_raw(obj_dict)

        return _encode


class GetPastObjectSC(GetPastObject):
    """SC variant: encode_fn maps GQL past object response to Object proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.Object]:
        """Return deserializer producing Object from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.Object:
            obj_dict = in_data.get("object") or {}
            return _encode_object_from_raw(obj_dict)

        return _encode


class GetMoveDataTypeSC(GetMoveDataType):
    """SC variant: encode_fn maps GQL datatype response to GetDatatypeResponse proto."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Use MoveStructureSC/MoveEnumSC fragments to include typeParameters and isPhantom."""
        struc = frag.MoveStructureSC().fragment(schema)
        enum = frag.MoveEnumSC().fragment(schema)

        qres = schema.Query.object(address=self.package).select(
            schema.Object.asMovePackage.select(
                schema.MovePackage.module(name=self.module).select(
                    schema.MoveModule.datatype(name=self.data_type_name).select(
                        schema.MoveDatatype.asMoveStruct.select(struc),
                        schema.MoveDatatype.asMoveEnum.select(enum),
                    )
                )
            )
        )
        return dsl_gql(struc, enum, DSLQuery(qres))

    def encode_fn(self) -> Callable[[dict], sui_prot.GetDatatypeResponse]:
        """Return deserializer producing GetDatatypeResponse from GQL datatype dict."""
        defining_id = self.package
        module_name = self.module

        def _encode(in_data: dict) -> sui_prot.GetDatatypeResponse:
            mod = (in_data.get("object") or {}).get("asMovePackage") or {}
            datatype = (mod.get("module") or {}).get("datatype") or {}
            struct_raw = datatype.get("asMoveStruct")
            enum_raw = datatype.get("asMoveEnum")
            if struct_raw:
                descriptor = _struct_to_datatype(struct_raw, defining_id, module_name)
            elif enum_raw:
                descriptor = _enum_to_datatype(enum_raw, defining_id, module_name)
            else:
                return sui_prot.GetDatatypeResponse()
            return sui_prot.GetDatatypeResponse(datatype=descriptor)

        return _encode


class GetStructureSC(GetStructure):
    """SC variant: encode_fn maps GQL struct response to GetDatatypeResponse proto."""

    def encode_fn(self) -> Callable[[dict], sui_prot.GetDatatypeResponse]:
        """Return deserializer producing GetDatatypeResponse from GQL struct dict."""
        defining_id = self.package
        module_name = self.module

        def _encode(in_data: dict) -> sui_prot.GetDatatypeResponse:
            mod = (in_data.get("object") or {}).get("asMovePackage") or {}
            struct_raw = (mod.get("module") or {}).get("struct") or {}
            if not struct_raw:
                return sui_prot.GetDatatypeResponse()
            return sui_prot.GetDatatypeResponse(
                datatype=_struct_to_datatype(struct_raw, defining_id, module_name)
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 2 — GetFunctionSC
# ---------------------------------------------------------------------------


class GetFunctionSC(GetFunction):
    """SC variant: encode_fn maps GQL function response to GetFunctionResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetFunctionResponse]:
        """Return deserializer producing GetFunctionResponse from GQL function dict."""

        def _encode(in_data: dict) -> sui_prot.GetFunctionResponse:
            mod = (in_data.get("object") or {}).get("asMovePackage") or {}
            func_raw = (mod.get("module") or {}).get("function") or {}
            if not func_raw:
                return sui_prot.GetFunctionResponse()
            return sui_prot.GetFunctionResponse(function=_func_to_descriptor(func_raw))

        return _encode


# ---------------------------------------------------------------------------
# Step 3 — Owned/paginated list SC siblings
# ---------------------------------------------------------------------------


class GetCoinsSC(GetCoins):
    """SC variant: encode_fn maps GQL coins response to ListOwnedObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL coins dict."""
        return _encode_coins_list


class GetGasSC(GetGas):
    """SC variant: encode_fn maps GQL SUI gas coins response to ListOwnedObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL gas dict."""
        return _encode_coins_list


class GetDelegatedStakesSC(GetDelegatedStakes):
    """SC variant: encode_fn maps GQL staked coins response to ListOwnedObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL staked coins dict."""

        def _encode(in_data: dict) -> sui_prot.ListOwnedObjectsResponse:
            objects_data = in_data.get("objects") or {}
            cursor = objects_data.get("cursor") or {}
            staked_coins = objects_data.get("staked_coin", [])
            objects: list[sui_prot.Object] = [
                _encode_coin_from_move_obj(sc.get("asMoveObject") or {})
                for sc in staked_coins
                if isinstance(sc, dict)
            ]
            end_cursor: Optional[str] = cursor.get("endCursor") if isinstance(cursor, dict) else None
            next_page_token: Optional[bytes] = (
                end_cursor.encode()
                if isinstance(cursor, dict) and cursor.get("hasNextPage") and end_cursor
                else None
            )
            return sui_prot.ListOwnedObjectsResponse(
                objects=objects,
                next_page_token=next_page_token,
            )

        return _encode


class GetObjectsOwnedByAddressSC(GetObjectsOwnedByAddress):
    """SC variant: encode_fn maps GQL owned objects response to ListOwnedObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL objects dict."""

        def _encode(in_data: dict) -> sui_prot.ListOwnedObjectsResponse:
            objects_data = in_data.get("objects") or {}
            cursor = objects_data.get("cursor") or {}
            obj_list = objects_data.get("objects_data", [])
            objects: list[sui_prot.Object] = [
                _encode_object_from_raw(o)
                for o in obj_list
                if isinstance(o, dict)
            ]
            end_cursor: Optional[str] = cursor.get("endCursor") if isinstance(cursor, dict) else None
            next_page_token: Optional[bytes] = (
                end_cursor.encode()
                if isinstance(cursor, dict) and cursor.get("hasNextPage") and end_cursor
                else None
            )
            return sui_prot.ListOwnedObjectsResponse(
                objects=objects,
                next_page_token=next_page_token,
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 4 — Batch object SC siblings
# ---------------------------------------------------------------------------


class GetMultipleObjectsSC(GetMultipleObjects):
    """SC variant: encode_fn maps GQL multi-object response to BatchGetObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.BatchGetObjectsResponse]:
        """Return deserializer producing BatchGetObjectsResponse from GQL multi-get dict."""

        def _encode(in_data: dict) -> sui_prot.BatchGetObjectsResponse:
            obj_list = in_data.get("multiGetObjects", [])
            return sui_prot.BatchGetObjectsResponse(objects=[
                sui_prot.GetObjectResult(object=_encode_object_from_raw(o))
                for o in obj_list
                if isinstance(o, dict)
            ])

        return _encode


class GetMultipleVersionedObjectsSC(GetMultipleVersionedObjects):
    """SC variant: encode_fn maps GQL multi-versioned response to BatchGetObjectsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.BatchGetObjectsResponse]:
        """Return deserializer producing BatchGetObjectsResponse from GQL multi-get dict."""

        def _encode(in_data: dict) -> sui_prot.BatchGetObjectsResponse:
            obj_list = in_data.get("multiGetObjects", [])
            return sui_prot.BatchGetObjectsResponse(objects=[
                sui_prot.GetObjectResult(object=_encode_object_from_raw(o))
                for o in obj_list
                if isinstance(o, dict)
            ])

        return _encode


# ---------------------------------------------------------------------------
# Step 5 — Checkpoint SC siblings
# ---------------------------------------------------------------------------


class GetLatestCheckpointSequenceSC(GetLatestCheckpointSequence):
    """SC variant: encode_fn maps GQL checkpoints response to GetCheckpointResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetCheckpointResponse]:
        """Return deserializer producing GetCheckpointResponse from GQL checkpoints dict."""

        def _encode(in_data: dict) -> sui_prot.GetCheckpointResponse:
            checkpoints = in_data.get("checkpoints") or {}
            nodes = checkpoints.get("nodes", [])
            if not nodes:
                return sui_prot.GetCheckpointResponse()
            return _encode_checkpoint_from_raw(nodes[0])

        return _encode


class GetCheckpointBySequenceSC(GetCheckpointBySequence):
    """SC variant: encode_fn maps GQL checkpoint response to GetCheckpointResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetCheckpointResponse]:
        """Return deserializer producing GetCheckpointResponse from GQL checkpoint dict."""

        def _encode(in_data: dict) -> sui_prot.GetCheckpointResponse:
            cp_dict = in_data.get("checkpoint") or {}
            return _encode_checkpoint_from_raw(cp_dict)

        return _encode


# ---------------------------------------------------------------------------
# Step 6 — Package/module/TX SC siblings
# ---------------------------------------------------------------------------


class GetModuleSC(GetModule):
    """SC variant: encode_fn maps GQL module response to Module proto."""

    def encode_fn(self) -> Callable[[dict], sui_prot.Module]:
        """Return deserializer producing Module from GQL module dict."""
        package_id = self.package

        def _encode(in_data: dict) -> sui_prot.Module:
            mod_raw = (in_data.get("object") or {}).get("asMovePackage") or {}
            module_raw = mod_raw.get("module") or {}
            if not module_raw:
                return sui_prot.Module()
            return _module_raw_to_proto(module_raw, package_id)

        return _encode


class GetPackageSC(GetPackage):
    """SC variant: encode_fn maps GQL package response to GetPackageResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.GetPackageResponse]:
        """Return deserializer producing GetPackageResponse from GQL package dict."""

        def _encode(in_data: dict) -> sui_prot.GetPackageResponse:
            pkg_raw = (in_data.get("object") or {}).get("asMovePackage") or {}
            if not pkg_raw:
                return sui_prot.GetPackageResponse()
            package_id: str = pkg_raw.get("package_id") or ""
            package_version = pkg_raw.get("package_version")
            nodes = pkg_raw.get("nodes") or []
            modules = [_module_raw_to_proto(m, package_id) for m in nodes if isinstance(m, dict)]
            return sui_prot.GetPackageResponse(
                package=sui_prot.Package(
                    storage_id=package_id,
                    version=int(package_version) if package_version is not None else None,
                    modules=modules,
                )
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 7b — Paged High-complexity SC siblings
# ---------------------------------------------------------------------------


class GetStructuresSC(GetStructures):
    """SC variant: accumulates raw MoveStruct nodes across pages → MoveStructuresGRPC."""

    def encode_fn(self) -> Callable[[list], "_rn.MoveStructuresGRPC"]:
        """Return deserializer producing MoveStructuresGRPC from accumulated struct nodes."""
        defining_id = self.package
        module_name = self.module

        def _encode(nodes: list) -> "_rn.MoveStructuresGRPC":
            return _rn.MoveStructuresGRPC(
                structures=[
                    _struct_to_datatype(n, defining_id, module_name)
                    for n in nodes
                    if isinstance(n, dict)
                ]
            )

        return _encode


class GetFunctionsSC(GetFunctions):
    """SC variant: accumulates raw MoveFunction nodes across pages → MoveFunctionsGRPC."""

    @staticmethod
    def encode_fn() -> Callable[[list], "_rn.MoveFunctionsGRPC"]:
        """Return deserializer producing MoveFunctionsGRPC from accumulated function nodes."""

        def _encode(nodes: list) -> "_rn.MoveFunctionsGRPC":
            return _rn.MoveFunctionsGRPC(
                functions=[
                    _func_to_descriptor(n)
                    for n in nodes
                    if isinstance(n, dict)
                ]
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 9 — High complexity SC siblings
# ---------------------------------------------------------------------------


class GetDynamicFieldsSC(GetDynamicFields):
    """SC variant: encode_fn maps GQL dynamic fields response to ListDynamicFieldsResponse proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.ListDynamicFieldsResponse]:
        """Return deserializer producing ListDynamicFieldsResponse from GQL dynamic fields dict."""

        def _encode(in_data: dict) -> sui_prot.ListDynamicFieldsResponse:
            obj = in_data.get("object") or {}
            parent_id: str = obj.get("parent_object_id", "")
            dyn_conn = obj.get("dynamicFields") or {}
            cursor = dyn_conn.get("cursor") or {}
            nodes = dyn_conn.get("dynamic_fields") or []

            fields: list[sui_prot.DynamicField] = []
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                field_kind_str = node.get("field_kind", "")
                kind = (
                    sui_prot.DynamicFieldDynamicFieldKind.FIELD
                    if field_kind_str == "DynamicField"
                    else sui_prot.DynamicFieldDynamicFieldKind.OBJECT
                )
                field_data = node.get("field_data") or {}
                data_kind = field_data.get("data_kind", "")
                if data_kind == "MoveObject":
                    fields.append(sui_prot.DynamicField(
                        kind=kind,
                        parent=parent_id,
                        child_id=field_data.get("address"),
                    ))
                else:
                    obj_type = field_data.get("object_type") or {}
                    fields.append(sui_prot.DynamicField(
                        kind=kind,
                        parent=parent_id,
                        value_type=(obj_type.get("layout")),
                    ))

            end_cursor: Optional[str] = cursor.get("endCursor") if isinstance(cursor, dict) else None
            next_page_token: Optional[bytes] = (
                end_cursor.encode()
                if isinstance(cursor, dict) and cursor.get("hasNextPage") and end_cursor
                else None
            )
            return sui_prot.ListDynamicFieldsResponse(
                dynamic_fields=fields,
                next_page_token=next_page_token,
            )

        return _encode


class GetChainIdentifier(PGQL_QueryNode):
    """Query the chain identifier (network genesis checkpoint digest)."""

    def __init__(self) -> None:
        """."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        return gql("{ chainIdentifier }")

    @staticmethod
    def encode_fn() -> Callable[[dict], str]:
        """Return deserializer extracting chain identifier string."""

        def _encode(in_data: dict) -> str:
            return in_data.get("chainIdentifier", "")

        return _encode


class GetChainIdentifierSC(GetChainIdentifier):
    """SC variant: encode_fn returns chain identifier as plain str."""

    @staticmethod
    def encode_fn() -> Callable[[dict], str]:
        """Return deserializer producing chain identifier string."""

        def _encode(in_data: dict) -> str:
            return in_data.get("chainIdentifier", "")

        return _encode


def _bcs_validator_to_proto(bcs_v: "sui_system_bcs.Validator") -> sui_prot.Validator:
    """Build sui_prot.Validator from a deserialized sui_system_bcs.Validator."""
    md = bcs_v.metadata
    sp = bcs_v.staking_pool
    staking_pool = sui_prot.StakingPool(
        id=sp.id.to_address_str() if sp.id else None,
        activation_epoch=sp.activation_epoch,
        sui_balance=sp.sui_balance,
        rewards_pool=sp.rewards_pool,
        pool_token_balance=sp.pool_token_balance,
        pending_stake=sp.pending_stake,
        pending_total_sui_withdraw=sp.pending_total_sui_withdraw,
        pending_pool_token_withdraw=sp.pending_pool_token_withdraw,
    )
    return sui_prot.Validator(
        name=md.name,
        address=md.sui_address.to_address_str(),
        description=md.description,
        image_url=md.image_url.url if md.image_url else None,
        project_url=md.project_url.url if md.project_url else None,
        voting_power=bcs_v.voting_power,
        gas_price=bcs_v.gas_price,
        commission_rate=bcs_v.commission_rate,
        next_epoch_stake=bcs_v.next_epoch_stake,
        next_epoch_gas_price=bcs_v.next_epoch_gas_price,
        next_epoch_commission_rate=bcs_v.next_epoch_commission_rate,
        staking_pool=staking_pool,
    )


def _bcs_system_state_to_proto(bcs_ss: "sui_system_bcs.SuiSystemStateInnerV2") -> sui_prot.SystemState:
    """Build sui_prot.SystemState from a deserialized sui_system_bcs.SuiSystemStateInnerV2."""
    params = bcs_ss.parameters
    system_parameters = sui_prot.SystemParameters(
        epoch_duration_ms=params.epoch_duration_ms,
        stake_subsidy_start_epoch=params.stake_subsidy_start_epoch,
        min_validator_count=params.min_validator_count,
        max_validator_count=params.max_validator_count,
        min_validator_joining_stake=params.min_validator_joining_stake,
        validator_low_stake_threshold=params.validator_low_stake_threshold,
        validator_very_low_stake_threshold=params.validator_very_low_stake_threshold,
    )
    subsidy = bcs_ss.stake_subsidy
    stake_subsidy = sui_prot.StakeSubsidy(
        balance=subsidy.balance,
        distribution_counter=subsidy.distribution_counter,
        current_distribution_amount=subsidy.current_distribution_amount,
        stake_subsidy_period_length=subsidy.stake_subsidy_period_length,
        stake_subsidy_decrease_rate=subsidy.stake_subsidy_decrease_rate,
    )
    sf = bcs_ss.storage_fund
    storage_fund = sui_prot.StorageFund(
        total_object_storage_rebates=sf.total_object_storage_rebates,
        non_refundable_balance=sf.non_refundable_balance,
    )
    vs = bcs_ss.validators
    validator_set = sui_prot.ValidatorSet(
        total_stake=vs.total_stake,
        active_validators=[_bcs_validator_to_proto(v) for v in vs.active_validators],
        pending_removals=list(vs.pending_removals),
    )
    return sui_prot.SystemState(
        version=bcs_ss.system_state_version,
        epoch=bcs_ss.epoch,
        reference_gas_price=bcs_ss.reference_gas_price,
        parameters=system_parameters,
        stake_subsidy=stake_subsidy,
        storage_fund=storage_fund,
        validators=validator_set,
        safe_mode=bcs_ss.safe_mode,
        epoch_start_timestamp_ms=bcs_ss.epoch_start_timestamp_ms,
    )


def _encode_validator_from_gql(v: dict, *, name_key: str = "validator_name", address_key: str = "validator_address") -> sui_prot.Validator:
    """Build a sui_prot.Validator from a GQL validator dict."""
    def _int(val):
        return int(val) if val is not None else None

    sp = sui_prot.StakingPool(
        id=v.get("staking_pool_address"),
        activation_epoch=v.get("stakingPoolActivationEpoch"),
        sui_balance=_int(v.get("stakingPoolSuiBalance")),
        rewards_pool=_int(v.get("rewardsPool")),
        pool_token_balance=_int(v.get("poolTokenBalance")),
        pending_stake=_int(v.get("pendingStake")),
        pending_total_sui_withdraw=_int(v.get("pendingTotalSuiWithdraw")),
        pending_pool_token_withdraw=_int(v.get("pendingPoolTokenWithdraw")),
    )
    return sui_prot.Validator(
        name=v.get(name_key),
        address=v.get(address_key),
        description=v.get("description"),
        image_url=v.get("imageUrl"),
        project_url=v.get("projectUrl"),
        voting_power=_int(v.get("votingPower")),
        gas_price=_int(v.get("gasPrice")),
        commission_rate=_int(v.get("commissionRate")),
        next_epoch_stake=_int(v.get("nextEpochStake")),
        next_epoch_gas_price=_int(v.get("nextEpochGasPrice")),
        next_epoch_commission_rate=_int(v.get("nextEpochCommissionRate")),
        staking_pool=sp,
    )


class GetLatestSuiSystemStateSC(GetLatestSuiSystemState):
    """SC variant: inherits BCS query from base; decodes systemState.bcs to SystemState proto."""

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.SystemState]:
        """Decode BCS system-state blob to SystemState proto."""

        def _encode(in_data: dict) -> sui_prot.SystemState:
            bcs_b64 = (in_data.get("epoch") or {}).get("systemState", {}).get("bcs")
            if not bcs_b64:
                return sui_prot.SystemState()
            bcs_bytes = base64.b64decode(bcs_b64)
            bcs_ss = sui_system_bcs.SuiSystemStateInnerV2.deserialize(bcs_bytes)
            return _bcs_system_state_to_proto(bcs_ss)

        return _encode


class GetCurrentValidatorsSC(GetCurrentValidators):
    """SC variant: inherits BCS query from base; decodes contents.bcs to list[Validator] proto."""

    def __init__(self, next_page: pgql_type.PagingCursor | None = None):
        """QueryNode initializer."""
        super().__init__(next_page=next_page)

    @staticmethod
    def encode_fn() -> Callable[[list], list[sui_prot.Validator]]:
        """Decode BCS validator blobs to list[Validator] proto."""

        def _encode(validators_data: list) -> list[sui_prot.Validator]:
            result = []
            for node in validators_data:
                if not isinstance(node, dict):
                    continue
                bcs_b64 = (node.get("contents") or {}).get("bcs")
                if not bcs_b64:
                    continue
                bcs_bytes = base64.b64decode(bcs_b64)
                bcs_v = sui_system_bcs.Validator.deserialize(bcs_bytes)
                result.append(_bcs_validator_to_proto(bcs_v))
            return result

        return _encode


def _parse_gql_datetime(ts_str: "str | None") -> "datetime.datetime | None":
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(ts_str)


def _encode_argument(arg_dict: dict) -> "sui_prot.Argument":
    tn = arg_dict.get("__typename")
    if tn == "GasCoin":
        return sui_prot.Argument(kind=sui_prot.ArgumentArgumentKind.GAS)
    if tn == "Input":
        return sui_prot.Argument(
            kind=sui_prot.ArgumentArgumentKind.INPUT,
            input=arg_dict.get("input_index"),
        )
    if tn == "TxResult":
        ix = arg_dict.get("result_index")
        return sui_prot.Argument(
            kind=sui_prot.ArgumentArgumentKind.RESULT,
            result=arg_dict.get("cmd"),
            subresult=ix,
        )
    return sui_prot.Argument()


def _encode_ptb_inputs(inputs_conn: "dict | None") -> "list[sui_prot.Input]":
    if not inputs_conn:
        return []
    nodes = inputs_conn.get("nodes") or []
    result = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        tn = node.get("input_typename")
        if tn == "OwnedOrImmutable":
            obj = node.get("object") or {}
            inp = sui_prot.Input(
                kind=sui_prot.InputInputKind.IMMUTABLE_OR_OWNED,
                object_id=obj.get("address"),
                version=obj.get("version"),
                digest=obj.get("digest"),
            )
        elif tn == "Pure":
            b64 = node.get("base64_bytes")
            inp = sui_prot.Input(
                kind=sui_prot.InputInputKind.PURE,
                pure=base64.b64decode(b64) if b64 else b"",
            )
        elif tn == "SharedInput":
            inp = sui_prot.Input(
                kind=sui_prot.InputInputKind.SHARED,
                object_id=node.get("address"),
                version=node.get("initialSharedVersion"),
                mutable=node.get("mutable"),
            )
        elif tn == "Receiving":
            obj = node.get("object") or {}
            inp = sui_prot.Input(
                kind=sui_prot.InputInputKind.RECEIVING,
                object_id=obj.get("address"),
                version=obj.get("version"),
                digest=obj.get("digest"),
            )
        else:
            inp = sui_prot.Input()
        result.append(inp)
    return result


def _encode_ptb_commands(commands_conn: "dict | None") -> "list[sui_prot.Command]":
    if not commands_conn:
        return []
    nodes = commands_conn.get("nodes") or []
    result = []
    for cmd in nodes:
        if not isinstance(cmd, dict):
            continue
        tn = cmd.get("tx_typename")
        if tn == "MoveCallCommand":
            func = cmd.get("function") or {}
            module = func.get("module") or {}
            package = module.get("package") or {}
            result.append(
                sui_prot.Command(
                    move_call=sui_prot.MoveCall(
                        package=package.get("address"),
                        module=module.get("name"),
                        function=func.get("name"),
                        arguments=[
                            _encode_argument(a) for a in (cmd.get("arguments") or [])
                        ],
                    )
                )
            )
        elif tn == "TransferObjectsCommand":
            result.append(
                sui_prot.Command(
                    transfer_objects=sui_prot.TransferObjects(
                        objects=[
                            _encode_argument(a) for a in (cmd.get("inputs") or [])
                        ],
                        address=_encode_argument(cmd.get("address") or {}),
                    )
                )
            )
        elif tn == "SplitCoinsCommand":
            result.append(
                sui_prot.Command(
                    split_coins=sui_prot.SplitCoins(
                        coin=_encode_argument(cmd.get("coin") or {}),
                        amounts=[
                            _encode_argument(a) for a in (cmd.get("amounts") or [])
                        ],
                    )
                )
            )
        elif tn == "MergeCoinsCommand":
            result.append(
                sui_prot.Command(
                    merge_coins=sui_prot.MergeCoins(
                        coin=_encode_argument(cmd.get("coin") or {}),
                        coins_to_merge=[
                            _encode_argument(a) for a in (cmd.get("coins") or [])
                        ],
                    )
                )
            )
        elif tn == "PublishCommand":
            result.append(
                sui_prot.Command(
                    publish=sui_prot.Publish(
                        modules=[
                            base64.b64decode(m) for m in (cmd.get("modules") or [])
                        ],
                        dependencies=cmd.get("dependencies") or [],
                    )
                )
            )
        elif tn == "UpgradeCommand":
            result.append(
                sui_prot.Command(
                    upgrade=sui_prot.Upgrade(
                        modules=[
                            base64.b64decode(m) for m in (cmd.get("modules") or [])
                        ],
                        dependencies=cmd.get("dependencies") or [],
                        package=cmd.get("currentPackage"),
                        ticket=_encode_argument(cmd.get("upgradeTicket") or {}),
                    )
                )
            )
        elif tn == "MakeMoveVecCommand":
            vtype = (cmd.get("vector_type") or {}).get("repr")
            result.append(
                sui_prot.Command(
                    make_move_vector=sui_prot.MakeMoveVector(
                        element_type=vtype,
                        elements=[
                            _encode_argument(a) for a in (cmd.get("elements") or [])
                        ],
                    )
                )
            )
        else:
            result.append(sui_prot.Command())
    return result


def _encode_programmable_tx(kind_dict: dict) -> "sui_prot.ProgrammableTransaction":
    return sui_prot.ProgrammableTransaction(
        inputs=_encode_ptb_inputs(kind_dict.get("inputs")),
        commands=_encode_ptb_commands(kind_dict.get("commands")),
    )


def _encode_ccp_kind(kind_dict: dict) -> "sui_prot.ConsensusCommitPrologue":
    return sui_prot.ConsensusCommitPrologue(
        epoch=(kind_dict.get("epoch") or {}).get("epochId"),
        round=kind_dict.get("consensusRound"),
        commit_timestamp=_parse_gql_datetime(kind_dict.get("commitTimestamp")),
        consensus_commit_digest=kind_dict.get("consensusCommitDigest"),
        sub_dag_index=kind_dict.get("subDagIndex"),
        additional_state_digest=kind_dict.get("additionalStateDigest"),
    )


def _encode_auth_state_update_kind(kind_dict: dict) -> "sui_prot.AuthenticatorStateUpdate":
    jwks = []
    for node in ((kind_dict.get("newActiveJwks") or {}).get("nodes") or []):
        jwk_id = sui_prot.JwkId(iss=node.get("iss"), kid=node.get("kid"))
        jwk = sui_prot.Jwk(
            kty=node.get("kty"), e=node.get("e"), n=node.get("n"), alg=node.get("alg")
        )
        epoch_id = (node.get("epoch") or {}).get("epochId")
        jwks.append(sui_prot.ActiveJwk(id=jwk_id, jwk=jwk, epoch=epoch_id))
    return sui_prot.AuthenticatorStateUpdate(
        epoch=(kind_dict.get("epoch") or {}).get("epochId"),
        round=kind_dict.get("consensusRound"),
        new_active_jwks=jwks,
        authenticator_object_initial_shared_version=kind_dict.get(
            "authenticatorObjInitialSharedVersion"
        ),
    )


def _encode_randomness_update_kind(kind_dict: dict) -> "sui_prot.RandomnessStateUpdate":
    rb = kind_dict.get("randomBytes")
    return sui_prot.RandomnessStateUpdate(
        epoch=(kind_dict.get("epoch") or {}).get("epochId"),
        randomness_round=kind_dict.get("randomnessRound"),
        random_bytes=base64.b64decode(rb) if rb else b"",
        randomness_object_initial_shared_version=kind_dict.get(
            "randomnessObjInitialSharedVersion"
        ),
    )


def _encode_change_epoch_kind(kind_dict: dict) -> "sui_prot.ChangeEpoch":
    return sui_prot.ChangeEpoch(
        epoch=(kind_dict.get("epoch") or {}).get("epochId"),
        protocol_version=(kind_dict.get("protocolConfigs") or {}).get("protocolVersion"),
        storage_charge=int(kind_dict.get("storageCharge") or 0),
        computation_charge=int(kind_dict.get("computationCharge") or 0),
        storage_rebate=int(kind_dict.get("storageRebate") or 0),
        non_refundable_storage_fee=int(kind_dict.get("nonRefundableStorageFee") or 0),
        epoch_start_timestamp=_parse_gql_datetime(kind_dict.get("epochStartTimestamp")),
    )


def _encode_end_of_epoch_kind(kind_dict: dict) -> "sui_prot.EndOfEpochTransaction":
    transactions = []
    for node in ((kind_dict.get("transactions") or {}).get("nodes") or []):
        tx_kind = node.get("tx_kind")
        if tx_kind == "ChangeEpochTransaction":
            transactions.append(
                sui_prot.EndOfEpochTransactionKind(
                    change_epoch=_encode_change_epoch_kind(node)
                )
            )
        elif tx_kind == "AuthenticatorStateExpireTransaction":
            min_epoch = (node.get("minEpoch") or {}).get("epochId")
            transactions.append(
                sui_prot.EndOfEpochTransactionKind(
                    authenticator_state_expire=sui_prot.AuthenticatorStateExpire(
                        min_epoch=min_epoch,
                        authenticator_object_initial_shared_version=node.get(
                            "authenticatorObjInitialSharedVersion"
                        ),
                    )
                )
            )
        else:
            transactions.append(sui_prot.EndOfEpochTransactionKind())
    return sui_prot.EndOfEpochTransaction(transactions=transactions)


def _encode_genesis_kind(kind_dict: dict) -> "sui_prot.GenesisTransaction":
    objs = []
    for node in ((kind_dict.get("objects") or {}).get("nodes") or []):
        objs.append(
            sui_prot.Object(
                object_id=node.get("address"),
                version=node.get("version"),
                digest=node.get("digest"),
            )
        )
    return sui_prot.GenesisTransaction(objects=objs)


def _encode_tx_kind(kind_dict: dict) -> "sui_prot.TransactionKind":
    tn = kind_dict.get("tx_kind")
    if tn == "ProgrammableTransaction":
        return sui_prot.TransactionKind(
            programmable_transaction=_encode_programmable_tx(kind_dict)
        )
    if tn == "ChangeEpochTransaction":
        return sui_prot.TransactionKind(change_epoch=_encode_change_epoch_kind(kind_dict))
    if tn == "GenesisTransaction":
        return sui_prot.TransactionKind(genesis=_encode_genesis_kind(kind_dict))
    if tn == "ConsensusCommitPrologueTransaction":
        return sui_prot.TransactionKind(
            consensus_commit_prologue=_encode_ccp_kind(kind_dict)
        )
    if tn == "AuthenticatorStateUpdateTransaction":
        return sui_prot.TransactionKind(
            authenticator_state_update=_encode_auth_state_update_kind(kind_dict)
        )
    if tn == "EndOfEpochTransaction":
        return sui_prot.TransactionKind(end_of_epoch=_encode_end_of_epoch_kind(kind_dict))
    if tn == "RandomnessStateUpdateTransaction":
        return sui_prot.TransactionKind(
            randomness_state_update=_encode_randomness_update_kind(kind_dict)
        )
    return sui_prot.TransactionKind()


def _encode_gas_payment(
    gas_input: dict, sender_addr: "str | None"
) -> "sui_prot.GasPayment":
    sponsor = gas_input.get("sponsor") or {}
    owner = sponsor.get("sponsor_address") or sender_addr
    gas_objects = (gas_input.get("sponsor_pay_with") or {}).get("gas_objects") or []
    obj_refs = [
        sui_prot.ObjectReference(
            object_id=go.get("object_id"),
            version=go.get("version"),
            digest=go.get("object_digest"),
        )
        for go in gas_objects
        if isinstance(go, dict)
    ]
    return sui_prot.GasPayment(
        objects=obj_refs,
        owner=owner,
        price=int(gas_input.get("price") or 0),
        budget=int(gas_input.get("transaction_budget") or 0),
    )


def _encode_expiration(
    exp_dict: "dict | None",
) -> "sui_prot.TransactionExpiration | None":
    if not exp_dict:
        return None
    epoch_id = exp_dict.get("epochId")
    if epoch_id is not None:
        return sui_prot.TransactionExpiration(
            kind=sui_prot.TransactionExpirationTransactionExpirationKind.EPOCH,
            epoch=epoch_id,
        )
    return None


def _encode_balance_changes(nodes: list) -> "list[sui_prot.BalanceChange]":
    result = []
    for bc in nodes:
        if not isinstance(bc, dict):
            continue
        coin_type_dict = bc.get("coinType") or {}
        result.append(
            sui_prot.BalanceChange(
                address=(bc.get("change_to") or {}).get("object_id"),
                coin_type=coin_type_dict.get("coin_type"),
                amount=bc.get("balance_change"),
            )
        )
    return result


def _encode_executed_tx(
    tx_dict: "dict | None",
) -> "sui_prot.ExecutedTransaction | None":
    if not tx_dict:
        return None
    digest = tx_dict.get("digest")
    if not digest:
        return None

    sigs = []
    for s in (tx_dict.get("signatures") or []):
        sig_bytes = s.get("signatureBytes")
        if sig_bytes:
            sigs.append(
                sui_prot.UserSignature(
                    bcs=sui_prot.Bcs(value=base64.b64decode(sig_bytes))
                )
            )

    kind_dict = tx_dict.get("kind") or {}
    tx_kind = _encode_tx_kind(kind_dict)

    sender_dict = tx_dict.get("sender") or {}
    sender_addr = sender_dict.get("submitter_address")

    expiration = _encode_expiration(tx_dict.get("expiration"))

    gas_input = tx_dict.get("gasInput") or {}
    gas_payment = _encode_gas_payment(gas_input, sender_addr)

    tx_bcs_b64 = tx_dict.get("transactionBcs")
    tx_bcs = sui_prot.Bcs(value=base64.b64decode(tx_bcs_b64)) if tx_bcs_b64 else None

    eff_dict = tx_dict.get("effects") or {}
    status_str = eff_dict.get("status")
    exec_status = (
        sui_prot.ExecutionStatus(success=(status_str == "SUCCESS")) if status_str else None
    )

    gas_effects = eff_dict.get("gasEffects") or {}
    gas_summary = gas_effects.get("gasSummary") or {}
    gas_used = sui_prot.GasCostSummary(
        computation_cost=int(gas_summary.get("computationCost") or 0),
        storage_cost=int(gas_summary.get("storageCost") or 0),
        storage_rebate=int(gas_summary.get("storageRebate") or 0),
        non_refundable_storage_fee=int(gas_summary.get("nonRefundableStorageFee") or 0),
    )

    bc_nodes = (eff_dict.get("balanceChanges") or {}).get("nodes") or []
    balance_changes = _encode_balance_changes(bc_nodes)

    checkpoint_dict = eff_dict.get("checkpoint") or {}
    checkpoint_seq = checkpoint_dict.get("sequenceNumber")
    checkpoint_epoch = (checkpoint_dict.get("epoch") or {}).get("epochId")
    ts_str = eff_dict.get("timestamp") or checkpoint_dict.get("timestamp")
    timestamp = _parse_gql_datetime(ts_str)

    effects_bcs_b64 = eff_dict.get("effectsBcs")
    effects_bcs = (
        sui_prot.Bcs(value=base64.b64decode(effects_bcs_b64)) if effects_bcs_b64 else None
    )

    return sui_prot.ExecutedTransaction(
        digest=digest,
        transaction=sui_prot.Transaction(
            bcs=tx_bcs,
            kind=tx_kind,
            sender=sender_addr,
            gas_payment=gas_payment,
            expiration=expiration,
        ),
        signatures=sigs,
        effects=sui_prot.TransactionEffects(
            bcs=effects_bcs,
            status=exec_status,
            epoch=checkpoint_epoch,
            gas_used=gas_used,
        ),
        balance_changes=balance_changes,
        checkpoint=checkpoint_seq,
        timestamp=timestamp,
    )
