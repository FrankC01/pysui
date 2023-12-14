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

# -*- coding: utf-8 -*-

"""QueryNode generators."""

from functools import cache
from pysui.sui.sui_pgql.pgql_clients import PGQL_Fragment
from gql.dsl import DSLFragment, DSLInlineFragment, DSLMetaField, DSLSchema


class GasCost(PGQL_Fragment):
    """GasCost is used to retrieve gas cost summaries on types that support it."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("GasSummary")
            .on(schema.GasCostSummary)
            .select(
                schema.GasCostSummary.computationCost,
                schema.GasCostSummary.storageCost,
                schema.GasCostSummary.storageRebate,
                schema.GasCostSummary.nonRefundableStorageFee,
            )
        )


class PageCursor(PGQL_Fragment):
    """PageCursor is used to retrieve paging control on types supporting PageInfo."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("PageCursor")
            .on(schema.PageInfo)
            .select(
                schema.PageInfo.hasNextPage,
                schema.PageInfo.endCursor,
            )
        )


class StandardCoin(PGQL_Fragment):
    """StandardCoin is used to retrieve standard coin shape."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        pg_cursor = PageCursor()
        return (
            DSLFragment("CoinStandard")
            .on(schema.CoinConnection)
            .select(
                cursor=schema.CoinConnection.pageInfo.select(
                    pg_cursor.fragment(schema)
                ),
                coin_objects=schema.CoinConnection.nodes.select(
                    schema.Coin.balance,
                    schema.Coin.asMoveObject.select(
                        schema.MoveObject.hasPublicTransfer,
                        schema.MoveObject.asObject.select(
                            schema.Object.version,
                            schema.Object.digest,
                            schema.Object.previousTransactionBlock.select(
                                previous_transaction=schema.TransactionBlock.digest
                            ),
                            coin_object_id=schema.Object.location,
                            owner=schema.Object.owner.select(
                                coin_owner=schema.Owner.location
                            ),
                        ),
                        schema.MoveObject.contents.select(
                            object_type=schema.MoveValue.type.select(
                                coin_type=schema.MoveType.repr
                            )
                        ),
                    ),
                ),
            )
        )


class BaseObject(PGQL_Fragment):
    """BaseObject applies to any object type."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("ObjectBase")
            .on(schema.Object)
            .select(
                schema.Object.version,
                object_digest=schema.Object.digest,
                object_id=schema.Object.location,
                object_kind=schema.Object.kind,
            )
        )


class StandardObject(PGQL_Fragment):
    """StandardObject is used to retrieve standard object shape."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        base_object = BaseObject()
        return (
            DSLFragment("ObjectStandard")
            .on(schema.Object)
            .select(
                schema.Object.bcs,
                base_object.fragment(schema),
                # object_digest=schema.Object.digest,
                # object_id=schema.Object.location,
                # object_kind=schema.Object.kind,
                storage_rebate=schema.Object.storageRebate,
                prior_transaction=schema.Object.previousTransactionBlock.select(
                    previous_transaction_digest=schema.TransactionBlock.digest
                ),
                as_move_content=schema.Object.asMoveObject.select(
                    has_public_transfer=schema.MoveObject.hasPublicTransfer,
                    as_object=schema.MoveObject.contents.select(
                        content=schema.MoveValue.json,
                        object_type_repr=schema.MoveValue.type.select(
                            object_type=schema.MoveType.repr
                        ),
                    ),
                ),
                owned_by=schema.Object.owner.select(owner_id=schema.Owner.location),
            )
        )


class StandardEvent(PGQL_Fragment):
    """StandardEvent is used to retrieve standard event shape."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("EventStandard")
            .on(schema.Event)
            .select(
                schema.Event.sendingModuleId.select(
                    schema.MoveModuleId.package.select(
                        schema.MovePackage.asObject.select(
                            package_id=schema.Object.location,
                        )
                    ),
                    module_name=schema.MoveModuleId.name,
                ),
                schema.Event.eventType.select(event_type=schema.MoveType.repr),
                schema.Event.senders.select(schema.Address.location),
                schema.Event.timestamp,
                schema.Event.json,
            )
        )


class StandardTransaction(PGQL_Fragment):
    """StandardTransaction is used to retrieve standard transaction shape."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        base_obj = BaseObject()
        gas_cost = GasCost()
        return (
            DSLFragment("TxStandard")
            .on(schema.TransactionBlock)
            .select(
                schema.TransactionBlock.digest,
                schema.TransactionBlock.sender.select(
                    submitter_address=schema.Address.location
                ),
                schema.TransactionBlock.expiration.select(schema.Epoch.epochId),
                schema.TransactionBlock.gasInput.select(
                    transaction_budget=schema.GasInput.gasBudget,
                    price=schema.GasInput.gasPrice,
                    sponsor=schema.GasInput.gasSponsor.select(
                        sponsor_address=schema.Address.location
                    ),
                    sponsor_pay_with=schema.GasInput.gasPayment.select(
                        gas_objects=schema.ObjectConnection.nodes.select(
                            base_obj.fragment(schema),
                        )
                    ),
                ),
                schema.TransactionBlock.effects.select(
                    schema.TransactionBlockEffects.status,
                    schema.TransactionBlockEffects.errors,
                    schema.TransactionBlockEffects.timestamp,
                    schema.TransactionBlockEffects.balanceChanges.select(
                        tx_cost=schema.BalanceChange.amount,
                        tx_cost_from=schema.BalanceChange.owner.select(
                            schema.Owner.location
                        ),
                    ),
                    schema.TransactionBlockEffects.gasEffects.select(
                        schema.GasEffects.gasObject.select(
                            gas_object_id=schema.Object.location,
                        ),
                        schema.GasEffects.gasSummary.select(gas_cost.fragment(schema)),
                    ),
                    schema.TransactionBlockEffects.objectChanges.select(
                        created=schema.ObjectChange.idCreated,
                        deleted=schema.ObjectChange.idDeleted,
                        input_state=schema.ObjectChange.inputState.select(
                            base_obj.fragment(schema)
                        ),
                        output_state=schema.ObjectChange.outputState.select(
                            base_obj.fragment(schema)
                        ),
                    ),
                    schema.TransactionBlockEffects.checkpoint.select(
                        schema.Checkpoint.sequenceNumber,
                        schema.Checkpoint.networkTotalTransactions,
                        schema.Checkpoint.timestamp,
                        schema.Checkpoint.epoch.select(
                            schema.Epoch.epochId,
                            schema.Epoch.startTimestamp,
                            schema.Epoch.endTimestamp,
                        ),
                    ),
                ),
                txn_kind=schema.TransactionBlock.kind.select(
                    DSLInlineFragment()
                    .on(schema.ProgrammableTransaction)
                    .select(
                        schema.ProgrammableTransaction.value,
                    ),
                    DSLInlineFragment()
                    .on(schema.GenesisTransaction)
                    .select(schema.GenesisTransaction.objects),
                    txn_kind=DSLMetaField("__typename"),
                ),
            )
        )


class StandardCheckpoint(PGQL_Fragment):
    """StandardChecpoint is used to retrieve standard checkpoint shape."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        pg_cursor = PageCursor()
        return (
            DSLFragment("Checkpoint")
            .on(schema.Checkpoint)
            .select(
                schema.Checkpoint.digest,
                schema.Checkpoint.sequenceNumber,
                schema.Checkpoint.timestamp,
                schema.Checkpoint.previousCheckpointDigest,
                schema.Checkpoint.networkTotalTransactions,
                transaction_blocks=schema.Checkpoint.transactionBlockConnection.select(
                    cursor=schema.TransactionBlockConnection.pageInfo.select(
                        pg_cursor.fragment(schema)
                    ),
                    tx_digests=schema.TransactionBlockConnection.nodes.select(
                        schema.TransactionBlock.digest
                    ),
                ),
            )
        )


class StandardProtocolConfig(PGQL_Fragment):
    """StandardChecpoint is used to retrieve standard checkpoint shape."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        return (
            DSLFragment("ProtcolConfig")
            .on(schema.ProtocolConfigs)
            .select(
                schema.ProtocolConfigs.protocolVersion,
                schema.ProtocolConfigs.configs.select(
                    schema.ProtocolConfigAttr.key,
                    schema.ProtocolConfigAttr.value,
                ),
                schema.ProtocolConfigs.featureFlags.select(
                    schema.ProtocolConfigFeatureFlag.key,
                    schema.ProtocolConfigFeatureFlag.value,
                ),
            )
        )
