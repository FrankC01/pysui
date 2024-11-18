#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""QueryNode generators."""

from functools import cache
from typing import Any
from pysui.sui.sui_pgql.pgql_clients import PGQL_Fragment
from gql.dsl import DSLFragment, DSLInlineFragment, DSLMetaField, DSLSchema, DSLField


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
                        schema.Parent.parent.select(parent_id=schema.Owner.address),
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
                as_move_package=schema.Object.asMovePackage.select(
                    bcs=schema.MovePackage.bcs
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
                    ),
                    module_name=schema.MoveModule.name,
                ),
                schema.Event.sender.select(schema.Address.address),
                schema.Event.timestamp,
                schema.Event.contents.select(schema.MoveValue.json),
            )
        )


class StandardTxEffects(PGQL_Fragment):
    """StandardTxEffects reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        # base_obj = BaseObject().fragment(schema)
        base_obj = StandardObject().fragment(schema)
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
                schema.TransactionBlock.signatures,
                schema.TransactionBlock.kind.select(
                    DSLMetaField("__typename").alias("tx_kind")
                ),
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
            )
        )


class ProgrammableTxKind(PGQL_Fragment):
    """Details of the ProgrammableTransaction type commands."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        return (
            DSLFragment("PrgTxKind")
            .on(schema.ProgrammableTransactionBlock)
            .select(
                schema.ProgrammableTransactionBlock.inputs.select(
                    DSLInlineFragment()
                    .on(schema.TransactionInputConnection)
                    .select(
                        schema.TransactionInputConnection.nodes.select(
                            DSLInlineFragment()
                            .on(schema.OwnedOrImmutable)
                            .select(
                                schema.OwnedOrImmutable.address,
                                schema.OwnedOrImmutable.version,
                                schema.OwnedOrImmutable.digest,
                            ),
                            DSLInlineFragment()
                            .on(schema.Pure)
                            .select(
                                schema.Pure.bytes.alias("base64_bytes"),
                            ),
                            DSLInlineFragment()
                            .on(schema.SharedInput)
                            .select(
                                schema.SharedInput.address,
                                schema.SharedInput.initialSharedVersion,
                                schema.SharedInput.mutable,
                            ),
                            DSLInlineFragment()
                            .on(schema.Receiving)
                            .select(
                                schema.Receiving.address,
                                schema.Receiving.version,
                                schema.Receiving.digest,
                            ),
                            DSLMetaField("__typename").alias("input_typename"),
                        )
                    ),
                ),
                schema.ProgrammableTransactionBlock.transactions.select(
                    DSLInlineFragment()
                    .on(schema.ProgrammableTransactionConnection)
                    .select(
                        schema.ProgrammableTransactionConnection.nodes.select(
                            DSLMetaField("__typename").alias("tx_typename"),
                            # Merge Coins
                            DSLInlineFragment()
                            .on(schema.MergeCoinsTransaction)
                            .select(
                                schema.MergeCoinsTransaction.coin.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                                schema.MergeCoinsTransaction.coins.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Split Coins
                            DSLInlineFragment()
                            .on(schema.SplitCoinsTransaction)
                            .select(
                                schema.SplitCoinsTransaction.coin.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                                schema.SplitCoinsTransaction.amounts.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Transfer Objects
                            DSLInlineFragment()
                            .on(schema.TransferObjectsTransaction)
                            .select(
                                schema.TransferObjectsTransaction.inputs.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                                schema.TransferObjectsTransaction.address.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Move Call
                            DSLInlineFragment()
                            .on(schema.MoveCallTransaction)
                            .select(
                                schema.MoveCallTransaction.package,
                                schema.MoveCallTransaction.module,
                                schema.MoveCallTransaction.functionName,
                                schema.MoveCallTransaction.typeArguments.select(
                                    schema.MoveType.repr
                                ),
                                schema.MoveCallTransaction.arguments.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Publish
                            DSLInlineFragment()
                            .on(schema.PublishTransaction)
                            .select(
                                schema.PublishTransaction.modules,
                                schema.PublishTransaction.dependencies,
                            ),
                            # Upgrade
                            DSLInlineFragment()
                            .on(schema.UpgradeTransaction)
                            .select(
                                schema.UpgradeTransaction.modules,
                                schema.UpgradeTransaction.dependencies,
                                schema.UpgradeTransaction.currentPackage,
                                schema.UpgradeTransaction.upgradeTicket.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Make Move Vec
                            DSLInlineFragment()
                            .on(schema.MakeMoveVecTransaction)
                            .select(
                                schema.MakeMoveVecTransaction.type.alias(
                                    "vector_type"
                                ).select(schema.MoveType.repr),
                                schema.MakeMoveVecTransaction.elements.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.Result)
                                    .select(
                                        schema.Result.cmd,
                                        result_index=schema.Result.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                        )
                    )
                ),
            )
        )


class ConsensusCommitPrologueKind(PGQL_Fragment):
    """Details of consensus commit transaction."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""

        return (
            DSLFragment("ConsensusTxKind")
            .on(schema.ConsensusCommitPrologueTransaction)
            .select(
                schema.ConsensusCommitPrologueTransaction.epoch.select(
                    schema.Epoch.epochId
                ),
                schema.ConsensusCommitPrologueTransaction.round.alias("consensusRound"),
                schema.ConsensusCommitPrologueTransaction.commitTimestamp,
                schema.ConsensusCommitPrologueTransaction.consensusCommitDigest,
            )
        )


class AuthenticatorStateUpdateTransactionKind(PGQL_Fragment):
    """Details of AuthenticatorStateUpdateTransaction.

    Not used by any pysui QueryNode but available to those creating them.
    """

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""

        return (
            DSLFragment("AuthenticatorStakeUpdateTxKind")
            .on(schema.AuthenticatorStateUpdateTransaction)
            .select(
                schema.AuthenticatorStateUpdateTransaction.epoch.select(
                    schema.Epoch.epochId
                ),
                schema.AuthenticatorStateUpdateTransaction.round.alias(
                    "consensusRound"
                ),
                schema.AuthenticatorStateUpdateTransaction.authenticatorObjInitialSharedVersion,
                schema.AuthenticatorStateUpdateTransaction.newActiveJwks.select(
                    schema.ActiveJwkConnection.nodes.select(
                        schema.ActiveJwk.iss,
                        schema.ActiveJwk.kid,
                        schema.ActiveJwk.kty,
                        schema.ActiveJwk.e,
                        schema.ActiveJwk.n,
                        schema.ActiveJwk.alg,
                        schema.ActiveJwk.epoch.select(schema.Epoch.epochId),
                    )
                ),
            )
        )


class RandomnessStateUpdateTransactionKind(PGQL_Fragment):
    """Details of RandomnessStateUpdateTransaction.

    Not used by any pysui QueryNode but available to those creating them.
    """

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""

        return (
            DSLFragment("RandomnessStateUpdateTxKind")
            .on(schema.RandomnessStateUpdateTransaction)
            .select(
                schema.RandomnessStateUpdateTransaction.epoch.select(
                    schema.Epoch.epochId
                ),
                schema.RandomnessStateUpdateTransaction.randomnessRound,
                schema.RandomnessStateUpdateTransaction.randomBytes,
                schema.RandomnessStateUpdateTransaction.randomnessObjInitialSharedVersion,
            )
        )


class StandardTransactionKind(PGQL_Fragment):
    """Details a transactions kind. Supports ProgrammableTransaction type only."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        prg_kind = ProgrammableTxKind().fragment(schema)
        ccp_kind = ConsensusCommitPrologueKind().fragment(schema)
        return (
            DSLFragment("TxKind")
            .on(schema.TransactionBlock)
            .select(
                schema.TransactionBlock.kind.select(
                    DSLInlineFragment()
                    .on(schema.ProgrammableTransactionBlock)
                    .select(prg_kind),
                    DSLInlineFragment()
                    .on(schema.ConsensusCommitPrologueTransaction)
                    .select(ccp_kind),
                    DSLInlineFragment()
                    .on(schema.GenesisTransaction)
                    .select(
                        schema.GenesisTransaction.objects.select(
                            schema.ObjectConnection.nodes.select(schema.Object.address)
                        )
                    ),
                    tx_kind=DSLMetaField("__typename"),
                )
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
        pg_cursor = PageCursor().fragment(schema)
        struc = MoveStructure().fragment(schema)
        func = MoveFunction().fragment(schema)
        return (
            DSLFragment("MoveModule")
            .on(schema.MoveModule)
            .select(
                schema.MoveModule.name.alias("module_name"),
                schema.MoveModule.structs.alias("structure_list").select(
                    schema.MoveStructConnection.pageInfo.select(pg_cursor).alias(
                        "cursor"
                    ),
                    module_structures=schema.MoveStructConnection.nodes.select(struc),
                ),
                schema.MoveModule.functions.alias("function_list").select(
                    schema.MoveFunctionConnection.pageInfo.select(pg_cursor).alias(
                        "cursor"
                    ),
                    module_functions=schema.MoveFunctionConnection.nodes.select(func),
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
                schema.Validator.stakingPoolId.alias("staking_pool_address"),
                schema.Validator.exchangeRatesSize,
                schema.Validator.exchangeRatesTable.select(
                    schema.Owner.address.alias("exchange_rates_address")
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
    def fragment(self, schema: DSLSchema, active_vals: DSLField) -> DSLFragment:
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
                active_vals.select(
                    cursor=schema.ValidatorConnection.pageInfo.select(
                        pg_cursor.fragment(schema)
                    ),
                    validators=schema.ValidatorConnection.nodes.select(
                        vals.fragment(schema)
                    ),
                ),
            )
        )
