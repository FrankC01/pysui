#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""QueryNode generators."""

from functools import cache
from typing import Any
from deprecated.sphinx import versionchanged
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


class BaseSuiObjectForCoin(PGQL_Fragment):
    """Base Sui Object Used since beta."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("BaseSuiObjectForCoin")
            .on(schema.Object)
            .select(
                schema.Object.asMoveObject.select(
                    schema.MoveObject.version,
                    schema.MoveObject.hasPublicTransfer,
                    schema.MoveObject.previousTransaction.select(
                        previous_transaction=schema.Transaction.digest
                    ),
                    schema.MoveObject.owner.select(
                        DSLInlineFragment()
                        .on(schema.AddressOwner)
                        .select(
                            address_id=schema.AddressOwner.address.select(
                                schema.Address.address
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
                        .on(schema.ObjectOwner)
                        .select(
                            parent_id=schema.ObjectOwner.address.select(
                                schema.Address.address
                            ),
                            obj_owner_kind=DSLMetaField("__typename"),
                        ),
                    ),
                    schema.MoveObject.contents.select(
                        schema.MoveValue.type.select(coin_type=schema.MoveType.repr),
                        schema.MoveValue.json,
                    ),
                    object_digest=schema.MoveObject.digest,
                    coin_object_id=schema.MoveObject.address,
                )
            )
        )


@versionchanged(version="0.91.0", reason="GraphQL Beta")
class StandardCoin(PGQL_Fragment):
    """StandardCoin reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        pg_cursor = PageCursor()
        return (
            DSLFragment("StandardCoin")
            .on(schema.MoveObjectConnection)
            .select(
                cursor=schema.MoveObjectConnection.pageInfo.select(
                    pg_cursor.fragment(schema)
                ),
                coin_objects=schema.MoveObjectConnection.nodes.select(
                    schema.MoveObject.version,
                    schema.MoveObject.hasPublicTransfer,
                    schema.MoveObject.previousTransaction.select(
                        previous_transaction=schema.Transaction.digest
                    ),
                    schema.MoveObject.owner.select(
                        DSLInlineFragment()
                        .on(schema.AddressOwner)
                        .select(
                            address_id=schema.AddressOwner.address.select(
                                schema.Address.address
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
                        .on(schema.ObjectOwner)
                        .select(
                            parent_id=schema.ObjectOwner.address.select(
                                schema.Address.address
                            ),
                            obj_owner_kind=DSLMetaField("__typename"),
                        ),
                    ),
                    schema.MoveObject.contents.select(
                        schema.MoveValue.type.select(coin_type=schema.MoveType.repr),
                        schema.MoveValue.json,
                    ),
                    object_digest=schema.MoveObject.digest,
                    coin_object_id=schema.MoveObject.address,
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
                schema.Object.objectBcs.alias("bcs"),
                base_object.fragment(schema),
                schema.Object.owner.select(
                    DSLInlineFragment()
                    .on(schema.AddressOwner)
                    .select(
                        address_id=schema.AddressOwner.address.select(
                            schema.Address.address
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
                    .on(schema.ObjectOwner)
                    .select(
                        parent_id=schema.ObjectOwner.address.select(
                            schema.Address.address
                        ),
                        obj_owner_kind=DSLMetaField("__typename"),
                    ),
                ),
                storage_rebate=schema.Object.storageRebate,
                prior_transaction=schema.Object.previousTransaction.select(
                    previous_transaction_digest=schema.Transaction.digest
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
                    bcs=schema.MovePackage.moduleBcs
                ),
            )
        )


@versionchanged(version="0.91.0", reason="GraphQL Beta changes to fields.")
class StandardEvent(PGQL_Fragment):
    """StandardEvent reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        return (
            DSLFragment("EventStandard")
            .on(schema.Event)
            .select(
                schema.Event.transactionModule.select(
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


@versionchanged(version="0.91.0", reason="GraphQL Beta changes to fields.")
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
            .on(schema.TransactionEffects)
            .select(
                schema.TransactionEffects.status,
                schema.TransactionEffects.executionError.select(
                    schema.ExecutionError.abortCode,
                    schema.ExecutionError.sourceLineNumber,
                    schema.ExecutionError.instructionOffset,
                    schema.ExecutionError.identifier,
                    schema.ExecutionError.constant,
                    schema.ExecutionError.message,
                    # schema.ExecutionError.module.select(
                    # )
                ),
                schema.TransactionEffects.timestamp,
                schema.TransactionEffects.balanceChanges.select(
                    schema.BalanceChangeConnection.nodes.select(
                        schema.BalanceChange.coinType.select(
                            coin_type=schema.MoveType.repr
                        ),
                        balance_change=schema.BalanceChange.amount,
                        change_to=schema.BalanceChange.owner.select(
                            object_id=schema.Address.address
                        ),
                    )
                ),
                schema.TransactionEffects.gasEffects.select(
                    schema.GasEffects.gasObject.select(
                        gas_object_id=schema.Object.address,
                    ),
                    schema.GasEffects.gasSummary.select(gas_cost),
                ),
                schema.TransactionEffects.objectChanges.select(
                    schema.ObjectChangeConnection.nodes.select(
                        address=schema.ObjectChange.address,
                        deleted=schema.ObjectChange.idDeleted,
                        created=schema.ObjectChange.idCreated,
                        input_state=schema.ObjectChange.inputState.select(base_obj),
                        output_state=schema.ObjectChange.outputState.select(base_obj),
                    )
                ),
                schema.TransactionEffects.checkpoint.select(
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


@versionchanged(version="0.91.0", reason="GraphQL Beta changes to fields.")
class StandardTransaction(PGQL_Fragment):
    """StandardTransaction reusable fragment."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        base_obj = BaseObject().fragment(schema)
        tx_effects = StandardTxEffects().fragment(schema)
        return (
            DSLFragment("TxStandard")
            .on(schema.Transaction)
            .select(
                schema.Transaction.digest,
                schema.Transaction.signatures.select(
                    schema.UserSignature.signatureBytes
                ),
                schema.Transaction.kind.select(
                    DSLMetaField("__typename").alias("tx_kind")
                ),
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
                        gas_objects=schema.ObjectConnection.nodes.select(
                            base_obj,
                        )
                    ),
                ),
                schema.Transaction.effects.select(tx_effects),
            )
        )


class ProgrammableTxKind(PGQL_Fragment):
    """Details of the ProgrammableTransaction type commands."""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""
        return (
            DSLFragment("PrgTxKind")
            .on(schema.ProgrammableTransaction)
            .select(
                schema.ProgrammableTransaction.inputs.select(
                    DSLInlineFragment()
                    .on(schema.TransactionInputConnection)
                    .select(
                        schema.TransactionInputConnection.nodes.select(
                            DSLInlineFragment()
                            .on(schema.OwnedOrImmutable)
                            .select(
                                schema.OwnedOrImmutable.object.select(
                                    schema.Object.address
                                ),
                                schema.OwnedOrImmutable.object.select(
                                    schema.Object.version
                                ),
                                schema.OwnedOrImmutable.object.select(
                                    schema.Object.digest
                                ),
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
                                schema.Receiving.object.select(schema.Object.address),
                                schema.Receiving.object.select(schema.Object.version),
                                schema.Receiving.object.select(schema.Object.digest),
                            ),
                            DSLMetaField("__typename").alias("input_typename"),
                        )
                    ),
                ),
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                schema.ProgrammableTransaction.commands.select(
=======
                schema.ProgrammableTransaction.transactions.select(
>>>>>>> 30fdd47 (GraphQL Beta Transition)
=======
                schema.ProgrammableTransaction.commands.select(
>>>>>>> ab55794 (Validating GraphQL Beta. Updates to gRPC protobuffs)
=======
                schema.ProgrammableTransaction.transactions.select(
>>>>>>> bafbf78 (GraphQL Beta Transition)
=======
                schema.ProgrammableTransaction.commands.select(
>>>>>>> b7a28a8 (Validating GraphQL Beta. Updates to gRPC protobuffs)
                    DSLInlineFragment()
                    .on(schema.CommandConnection)
                    .select(
                        schema.CommandConnection.nodes.select(
                            DSLMetaField("__typename").alias("tx_typename"),
                            # Merge Coins
                            DSLInlineFragment()
                            .on(schema.MergeCoinsCommand)
                            .select(
                                schema.MergeCoinsCommand.coin.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                                schema.MergeCoinsCommand.coins.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Split Coins
                            DSLInlineFragment()
                            .on(schema.SplitCoinsCommand)
                            .select(
                                schema.SplitCoinsCommand.coin.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                                schema.SplitCoinsCommand.amounts.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Transfer Objects
                            DSLInlineFragment()
                            .on(schema.TransferObjectsCommand)
                            .select(
                                schema.TransferObjectsCommand.inputs.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                                schema.TransferObjectsCommand.address.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Move Call
                            DSLInlineFragment()
                            .on(schema.MoveCallCommand)
                            .select(
                                schema.MoveCallCommand.function.select(
                                    schema.MoveFunction.module.select(
                                        schema.MoveModule.package.select(
                                            schema.MovePackage.address
                                        )
                                    ),
                                    schema.MoveFunction.module.select(
                                        schema.MoveModule.name
                                    ),
                                    schema.MoveFunction.name,
                                    # schema.MoveFunction.typeArguments.select(
                                    #     schema.MoveType.repr
                                    # ),
                                ),
                                schema.MoveCallCommand.arguments.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Publish
                            DSLInlineFragment()
                            .on(schema.PublishCommand)
                            .select(
                                schema.PublishCommand.modules,
                                schema.PublishCommand.dependencies,
                            ),
                            # Upgrade
                            DSLInlineFragment()
                            .on(schema.UpgradeCommand)
                            .select(
                                schema.UpgradeCommand.modules,
                                schema.UpgradeCommand.dependencies,
                                schema.UpgradeCommand.currentPackage,
                                schema.UpgradeCommand.upgradeTicket.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
                                    ),
                                    DSLInlineFragment()
                                    .on(schema.GasCoin)
                                    .select(schema.GasCoin._.alias("gas_ref")),
                                ),
                            ),
                            # Make Move Vec
                            DSLInlineFragment()
                            .on(schema.MakeMoveVecCommand)
                            .select(
                                schema.MakeMoveVecCommand.type.alias(
                                    "vector_type"
                                ).select(schema.MoveType.repr),
                                schema.MakeMoveVecCommand.elements.select(
                                    DSLMetaField("__typename"),
                                    DSLInlineFragment()
                                    .on(schema.Input)
                                    .select(input_index=schema.Input.ix),
                                    DSLInlineFragment()
                                    .on(schema.TxResult)
                                    .select(
                                        schema.TxResult.cmd,
                                        result_index=schema.TxResult.ix,
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
            .on(schema.Transaction)
            .select(
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                schema.Transaction.digest,
=======
>>>>>>> 30fdd47 (GraphQL Beta Transition)
=======
                schema.Transaction.digest,
>>>>>>> ab55794 (Validating GraphQL Beta. Updates to gRPC protobuffs)
=======
>>>>>>> bafbf78 (GraphQL Beta Transition)
=======
                schema.Transaction.digest,
>>>>>>> b7a28a8 (Validating GraphQL Beta. Updates to gRPC protobuffs)
                schema.Transaction.kind.select(
                    DSLInlineFragment()
                    .on(schema.ProgrammableTransaction)
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
                ),
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
                transaction_blocks=schema.Checkpoint.transactions.select(
=======
                transaction_blocks=schema.Checkpoint.transactionBlocks.select(
<<<<<<< HEAD
>>>>>>> 30fdd47 (GraphQL Beta Transition)
=======
                transaction_blocks=schema.Checkpoint.transactions.select(
>>>>>>> ab55794 (Validating GraphQL Beta. Updates to gRPC protobuffs)
=======
>>>>>>> bafbf78 (GraphQL Beta Transition)
=======
                transaction_blocks=schema.Checkpoint.transactions.select(
>>>>>>> b7a28a8 (Validating GraphQL Beta. Updates to gRPC protobuffs)
                    cursor=schema.TransactionConnection.pageInfo.select(
                        pg_cursor.fragment(schema)
                    ),
                    tx_digests=schema.TransactionConnection.nodes.select(
                        schema.Transaction.digest
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
                    schema.ProtocolConfig.key,
                    schema.ProtocolConfig.value,
                ),
                schema.ProtocolConfigs.featureFlags.select(
                    schema.FeatureFlag.key,
                    schema.FeatureFlag.value,
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


class MoveEnum(PGQL_Fragment):
    """MoveEnum reusable fragment"""

    @cache
    def fragment(self, schema: DSLSchema) -> DSLFragment:
        """."""

        return (
            DSLFragment("MoveEnum")
            .on(schema.MoveEnum)
            .select(
                schema.MoveEnum.name.alias("enum_name"),
                schema.MoveEnum.abilities,
                schema.MoveEnum.variants.select(
                    schema.MoveEnumVariant.name.alias("variant_name"),
                    schema.MoveEnumVariant.fields.select(
                        schema.MoveField.name.alias("field_name"),
                        schema.MoveField.type.alias("field_type").select(
                            schema.OpenMoveType.signature
                        ),
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
