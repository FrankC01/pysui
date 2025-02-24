#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-#

"""QueryNode generators."""

from typing import Optional, Callable, Union, Any
from deprecated.sphinx import versionadded, deprecated
from gql import gql
from gql.dsl import (
    DSLQuery,
    dsl_gql,
    DSLSchema,
    DSLMetaField,
    DSLInlineFragment,
    DSLMutation,
)
from graphql import DocumentNode

from pysui.sui.sui_pgql.pgql_clients import PGQL_QueryNode, PGQL_NoOp
import pysui.sui.sui_pgql.pgql_types as pgql_type
import pysui.sui.sui_pgql.pgql_fragments as frag
from pysui.sui.sui_pgql.pgql_validators import TypeValidator


class GetCoinMetaData(PGQL_QueryNode):
    """GetCoinMetaData returns meta data for a specific `coin_type`."""

    def __init__(self, *, coin_type: Optional[str] = "0x2::sui::SUI") -> None:
        """QueryNode initializer.

        :param coin_type: The specific coin type string, defaults to "0x2::sui::SUI"
        :type coin_type: str, optional
        """
        self.coin_type = coin_type

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build the DocumentNode."""
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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
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
                schema.Balance.coinObjectCount,
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


class GetCoinSummary(PGQL_QueryNode):
    """GetCoinSummary Returns balance,digest and version"""

    def __init__(self, *, owner: str, coin_id: str):
        """Set up."""
        self.owner = owner
        self.coin_id = coin_id

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""

        _QUERY = """
            {
            address(
                address: "OWNER"
            ) {
                objects (filter:{objectIds:["COIN_ID"]}) {
                nodes {
                    asCoin {
                        coin_object_id:address
                        object_digest:digest
                        version
                        balance:coinBalance
                    }
                }
                }
            }
            }
        """
        _QUERY = _QUERY.replace("OWNER", self.owner).replace("COIN_ID", self.coin_id)
        return gql(_QUERY)

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinObjectSummaryGQL]:
        """Return summary serialized to data object."""
        return pgql_type.SuiCoinObjectSummaryGQL.from_query


class GetCoins(PGQL_QueryNode):
    """GetCoins Returns all Coin objects of a specific type for owner."""

    def __init__(
        self,
        *,
        owner: str,
        coin_type: Optional[str] = "0x2::sui::SUI",
        next_page: Optional[pgql_type.PagingCursor] = None,
    ):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param coin_type: The coin type to use in filtering, defaults to "0x2::sui::SUI"
        :type coin_type: str, optional
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.owner = owner
        self.coin_type = coin_type
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.address(address=self.owner).alias("qres")
        coin_connection = schema.Address.coins(type=self.coin_type).alias("coins")
        if self.next_page:
            coin_connection(after=self.next_page.endCursor)

        std_coin = frag.StandardCoin()
        pg_cursor = frag.PageCursor()
        coin_connection.select(std_coin.fragment(schema))
        qres.select(coin_connection)
        return dsl_gql(
            std_coin.fragment(schema), pg_cursor.fragment(schema), DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinObjectsGQL]:
        """Return the serializer to SuiCoinObjectsGQL function."""
        return pgql_type.SuiCoinObjectsGQL.from_query


class GetLatestSuiSystemState(PGQL_QueryNode):
    """GetLatestSuiSystemState return the latest known SUI system state."""

    def __init__(self) -> None:
        """QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
        qres = schema.Query.epoch.alias("qres").select(
            schema.Epoch.totalTransactions,
            schema.Epoch.systemStateVersion,
            schema.Epoch.referenceGasPrice,
            schema.Epoch.systemParameters.select(
                schema.SystemParameters.durationMs,
                schema.SystemParameters.stakeSubsidyStartEpoch,
                schema.SystemParameters.minValidatorCount,
                schema.SystemParameters.maxValidatorCount,
                schema.SystemParameters.minValidatorJoiningStake,
                schema.SystemParameters.validatorLowStakeThreshold,
                schema.SystemParameters.validatorVeryLowStakeThreshold,
                schema.SystemParameters.validatorLowStakeThreshold,
            ),
            schema.Epoch.systemStakeSubsidy.select(
                schema.StakeSubsidy.balance,
                schema.StakeSubsidy.distributionCounter,
                schema.StakeSubsidy.currentDistributionAmount,
                schema.StakeSubsidy.periodLength,
                schema.StakeSubsidy.decreaseRate,
            ),
            schema.Epoch.validatorSet.select(
                schema.ValidatorSet.totalStake,
                schema.ValidatorSet.pendingRemovals,
                schema.ValidatorSet.pendingActiveValidatorsSize,
                schema.ValidatorSet.inactivePoolsSize,
                schema.ValidatorSet.validatorCandidatesSize,
                validators=schema.ValidatorSet.activeValidators.select(
                    validators=schema.ValidatorConnection.nodes.select(
                        schema.Validator.description,
                        schema.Validator.projectUrl,
                        schema.Validator.commissionRate,
                        schema.Validator.stakingPoolSuiBalance,
                        schema.Validator.pendingStake,
                        schema.Validator.pendingPoolTokenWithdraw,
                        schema.Validator.pendingTotalSuiWithdraw,
                        schema.Validator.votingPower,
                        schema.Validator.gasPrice,
                        schema.Validator.atRisk,
                        schema.Validator.nextEpochStake,
                        schema.Validator.nextEpochCommissionRate,
                        schema.Validator.nextEpochGasPrice,
                        schema.Validator.address.select(
                            validatorAddress=schema.Address.address
                        ),
                        validatorName=schema.Validator.name,
                    ),
                ),
            ),
            schema.Epoch.storageFund.select(
                schema.StorageFund.totalObjectStorageRebates,
                schema.StorageFund.nonRefundableBalance,
            ),
            schema.Epoch.safeMode.select(schema.SafeMode.enabled),
            # schema.SuiSystemStateSummary.startTimestamp,
            schema.Epoch.epochId,
            schema.Epoch.startTimestamp,
            schema.Epoch.endTimestamp,
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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode"""
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
        return pgql_type.ObjectReadGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
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


class GetMultipleGasObjects(PGQL_QueryNode):
    """Return basic Sui gas represnetation for each coin_id string."""

    def __init__(self, *, coin_object_ids: list[str]):
        """QueryNode initializer.

        :param coin_object_ids: list of object ids to fetch
        :type coin_object_ids: list[str]
        """
        self.coin_ids = coin_object_ids

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:

        qres = schema.Query.objects(filter={"objectIds": self.coin_ids}).select(
            schema.ObjectConnection.nodes.select(
                schema.Object.version,
                object_id=schema.Object.address,
                object_kind=schema.Object.status,
                amo=schema.Object.asMoveObject.select(
                    schema.MoveObject.asCoin.select(
                        schema.Coin.version,
                        schema.Coin.hasPublicTransfer,
                        schema.Coin.previousTransactionBlock.select(
                            previous_transaction=schema.TransactionBlock.digest
                        ),
                        schema.Coin.owner.select(
                            DSLInlineFragment()
                            .on(schema.AddressOwner)
                            .select(
                                schema.AddressOwner.owner.select(
                                    coin_owner=schema.Owner.address
                                )
                            ),
                        ),
                        schema.Coin.contents.select(
                            schema.MoveValue.type.select(coin_type=schema.MoveType.repr)
                        ),
                        object_digest=schema.Coin.digest,
                        balance=schema.Coin.coinBalance,
                        coin_object_id=schema.Coin.address,
                    ),
                ),
            )
        )
        return dsl_gql(
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.SuiCoinFromObjectsGQL]:
        """Return the serializer to SuiCoinFromObjectsGQL function."""
        return pgql_type.SuiCoinFromObjectsGQL.from_query


class GetMultipleObjects(PGQL_QueryNode):
    """Returns object data for list of object ids."""

    def __init__(
        self,
        *,
        object_ids: list[str],
        next_page: Optional[pgql_type.PagingCursor] = None,
    ):
        """QueryNode initializer.

        :param object_ids: List of Sui object_ids hex string prefixed with 0x
        :type object_ids: list[str]
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.object_ids = TypeValidator.check_object_ids(object_ids)
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.objects(filter={"objectIds": self.object_ids})
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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
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
        return pgql_type.ObjectReadGQL.from_query


@deprecated(
    version="0.76.0",
    reason="Deprecated by Sui. Use GetMultipleVersionedObjects instead",
)
class GetMultiplePastObjects(PGQL_QueryNode):
    """GetMultiplePastObjects When executed, return the object information for a specified version.

    Note there is no software-level guarantee/SLA that objects with past versions can be retrieved by this API,
    even if the object and version exists/existed. The result may vary across nodes depending on their pruning
    policies.
    """

    def __init__(self, *, for_versions: list[dict]):
        """QueryNode initializer to fetch past object information for a list of object keys.

        Where each `dict` (key) is of construct:
        {
            objectId:str, # Object id
            version:int   # Previous version id to fetch
        }

        :param history: The list of ObjectKsy dictionaries
        :type history: list[dict]

        """

        self.version_list = for_versions

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)

        return dsl_gql(
            std_object,
            base_object,
            pg_cursor,
            DSLQuery(
                schema.Query.objects(filter={"objectKeys": self.version_list}).select(
                    cursor=schema.ObjectConnection.pageInfo.select(pg_cursor),
                    objects_data=schema.ObjectConnection.nodes.select(std_object),
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadsGQL]:
        """Return the serializer to ObjectReadsGQL function."""
        return pgql_type.ObjectReadsGQL.from_query


@versionadded(version="0.76.0", reason="Sui 1.40.0 introduced")
class GetMultipleVersionedObjects(PGQL_QueryNode):
    """GetMultipleVersionedObjects When executed, return the object information for a specified version.

    Note there is no software-level guarantee/SLA that objects with past versions can be retrieved by this API,
    even if the object and version exists/existed. The result may vary across nodes depending on their pruning
    policies.
    """

    def __init__(self, *, for_versions: list[dict[str, int]]):
        """QueryNode initializer to fetch past object information for a list of object keys.

        Where each `dict` (key) is of construct:
        {
            objectId:str, # Object id
            version:int   # Version to fetch
        }

        :param history: The list of ObjectKey dictionaries
        :type history: list[dict]

        """

        self.version_list = for_versions

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
                    name_data=schema.MoveValue.data,
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
        return pgql_type.DynamicFieldsGQL.from_query


class GetEvents(PGQL_QueryNode):
    """GetEvents When executed, return list of events for the filter choice."""

    def __init__(
        self,
        *,
        event_filter: dict,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """QueryNode initializer to query chain events of type defined by event_filter.

        Choice is one key/value pair of:
            {
                'sender': 'SOME_SUI_ACCOUNT'
            },
            {
                'transactionDigest': 'SOME_SUI_TX_DIGEST'
            },
            {
                'emittingModule': 'FULLY QUALIFIED MODULE'
            },
            {
                'eventType': 'FULLY QUALIFED EVENT TYPE'
            }

        Example filter:
          {
              "eventType": "0x3::validator::StakingRequestEvent"
          }

        :param event_filter: Filter key/values aligned to Sui GraphQL schema's EventFilter
        :type event_filter: dict
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.event_filter = event_filter
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
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


class GetTx(PGQL_QueryNode):
    """GetTx When executed, return the transaction response object."""

    def __init__(self, *, digest: str) -> None:
        """QueryNode initializer to fetch a transaction by digest id.

        :param digest: The transaction digest to fetch
        :type digest: str
        """
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Builds the GQL DocumentNode

        :return: The transaction query DocumentNode for specific digest
        :rtype: DocumentNode
        """
        std_txn = frag.StandardTransaction().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.transactionBlock(digest=self.digest)
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
        return pgql_type.TransactionResultGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Builds the GQL DocumentNode

        :return: The transactions query DocumentNode
        :rtype: DocumentNode
        """
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.transactionBlocks(filter=self.qfilter)
        if self.next_page:
            qres(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor().fragment(schema)
        qres.select(
            cursor=schema.TransactionBlockConnection.pageInfo.select(pg_cursor),
            tx_blocks=schema.TransactionBlockConnection.nodes.select(
                schema.TransactionBlock.digest,
                schema.TransactionBlock.signatures,
                schema.TransactionBlock.effects.select(
                    schema.TransactionBlockEffects.status,
                    schema.TransactionBlockEffects.timestamp,
                    schema.TransactionBlockEffects.errors,
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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Builds the GQL DocumentNode

        :return: The transactions query DocumentNode
        :rtype: DocumentNode
        """
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.transactionBlocks(filter=self.filter)
        if self.next_page:
            qres(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor().fragment(schema)

        qres.select(
            cursor=schema.TransactionBlockConnection.pageInfo.select(pg_cursor),
            tx_blocks=schema.TransactionBlockConnection.nodes.select(
                schema.TransactionBlock.digest,
                schema.TransactionBlock.signatures,
                schema.TransactionBlock.kind.select(tx_kind=DSLMetaField("__typename")),
                schema.TransactionBlock.effects.select(
                    schema.TransactionBlockEffects.status,
                    schema.TransactionBlockEffects.timestamp,
                    schema.TransactionBlockEffects.errors,
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


class GetTxKind(PGQL_QueryNode):
    """Gets details of Transaction kind."""

    def __init__(self, digest: str):
        """QueryNode initializer."""
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Builds the GQL DocumentNode

        :return: The transaction query DocumentNode for specific digest
        :rtype: DocumentNode
        """
        tx_kind = frag.StandardTransactionKind().fragment(schema)
        prg_kind = frag.ProgrammableTxKind().fragment(schema)
        ccp_kind = frag.ConsensusCommitPrologueKind().fragment(schema)

        qres = schema.Query.transactionBlock(digest=self.digest).select(
            schema.TransactionBlock.digest,
            schema.TransactionBlock.effects.select(
                schema.TransactionBlockEffects.timestamp
            ),
            tx_kind,
        )
        return dsl_gql(prg_kind, tx_kind, ccp_kind, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.TransactionKindGQL], None]:
        """Return the serializer to TransactionKindGQL function."""
        return pgql_type.TransactionKindGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        qres = schema.Query.address(address=self.owner)
        staked_coin = schema.Address.stakedSuis
        if self.next_page:
            staked_coin(after=self.next_page.endCursor)

        # Build fragment
        pg_cursor = frag.PageCursor()

        staked_coin.select(
            cursor=schema.StakedSuiConnection.pageInfo.select(
                pg_cursor.fragment(schema)
            ),
            staked_coin=schema.StakedSuiConnection.nodes.select(
                schema.StakedSui.poolId,
                schema.StakedSui.version,
                schema.StakedSui.hasPublicTransfer,
                schema.StakedSui.principal,
                schema.StakedSui.estimatedReward,
                schema.StakedSui.owner.select(
                    DSLInlineFragment()
                    .on(schema.AddressOwner)
                    .select(
                        schema.AddressOwner.owner.select(
                            address_id=schema.Owner.address
                        ),
                        obj_owner_kind=DSLMetaField("__typename"),
                    ),
                    DSLInlineFragment()
                    .on(schema.Shared)
                    .select(
                        initial_version=schema.Shared.initialSharedVersion,
                        obj_owner_kind=DSLMetaField("__typename"),
                    ),
                    DSLInlineFragment()
                    .on(schema.Immutable)
                    .select(
                        obj_owner_kind=DSLMetaField("__typename"),
                    ),
                    DSLInlineFragment()
                    .on(schema.Parent)
                    .select(
                        schema.Parent.parent.select(parent_id=schema.Owner.address),
                        obj_owner_kind=DSLMetaField("__typename"),
                    ),
                ),
                activated=schema.StakedSui.activatedEpoch.select(schema.Epoch.epochId),
                requested=schema.StakedSui.requestedEpoch.select(schema.Epoch.epochId),
                status=schema.StakedSui.stakeStatus,
                object_digest=schema.StakedSui.digest,
                object_id=schema.StakedSui.address,
            ),
        )
        qres.select(schema.Address.address, staked_coin)
        return dsl_gql(pg_cursor.fragment(schema), DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.SuiStakedCoinsGQL], None]:
        """Return the serializer to SuiStakedCoinsGQL function."""
        return pgql_type.SuiStakedCoinsGQL.from_query


class GetLatestCheckpointSequence(PGQL_QueryNode):
    """GetLatestCheckpointSequence return the sequence number of the latest checkpoint that has been executed."""

    def __init__(self):
        """__init__ QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        std_checkpoint = frag.StandardCheckpoint()
        pg_cursor = frag.PageCursor()
        qres = schema.Query.checkpoints(last=1).select(
            schema.CheckpointConnection.nodes.select(std_checkpoint.fragment(schema))
        )
        return dsl_gql(
            pg_cursor.fragment(schema), std_checkpoint.fragment(schema), DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.CheckpointGQL], None]:
        """Return the serializer to CheckpointGQL function."""
        return pgql_type.CheckpointGQL.from_last_checkpoint


class GetCheckpointByDigest(PGQL_QueryNode):
    """GetCheckpointByDigest return a checkpoint for cp_id."""

    def __init__(self, *, digest: str):
        """__init__ QueryNode initializer.

        :param digest: Checkpoint digest id
        :type digest: str
        """
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        std_checkpoint = frag.StandardCheckpoint()
        pg_cursor = frag.PageCursor()
        qres = schema.Query.checkpoint(id={"digest": self.digest}).select(
            std_checkpoint.fragment(schema)
        )
        return dsl_gql(
            pg_cursor.fragment(schema), std_checkpoint.fragment(schema), DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.CheckpointGQL], None]:
        """Return the serializer to CheckpointGQL function."""
        return pgql_type.CheckpointGQL.from_query


class GetCheckpointBySequence(PGQL_QueryNode):
    """GetCheckpoint return a checkpoint for cp_id."""

    def __init__(self, *, sequence_number: int):
        """__init__ QueryNode initializer.

        :param sequence_number: Checkpoint sequence number
        :type cp_seq: int
        """
        self.sequence_number = sequence_number

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        std_checkpoint = frag.StandardCheckpoint()
        pg_cursor = frag.PageCursor()
        qres = schema.Query.checkpoint(
            id={"sequenceNumber": self.sequence_number}
        ).select(std_checkpoint.fragment(schema))
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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
    """Return the protocol config table for the given version number."""

    def __init__(self, *, version: int):
        """QueryNode initializer

        :param version: The protocol version to retreive
        :type version: int
        """
        self.version = version

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        std_prot_cfg = frag.StandardProtocolConfig().fragment(schema)
        qres = schema.Query.protocolConfig(protocolVersion=self.version).select(
            std_prot_cfg
        )
        return dsl_gql(std_prot_cfg, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ProtocolConfigGQL], None]:
        """Return the serialization function for ProtocolConfig."""
        return pgql_type.ProtocolConfigGQL.from_query


class GetReferenceGasPrice(PGQL_QueryNode):
    """GetReferenceGasPrice return the reference gas price for the network."""

    def __init__(self):
        """QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
    """Return the resolved name service address for name."""

    def __init__(self, *, name: str):
        """__init__ QueryNode initializer."""
        self.name = name

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        return dsl_gql(
            DSLQuery(
                schema.Query.resolveSuinsAddress(domain=self.name).select(
                    schema.Address.address
                )
            )
        )


# TODO: Need object rep
# Renamed from Builder NameServiceName
class GetNameServiceNames(PGQL_QueryNode):
    """Return the resolved names given address, if multiple names are resolved, the first one is the primary name."""

    def __init__(
        self,
        *,
        owner: str,
    ):
        """QueryNode initializer."""
        self.owner = owner

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""
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


class GetValidatorsApy(PGQL_QueryNode):
    """Return the validator APY."""

    def __init__(self, next_page: Optional[pgql_type.PagingCursor] = None):
        """QueryNode initializer."""
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp
        elif self.next_page:
            avals_q = schema.ValidatorSet.activeValidators(
                after=self.next_page.endCursor
            )
        else:
            avals_q = schema.ValidatorSet.activeValidators

        pg_cursor = frag.PageCursor().fragment(schema)
        return dsl_gql(
            pg_cursor,
            DSLQuery(
                schema.Query.checkpoint.select(
                    schema.Checkpoint.epoch.select(
                        schema.Epoch.validatorSet.select(
                            avals_q.select(
                                cursor=schema.ValidatorConnection.pageInfo.select(
                                    pg_cursor
                                ),
                                validators_apy=schema.ValidatorConnection.nodes.select(
                                    schema.Validator.name,
                                    schema.Validator.apy,
                                ),
                            ),
                        )
                    )
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ValidatorApysGQL], None]:
        """Return the serialization function for ValidatorSetGQL."""
        return pgql_type.ValidatorApysGQL.from_query


class GetCurrentValidators(PGQL_QueryNode):
    """Return the set of validators from the current Epoch."""

    def __init__(self, next_page: Optional[pgql_type.PagingCursor] = None):
        """QueryNode initializer."""
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""
        if self.next_page and not self.next_page.hasNextPage:
            return PGQL_NoOp

        active_vals = schema.ValidatorSet.activeValidators
        if self.next_page:
            active_vals(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor().fragment(schema)
        val = frag.Validator().fragment(schema)
        valset = frag.ValidatorSet().fragment(schema, active_vals)
        return dsl_gql(
            valset,
            pg_cursor,
            val,
            DSLQuery(
                schema.Query.checkpoint.select(
                    schema.Checkpoint.epoch.select(
                        schema.Epoch.validatorSet.select(valset)
                    )
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ValidatorSetsGQL], None]:
        """Return the serialization function for ValidatorSetsGQL."""
        return pgql_type.ValidatorSetsGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
    def encode_fn() -> Union[Callable[[dict], pgql_type.MoveStructureGQL], None]:
        """Return the serialization function for ReferenceGasPrice."""
        return pgql_type.MoveStructureGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
        return pgql_type.MoveStructuresGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
        return pgql_type.MoveFunctionGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
        return pgql_type.MoveFunctionsGQL.from_query


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

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
        return pgql_type.MoveModuleGQL.from_query


class GetPackage(PGQL_QueryNode):
    """GetPackage When executed, return structured representations of the package."""

    def __init__(
        self, *, package: str, next_page: Optional[pgql_type.PagingCursor] = None
    ) -> None:
        """__init__ Initialize GetPackage object."""
        self.package = package
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
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
        return pgql_type.MovePackageGQL.from_query


class DryRunTransactionKind(PGQL_QueryNode):
    """."""

    def __init__(
        self,
        *,
        tx_bytestr: str,
        tx_meta: Optional[dict] = None,
        skip_checks: Optional[bool] = True,
    ) -> None:
        """__init__ Initialize DryRunTransactionKind object.

        for the `tx_meta` argument, it expects a dictionary with one or more keys set.
        {
            sender: The Sui address string for the sender (defaults to 0x0),
            gasPrice: The gas price integer (defaults to reference gas price)
            gasObjects: list[dict] A list of gas object references, defaults to mock Coin object. Reference dict:
                {
                    address: The object id string of the gas object
                    version: The version integer of the gas object
                    digest: The digest of the gas object
                }
            gasBudget: The budget to use. Defaults to max gas budget
            gasSponsor: The Sui address string of the sponsor, defaults to the sender
        }

        """
        self.tx_data = tx_bytestr
        self.tx_meta = tx_meta if tx_meta else {}
        self.tx_skipchecks = skip_checks

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""
        std_txn = frag.StandardTransaction().fragment(schema)
        base_obj = frag.BaseObject().fragment(schema)
        standard_obj = frag.StandardObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)

        qres = (
            schema.Query.dryRunTransactionBlock(
                txBytes=self.tx_data,
                txMeta=self.tx_meta,
                skipChecks=self.tx_skipchecks,
            )
            .alias("dryRun")
            .select(
                schema.DryRunResult.error,
                schema.DryRunResult.results.select(
                    schema.DryRunEffect.returnValues.select(
                        schema.DryRunReturn.type.select(schema.MoveType.repr),
                        schema.DryRunReturn.bcs,
                    )
                ),
                transactionBlock=schema.DryRunResult.transaction.select(std_txn),
            )
        )
        return dsl_gql(
            base_obj, standard_obj, gas_cost, std_txn, tx_effects, DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.DryRunResultGQL], None]:
        """Return the serialization MovePackage."""
        return pgql_type.DryRunResultGQL.from_query


class DryRunTransaction(PGQL_QueryNode):
    """."""

    def __init__(self, *, tx_bytestr) -> None:
        """__init__ Initialize DryRunTransaction object."""
        self.tx_data = tx_bytestr

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""
        std_txn = frag.StandardTransaction().fragment(schema)
        base_obj = frag.BaseObject().fragment(schema)
        standard_obj = frag.StandardObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        tx_effects = frag.StandardTxEffects().fragment(schema)

        qres = (
            schema.Query.dryRunTransactionBlock(txBytes=self.tx_data)
            .alias("dryRun")
            .select(
                schema.DryRunResult.error,
                schema.DryRunResult.results.select(
                    schema.DryRunEffect.returnValues.select(
                        schema.DryRunReturn.type.select(schema.MoveType.repr),
                        schema.DryRunReturn.bcs,
                    )
                ),
                transactionBlock=schema.DryRunResult.transaction.select(std_txn),
            )
        )
        return dsl_gql(
            base_obj, standard_obj, gas_cost, std_txn, tx_effects, DSLQuery(qres)
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.DryRunResultGQL], None]:
        """Return the serialization MovePackage."""
        return pgql_type.DryRunResultGQL.from_query


class ExecuteTransaction(PGQL_QueryNode):
    """."""

    def __init__(self, *, tx_bytestr: str, sig_array: list[str]) -> None:
        """__init__ Initialize ExecuteTransaction object."""
        self.tx_data: str = tx_bytestr
        self.sigs: list[str] = sig_array

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """."""

        qres = schema.Mutation.executeTransactionBlock(
            txBytes=self.tx_data, signatures=self.sigs
        ).select(
            schema.ExecutionResult.errors,
            schema.ExecutionResult.effects.select(
                schema.TransactionBlockEffects.status,
                schema.TransactionBlockEffects.lamportVersion,
                schema.TransactionBlockEffects.transactionBlock.select(
                    schema.TransactionBlock.digest
                ),
                schema.TransactionBlockEffects.bcs,
            ),
        )
        return dsl_gql(DSLMutation(qres))

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ExecutionResultGQL], None]:
        """Return the serialization Execution result function."""
        return pgql_type.ExecutionResultGQL.from_query
