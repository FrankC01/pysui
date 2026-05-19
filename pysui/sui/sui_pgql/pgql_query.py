#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-#

"""QueryNode generators."""

from typing import Any, Optional, Callable, Union
import base64
import datetime
import re
from deprecated.sphinx import versionadded, versionchanged
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
from pysui.sui.sui_bcs.bcs import TransactionKind, TransactionData, SuiSignature, SuiU64
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_grpc.suimsgs.google import protobuf as _google_protobuf
import pysui.sui.sui_grpc.pgrpc_requests as _rn
from pysui.sui.sui_common.shared_types import ObjectSummary
import pysui.sui.sui_bcs.sui_system_bcs as sui_system_bcs




class GetCoinSummarySC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL object response to sui_prot.Object (matches gRPC shape)."""

    def __init__(self, *, owner: str | None = None, coin_id: str):
        """Set up."""
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
    def encode_fn() -> Callable[[dict], sui_prot.Object]:
        """Return deserializer producing sui_prot.Object from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.Object:
            obj = in_data.get("object", {})
            flat: dict = {}
            pgql_type._fast_flat(obj, flat)
            return sui_prot.Object(
                object_id=flat.get("coin_object_id"),
                version=flat.get("version", 0),
                digest=flat.get("object_digest"),
                balance=int(flat.get("balance", 0)) if flat.get("balance") else None,
            )

        return _encode


class GetObjectsForTypeSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL objects response to ListOwnedObjectsResponse proto."""

    def __init__(
        self,
        *,
        owner: str,
        object_type: str,
        next_page_token: bytes | None = None,
    ):
        """QueryNode initializer with owner filter.

        :param owner: Owner's Sui address
        :type owner: str
        :param object_type: The fully qualified type (i.e. `"0x2::coin::Coin<0x2::sui::SUI>"`)
        :type object_type: str
        :param next_page_token: page cursor bytes to advance query, defaults to None
        :type next_page_token: bytes | None
        """
        self.owner = owner
        self.object_type = object_type
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest with owner and type filters."""
        std_object = frag.StandardObject().fragment(schema)
        pg_cursor = frag.PageCursor().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)

        if self.next_page_token:
            obj_connection = schema.Query.objects(
                filter={"owner": self.owner, "type": self.object_type},
                after=self.next_page_token.decode(),
            )
        else:
            obj_connection = schema.Query.objects(
                filter={"owner": self.owner, "type": self.object_type}
            )
        obj_connection.select(
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



class GetObjectContentSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL object content response to GetObjectResponse proto."""

    def __init__(self, *, object_id: str):
        """QueryNode initializer."""
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



class GetMultipleObjectContentSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL objects content response to BatchGetObjectsResponse proto."""

    def __init__(
        self,
        *,
        object_ids: list[str],
    ):
        """QueryNode initializer."""
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


class GetMultipleObjectsSummarySC(PGQL_QueryNode):
    """SC variant: encode_fn normalizes multiGetObjects → list[ObjectSummary]."""

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
        """Build GraphQLRequest using the leaner SummaryObject fragment."""
        obj_ids = [{"address": cid} for cid in self.object_ids]
        qres = schema.Query.multiGetObjects(keys=obj_ids)
        summary_frag = frag.SummaryObject().fragment(schema)
        qres.select(summary_frag)
        return dsl_gql(summary_frag, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], list]:
        """Return deserializer producing list[ObjectSummary] from multiGetObjects response."""

        def _encode(in_data: dict) -> list:
            entries: list[ObjectSummary] = []
            for raw in in_data.get("multiGetObjects", []):
                if raw is None:
                    continue
                owner_str = None
                shared_v = None
                ow = raw.get("owner") or {}
                kind = ow.get("obj_owner_kind", "")
                if kind == "AddressOwner":
                    owner_str = ow.get("address_id")
                elif kind == "Shared":
                    shared_v = str(ow.get("initial_version", 0))
                elif kind == "ObjectOwner":
                    owner_str = ow.get("parent_id")
                entries.append(
                    ObjectSummary(
                        objectId=raw.get("object_id", ""),
                        version=str(raw.get("version", 0)),
                        digest=raw.get("object_digest", ""),
                        owner=owner_str,
                        initialSharedVersion=shared_v,
                    )
                )
            return entries

        return _encode


class GetObjectSummarySC(PGQL_QueryNode):
    """SC variant: encode_fn resolves a single object to ObjectSummary."""

    def __init__(self, *, object_id: str):
        """QueryNode initializer.

        :param object_id: The object id hex string with 0x prefix
        :type object_id: str
        """
        self.object_id = TypeValidator.check_object_id(object_id)

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest using the SummaryObject fragment."""
        summary_frag = frag.SummaryObject().fragment(schema)
        return dsl_gql(
            summary_frag,
            DSLQuery(
                object=schema.Query.object(address=self.object_id).select(summary_frag)
            ),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], "ObjectSummary"]:
        """Return deserializer producing ObjectSummary from single-object response."""

        def _encode(in_data: dict) -> ObjectSummary:
            raw = in_data.get("object") or {}
            owner_str = None
            shared_v = None
            ow = raw.get("owner") or {}
            kind = ow.get("obj_owner_kind", "")
            if kind == "AddressOwner":
                owner_str = ow.get("address_id")
            elif kind == "Shared":
                shared_v = str(ow.get("initial_version", 0))
            elif kind == "ObjectOwner":
                owner_str = ow.get("parent_id")
            return ObjectSummary(
                objectId=raw.get("object_id", ""),
                version=str(raw.get("version", 0)),
                digest=raw.get("object_digest", ""),
                owner=owner_str,
                initialSharedVersion=shared_v,
            )

        return _encode


@versionchanged(
    version="0.91.0", reason="Name MoveValue dropped 'data', using json instead"
)

class GetTransactionSC(PGQL_QueryNode):
    """SC variant: maps GQL transaction query to ExecutedTransaction proto."""

    def __init__(self, *, digest: str) -> None:
        """QueryNode initializer."""
        self.digest = digest

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build transaction query with metadata + BCS fields. Kind decoded from BCS."""
        tx_effects = frag.ExecutedTxEffects().fragment(schema)
        exec_object = frag.ExecutedObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.transaction(digest=self.digest)
        qres.select(
            schema.Transaction.digest,
            schema.Transaction.signatures.select(schema.UserSignature.signatureBytes),
            schema.Transaction.sender.select(submitter_address=schema.Address.address),
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
                schema.TransactionEffects.effectsJson,
                schema.TransactionEffects.balanceChangesJson,
            ),
            schema.Transaction.transactionBcs,
            schema.Transaction.transactionJson,
        )
        return dsl_gql(
            tx_effects,
            exec_object,
            base_object,
            gas_cost,
            DSLQuery(qres),
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], "sui_prot.ExecutedTransaction | None"]:
        """Return encoder mapping GQL transaction dict to ExecutedTransaction proto."""

        def _encode(in_data: dict) -> "sui_prot.ExecutedTransaction | None":
            return _encode_executed_tx(in_data.get("transaction"))

        return _encode


class GetTransactionsSC(PGQL_QueryNode):
    """SC variant: maps GQL multi-transaction query to list[ExecutedTransaction | None]."""

    def __init__(self, *, digests: list[str]) -> None:
        """QueryNode initializer."""
        self.digests = digests

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build multi-transaction query with metadata + BCS fields. Kind decoded from BCS."""
        tx_effects = frag.ExecutedTxEffects().fragment(schema)
        exec_object = frag.ExecutedObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Query.multiGetTransactions(keys=self.digests)
        qres.select(
            schema.Transaction.digest,
            schema.Transaction.signatures.select(schema.UserSignature.signatureBytes),
            schema.Transaction.sender.select(submitter_address=schema.Address.address),
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
                schema.TransactionEffects.effectsJson,
                schema.TransactionEffects.balanceChangesJson,
            ),
            schema.Transaction.transactionBcs,
            schema.Transaction.transactionJson,
        )
        return dsl_gql(
            tx_effects,
            exec_object,
            base_object,
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


class GetTransactionKindSC(PGQL_QueryNode):
    """SC variant: maps GQL transaction kind query to TransactionKind proto."""

    def __init__(self, *, digest: str) -> None:
        """QueryNode initializer."""
        self.digest = digest

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





class GetProtocolConfigSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL protocol config response to ProtocolConfig proto."""

    def __init__(self, *, version: Optional[int] = None):
        """QueryNode initializer."""
        self.version = version

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        std_prot_cfg = frag.StandardProtocolConfig().fragment(schema)
        if self.version is not None:
            qres = schema.Query.protocolConfigs(version=self.version).select(
                std_prot_cfg
            )
        else:
            qres = schema.Query.protocolConfigs().select(std_prot_cfg)
        return dsl_gql(std_prot_cfg, DSLQuery(qres))

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













@versionchanged(
    version="0.91.0", reason="tx_bytestr arg now requires bcs.TransactionKind"
)
@versionchanged(version="0.92.0", reason="Sui GraphQL requires sender set in tx_meta.")
@versionchanged(version="0.93.0", reason="tx_bytestr arg changed to tx_kind.")
@versionchanged(
    version="0.95.0", reason="Enabled ``skip_checks`` and ``do_gas_selection``"
)
class SimulateTransactionKindSC(PGQL_QueryNode):
    """SC variant: standalone query node with rich GQL query; encode_fn maps to SimulateTransactionResponse proto."""

    def __init__(
        self,
        *,
        tx_kind: TransactionKind,
        tx_meta: dict,
        skip_checks: Optional[bool] = True,
        do_gas_selection: Optional[bool] = False,
    ) -> None:
        """__init__ Initialize SimulateTransactionKindSC object.

        :param tx_kind: The programmable TransactionKind BCS object
        :type tx_kind: TransactionKind
        :param tx_meta: Dict with at minimum ``sender`` (str Sui address).
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
                kind=sui_prot.TransactionKindKind.PROGRAMMABLE_TRANSACTION,
                programmable_transaction=sui_prot.ProgrammableTransaction(
                    inputs=inputs, commands=cmds
                ),
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

        base_object = frag.BaseObject().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        qres = (
            schema.Query.simulateTransaction(
                transaction=self.transaction.to_dict(casing=betterproto2.Casing.SNAKE),
                checksEnabled=self.tx_skipchecks,
                doGasSelection=self.tx_do_gas_selection,
            )
            .alias("simulate")
            .select(
                effects=schema.SimulationResult.effects.select(
                    schema.TransactionEffects.digest,
                    schema.TransactionEffects.effectsDigest,
                    schema.TransactionEffects.effectsBcs,
                    schema.TransactionEffects.effectsJson,
                    schema.TransactionEffects.lamportVersion,
                    schema.TransactionEffects.status,
                    schema.TransactionEffects.executionError.select(
                        schema.ExecutionError.abortCode,
                        schema.ExecutionError.message,
                    ),
                    schema.TransactionEffects.epoch.select(
                        schema.Epoch.epochId,
                    ),
                    schema.TransactionEffects.gasEffects.select(
                        schema.GasEffects.gasSummary.select(
                            schema.GasCostSummary.computationCost,
                            schema.GasCostSummary.storageCost,
                            schema.GasCostSummary.storageRebate,
                            schema.GasCostSummary.nonRefundableStorageFee,
                        ),
                    ),
                    schema.TransactionEffects.timestamp,
                    schema.TransactionEffects.checkpoint.select(
                        schema.Checkpoint.sequenceNumber,
                    ),
                    schema.TransactionEffects.balanceChangesJson,
                    schema.TransactionEffects.events.select(
                        schema.EventConnection.nodes.select(
                            schema.Event.sequenceNumber,
                            schema.Event.eventBcs,
                            schema.Event.sender.select(
                                sender_address=schema.Address.address
                            ),
                            schema.Event.contents.select(
                                schema.MoveValue.type.select(
                                    event_type=schema.MoveType.repr
                                ),
                            ),
                            schema.Event.transactionModule.select(
                                schema.MoveModule.package.select(
                                    package_id=schema.MovePackage.address,
                                ),
                                module_name=schema.MoveModule.name,
                            ),
                        )
                    ),
                    schema.TransactionEffects.dependencies.select(
                        schema.TransactionConnection.nodes.select(
                            schema.Transaction.digest
                        )
                    ),
                    schema.TransactionEffects.transaction.select(
                        schema.Transaction.transactionBcs,
                        schema.Transaction.transactionJson,
                        schema.Transaction.digest,
                    ),
                    object_changes=schema.TransactionEffects.objectChanges.select(
                        schema.ObjectChangeConnection.nodes.select(
                            address=schema.ObjectChange.address,
                            deleted=schema.ObjectChange.idDeleted,
                            created=schema.ObjectChange.idCreated,
                            input_state=schema.ObjectChange.inputState.select(
                                std_object
                            ),
                            output_state=schema.ObjectChange.outputState.select(
                                std_object
                            ),
                        )
                    ),
                ),
                outputs=schema.SimulationResult.outputs.select(
                    schema.CommandResult.returnValues.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.bcs,
                            schema.MoveValue.json,
                            schema.MoveValue.type.select(
                                value_type=schema.MoveType.repr
                            ),
                        ),
                    ),
                    schema.CommandResult.mutatedReferences.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.bcs,
                            schema.MoveValue.json,
                            schema.MoveValue.type.select(
                                value_type=schema.MoveType.repr
                            ),
                        ),
                    ),
                ),
            )
        )
        return dsl_gql(base_object, std_object, DSLQuery(qres))

    def encode_fn(self) -> Callable[[dict], sui_prot.SimulateTransactionResponse]:
        """Return encoder mapping GQL simulate result to SimulateTransactionResponse proto."""

        def _encode(in_data: dict) -> sui_prot.SimulateTransactionResponse:
            raw = in_data.get("simulate") or {}
            eff = raw.get("effects") or {}

            # --- Transaction ---
            txn_node = eff.get("transaction") or {}
            txn_bcs_b64 = txn_node.get("transactionBcs")
            txn_json = txn_node.get("transactionJson")
            if txn_json:
                self.transaction = sui_prot.Transaction.from_dict(
                    txn_json, ignore_unknown_fields=True
                )
                if txn_bcs_b64:
                    self.transaction.bcs = sui_prot.Bcs(
                        name="TransactionData", value=base64.b64decode(txn_bcs_b64)
                    )
            elif txn_bcs_b64:
                txn_bcs_bytes = base64.b64decode(txn_bcs_b64)
                self.transaction.bcs = sui_prot.Bcs(
                    name="TransactionData", value=txn_bcs_bytes
                )
                self.transaction.version = 1
                txdata = TransactionData.deserialize(txn_bcs_bytes)
                gas_data = txdata.value.GasData
                self.transaction.gas_payment = sui_prot.GasPayment(
                    owner=gas_data.Owner.to_address_str(),
                    price=gas_data.Price,
                    budget=gas_data.Budget,
                )
                if txn_node.get("digest"):
                    self.transaction.digest = txn_node["digest"]

            # --- Effects via effectsJson ---
            # betterproto2.from_dict() maps camelCase→snake_case, so "integerValue"
            # becomes "integer_value" — but the proto field is named "value". Rename
            # before deserializing so AccumulatorWrite.value is populated correctly.
            effects_json_dict = eff.get("effectsJson") or {}
            for _co in effects_json_dict.get("changedObjects") or []:
                _aw = _co.get("accumulatorWrite")
                if _aw and "integerValue" in _aw:
                    _aw["value"] = int(_aw["integerValue"])
            effects_proto = sui_prot.TransactionEffects.from_dict(
                effects_json_dict, ignore_unknown_fields=True
            )
            effects_bcs_b64 = eff.get("effectsBcs")
            if effects_bcs_b64:
                effects_proto.bcs = sui_prot.Bcs(
                    name="TransactionEffects", value=base64.b64decode(effects_bcs_b64)
                )

            # --- objectChanges typed nodes: object_type_map + ObjectSet ---
            objects, object_type_map = _encode_simulate_object_changes(eff)

            # Back-fill object_type from typed nodes (effectsJson omits objectType)
            for co in effects_proto.changed_objects:
                if not co.object_type and co.object_id in object_type_map:
                    co.object_type = object_type_map[co.object_id]

            # --- Balance changes via balanceChangesJson ---
            balance_changes = [
                sui_prot.BalanceChange.from_dict(bc)
                for bc in (eff.get("balanceChangesJson") or [])
            ]

            timestamp = _parse_gql_datetime(eff.get("timestamp"))
            checkpoint_seq = (eff.get("checkpoint") or {}).get("sequenceNumber")

            # --- Events (typed — no eventsJson in GQL) ---
            events = _encode_simulate_events(
                ((eff.get("events") or {}).get("nodes") or [])
            )

            # --- CommandResult outputs ---
            cmd_outputs = _encode_simulate_outputs(raw.get("outputs") or [])

            return sui_prot.SimulateTransactionResponse(
                transaction=sui_prot.ExecutedTransaction(
                    transaction=self.transaction,
                    signatures=[],
                    effects=effects_proto,
                    balance_changes=balance_changes,
                    timestamp=timestamp,
                    checkpoint=checkpoint_seq,
                    objects=sui_prot.ObjectSet(objects=objects) if objects else None,
                ),
                command_outputs=cmd_outputs,
            )

        return _encode


@versionadded(version="0.99.0", reason="Replaces deprecated DryRunTransaction.")
class SimulateTransactionSC(SimulateTransactionKindSC):
    """SC variant: simulates a fully serialized transaction (BCS bytes or base64 string).

    Accepts a pre-serialized ``TransactionData`` BCS blob rather than a structured
    ``TransactionKind``. Inherits ``encode_fn()`` from ``SimulateTransactionKindSC``
    unchanged — the GQL ``SimulationResult`` shape is identical for both inputs.
    The original ``SimulateTransaction`` class is preserved for backwards compatibility.
    """

    def __init__(
        self,
        *,
        tx_bytestr: bytes | str,
        skip_checks: Optional[bool] = True,
        do_gas_selection: Optional[bool] = False,
    ) -> None:
        """__init__ Initialize SimulateTransactionSC.

        :param tx_bytestr: Serialized BCS bytes of TransactionData, or base64 string of same
        :type tx_bytestr: bytes | str
        :param skip_checks: Whether to skip transaction checks, defaults to True
        :type skip_checks: Optional[bool]
        :param do_gas_selection: Whether to perform gas selection, defaults to False
        :type do_gas_selection: Optional[bool]
        """
        transaction = (
            tx_bytestr
            if isinstance(tx_bytestr, bytes)
            else base64.b64decode(tx_bytestr)
        )
        self.transaction = sui_prot.Transaction(
            bcs=sui_prot.Bcs(value=transaction, name="TransactionData")
        )
        self.tx_skipchecks = skip_checks
        self.tx_do_gas_selection = do_gas_selection

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build rich simulate query; self.transaction is pre-set from BCS bytes."""
        base_object = frag.BaseObject().fragment(schema)
        std_object = frag.StandardObject().fragment(schema)
        qres = (
            schema.Query.simulateTransaction(
                transaction=self.transaction.to_dict(casing=betterproto2.Casing.SNAKE),
                checksEnabled=self.tx_skipchecks,
                doGasSelection=self.tx_do_gas_selection,
            )
            .alias("simulate")
            .select(
                effects=schema.SimulationResult.effects.select(
                    schema.TransactionEffects.digest,
                    schema.TransactionEffects.effectsDigest,
                    schema.TransactionEffects.effectsBcs,
                    schema.TransactionEffects.effectsJson,
                    schema.TransactionEffects.lamportVersion,
                    schema.TransactionEffects.status,
                    schema.TransactionEffects.executionError.select(
                        schema.ExecutionError.abortCode,
                        schema.ExecutionError.message,
                    ),
                    schema.TransactionEffects.epoch.select(
                        schema.Epoch.epochId,
                    ),
                    schema.TransactionEffects.gasEffects.select(
                        schema.GasEffects.gasSummary.select(
                            schema.GasCostSummary.computationCost,
                            schema.GasCostSummary.storageCost,
                            schema.GasCostSummary.storageRebate,
                            schema.GasCostSummary.nonRefundableStorageFee,
                        ),
                    ),
                    schema.TransactionEffects.timestamp,
                    schema.TransactionEffects.checkpoint.select(
                        schema.Checkpoint.sequenceNumber,
                    ),
                    schema.TransactionEffects.balanceChangesJson,
                    schema.TransactionEffects.events.select(
                        schema.EventConnection.nodes.select(
                            schema.Event.sequenceNumber,
                            schema.Event.eventBcs,
                            schema.Event.sender.select(
                                sender_address=schema.Address.address
                            ),
                            schema.Event.contents.select(
                                schema.MoveValue.type.select(
                                    event_type=schema.MoveType.repr
                                ),
                            ),
                            schema.Event.transactionModule.select(
                                schema.MoveModule.package.select(
                                    package_id=schema.MovePackage.address,
                                ),
                                module_name=schema.MoveModule.name,
                            ),
                        )
                    ),
                    schema.TransactionEffects.dependencies.select(
                        schema.TransactionConnection.nodes.select(
                            schema.Transaction.digest
                        )
                    ),
                    schema.TransactionEffects.transaction.select(
                        schema.Transaction.transactionBcs,
                        schema.Transaction.transactionJson,
                        schema.Transaction.digest,
                    ),
                    object_changes=schema.TransactionEffects.objectChanges.select(
                        schema.ObjectChangeConnection.nodes.select(
                            address=schema.ObjectChange.address,
                            deleted=schema.ObjectChange.idDeleted,
                            created=schema.ObjectChange.idCreated,
                            input_state=schema.ObjectChange.inputState.select(
                                std_object
                            ),
                            output_state=schema.ObjectChange.outputState.select(
                                std_object
                            ),
                        )
                    ),
                ),
                outputs=schema.SimulationResult.outputs.select(
                    schema.CommandResult.returnValues.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.bcs,
                            schema.MoveValue.json,
                            schema.MoveValue.type.select(
                                value_type=schema.MoveType.repr
                            ),
                        ),
                    ),
                    schema.CommandResult.mutatedReferences.select(
                        schema.CommandOutput.value.select(
                            schema.MoveValue.bcs,
                            schema.MoveValue.json,
                            schema.MoveValue.type.select(
                                value_type=schema.MoveType.repr
                            ),
                        ),
                    ),
                ),
            )
        )
        return dsl_gql(base_object, std_object, DSLQuery(qres))

    # encode_fn() inherited from SimulateTransactionKindSC unchanged.



class ExecuteTransactionSC(PGQL_QueryNode):
    """SC variant: executes a transaction and returns an ExecutedTransaction proto."""

    def __init__(self, *, tx_bytestr: str, sig_array: list[str]) -> None:
        """__init__ Initialize ExecuteTransactionSC object."""
        self.tx_data: str = tx_bytestr
        self.sigs: list[str] = sig_array

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Execute transaction; fetch fields that mirror GetTransactionSC via effects.transaction."""
        tx_effects = frag.ExecutedTxEffects().fragment(schema)
        exec_object = frag.ExecutedObject().fragment(schema)
        base_object = frag.BaseObject().fragment(schema)
        gas_cost = frag.GasCost().fragment(schema)
        qres = schema.Mutation.executeTransaction(
            transactionDataBcs=self.tx_data, signatures=self.sigs
        ).select(
            schema.ExecutionResult.effects.select(
                tx_effects,
                schema.TransactionEffects.effectsBcs,
                schema.TransactionEffects.effectsJson,
                schema.TransactionEffects.balanceChangesJson,
                schema.TransactionEffects.transaction.select(
                    schema.Transaction.signatures.select(
                        schema.UserSignature.signatureBytes
                    ),
                    schema.Transaction.transactionBcs,
                    schema.Transaction.transactionJson,
                ),
            )
        )
        return dsl_gql(
            tx_effects, exec_object, base_object, gas_cost, DSLMutation(qres)
        )

    @staticmethod
    def encode_fn() -> Callable[[dict], "sui_prot.ExecutedTransaction | None"]:
        """Return encoder mapping executeTransaction response to ExecutedTransaction proto."""

        def _encode(in_data: dict) -> "sui_prot.ExecutedTransaction | None":
            effects_dict = (in_data.get("executeTransaction") or {}).get(
                "effects"
            ) or {}
            txn_inner = effects_dict.get("transaction") or {}
            tx_dict = {**txn_inner, "effects": effects_dict}
            return _encode_executed_tx(tx_dict)

        return _encode


# ---------------------------------------------------------------------------
# SC siblings — these subclasses inherit as_document_node() unchanged and
# override encode_fn() to return gRPC proto instances instead of GQL types.
# Used by SuiCommand subclasses that dispatch over both GQL and gRPC.
# ---------------------------------------------------------------------------


class GetCoinMetaDataSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL coinMetadata response to GetCoinInfoResponse proto."""

    def __init__(self, *, coin_type: Optional[str] = "0x2::sui::SUI") -> None:
        """QueryNode initializer."""
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


class GetAddressCoinBalanceSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL address.balance response to GetBalanceResponse proto."""

    def __init__(self, *, owner: str, coin_type: Optional[str] = "0x2::sui::SUI"):
        self.owner = owner
        self.coin_type = coin_type

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
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


class GetAddressCoinBalancesSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL address.balances response to ListBalancesResponse proto."""

    def __init__(self, *, owner: str, next_page_token: bytes | None = None):
        """QueryNode initializer.

        :param owner: the owner's Sui address
        :type owner: str
        :param next_page_token: page cursor bytes to advance query, defaults to None
        :type next_page_token: bytes | None
        """
        self.owner = owner
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        qres = schema.Query.address(address=self.owner).alias("qres")
        balance_connection = schema.Address.balances
        if self.next_page_token:
            balance_connection(after=self.next_page_token.decode())

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


class GetEpochSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL epoch response to GetEpochResponse proto."""

    def __init__(self, *, epoch_id: Optional[int] = None) -> None:
        """QueryNode initializer."""
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


class GetBasicCurrentEpochInfoSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL basic epoch response to Epoch proto."""

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


class GetPackageVersionsSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL packageVersions response to ListPackageVersionsResponse proto."""

    def __init__(
        self,
        *,
        package_address: str,
        next_page_token: bytes | None = None,
    ) -> None:
        """QueryNode initializer."""
        self.package_address = package_address
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """."""
        pg_cursor = frag.PageCursor()
        qres = schema.Query.packageVersions(address=self.package_address)
        if self.next_page_token:
            qres(after=self.next_page_token.decode())
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


class GetNameServiceAddressSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL suinsName response to LookupNameResponse proto.

    Overrides as_document_node to also select Address.address (parent only selects
    defaultSuinsName, which is insufficient to populate NameRecord.target_address).
    """

    def __init__(self, *, name: str):
        """__init__ QueryNode initializer."""
        self.name = name

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


class GetNameServiceNamesSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL address response to ReverseLookupNameResponse proto.

    Overrides as_document_node to use clean field selection without aliases and
    to also select Address.address for populating NameRecord.target_address.
    Returns empty response when the address has no SuiNS name registered.
    """

    def __init__(self, *, owner: str):
        """QueryNode initializer."""
        self.owner = owner

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
            raise ValueError(
                f"_gql_sig_body_to_proto: unrecognized scalar type '{body}'"
            )
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
            type_params = [
                _gql_sig_body_to_proto(p) for p in dt.get("typeParameters", [])
            ]
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
        reference: Optional[sui_prot.OpenSignatureReference] = (
            sui_prot.OpenSignatureReference.IMMUTABLE
        )
    elif ref == "&mut":
        reference = sui_prot.OpenSignatureReference.MUTABLE
    else:
        reference = None
    return sui_prot.OpenSignature(
        reference=reference,
        body=_gql_sig_body_to_proto(sig_dict.get("body", {})),
    )


def _encode_object_from_raw(obj_dict: dict) -> sui_prot.Object:
    """Map a StandardObject or ExecutedObject raw GQL dict to an Object proto.

    All dict keys are DSL aliases defined in BaseObject / StandardObject / ExecutedObject
    fragments (pgql_fragments.py) — they are snake_case aliases, not camelCase GQL field
    names, so betterproto2 from_dict() cannot be used here.

    Key alias mappings (fragment → dict key):
      BaseObject:      Object.address                 → "object_id"
                       Object.digest                  → "object_digest"
                       Object.version                 → "version"
      StandardObject:  Object.objectBcs.alias("bcs")  → "bcs"  (Base64 scalar, not Bcs message)
                       Object.storageRebate            → "storage_rebate"
                       Object.previousTransaction.Transaction.digest
                                                      → "prior_transaction.previous_transaction_digest"
                       Object.asMoveObject             → "as_move_content"
                       MoveObject.contents             → "as_move_content.as_object"
                       MoveValue.type.MoveType.repr    → "as_move_content.as_object.object_type_repr.object_type"
                       MoveObject.hasPublicTransfer    → "as_move_content.has_public_transfer"
      ExecutedObject:  MoveValue.json                 → "as_move_content.as_object.content"
                                                         (Move struct as parsed dict; maps → Object.json via
                                                          _google_protobuf.Value.from_dict(); also used to
                                                          derive Object.balance for Coin<T> objects.)
                       MoveValue.bcs                  → "as_move_content.as_object.contents_bcs"
                                                         (Base64 BCS of Move struct value;
                                                          maps → Object.contents as Bcs(name=object_type, value=...))

    Object.balance is derived from content JSON rather than MoveObject.balance:
    MoveObject.balance(coinType) requires a coinType argument and returns a composite
    Balance type — unusable in a generic fragment. For Coin<T> objects, MoveValue.json
    produces {"balance": "..."}, so balance is parsed from json_str after deserialization.

    ExecutedObject-only fields are absent when called from StandardObject callers — .get()
    returns None and those proto fields are left unset, which is correct behaviour.

    Protocol gaps (never available from GQL typed fields):
      Object.id_operation — not a GQL typed field; sourced from effectsJson if needed
    """
    if not obj_dict:
        return sui_prot.Object()
    bcs_str: Optional[str] = obj_dict.get("bcs")
    object_bcs = (
        sui_prot.Bcs(name="Object", value=base64.b64decode(bcs_str))
        if bcs_str
        else None
    )
    owner = _owner_from_inline_frag(obj_dict.get("owner"))
    prior_tx = obj_dict.get("prior_transaction") or {}
    prev_tx: Optional[str] = (
        prior_tx.get("previous_transaction_digest")
        if isinstance(prior_tx, dict)
        else None
    )
    object_type: Optional[str] = None
    has_public_transfer: Optional[bool] = None
    contents_bcs: Optional[sui_prot.Bcs] = None
    json_val: Optional[_google_protobuf.Value] = None
    balance: Optional[int] = None
    as_move_content = obj_dict.get("as_move_content")
    if isinstance(as_move_content, dict):
        has_public_transfer = as_move_content.get("has_public_transfer")
        as_object = as_move_content.get("as_object") or {}
        if isinstance(as_object, dict):
            obj_type_repr = as_object.get("object_type_repr") or {}
            if isinstance(obj_type_repr, dict):
                object_type = obj_type_repr.get("object_type")
            cbcs = as_object.get("contents_bcs")
            if cbcs and object_type:
                contents_bcs = sui_prot.Bcs(
                    name=object_type, value=base64.b64decode(cbcs)
                )
            # content (MoveValue.json) arrives as a parsed dict from the GQL scalar.
            # Wrapped as google.protobuf.Value for Object.json; balance extracted for Coin<T>.
            content = as_object.get("content")
            if isinstance(content, dict):
                json_val = _google_protobuf.Value.from_dict(content)
                bal_raw = content.get("balance")
                if bal_raw is not None:
                    try:
                        balance = int(bal_raw)
                    except (ValueError, TypeError):
                        pass
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
        contents=contents_bcs,
        json=json_val,
        balance=balance,
    )


def _encode_coin_from_move_obj(mo_dict: dict) -> sui_prot.Object:
    """Map a MoveObject-level GQL dict (coin or staked coin node) to an Object proto."""
    if not mo_dict:
        return sui_prot.Object()
    owner = _owner_from_inline_frag(mo_dict.get("owner"))
    prev_tx_info = mo_dict.get("previousTransaction") or {}
    prev_tx: Optional[str] = (
        prev_tx_info.get("previous_transaction")
        if isinstance(prev_tx_info, dict)
        else None
    )
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
        objects: list[sui_prot.Object] = [
            _encode_coin_from_move_obj(c) for c in in_data
        ]
        return sui_prot.ListOwnedObjectsResponse(objects=objects, next_page_token=None)
    qres = in_data.get("qres", in_data)
    coins = qres.get("coins", {}) if isinstance(qres, dict) else {}
    cursor = coins.get("cursor", {}) if isinstance(coins, dict) else {}
    coin_objects = coins.get("coin_objects", []) if isinstance(coins, dict) else []
    objects = [_encode_coin_from_move_obj(c) for c in coin_objects]
    end_cursor: Optional[str] = (
        cursor.get("endCursor") if isinstance(cursor, dict) else None
    )
    next_page_token: Optional[bytes] = (
        end_cursor.encode()
        if isinstance(cursor, dict) and cursor.get("hasNextPage") and end_cursor
        else None
    )
    return sui_prot.ListOwnedObjectsResponse(
        objects=objects, next_page_token=next_page_token
    )


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
                total_network_transactions=(
                    int(net_txns) if net_txns is not None else None
                ),
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
        sig_dict = (
            sig_container.get("signature") or {}
            if isinstance(sig_container, dict)
            else {}
        )
        body = sig_dict.get("body") if isinstance(sig_dict, dict) else None
        field_type = _gql_sig_body_to_proto(body) if body is not None else None
        result.append(
            sui_prot.FieldDescriptor(
                name=f.get("field_name"),
                position=i,
                type=field_type,
            )
        )
    return result


def _struct_to_datatype(
    struct_dict: dict,
    defining_id: str,
    module_name: str,
) -> sui_prot.DatatypeDescriptor:
    """Map a MoveStruct raw dict to a DatatypeDescriptor proto."""
    name = struct_dict.get("struct_name", "")
    abilities = [
        _GQL_ABILITY_MAP[a]
        for a in struct_dict.get("abilities", [])
        if a in _GQL_ABILITY_MAP
    ]
    type_params = [
        sui_prot.TypeParameter(
            constraints=[
                _GQL_ABILITY_MAP[c]
                for c in tp.get("constraints", [])
                if c in _GQL_ABILITY_MAP
            ],
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
    abilities = [
        _GQL_ABILITY_MAP[a]
        for a in enum_dict.get("abilities", [])
        if a in _GQL_ABILITY_MAP
    ]
    type_params = [
        sui_prot.TypeParameter(
            constraints=[
                _GQL_ABILITY_MAP[c]
                for c in tp.get("constraints", [])
                if c in _GQL_ABILITY_MAP
            ],
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
    visibility = _GQL_VIS_MAP.get(
        vis_str, sui_prot.FunctionDescriptorVisibility.PRIVATE
    )
    is_entry = bool(func_dict.get("isEntry", False))
    type_params = [
        sui_prot.TypeParameter(
            constraints=[
                _GQL_ABILITY_MAP[c]
                for c in tp.get("constraints", [])
                if c in _GQL_ABILITY_MAP
            ],
            is_phantom=False,
        )
        for tp in func_dict.get("typeParameters", [])
        if isinstance(tp, dict)
    ]
    raw_params = func_dict.get("parameters", [])
    parameters = [
        _gql_sig_to_proto_open_sig(p["signature"])
        for p in raw_params
        if isinstance(p, dict)
        and "signature" in p
        and not _is_tx_context_sig(p["signature"])
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
    module_structures = (
        struct_list_data.get("module_structures", [])
        if isinstance(struct_list_data, dict)
        else []
    )
    module_functions = (
        func_list_data.get("module_functions", [])
        if isinstance(func_list_data, dict)
        else []
    )
    datatypes = [
        _struct_to_datatype(s, package_id, module_name)
        for s in module_structures
        if isinstance(s, dict)
    ]
    functions = [
        _func_to_descriptor(f) for f in module_functions if isinstance(f, dict)
    ]
    return sui_prot.Module(
        name=module_name,
        datatypes=datatypes,
        functions=functions,
    )


# ---------------------------------------------------------------------------
# Step 1 — Simple GQL SC siblings
# ---------------------------------------------------------------------------


class GetObjectSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL object response to Object proto."""

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
    def encode_fn() -> Callable[[dict], sui_prot.Object]:
        """Return deserializer producing Object from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.Object:
            obj_dict = in_data.get("object") or {}
            return _encode_object_from_raw(obj_dict)

        return _encode


class GetPastObjectSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL past object response to Object proto."""

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
    def encode_fn() -> Callable[[dict], sui_prot.Object]:
        """Return deserializer producing Object from GQL object dict."""

        def _encode(in_data: dict) -> sui_prot.Object:
            obj_dict = in_data.get("object") or {}
            return _encode_object_from_raw(obj_dict)

        return _encode


class GetMoveDataTypeSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL datatype response to GetDatatypeResponse proto."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        data_type_name: str,
    ) -> None:
        """QueryNode initializer."""
        self.package = package
        self.module = module_name
        self.data_type_name = data_type_name

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


class GetStructureSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL struct response to GetDatatypeResponse proto."""

    def __init__(
        self,
        *,
        package: str,
        module_name: str,
        structure_name: str,
    ) -> None:
        """QueryNode initializer."""
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


class GetFunctionSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL function response to GetFunctionResponse proto."""

    def __init__(self, *, package: str, module_name: str, function_name: str) -> None:
        """QueryNode initializer."""
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


class GetCoinsSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL coins response to ListOwnedObjectsResponse proto."""

    def __init__(
        self,
        *,
        owner: str,
        coin_type: Optional[str] = "0x2::coin::Coin<0x2::sui::SUI>",
        next_page_token: bytes | None = None,
    ):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param coin_type: The fully qualified coin type to use in filtering, defaults to "0x2::coin::Coin<0x2::sui::SUI>"
        :type coin_type: str, optional
        :param next_page_token: page cursor bytes to advance query, defaults to None
        :type next_page_token: bytes | None
        """
        self.owner = owner
        self.coin_type = coin_type
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        qres = schema.Query.address(address=self.owner).alias("qres")
        coin_connection = schema.Address.objects(filter={"type": self.coin_type}).alias(
            "coins"
        )
        if self.next_page_token:
            coin_connection(after=self.next_page_token.decode())

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
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL coins dict."""
        return _encode_coins_list


class GetGasSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL SUI gas coins response to ListOwnedObjectsResponse proto."""

    def __init__(self, *, owner: str, next_page_token: bytes | None = None, **kwargs):
        self.owner = owner
        self.coin_type = "0x2::coin::Coin<0x2::sui::SUI>"
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest with optional paging cursor."""
        qres = schema.Query.address(address=self.owner).alias("qres")
        coin_connection = schema.Address.objects(filter={"type": self.coin_type}).alias(
            "coins"
        )
        if self.next_page_token:
            coin_connection(after=self.next_page_token.decode())

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
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL gas dict."""
        return _encode_coins_list


class GetDelegatedStakesSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL staked coins response to ListOwnedObjectsResponse proto."""

    def __init__(self, owner: str, next_page_token: bytes | None = None):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param next_page_token: page cursor bytes to advance query, defaults to None
        :type next_page_token: bytes | None
        """
        self.owner = owner
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        if self.next_page_token:
            qres = schema.Query.objects(
                after=self.next_page_token.decode(),
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
            end_cursor: Optional[str] = (
                cursor.get("endCursor") if isinstance(cursor, dict) else None
            )
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


class GetObjectsOwnedByAddressSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL owned objects response to ListOwnedObjectsResponse proto."""

    def __init__(self, *, owner: str, next_page_token: bytes | None = None):
        """QueryNode initializer.

        :param owner: Owner's Sui address
        :type owner: str
        :param next_page_token: page cursor bytes to advance query, defaults to None
        :type next_page_token: bytes | None
        """
        self.owner = owner
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest."""
        qres = schema.Query.objects(filter={"owner": self.owner})
        if self.next_page_token:
            qres(after=self.next_page_token.decode())

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
    def encode_fn() -> Callable[[dict], sui_prot.ListOwnedObjectsResponse]:
        """Return deserializer producing ListOwnedObjectsResponse from GQL objects dict."""

        def _encode(in_data: dict) -> sui_prot.ListOwnedObjectsResponse:
            objects_data = in_data.get("objects") or {}
            cursor = objects_data.get("cursor") or {}
            obj_list = objects_data.get("objects_data", [])
            objects: list[sui_prot.Object] = [
                _encode_object_from_raw(o) for o in obj_list if isinstance(o, dict)
            ]
            end_cursor: Optional[str] = (
                cursor.get("endCursor") if isinstance(cursor, dict) else None
            )
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


class GetMultipleObjectsSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL multi-object response to BatchGetObjectsResponse proto."""

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
    def encode_fn() -> Callable[[dict], sui_prot.BatchGetObjectsResponse]:
        """Return deserializer producing BatchGetObjectsResponse from GQL multi-get dict."""

        def _encode(in_data: dict) -> sui_prot.BatchGetObjectsResponse:
            obj_list = in_data.get("multiGetObjects", [])
            return sui_prot.BatchGetObjectsResponse(
                objects=[
                    sui_prot.GetObjectResult(object=_encode_object_from_raw(o))
                    for o in obj_list
                    if isinstance(o, dict)
                ]
            )

        return _encode


class GetMultipleVersionedObjectsSC(PGQL_QueryNode):
    """GetMultipleVersionedObjectsSC When executed, return the object information for a specified version.

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
    def encode_fn() -> Callable[[dict], sui_prot.BatchGetObjectsResponse]:
        """Return deserializer producing BatchGetObjectsResponse from GQL multi-get dict."""

        def _encode(in_data: dict) -> sui_prot.BatchGetObjectsResponse:
            obj_list = in_data.get("multiGetObjects", [])
            return sui_prot.BatchGetObjectsResponse(
                objects=[
                    sui_prot.GetObjectResult(object=_encode_object_from_raw(o))
                    for o in obj_list
                    if isinstance(o, dict)
                ]
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 5 — Checkpoint SC siblings
# ---------------------------------------------------------------------------


class GetLatestCheckpointSequenceSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL checkpoints response to GetCheckpointResponse proto."""

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
    def encode_fn() -> Callable[[dict], sui_prot.GetCheckpointResponse]:
        """Return deserializer producing GetCheckpointResponse from GQL checkpoints dict."""

        def _encode(in_data: dict) -> sui_prot.GetCheckpointResponse:
            checkpoints = in_data.get("checkpoints") or {}
            nodes = checkpoints.get("nodes", [])
            if not nodes:
                return sui_prot.GetCheckpointResponse()
            return _encode_checkpoint_from_raw(nodes[0])

        return _encode


class GetCheckpointBySequenceSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL checkpoint response to GetCheckpointResponse proto."""

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
    def encode_fn() -> Callable[[dict], sui_prot.GetCheckpointResponse]:
        """Return deserializer producing GetCheckpointResponse from GQL checkpoint dict."""

        def _encode(in_data: dict) -> sui_prot.GetCheckpointResponse:
            cp_dict = in_data.get("checkpoint") or {}
            return _encode_checkpoint_from_raw(cp_dict)

        return _encode


# ---------------------------------------------------------------------------
# Step 6 — Package/module/TX SC siblings
# ---------------------------------------------------------------------------


class GetModuleSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL module response to Module proto."""

    def __init__(self, *, package: str, module_name: str) -> None:
        """QueryNode initializer."""
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


class GetPackageSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL package response to PackageModulesResult proto."""

    def __init__(self, *, package: str, next_page_token: bytes | None = None, **kwargs):
        """Init with bytes-based cursor."""
        self.package = package
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build request using bytes cursor for modules paging."""
        if self.next_page_token:
            mod_q = schema.MovePackage.modules(after=self.next_page_token.decode())
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
        return dsl_gql(pg_cursor, func, struc, mod, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], "_rn.PackageModulesResult"]:
        """Return deserializer producing PackageModulesResult from GQL package dict."""

        def _encode(in_data: dict) -> "_rn.PackageModulesResult":
            pkg_raw = (in_data.get("object") or {}).get("asMovePackage") or {}
            if not pkg_raw:
                return _rn.PackageModulesResult(
                    package=sui_prot.Package(), modules=[], next_page_token=None
                )
            package_id: str = pkg_raw.get("package_id") or ""
            package_version = pkg_raw.get("package_version")
            modules_conn = pkg_raw.get("modules") or {}
            cursor = modules_conn.get("cursor") or {}
            nodes = modules_conn.get("nodes") or []
            end_cursor = cursor.get("endCursor")
            has_next = cursor.get("hasNextPage", False)
            next_token = end_cursor.encode() if has_next and end_cursor else None
            modules = [
                _module_raw_to_proto(m, package_id)
                for m in nodes
                if isinstance(m, dict)
            ]
            return _rn.PackageModulesResult(
                package=sui_prot.Package(
                    storage_id=package_id,
                    version=(
                        int(package_version) if package_version is not None else None
                    ),
                ),
                modules=modules,
                next_page_token=next_token,
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 7b — Paged High-complexity SC siblings
# ---------------------------------------------------------------------------


class GetStructuresSC(PGQL_QueryNode):
    """SC variant: encode_fn maps one GQL page to MoveStructuresGRPC with next_page_token."""

    def __init__(
        self, *, package: str, module_name: str, next_page_token: bytes | None = None
    ):
        """Init with bytes-based cursor."""
        self.package = package
        self.module = module_name
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build request using bytes cursor for structs paging."""
        if self.next_page_token:
            struct_q = schema.MoveModule.structs(after=self.next_page_token.decode())
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

    def encode_fn(self) -> Callable[[dict], "_rn.MoveStructuresGRPC"]:
        """Return deserializer producing MoveStructuresGRPC from one GQL page dict."""
        defining_id = self.package
        module_name = self.module

        def _encode(in_data: dict) -> "_rn.MoveStructuresGRPC":
            mod = ((in_data.get("object") or {}).get("asMovePackage") or {}).get(
                "module"
            ) or {}
            structs_conn = mod.get("structs") or {}
            cursor = structs_conn.get("cursor") or {}
            nodes = structs_conn.get("nodes") or []
            end_cursor = cursor.get("endCursor")
            has_next = cursor.get("hasNextPage", False)
            next_token = end_cursor.encode() if has_next and end_cursor else None
            return _rn.MoveStructuresGRPC(
                structures=[
                    _struct_to_datatype(n, defining_id, module_name)
                    for n in nodes
                    if isinstance(n, dict)
                ],
                next_page_token=next_token,
            )

        return _encode


class GetFunctionsSC(PGQL_QueryNode):
    """SC variant: encode_fn maps one GQL page to MoveFunctionsGRPC with next_page_token."""

    def __init__(
        self, *, package: str, module_name: str, next_page_token: bytes | None = None
    ):
        """Init with bytes-based cursor."""
        self.package = package
        self.module = module_name
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build request using bytes cursor for functions paging."""
        if self.next_page_token:
            func_q = schema.MoveModule.functions(after=self.next_page_token.decode())
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
    def encode_fn() -> Callable[[dict], "_rn.MoveFunctionsGRPC"]:
        """Return deserializer producing MoveFunctionsGRPC from one GQL page dict."""

        def _encode(in_data: dict) -> "_rn.MoveFunctionsGRPC":
            mod = ((in_data.get("object") or {}).get("asMovePackage") or {}).get(
                "module"
            ) or {}
            funcs_conn = mod.get("functions") or {}
            cursor = funcs_conn.get("cursor") or {}
            nodes = funcs_conn.get("nodes") or []
            end_cursor = cursor.get("endCursor")
            has_next = cursor.get("hasNextPage", False)
            next_token = end_cursor.encode() if has_next and end_cursor else None
            return _rn.MoveFunctionsGRPC(
                functions=[
                    _func_to_descriptor(n) for n in nodes if isinstance(n, dict)
                ],
                next_page_token=next_token,
            )

        return _encode


# ---------------------------------------------------------------------------
# Step 9 — High complexity SC siblings
# ---------------------------------------------------------------------------


class GetDynamicFieldsSC(PGQL_QueryNode):
    """SC variant: encode_fn maps GQL dynamic fields response to ListDynamicFieldsResponse proto."""

    def __init__(
        self,
        *,
        object_id: str,
        next_page_token: bytes | None = None,
    ) -> None:
        """QueryNode initializer."""
        self.object_id = object_id
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Return a query for dynamic fields."""
        qres = schema.Query.object(address=self.object_id)
        qres = qres.select(
            schema.Object.address.alias("parent_object_id"), schema.Object.version
        )
        dfield_connection = schema.Object.dynamicFields
        if self.next_page_token:
            dfield_connection(after=self.next_page_token.decode())

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
                    fields.append(
                        sui_prot.DynamicField(
                            kind=kind,
                            parent=parent_id,
                            child_id=field_data.get("address"),
                        )
                    )
                else:
                    obj_type = field_data.get("object_type") or {}
                    fields.append(
                        sui_prot.DynamicField(
                            kind=kind,
                            parent=parent_id,
                            value_type=(obj_type.get("layout")),
                        )
                    )

            end_cursor: Optional[str] = (
                cursor.get("endCursor") if isinstance(cursor, dict) else None
            )
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



class GetChainIdentifierSC(PGQL_QueryNode):
    """SC variant: encode_fn returns chain identifier as plain str."""

    def __init__(self) -> None:
        """."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQL DSL request."""
        return gql("{ chainIdentifier }")

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


def _bcs_system_state_to_proto(
    bcs_ss: "sui_system_bcs.SuiSystemStateInnerV2",
) -> sui_prot.SystemState:
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


def _encode_validator_from_gql(
    v: dict, *, name_key: str = "validator_name", address_key: str = "validator_address"
) -> sui_prot.Validator:
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


class GetLatestSuiSystemStateSC(PGQL_QueryNode):
    """SC variant: inherits BCS query from base; decodes systemState.bcs to SystemState proto."""

    def __init__(self) -> None:
        """QueryNode initializer."""

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GraphQLRequest using BCS system-state path."""
        qres = schema.Query.epoch.select(
            schema.Epoch.systemState.select(schema.MoveValue.bcs)
        )
        return dsl_gql(DSLQuery(qres))

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


class GetCurrentValidatorsSC(PGQL_QueryNode):
    """SC variant: encode_fn maps one GQL page to ValidatorsResult with next_page_token."""

    def __init__(self, next_page_token: bytes | None = None):
        """QueryNode initializer."""
        self.next_page_token = next_page_token

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build request using bytes cursor for validators paging."""
        pg_cursor = frag.PageCursor().fragment(schema)
        if self.next_page_token:
            active_vals = schema.ValidatorSet.activeValidators(
                after=self.next_page_token.decode()
            )
        else:
            active_vals = schema.ValidatorSet.activeValidators
        qres = schema.Query.epoch.select(
            schema.Epoch.validatorSet.select(
                active_vals.select(
                    schema.ValidatorConnection.pageInfo.select(pg_cursor).alias(
                        "cursor"
                    ),
                    schema.ValidatorConnection.nodes.select(
                        schema.Validator.contents.select(schema.MoveValue.bcs)
                    ),
                )
            )
        )
        return dsl_gql(pg_cursor, DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], "_rn.ValidatorsResult"]:
        """Decode one GQL page of BCS validator blobs to ValidatorsResult."""

        def _encode(in_data: dict) -> "_rn.ValidatorsResult":
            active_conn = ((in_data.get("epoch") or {}).get("validatorSet") or {}).get(
                "activeValidators"
            ) or {}
            cursor = active_conn.get("cursor") or {}
            nodes = active_conn.get("nodes") or []
            end_cursor = cursor.get("endCursor")
            has_next = cursor.get("hasNextPage", False)
            next_token = end_cursor.encode() if has_next and end_cursor else None
            result = []
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                bcs_b64 = (node.get("contents") or {}).get("bcs")
                if not bcs_b64:
                    continue
                bcs_bytes = base64.b64decode(bcs_b64)
                bcs_v = sui_system_bcs.Validator.deserialize(bcs_bytes)
                result.append(_bcs_validator_to_proto(bcs_v))
            return _rn.ValidatorsResult(validators=result, next_page_token=next_token)

        return _encode


class VerifySignatureSC(PGQL_QueryNode):
    """Verify a Sui signature against a message and author address.

    GQL ``verifySignature`` returns ``SignatureVerifyResult { success }``. Failure
    reasons come back in the top-level GraphQL ``errors`` array, captured via
    ``capture_errors=True`` on the SuiCommand wrapper and surfaced under ``errors``.

    Returns a :class:`~sui_prot.VerifySignatureResponse` for protocol parity with gRPC.
    """

    _VALID_INTENTS = frozenset({"TRANSACTION_DATA", "PERSONAL_MESSAGE"})

    def __init__(
        self,
        *,
        intent: str,
        message: str,
        signature: str,
        author: str,
    ) -> None:
        """Initialize VerifySignatureSC.

        :param intent: Must be 'TRANSACTION_DATA' or 'PERSONAL_MESSAGE'
        :param message: Base64-encoded message bytes
        :param signature: Base64-encoded Sui signature (scheme prefix byte included)
        :param author: Signer address (required by GQL schema)
        """
        if intent not in self._VALID_INTENTS:
            raise ValueError(
                f"VerifySignatureSC: intent must be one of "
                f"{sorted(self._VALID_INTENTS)}, got {intent!r}"
            )
        if not author:
            raise ValueError("VerifySignatureSC: author is required (GQL constraint)")
        if not message:
            raise ValueError(
                "VerifySignatureSC: message must be a non-empty base64 string"
            )
        if not signature:
            raise ValueError(
                "VerifySignatureSC: signature must be a non-empty base64 string"
            )
        try:
            base64.b64decode(message, validate=True)
        except Exception as exc:
            raise ValueError(
                f"VerifySignatureSC: message is not valid base64: {exc}"
            ) from exc
        try:
            base64.b64decode(signature, validate=True)
        except Exception as exc:
            raise ValueError(
                f"VerifySignatureSC: signature is not valid base64: {exc}"
            ) from exc
        self.intent = intent
        self.message = message
        self.signature = signature
        self.author = author

    def as_document_node(self, schema: DSLSchema) -> GraphQLRequest:
        """Build GQL verifySignature DSL request."""
        qres = schema.Query.verifySignature(
            message=self.message,
            signature=self.signature,
            intentScope=self.intent,
            author=self.author,
        ).select(schema.SignatureVerifyResult.success)
        return dsl_gql(DSLQuery(qres))

    @staticmethod
    def encode_fn() -> Callable[[dict], sui_prot.VerifySignatureResponse]:
        """Return encoder: maps GQL success + errors → VerifySignatureResponse."""

        def _encode(data: dict) -> sui_prot.VerifySignatureResponse:
            errors = data.get("errors") or []
            verify = data.get("verifySignature") or {}
            success = verify.get("success")
            reason: str | None = None
            if errors:
                first = errors[0]
                reason = first.get("message") if isinstance(first, dict) else str(first)
            return sui_prot.VerifySignatureResponse(
                is_valid=(success is True and not errors),
                reason=reason,
            )

        return _encode


def _owner_from_flat(f: dict) -> "sui_prot.Owner | None":
    kind = f.get("obj_owner_kind")
    if kind == "AddressOwner":
        return sui_prot.Owner(
            kind=sui_prot.OwnerOwnerKind.ADDRESS, address=f.get("address")
        )
    if kind == "Shared":
        return sui_prot.Owner(
            kind=sui_prot.OwnerOwnerKind.SHARED, version=f.get("initial_version")
        )
    if kind == "Immutable":
        return sui_prot.Owner(kind=sui_prot.OwnerOwnerKind.IMMUTABLE)
    if kind == "ObjectOwner":
        return sui_prot.Owner(
            kind=sui_prot.OwnerOwnerKind.OBJECT, address=f.get("address")
        )
    return None


def _encode_simulate_object_changes(
    eff: dict,
) -> "tuple[list[sui_prot.Object], dict[str, str]]":
    object_type_map: dict[str, str] = {}
    objects: list[sui_prot.Object] = []
    for node in (eff.get("object_changes") or {}).get("nodes") or []:
        addr = node.get("address")
        for state_key in ("input_state", "output_state"):
            obj_node = node.get(state_key)
            if isinstance(obj_node, dict) and addr and addr not in object_type_map:
                flat: dict = {}
                pgql_type._fast_flat(obj_node, flat)
                obj_type = flat.get("object_type") or (
                    "package" if obj_node.get("as_move_package") else None
                )
                if obj_type:
                    object_type_map[addr] = obj_type

        out = node.get("output_state")
        if out:
            flat_out: dict = {}
            pgql_type._fast_flat(out, flat_out)
            out_type = flat_out.get("object_type") or (
                "package" if out.get("as_move_package") else None
            )
            bcs_b64 = flat_out.get("bcs")
            contents_bcs_b64 = flat_out.get("contents_bcs")
            obj_json = ((out.get("as_move_content") or {}).get("as_object") or {}).get(
                "content"
            )
            obj_balance = (
                int(obj_json["balance"])
                if isinstance(obj_json, dict) and "balance" in obj_json
                else None
            )
            objects.append(
                sui_prot.Object(
                    object_id=flat_out.get("object_id"),
                    version=int(flat_out.get("version") or 0),
                    digest=flat_out.get("object_digest"),
                    object_type=out_type,
                    owner=_owner_from_flat(flat_out),
                    bcs=(
                        sui_prot.Bcs(name="Object", value=base64.b64decode(bcs_b64))
                        if bcs_b64
                        else None
                    ),
                    previous_transaction=flat_out.get("previous_transaction_digest"),
                    has_public_transfer=flat_out.get("has_public_transfer"),
                    storage_rebate=(
                        int(flat_out.get("storage_rebate"))
                        if flat_out.get("storage_rebate") is not None
                        else None
                    ),
                    json=(
                        _google_protobuf.Value.from_dict(obj_json)
                        if obj_json is not None
                        else None
                    ),
                    balance=obj_balance,
                    contents=(
                        sui_prot.Bcs(
                            name=out_type, value=base64.b64decode(contents_bcs_b64)
                        )
                        if contents_bcs_b64
                        else None
                    ),
                )
            )
    return objects, object_type_map


def _encode_simulate_events(nodes: list) -> "list[sui_prot.Event]":
    events: list[sui_prot.Event] = []
    for ev in nodes:
        ev_bcs_b64 = ev.get("eventBcs")
        sender_dict = ev.get("sender") or {}
        type_dict = (ev.get("contents") or {}).get("type") or {}
        tx_mod = ev.get("transactionModule") or {}
        pkg = tx_mod.get("package") or {}
        events.append(
            sui_prot.Event(
                package_id=pkg.get("package_id"),
                module=tx_mod.get("module_name"),
                sender=sender_dict.get("sender_address"),
                event_type=type_dict.get("event_type"),
                contents=(
                    sui_prot.Bcs(value=base64.b64decode(ev_bcs_b64))
                    if ev_bcs_b64
                    else None
                ),
            )
        )
    return events


def _decode_command_output_list(items: list) -> "list[sui_prot.CommandOutput]":
    result = []
    for item in items:
        val = item.get("value") or {}
        bcs_b64 = val.get("bcs")
        item_json = val.get("json")
        item_type = (val.get("type") or {}).get("value_type")
        result.append(
            sui_prot.CommandOutput(
                value=(
                    sui_prot.Bcs(name=item_type, value=base64.b64decode(bcs_b64))
                    if bcs_b64
                    else None
                ),
                json=(
                    _google_protobuf.Value.from_dict(item_json)
                    if item_json is not None
                    else None
                ),
            )
        )
    return result


def _encode_simulate_outputs(outputs: list) -> "list[sui_prot.CommandResult]":
    cmd_outputs: list[sui_prot.CommandResult] = []
    for cmd in outputs:
        cmd_outputs.append(
            sui_prot.CommandResult(
                return_values=_decode_command_output_list(
                    cmd.get("returnValues") or []
                ),
                mutated_by_ref=_decode_command_output_list(
                    cmd.get("mutatedReferences") or []
                ),
            )
        )
    return cmd_outputs


def _encode_execute_object_changes(
    eff_dict: dict, effects: "sui_prot.TransactionEffects"
) -> "sui_prot.ObjectSet | None":
    oc_nodes = (eff_dict.get("objectChanges") or {}).get("nodes") or []
    obj_list = []
    object_type_map: dict[str, str] = {}
    for oc in oc_nodes:
        addr = oc.get("address")
        for state_key in ("input_state", "output_state"):
            obj_node = oc.get(state_key)
            if isinstance(obj_node, dict):
                obj = _encode_object_from_raw(obj_node)
                if addr and not obj.object_id:
                    obj.object_id = addr
                obj_list.append(obj)
                if addr and addr not in object_type_map:
                    obj_type = (
                        (obj_node.get("as_move_content") or {})
                        .get("as_object", {})
                        .get("object_type_repr", {})
                        .get("object_type")
                    )
                    if obj_type:
                        object_type_map[addr] = obj_type
    objects = sui_prot.ObjectSet(objects=obj_list) if obj_list else None
    for co in effects.changed_objects:
        if not co.object_type and co.object_id in object_type_map:
            co.object_type = object_type_map[co.object_id]
    return objects


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


def _encode_auth_state_update_kind(
    kind_dict: dict,
) -> "sui_prot.AuthenticatorStateUpdate":
    jwks = []
    for node in (kind_dict.get("newActiveJwks") or {}).get("nodes") or []:
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
        protocol_version=(kind_dict.get("protocolConfigs") or {}).get(
            "protocolVersion"
        ),
        storage_charge=int(kind_dict.get("storageCharge") or 0),
        computation_charge=int(kind_dict.get("computationCharge") or 0),
        storage_rebate=int(kind_dict.get("storageRebate") or 0),
        non_refundable_storage_fee=int(kind_dict.get("nonRefundableStorageFee") or 0),
        epoch_start_timestamp=_parse_gql_datetime(kind_dict.get("epochStartTimestamp")),
    )


def _encode_end_of_epoch_kind(kind_dict: dict) -> "sui_prot.EndOfEpochTransaction":
    transactions = []
    for node in (kind_dict.get("transactions") or {}).get("nodes") or []:
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
    for node in (kind_dict.get("objects") or {}).get("nodes") or []:
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
        return sui_prot.TransactionKind(
            change_epoch=_encode_change_epoch_kind(kind_dict)
        )
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
        return sui_prot.TransactionKind(
            end_of_epoch=_encode_end_of_epoch_kind(kind_dict)
        )
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


_SIG_SCHEME_MAP = {
    0: sui_prot.SignatureScheme.ED25519,
    1: sui_prot.SignatureScheme.SECP256K1,
    2: sui_prot.SignatureScheme.SECP256R1,
    3: sui_prot.SignatureScheme.MULTISIG,
    4: sui_prot.SignatureScheme.BLS12381,
    5: sui_prot.SignatureScheme.ZKLOGIN,
    6: sui_prot.SignatureScheme.PASSKEY,
}


def _parse_simple_sig_bytes(raw: bytes) -> "sui_prot.SimpleSignature | None":
    """Parse raw [flag + sig + pubkey] bytes into a SimpleSignature proto."""
    if not raw:
        return None
    scheme = _SIG_SCHEME_MAP.get(raw[0])
    if scheme is None:
        return None
    return sui_prot.SimpleSignature(
        scheme=scheme,
        signature=raw[1:65],
        public_key=raw[65:],
    )


def _parse_user_signature(sig_b64: str) -> "sui_prot.UserSignature":
    """Parse a base64-encoded Sui signature into a fully-populated UserSignature proto.

    Decodes the BCS blob, dispatches on the flag byte via SuiSignature enum,
    and populates the appropriate proto variant. Falls back to BCS-only on any
    unrecognized or unparseable variant.
    """
    raw = base64.b64decode(sig_b64)
    sig_bcs = sui_prot.Bcs(name="UserSignatureBytes", value=raw)
    fallback = sui_prot.UserSignature(bcs=sig_bcs)
    try:
        parsed = SuiSignature.deserialize(raw)
    except Exception:
        return fallback

    flag = parsed.index
    payload = parsed.value
    scheme = _SIG_SCHEME_MAP.get(flag)

    # --- Simple schemes: Ed25519 (0), Secp256k1 (1), Secp256r1 (2), Bls12381 (4) ---
    if flag in (0, 1, 2, 4):
        return sui_prot.UserSignature(
            bcs=sig_bcs,
            scheme=scheme,
            simple=sui_prot.SimpleSignature(
                scheme=scheme,
                signature=bytes(payload.Signature),
                public_key=bytes(payload.PublicKey),
            ),
        )

    # --- MultiSig (3) ---
    if flag == 3:
        ms_sigs = []
        for cs in payload.Sigs:
            sig_raw = bytes(cs.Sig)
            cs_scheme = _SIG_SCHEME_MAP.get(sig_raw[0])
            if cs_scheme is not None:
                ms_sigs.append(
                    sui_prot.MultisigMemberSignature(
                        scheme=cs_scheme,
                        signature=sig_raw[1:],
                    )
                )
        members = []
        for pk in payload.PkMap:
            pk_scheme = _SIG_SCHEME_MAP.get(pk.index)
            if pk_scheme is not None:
                members.append(
                    sui_prot.MultisigMember(
                        public_key=sui_prot.MultisigMemberPublicKey(
                            scheme=pk_scheme,
                            public_key=bytes(pk.value.PublicKey),
                        ),
                        weight=pk.value.Weight,
                    )
                )
        return sui_prot.UserSignature(
            bcs=sig_bcs,
            scheme=scheme,
            multisig=sui_prot.MultisigAggregatedSignature(
                signatures=ms_sigs,
                bitmap=payload.BitMap.Bitmap,
                committee=sui_prot.MultisigCommittee(
                    members=members,
                    threshold=payload.Threshold,
                ),
            ),
        )

    # --- ZkLogin (5) ---
    if flag == 5:
        pp = payload.Inputs.ProofPoints
        b = pp.B
        proof = sui_prot.ZkLoginProof(
            a=(
                sui_prot.CircomG1(e0=pp.A[0], e1=pp.A[1], e2=pp.A[2])
                if len(pp.A) >= 3
                else None
            ),
            b=(
                sui_prot.CircomG2(
                    e00=b[0].Items[0],
                    e01=b[0].Items[1],
                    e10=b[1].Items[0],
                    e11=b[1].Items[1],
                    e20=b[2].Items[0],
                    e21=b[2].Items[1],
                )
                if len(b) >= 3
                else None
            ),
            c=(
                sui_prot.CircomG1(e0=pp.C[0], e1=pp.C[1], e2=pp.C[2])
                if len(pp.C) >= 3
                else None
            ),
        )
        try:
            iss_fragment = base64.urlsafe_b64decode(
                payload.Inputs.IssBase64Details.Value + "=="
            ).decode("utf-8", errors="replace")
            m = re.search(r'"iss"\s*:\s*"([^"]+)"', iss_fragment)
            iss = m.group(1) if m else None
        except Exception:
            iss = None
        return sui_prot.UserSignature(
            bcs=sig_bcs,
            scheme=scheme,
            zklogin=sui_prot.ZkLoginAuthenticator(
                inputs=sui_prot.ZkLoginInputs(
                    proof_points=proof,
                    iss_base64_details=sui_prot.ZkLoginClaim(
                        value=payload.Inputs.IssBase64Details.Value,
                        index_mod_4=payload.Inputs.IssBase64Details.IndexMod4,
                    ),
                    header_base64=payload.Inputs.HeaderBase64,
                    address_seed=payload.Inputs.AddressSeed,
                ),
                max_epoch=payload.MaxEpoch,
                signature=_parse_simple_sig_bytes(bytes(payload.UserSignature)),
                public_identifier=sui_prot.ZkLoginPublicIdentifier(iss=iss),
            ),
        )

    # --- Passkey (6) ---
    if flag == 6:
        return sui_prot.UserSignature(
            bcs=sig_bcs,
            scheme=scheme,
            passkey=sui_prot.PasskeyAuthenticator(
                authenticator_data=bytes(payload.AuthenticatorData),
                client_data_json=payload.ClientDataJson,
                signature=_parse_simple_sig_bytes(bytes(payload.UserSignature)),
            ),
        )

    return fallback


def _encode_executed_tx(
    tx_dict: "dict | None",
) -> "sui_prot.ExecutedTransaction | None":
    """Map a GQL transaction response dict to an ExecutedTransaction proto.

    GQL → gRPC mapping strategy (confirmed against Mysten Labs TS SDK, 2026-05-05):

    JSON blob fields (primary data source for typed proto fields):
      transactionJson      → Transaction proto (excl. bcs/signatures)
      effectsJson          → TransactionEffects proto (excl. bcs)
      balanceChangesJson   → list[BalanceChange] proto
    These blobs match the gRPC proto JSON format. betterproto2 from_dict() handles
    camelCase → snake_case automatically and resolves string enum values via
    field_type.from_string(). Typed GQL fields for enum states (inputState,
    outputState, idOperation, accumulatorWrite) and effects.version do NOT exist
    as GQL typed fields — confirmed by Mysten Labs; JSON blobs are the only source.

    BCS fields (excluded from all JSON blobs, set separately):
      transactionBcs       → transaction.bcs  (Bcs.name = "TransactionData")
      effectsBcs           → effects.bcs      (Bcs.name = "TransactionEffects")
      UserSignature.bcs    → set in _parse_user_signature (Bcs.name = "UserSignatureBytes")
      Object.bcs           → set in _encode_object_from_raw (Bcs.name = "Object")
    GQL Bcs scalar has no name field; name is deterministic from the field that
    provides the bytes and must be hardcoded here.

    Signatures: sourced from effects.transaction.signatures (GQL nesting under effects),
    not from a top-level signatures field. signatureBytes is Base64; full parsing
    (scheme, simple/multisig/zklogin variants) is done in _parse_user_signature.

    checkpoint / timestamp: not in any JSON blob; sourced from StandardTxEffects
    typed fields (checkpoint.sequenceNumber, timestamp).

    objects (ObjectSet): GQL name is objectChanges (ObjectChangeConnection), not
    objects. Each ObjectChange node has inputState: Object and outputState: Object —
    both versions of every mutated object. gRPC ObjectSet flattens these as
    separate Object entries (input version + output version per changed object,
    plus output-only for created objects). Mapped via _encode_object_from_raw()
    which handles the StandardObject DSL alias → proto field translation.

    Protocol gaps (no GQL equivalent — will always be empty):
      TransactionEffects.events_digest, .auxiliary_data_digest,
      .unchanged_loaded_runtime_objects, .version; Transaction.version.
    """
    if not tx_dict:
        return None

    # transactionJson matches proto format; digest is the authoritative identity key
    tx_json = tx_dict.get("transactionJson") or {}
    digest = tx_json.get("digest")
    if not digest:
        return None

    # from_dict() populates all Transaction fields except bcs and signatures
    transaction = sui_prot.Transaction.from_dict(tx_json, ignore_unknown_fields=True)
    tx_bcs_b64 = tx_dict.get("transactionBcs")
    if tx_bcs_b64:
        transaction.bcs = sui_prot.Bcs(
            name="TransactionData", value=base64.b64decode(tx_bcs_b64)
        )

    # signatures are under effects.transaction.signatures in GQL (not top-level)
    sigs = [
        _parse_user_signature(s["signatureBytes"])
        for s in (tx_dict.get("signatures") or [])
        if s.get("signatureBytes")
    ]

    eff_dict = tx_dict.get("effects") or {}

    # effectsJson matches proto format; from_dict() populates all TransactionEffects fields except bcs
    effects_json = eff_dict.get("effectsJson") or {}
    for _co in effects_json.get("changedObjects") or []:
        _aw = _co.get("accumulatorWrite")
        if _aw and "integerValue" in _aw:
            _aw["value"] = int(_aw["integerValue"])
    effects = sui_prot.TransactionEffects.from_dict(
        effects_json, ignore_unknown_fields=True
    )
    effects_bcs_b64 = eff_dict.get("effectsBcs")
    if effects_bcs_b64:
        effects.bcs = sui_prot.Bcs(
            name="TransactionEffects", value=base64.b64decode(effects_bcs_b64)
        )

    # balanceChangesJson is on TransactionEffects (not Transaction) in GQL schema
    balance_changes = [
        sui_prot.BalanceChange.from_dict(bc, ignore_unknown_fields=True)
        for bc in (eff_dict.get("balanceChangesJson") or [])
        if isinstance(bc, dict)
    ]

    # checkpoint and timestamp are typed fields from StandardTxEffects fragment — not in JSON blobs
    checkpoint_dict = eff_dict.get("checkpoint") or {}
    checkpoint_seq = checkpoint_dict.get("sequenceNumber")
    ts_str = eff_dict.get("timestamp") or checkpoint_dict.get("timestamp")
    timestamp = _parse_gql_datetime(ts_str)

    # GQL objectChanges → gRPC ExecutedTransaction.objects (ObjectSet)
    # Each ObjectChange node yields up to two Object entries: inputState (pre-tx version)
    # and outputState (post-tx version). Created objects have inputState=None;
    # deleted objects have outputState=None. _encode_object_from_raw handles the
    # StandardObject DSL alias mapping (from_dict() cannot be used due to snake_case aliases).
    # object_type_map: objectId → objectType; used to patch effects.changedObjects because
    # effectsJson omits objectType (confirmed GQL indexer behaviour, 2026-05-06).
    objects = _encode_execute_object_changes(eff_dict, effects)

    return sui_prot.ExecutedTransaction(
        digest=digest,
        transaction=transaction,
        signatures=sigs,
        effects=effects,
        balance_changes=balance_changes,
        checkpoint=checkpoint_seq,
        timestamp=timestamp,
        objects=objects,
    )
