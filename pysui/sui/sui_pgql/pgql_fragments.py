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
    """GasCost reusable fragment."""

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
    """PageCursor reusable fragment."""

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
    """StandardCoin reusable fragment."""

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
            )
        )


class BaseObject(PGQL_Fragment):
    """BaseObject reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("ObjectBase")
            .on(schema.Object)
            .select(
                schema.Object.version,
                object_digest=schema.Object.digest,
                object_id=schema.Object.address,
                object_kind=schema.Object.status,
            )
        )


class StandardObject(PGQL_Fragment):
    """StandardObject reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        base_object = BaseObject()
        return (
            DSLFragment("ObjectStandard")
            .on(schema.Object)
            .select(
                schema.Object.bcs,
                base_object.fragment(schema),
                schema.Object.owner.select(
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
                        schema.Parent.parent.select(parent_id=schema.Object.address),
                        obj_owner_kind=DSLMetaField("__typename"),
                    ),
                ),
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
            )
        )


class StandardEvent(PGQL_Fragment):
    """StandardEvent reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("EventStandard")
            .on(schema.Event)
            .select(
                schema.Event.sendingModule.select(
                    schema.MoveModule.package.select(
                        package_id=schema.MovePackage.address
                        # schema.MovePackage.asObject.select(
                        #     package_id=schema.Object.location,
                        # )
                    ),
                    module_name=schema.MoveModule.name,
                ),
                schema.Event.type.select(event_type=schema.MoveType.repr),
                schema.Event.sender.select(schema.Address.address),
                schema.Event.timestamp,
                schema.Event.json,
            )
        )


class StandardTxEffects(PGQL_Fragment):
    """StandardTxEffects reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        base_obj = BaseObject().fragment(schema)
        gas_cost = GasCost().fragment(schema)

        return (
            DSLFragment("TxEffects")
            .on(schema.TransactionBlockEffects)
            .select(
                schema.TransactionBlockEffects.status,
                schema.TransactionBlockEffects.errors,
                schema.TransactionBlockEffects.timestamp,
                schema.TransactionBlockEffects.balanceChanges.select(
                    schema.BalanceChangeConnection.nodes.select(
                        schema.BalanceChange.coinType.select(
                            coin_type=schema.MoveType.repr
                        ),
                        balance_change=schema.BalanceChange.amount,
                        change_to=schema.BalanceChange.owner.select(
                            object_id=schema.Owner.address
                        ),
                    )
                ),
                schema.TransactionBlockEffects.gasEffects.select(
                    schema.GasEffects.gasObject.select(
                        gas_object_id=schema.Object.address,
                    ),
                    schema.GasEffects.gasSummary.select(gas_cost),
                ),
                schema.TransactionBlockEffects.objectChanges.select(
                    schema.ObjectChangeConnection.nodes.select(
                        address=schema.ObjectChange.address,
                        deleted=schema.ObjectChange.idDeleted,
                        created=schema.ObjectChange.idCreated,
                        input_state=schema.ObjectChange.inputState.select(base_obj),
                        output_state=schema.ObjectChange.outputState.select(base_obj),
                    )
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
            )
        )


class StandardTransaction(PGQL_Fragment):
    """StandardTransaction reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        base_obj = BaseObject().fragment(schema)
        tx_effects = StandardTxEffects().fragment(schema)
        return (
            DSLFragment("TxStandard")
            .on(schema.TransactionBlock)
            .select(
                schema.TransactionBlock.digest,
                schema.TransactionBlock.sender.select(
                    submitter_address=schema.Address.address
                ),
                schema.TransactionBlock.expiration.select(schema.Epoch.epochId),
                schema.TransactionBlock.gasInput.select(
                    transaction_budget=schema.GasInput.gasBudget,
                    price=schema.GasInput.gasPrice,
                    sponsor=schema.GasInput.gasSponsor.select(
                        sponsor_address=schema.Address.address
                    ),
                    sponsor_pay_with=schema.GasInput.gasPayment.select(
                        gas_objects=schema.ObjectConnection.nodes.select(
                            base_obj,
                        )
                    ),
                ),
                schema.TransactionBlock.effects.select(tx_effects),
                #     schema.TransactionBlockEffects.status,
                #     schema.TransactionBlockEffects.errors,
                #     schema.TransactionBlockEffects.timestamp,
                #     schema.TransactionBlockEffects.balanceChanges.select(
                #         schema.BalanceChangeConnection.nodes.select(
                #             schema.BalanceChange.coinType.select(
                #                 coin_type=schema.MoveType.repr
                #             ),
                #             balance_change=schema.BalanceChange.amount,
                #             change_to=schema.BalanceChange.owner.select(
                #                 object_id=schema.Owner.address
                #             ),
                #         )
                #     ),
                #     schema.TransactionBlockEffects.gasEffects.select(
                #         schema.GasEffects.gasObject.select(
                #             gas_object_id=schema.Object.address,
                #         ),
                #         schema.GasEffects.gasSummary.select(gas_cost.fragment(schema)),
                #     ),
                #     schema.TransactionBlockEffects.objectChanges.select(
                #         schema.ObjectChangeConnection.nodes.select(
                #             address=schema.ObjectChange.address,
                #             deleted=schema.ObjectChange.idDeleted,
                #             created=schema.ObjectChange.idCreated,
                #             input_state=schema.ObjectChange.inputState.select(
                #                 base_obj.fragment(schema)
                #             ),
                #             output_state=schema.ObjectChange.outputState.select(
                #                 base_obj.fragment(schema)
                #             ),
                #         )
                #     ),
                #     schema.TransactionBlockEffects.checkpoint.select(
                #         schema.Checkpoint.sequenceNumber,
                #         schema.Checkpoint.networkTotalTransactions,
                #         schema.Checkpoint.timestamp,
                #         schema.Checkpoint.epoch.select(
                #             schema.Epoch.epochId,
                #             schema.Epoch.startTimestamp,
                #             schema.Epoch.endTimestamp,
                #         ),
                #     ),
                # ),
                # txn_kind=schema.TransactionBlock.kind.select(
                #     DSLInlineFragment()
                #     .on(schema.ProgrammableTransactionBlock)
                #     .select(
                #         inputs=schema.ProgrammableTransactionBlock.inputs.select(
                #             DSLInlineFragment()
                #             .on(schema.TransactionInputConnection)
                #             .select(
                #                 schema.TransactionInputConnection.nodes.select(
                #                     DSLInlineFragment()
                #                     .on(schema.Pure)
                #                     .select(
                #                         schema.Pure.bytes,
                #                         DSLMetaField("__typename"),
                #                     ),
                #                     DSLInlineFragment()
                #                     .on(schema.OwnedOrImmutable)
                #                     .select(
                #                         schema.OwnedOrImmutable.address,
                #                         schema.OwnedOrImmutable.version,
                #                         schema.OwnedOrImmutable.digest,
                #                         DSLMetaField("__typename"),
                #                     ),
                #                     DSLInlineFragment()
                #                     .on(schema.SharedInput)
                #                     .select(
                #                         schema.SharedInput.address,
                #                         schema.SharedInput.initialSharedVersion,
                #                         schema.SharedInput.mutable,
                #                         DSLMetaField("__typename"),
                #                     ),
                #                     DSLInlineFragment()
                #                     .on(schema.Receiving)
                #                     .select(
                #                         schema.Receiving.address,
                #                         schema.Receiving.version,
                #                         schema.Receiving.digest,
                #                         DSLMetaField("__typename"),
                #                     ),
                #                 )
                #             ),
                #         ),
                #     ),
                #     txn_kind=DSLMetaField("__typename"),
                # ),
            )
        )


class StandardCheckpoint(PGQL_Fragment):
    """StandardChecpoint reusable fragment."""

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
                transaction_blocks=schema.Checkpoint.transactionBlocks.select(
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
    """StandardChecpoint reusable fragment."""

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


class MoveStructure(PGQL_Fragment):
    """MoveStructure reusable fragment"""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""

        return (
            DSLFragment("MoveStruct")
            .on(schema.MoveStruct)
            .select(
                schema.MoveStruct.name.alias("struct_name"),
                schema.MoveStruct.abilities,
                schema.MoveStruct.fields.select(
                    schema.MoveField.name.alias("field_name"),
                    schema.MoveField.type.alias("field_type").select(
                        schema.OpenMoveType.signature
                    ),
                ),
            )
        )


class MoveFunction(PGQL_Fragment):
    """MoveFunction reusable fragment"""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""

        return (
            DSLFragment("MoveFunction")
            .on(schema.MoveFunction)
            .select(
                schema.MoveFunction.name.alias("function_name"),
                schema.MoveFunction.isEntry,
                schema.MoveFunction.visibility,
                schema.MoveFunction.typeParameters.select(
                    schema.MoveFunctionTypeParameter.constraints
                ),
                getattr(schema.MoveFunction, "return")
                .alias("returns")
                .select(schema.OpenMoveType.signature),
                schema.MoveFunction.parameters.select(schema.OpenMoveType.signature),
            )
        )


class MoveModule(PGQL_Fragment):
    """MoveModule reusable fragment.

    Contains structs and functions
    """

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        struc = MoveStructure().fragment(schema)
        func = MoveFunction().fragment(schema)
        return (
            DSLFragment("MoveModule")
            .on(schema.MoveModule)
            .select(
                schema.MoveModule.name.alias("module_name"),
                schema.MoveModule.structs.alias("structure_list").select(
                    module_structures=schema.MoveStructConnection.nodes.select(struc)
                ),
                schema.MoveModule.functions.alias("function_list").select(
                    module_functions=schema.MoveFunctionConnection.nodes.select(func)
                ),
            )
        )


class Validator(PGQL_Fragment):
    """Validator reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        return (
            DSLFragment("Validator")
            .on(schema.Validator)
            .select(
                schema.Validator.name.alias("validator_name"),
                schema.Validator.address.select(
                    schema.Address.address.alias("validator_address")
                ),
                schema.Validator.description,
                schema.Validator.imageUrl,
                schema.Validator.projectUrl,
                schema.Validator.operationCap.select(
                    schema.MoveObject.address.alias("operating_cap_address")
                ),
                schema.Validator.stakingPoolSuiBalance,
                schema.Validator.stakingPoolActivationEpoch,
                schema.Validator.stakingPool.select(
                    schema.MoveObject.address.alias("staking_pool_address")
                ),
                schema.Validator.exchangeRatesSize,
                schema.Validator.exchangeRates.select(
                    schema.MoveObject.address.alias("exchange_rates_address")
                ),
                schema.Validator.rewardsPool,
                schema.Validator.poolTokenBalance,
                schema.Validator.pendingStake,
                schema.Validator.pendingTotalSuiWithdraw,
                schema.Validator.pendingPoolTokenWithdraw,
                schema.Validator.votingPower,
                schema.Validator.gasPrice,
                schema.Validator.commissionRate,
                schema.Validator.nextEpochStake,
                schema.Validator.nextEpochGasPrice,
                schema.Validator.nextEpochCommissionRate,
                schema.Validator.atRisk,
                schema.Validator.apy,
            )
        )


class ValidatorSet(PGQL_Fragment):
    """ValidatorSet reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        pg_cursor = PageCursor()
        vals = Validator()
        return (
            DSLFragment("ValidatorSet")
            .on(schema.ValidatorSet)
            .select(
                schema.ValidatorSet.totalStake,
                schema.ValidatorSet.pendingRemovals,
                schema.ValidatorSet.pendingActiveValidatorsId,
                schema.ValidatorSet.pendingActiveValidatorsSize,
                schema.ValidatorSet.stakingPoolMappingsId,
                schema.ValidatorSet.inactivePoolsId,
                schema.ValidatorSet.validatorCandidatesId,
                schema.ValidatorSet.validatorCandidatesSize,
                schema.ValidatorSet.activeValidators.select(
                    cursor=schema.ValidatorConnection.pageInfo.select(
                        pg_cursor.fragment(schema)
                    ),
                    validators=schema.ValidatorConnection.nodes.select(
                        vals.fragment(schema)
                    ),
                ),
            )
        )
