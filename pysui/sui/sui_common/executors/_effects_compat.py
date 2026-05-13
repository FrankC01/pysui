#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Compatibility shim: effects conversion functions for parallel executors.

These functions are preserved here to avoid touching parallel executors in
Plan #41. They will be eliminated when parallel executors are UCI-aligned.
"""

import pysui.sui.sui_bcs.bcs_txne as bcst
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_common.types import (
    TransactionEffects, ExecutionStatus, GasCostSummary, Owner, ChangedObject
)


def _gql_effects_to_common(effects: bcst.TransactionEffects) -> TransactionEffects:
    """Convert GQL BCS TransactionEffects to the protocol-agnostic common type.

    :param effects: BCS-deserialized transaction effects from GraphQL
    :type effects: bcst.TransactionEffects
    :return: Protocol-agnostic TransactionEffects
    :rtype: TransactionEffects
    :raises ValueError: If effects version is not V2
    """
    if effects.enum_name != "V2":
        raise ValueError(f"Expect V2 effects, found {effects.enum_name}")
    v2 = effects.value

    changed_objects = []
    for addr, change in v2.changedObjects:
        obj_id = addr.to_address_str()
        out = change.outputState
        if out.enum_name == "NotExist":
            changed_objects.append(ChangedObject(object_id=obj_id, output_state="DoesNotExist"))
        elif out.enum_name in ("ObjectWrite", "PackageWrite"):
            digest, owner = out.value
            owner_kind = owner.enum_name
            output_owner = Owner(
                kind=owner_kind,
                address=owner.value.to_address_str() if owner_kind == "AddressOwner" else None,
                initial_shared_version=owner.value if owner_kind == "SharedInitialVersion" else None,
            )
            changed_objects.append(ChangedObject(
                object_id=obj_id,
                output_state=out.enum_name,
                output_digest=digest.to_digest_str(),
                output_owner=output_owner,
            ))

    gas_used = GasCostSummary(
        computation_cost=v2.gasUsed.computationCost,
        storage_cost=v2.gasUsed.storageCost,
        storage_rebate=v2.gasUsed.storageRebate,
        non_refundable_storage_fee=getattr(v2.gasUsed, 'nonRefundableStorageFee', 0),
    )

    gas_object = None
    try:
        gas_idx = v2.gasObjectIndex.value
        if gas_idx < len(v2.changedObjects):
            gas_addr, gas_change = v2.changedObjects[gas_idx]
            if gas_change.outputState.enum_name == "ObjectWrite":
                gas_digest, gas_owner = gas_change.outputState.value
                gas_object = ChangedObject(
                    object_id=gas_addr.to_address_str(),
                    output_state="ObjectWrite",
                    output_digest=gas_digest.to_digest_str(),
                    output_owner=Owner(
                        kind=gas_owner.enum_name,
                        address=gas_owner.value.to_address_str() if gas_owner.enum_name == "AddressOwner" else None,
                    ),
                )
    except Exception:
        pass

    return TransactionEffects(
        transaction_digest=v2.transactionDigest.to_digest_str(),
        status=ExecutionStatus(success=True),
        gas_used=gas_used,
        lamport_version=v2.lamportVersion,
        changed_objects=changed_objects,
        gas_object=gas_object,
    )


_OUTPUT_STATE_MAP = {
    sui_prot.ChangedObjectOutputObjectState.DOES_NOT_EXIST: "DoesNotExist",
    sui_prot.ChangedObjectOutputObjectState.OBJECT_WRITE: "ObjectWrite",
    sui_prot.ChangedObjectOutputObjectState.PACKAGE_WRITE: "PackageWrite",
}

_OWNER_KIND_MAP = {
    sui_prot.OwnerOwnerKind.ADDRESS: "AddressOwner",
    sui_prot.OwnerOwnerKind.OBJECT: "ObjectOwner",
    sui_prot.OwnerOwnerKind.SHARED: "SharedInitialVersion",
    sui_prot.OwnerOwnerKind.IMMUTABLE: "Immutable",
}


def _grpc_effects_to_common(grpc_effects: sui_prot.TransactionEffects) -> TransactionEffects:
    """Convert gRPC TransactionEffects to the protocol-agnostic common type.

    :param grpc_effects: gRPC TransactionEffects protobuf message
    :type grpc_effects: sui_prot.TransactionEffects
    :return: Protocol-agnostic TransactionEffects
    :rtype: TransactionEffects
    :raises ValueError: If required fields are missing
    """
    if grpc_effects is None:
        raise ValueError("TransactionEffects is None")

    gas_used_proto = grpc_effects.gas_used
    gas_used = GasCostSummary(
        computation_cost=gas_used_proto.computation_cost or 0,
        storage_cost=gas_used_proto.storage_cost or 0,
        storage_rebate=gas_used_proto.storage_rebate or 0,
        non_refundable_storage_fee=getattr(gas_used_proto, "non_refundable_storage_fee", None) or 0,
    ) if gas_used_proto else GasCostSummary(
        computation_cost=0, storage_cost=0, storage_rebate=0
    )

    changed_objects = []
    for co in grpc_effects.changed_objects:
        output_state_enum = co.output_state
        output_state_str = _OUTPUT_STATE_MAP.get(output_state_enum)
        if output_state_str is None:
            continue

        output_owner = None
        if co.output_owner is not None:
            kind_str = _OWNER_KIND_MAP.get(co.output_owner.kind, "Unknown")
            output_owner = Owner(
                kind=kind_str,
                address=co.output_owner.address if co.output_owner.kind in (
                    sui_prot.OwnerOwnerKind.ADDRESS, sui_prot.OwnerOwnerKind.OBJECT
                ) else None,
                initial_shared_version=co.output_owner.version if co.output_owner.kind == (
                    sui_prot.OwnerOwnerKind.SHARED
                ) else None,
            )

        changed_objects.append(ChangedObject(
            object_id=co.object_id or "",
            output_state=output_state_str,
            output_digest=co.output_digest,
            output_owner=output_owner,
        ))

    gas_object = None
    go = grpc_effects.gas_object
    if go is not None:
        go_output_state = _OUTPUT_STATE_MAP.get(go.output_state)
        if go_output_state:
            go_owner = None
            if go.output_owner is not None:
                kind_str = _OWNER_KIND_MAP.get(go.output_owner.kind, "Unknown")
                go_owner = Owner(
                    kind=kind_str,
                    address=go.output_owner.address if go.output_owner.kind in (
                        sui_prot.OwnerOwnerKind.ADDRESS, sui_prot.OwnerOwnerKind.OBJECT
                    ) else None,
                )
            gas_object = ChangedObject(
                object_id=go.object_id or "",
                output_state=go_output_state,
                output_digest=go.output_digest,
                output_owner=go_owner,
            )

    status_proto = grpc_effects.status
    success = bool(status_proto and status_proto.success)

    return TransactionEffects(
        transaction_digest=grpc_effects.transaction_digest or "",
        status=ExecutionStatus(success=success),
        gas_used=gas_used,
        lamport_version=grpc_effects.lamport_version or 0,
        changed_objects=changed_objects,
        gas_object=gas_object,
    )
