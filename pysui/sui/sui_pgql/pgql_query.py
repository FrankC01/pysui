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

# -*- coding: utf-8 -*-#

"""QueryNode generators."""

from typing import Optional, Callable, Union, Any
from gql.dsl import DSLQuery, dsl_gql, DSLSchema
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
            object_data=schema.CoinMetadata.asMoveObject.select(
                schema.MoveObject.asObject.select(meta_object_id=schema.Object.location)
            ),
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
        balance_connection = schema.Address.balanceConnection
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
        qres.select(owner_address=schema.Address.location, balances=balance_connection)

        return dsl_gql(pg_cursor.fragment(schema), DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.BalancesGQL]:
        """Return the serializer to BalancesGQL function."""
        return pgql_type.BalancesGQL.from_query


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
        coin_connection = schema.Address.coinConnection(type=self.coin_type).alias(
            "coins"
        )
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
        qres = schema.Query.latestSuiSystemState.alias("qres").select(
            schema.SuiSystemStateSummary.systemStateVersion,
            schema.SuiSystemStateSummary.referenceGasPrice,
            schema.SuiSystemStateSummary.systemParameters.select(
                schema.SystemParameters.durationMs,
                schema.SystemParameters.stakeSubsidyStartEpoch,
                schema.SystemParameters.minValidatorCount,
                schema.SystemParameters.maxValidatorCount,
                schema.SystemParameters.minValidatorJoiningStake,
                schema.SystemParameters.validatorLowStakeThreshold,
                schema.SystemParameters.validatorVeryLowStakeThreshold,
                schema.SystemParameters.validatorLowStakeThreshold,
            ),
            schema.SuiSystemStateSummary.stakeSubsidy.select(
                schema.StakeSubsidy.balance,
                schema.StakeSubsidy.distributionCounter,
                schema.StakeSubsidy.currentDistributionAmount,
                schema.StakeSubsidy.periodLength,
                schema.StakeSubsidy.decreaseRate,
            ),
            schema.SuiSystemStateSummary.validatorSet.select(
                schema.ValidatorSet.totalStake,
                schema.ValidatorSet.pendingRemovals,
                schema.ValidatorSet.pendingActiveValidatorsSize,
                schema.ValidatorSet.stakePoolMappingsSize,
                schema.ValidatorSet.inactivePoolsSize,
                schema.ValidatorSet.validatorCandidatesSize,
                validators=schema.ValidatorSet.activeValidators.select(
                    schema.Validator.name,
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
                    validatorAddress=schema.Validator.address.select(
                        schema.Address.location
                    ),
                ),
            ),
            schema.SuiSystemStateSummary.storageFund.select(
                schema.StorageFund.totalObjectStorageRebates,
                schema.StorageFund.nonRefundableBalance,
            ),
            schema.SuiSystemStateSummary.safeMode.select(schema.SafeMode.enabled),
            schema.SuiSystemStateSummary.startTimestamp,
            schema.SuiSystemStateSummary.epoch.select(
                schema.Epoch.epochId,
                schema.Epoch.startTimestamp,
                schema.Epoch.endTimestamp,
            ),
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

        qres = schema.Query.objectConnection(filter={"owner": self.owner})
        if self.next_page:
            qres(after=self.next_page.endCursor)

        std_object = frag.StandardObject()
        pg_cursor = frag.PageCursor()
        base_object = frag.BaseObject()
        qres.select(
            cursor=schema.ObjectConnection.pageInfo.select(pg_cursor.fragment(schema)),
            objects_data=schema.ObjectConnection.nodes.select(
                std_object.fragment(schema)
            ),
        )

        return dsl_gql(
            pg_cursor.fragment(schema),
            std_object.fragment(schema),
            base_object.fragment(schema),
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadsGQL]:
        """Return the serializer to ObjectReadsGQL function."""
        return pgql_type.ObjectReadsGQL.from_query


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

        qres = schema.Query.objectConnection(filter={"objectIds": self.object_ids})
        if self.next_page:
            qres(after=self.next_page.endCursor)

        std_object = frag.StandardObject()
        pg_cursor = frag.PageCursor()
        base_object = frag.BaseObject()
        qres.select(
            cursor=schema.ObjectConnection.pageInfo.select(pg_cursor.fragment(schema)),
            objects_data=schema.ObjectConnection.nodes.select(
                std_object.fragment(schema)
            ),
        )

        return dsl_gql(
            pg_cursor.fragment(schema),
            std_object.fragment(schema),
            base_object.fragment(schema),
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
        std_object = frag.StandardObject()
        base_object = frag.BaseObject()

        return dsl_gql(
            std_object.fragment(schema),
            base_object.fragment(schema),
            DSLQuery(
                object=schema.Query.object(
                    address=self.object_id, version=self.version
                ).select(
                    std_object.fragment(schema),
                )
            ),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], pgql_type.ObjectReadGQL]:
        """Return the serializer to ObjectReadGQL function."""
        return pgql_type.ObjectReadGQL.from_query


class GetEvents(PGQL_QueryNode):
    """GetEvents When executed, return list of events for a specified transaction block."""

    def __init__(
        self,
        *,
        event_filter: dict,
        next_page: Optional[pgql_type.PagingCursor] = None,
    ) -> None:
        """QueryNode initializer

        :param event_filter: Filter key/values aligned to Sui GraphQL schema's EventFilter
        :type event_filter: str
        :param next_page: pgql_type.PagingCursor to advance query, defaults to None
        :type next_page: pgql_type.PagingCursor
        """
        self.event_filter = event_filter or {}
        self.next_page = next_page

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Build DocumentNode."""
        pg_cursor = frag.PageCursor()
        std_event = frag.StandardEvent()
        qres = schema.Query.eventConnection(filter=self.event_filter).select(
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
        """Initialize QueryNode.

        :param digest: The transaction digest to fetch
        :type digest: str
        """
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        """Builds the GQL DocumentNode

        :return: The transaction query DocumentNode for specific digest
        :rtype: DocumentNode
        """
        std_txn = frag.StandardTransaction()
        base_object = frag.BaseObject()
        gas_cost = frag.GasCost()
        qres = schema.Query.transactionBlock(digest=self.digest)
        qres.select(std_txn.fragment(schema))
        return dsl_gql(
            std_txn.fragment(schema),
            base_object.fragment(schema),
            gas_cost.fragment(schema),
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
        """QueryNode initializer.

        :param next_page: _description_, defaults to None
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

        qres = schema.Query.transactionBlockConnection(filter=self.qfilter)
        if self.next_page:
            qres(after=self.next_page.endCursor)

        pg_cursor = frag.PageCursor()
        qres.select(
            cursor=schema.TransactionBlockConnection.pageInfo.select(
                pg_cursor.fragment(schema)
            ),
            tx_blocks=schema.TransactionBlockConnection.nodes.select(
                schema.TransactionBlock.digest,
                schema.TransactionBlock.effects.select(
                    schema.TransactionBlockEffects.status,
                    schema.TransactionBlockEffects.timestamp,
                    schema.TransactionBlockEffects.errors,
                ),
            ),
        )
        return dsl_gql(
            pg_cursor.fragment(schema),
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.TransactionSummariesGQL], None]:
        """Return the serializer to TransactionSummariesGQL function."""
        return pgql_type.TransactionSummariesGQL.from_query


# TODO: Need object rep
# TODO: When staking matures
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
        staked_coin = schema.Address.stakedSuiConnection
        if self.next_page:
            staked_coin(after=self.next_page.endCursor)

        # Build fragment
        pg_cursor = frag.PageCursor()

        staked_coin.select(
            cursor=schema.StakedSuiConnection.pageInfo.select(
                pg_cursor.fragment(schema)
            ),
            staked_coin=schema.StakedSuiConnection.nodes.select(
                schema.StakedSui.status,
                schema.StakedSui.principal,
                schema.StakedSui.estimatedReward,
                schema.StakedSui.activeEpoch.select(activated=schema.Epoch.epochId),
                schema.StakedSui.requestEpoch.select(activated=schema.Epoch.epochId),
                schema.StakedSui.asMoveObject.select(
                    schema.MoveObject.hasPublicTransfer,
                    schema.MoveObject.asObject.select(
                        schema.Object.version,
                        coin_object_id=schema.Object.location,
                    ),
                ),
            ),
        )
        qres.select(staked_coin)
        return dsl_gql(pg_cursor.fragment(schema), DSLQuery(qres))


# TODO: When staking matures
class GetStakesById:
    """GetStakesById return all [DelegatedStake] coins identified.If a Stake was withdrawn its status will be Unstaked."""

    def __init__(self, staked_sui_ids: list[str]):
        """__init__ Builder initializer.

        :param staked_sui_ids: Array of delegated stake object ids.
        :type staked_sui_ids: SuiArray[ObjectID]
        """
        # super().__init__(
        #     "suix_getStakesByIds",
        #     handler_cls=DelegatedStakes,
        #     handler_func="factory",
        # )


class GetLatestCheckpointSequence(PGQL_QueryNode):
    """GetLatestCheckpointSequence return the sequence number of the latest checkpoint that has been executed."""

    def __init__(self):
        """__init__ QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        std_checkpoint = frag.StandardCheckpoint()
        pg_cursor = frag.PageCursor()
        qres = schema.Query.checkpointConnection(last=1).select(
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

        qres = schema.Query.checkpointConnection
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
        std_prot_cfg = frag.StandardProtocolConfig()
        qres = schema.Query.protocolConfig(protocolVersion=self.version).select(
            std_prot_cfg.fragment(schema)
        )
        return dsl_gql(std_prot_cfg.fragment(schema), DSLQuery(qres))

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
            DSLQuery(
                schema.Query.latestSuiSystemState.select(
                    schema.SuiSystemStateSummary.referenceGasPrice
                )
            )
        )

    @staticmethod
    def encode_fn() -> Union[Callable[[dict], pgql_type.ReferenceGasPriceGQL], None]:
        """Return the serialization function for ReferenceGasPrice."""
        return pgql_type.ReferenceGasPriceGQL.from_query


# TODO: Need object rep
# TODO: Renamed from Builder NameServiceAddress
class GetNameServiceAddress(PGQL_QueryNode):
    """Return the resolved name service address for name."""

    def __init__(self, *, name: str):
        """__init__ QueryNode initializer."""
        self.name = name

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        return dsl_gql(
            DSLQuery(
                schema.Query.resolveNameServiceAddress(name=self.name).select(
                    schema.Address.location
                )
            )
        )


# TODO: Renamed from Builder NameServiceName
class GetNameServiceNames:
    """Return the resolved names given address, if multiple names are resolved, the first one is the primary name."""

    def __init__(
        self,
        *,
        address: str,
    ):
        """QueryNode initializer."""


# TODO: May be deprecated
class GetLoadedChildObjects:
    """Returns the child object versions loaded by the object runtime particularly dynamic fields."""

    def __init__(self, *, digest: str):
        """QueryNode initializer."""


# TODO: To be implemented
class GetValidatorsApy:
    """Return the validator APY."""

    def __init__(self):
        """QueryNode initializer."""


# TODO: Not sure where to get the data yet
class GetMultiplePastObjects:
    """GetMultiplePastObjects When executed, return the object information for a specified version.

    Note there is no software-level guarantee/SLA that objects with past versions can be retrieved by this API,
    even if the object and version exists/existed. The result may vary across nodes depending on their pruning
    policies.
    """


# TODO: Not sure where to get the data yet
class GetPackage:
    """GetPackage When executed, return structured representations of all modules in the given package."""

    def __init__(self, *, package: str) -> None:
        """__init__ Initialize GetPackage object."""


# TODO: Not sure where to get the data yet
class GetModule:
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


# TODO: Not sure where to get the data yet
class GetFunction:
    """GetFunction When executed, returns the structural representation of a module's function.

    Includes general function arguments and return type definitions.
    """

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        function_name: str,
    ) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module_name: Name of module from package containing function_name to fetch
        :type module_name: SuiString
        :param function_name: Name of module from package to fetch
        :type function_name: SuiString
        """


# TODO: Not sure where to get the data yet
class GetFunctionArgs:
    """GetFunction When executed, returns the argument types of a Move function."""

    def __init__(self, *, package: str, module: str, function: str) -> None:
        """__init__ Initialize GetModule object.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module: Name of module from package containing function_name to fetch
        :type module: SuiString
        :param function: Name of module's function to fetch arguments for
        :type function: SuiString
        """


# TODO: Not sure where to get the data yet
class GetStructure:
    """GetStructure When executed, returns a module's structure representation."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        structure_name: str,
    ) -> None:
        """QueryNode initializer.

        :param package: ObjectID of package to query
        :type package: ObjectID
        :param module_name: Name of module from package containing function_name to fetch
        :type module_name: SuiString
        :param structure_name: Name of structure from structure to fetch
        :type structure_name: SuiString
        """


# TODO: Not sure where to get the data yet
class GetCommittee(PGQL_QueryNode):
    """GetCommittee When executed, returns information on committee (collection of nodes)."""

    def __init__(self, epoch: Optional[str] = None) -> None:
        """QueryNode initializer.

        :param epoch: Epoch to return state of committee from, defaults to None
        :type epoch: SuiString, optional
        """
        self.epoch = epoch

    def as_document_node(self, schema: DSLSchema) -> DocumentNode:
        qres = schema.Query
        return dsl_gql(DSLQuery(qres))


# TODO:From Query.eventConnection
class QueryEvents:
    """QueryEvents returns a list of events for a specified query criteria."""

    def __init__(
        self,
        *,
        query: dict,
    ) -> None:
        """QueryNode initializer."""


# TODO:From Query.transactionBlockConnection
class QueryTransactions:
    """QueryTransactions returns a list of transactions for a specified query criteria.."""

    def __init__(
        self,
        *,
        query: dict,
    ) -> None:
        """QueryNode initializer."""


############################
# Not supported in GraphQL #
############################


class GetAllCoins:
    """GetAllCoins Returns all Coin objects owned by an address."""

    def __init__(
        self, *, owner: Any, cursor: Optional[Any] = None, limit: Optional[Any] = None
    ):
        """."""
        raise NotImplemented("Deprecated in GraphQL, use GetCoins instead.")


class GetCoinTypeBalance:
    """GetCoinTypeBalance Return the total coin balance for a coin type."""

    def __init__(self, *, owner: Any, coin_type: Optional[Any] = None):
        """."""
        raise NotImplemented("Deprecated in GraphQL, use GetAllCoinBalances instead.")


class GetTotalSupply:
    """Return the total supply for a given coin type (eg. 0x2::sui::SUI)."""

    def __init__(self, *, coin_type: Optional[Any] = None):
        """."""
        raise NotImplemented("Deprecated in GraphQL, use GetCoinMetaData instead.")


class GetRpcAPI:
    """GetRpcAPI When executed, returns full list of SUI node RPC API supported."""

    def __init__(self) -> None:
        """Initialize builder."""
        raise NotImplemented("Deprecated in GraphQL.")


class GetTotalTxCount:
    """GetTotalTxCount When executed, return the total number of transactions known to the server."""

    def __init__(self) -> None:
        """Initialize builder."""
        raise NotImplemented(
            "Deprecated in GraphQL. Use propery `network_total_transactions` from GetLatestCheckpointSequence"
        )


class GetChainID:
    """Return the chain's identifier."""

    def __init__(self) -> None:
        """QueryNode initializer.."""
        raise NotImplemented(
            "Deprecated in GraphQL. Use property SuiGQLClient.chain_id"
        )


class GetCurrentValidators:
    """Return the set of validators at the time of this execution."""

    def __init__(
        self,
    ) -> None:
        """QueryNode initializer."""
        raise NotImplemented(
            "Deprecated in GraphQL. Use validator_set property GetLatestSuiSystemState"
        )
