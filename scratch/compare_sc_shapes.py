#!/usr/bin/env python3
#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Validate UCI shape parity for full-Object SuiCommands.

Runs each full-shape SuiCommand on both GQL and gRPC, compares
sui_prot.Object fields side-by-side. Reports MATCH or lists field diffs.

Usage:
    python scratch/compare_sc_shapes.py
    python scratch/compare_sc_shapes.py --profile mainnet
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from pysui import PysuiConfiguration, client_factory, AsyncClientBase
import pysui.sui.sui_common.sui_commands as cmd
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
from pysui.sui.sui_common.shared_types import ObjectSummary, ObjectSummaryList

SUI_COIN_TYPE = (
    "0x0000000000000000000000000000000000000000000000000000000000000002"
    "::coin::Coin<"
    "0x0000000000000000000000000000000000000000000000000000000000000002"
    "::sui::SUI>"
)

# Fields compared on every sui_prot.Object
SCALAR_FIELDS = [
    "object_id",
    "version",
    "digest",
    "object_type",
    "balance",
    "has_public_transfer",
    "previous_transaction",
    "storage_rebate",
]


def obj_summary(obj: sui_prot.Object) -> dict:
    """Normalize an Object proto to a flat comparable dict."""
    return {
        "object_id": obj.object_id,
        "version": obj.version,
        "digest": obj.digest,
        "object_type": obj.object_type,
        "balance": obj.balance,
        "has_public_transfer": obj.has_public_transfer,
        "previous_transaction": obj.previous_transaction,
        "storage_rebate": obj.storage_rebate,
        # bcs and contents — full name+value comparison
        "bcs_name": obj.bcs.name if obj.bcs else None,
        "bcs_value": obj.bcs.value if obj.bcs else None,
        "contents_name": obj.contents.name if obj.contents else None,
        "contents_value": obj.contents.value if obj.contents else None,
        # presence-only fields
        "json_set": obj.json is not None,
        "display_set": bool(obj.display),
        "owner_kind": str(obj.owner.kind) if obj.owner else None,
        "owner_address": obj.owner.address if obj.owner else None,
    }


def _extract_single(result_data) -> Optional[sui_prot.Object]:
    """Extract a single Object from GQL (Object) or gRPC (GetObjectResponse)."""
    if isinstance(result_data, sui_prot.Object):
        return result_data
    if hasattr(result_data, "object"):
        return result_data.object
    return None


def _unwrap_obj(item) -> Optional[sui_prot.Object]:
    """Return sui_prot.Object from either Object or GetObjectResult wrapper."""
    if isinstance(item, sui_prot.Object):
        return item
    if hasattr(item, "object") and isinstance(item.object, sui_prot.Object):
        return item.object
    return None


def _extract_list(result_data) -> tuple[list[sui_prot.Object], list[str]]:
    """Extract Objects and error messages from ListOwnedObjectsResponse or BatchGetObjectsResponse."""
    raw: list
    if hasattr(result_data, "objects"):
        raw = list(result_data.objects or [])
    elif isinstance(result_data, list):
        raw = result_data
    else:
        return [], []
    objects = []
    errors = []
    for item in raw:
        obj = _unwrap_obj(item)
        if obj is not None:
            objects.append(obj)
        elif hasattr(item, "error") and item.error:
            errors.append(f"code={item.error.code} message={item.error.message!r}")
    return objects, errors


def _compare_objects(gql_obj: sui_prot.Object, grpc_obj: sui_prot.Object) -> list[str]:
    """Return list of diff lines; empty if all fields match."""
    gd = obj_summary(gql_obj)
    grd = obj_summary(grpc_obj)
    diffs = []
    for k in gd:
        gv, grv = gd[k], grd[k]
        if gv != grv:
            diffs.append(f"    {k}: gql={gv!r}  grpc={grv!r}")
    return diffs


def _report(name: str, all_diffs: list[str], compared: int, skipped: str = "") -> None:
    if skipped:
        print(f"\n{name}: SKIPPED — {skipped}")
        return
    status = "MATCH ✓" if not all_diffs else f"DIFF ({len(all_diffs)} line(s))"
    print(f"\n{name}: {status}  [{compared} object(s) compared]")
    for line in all_diffs:
        print(line)


# ---------------------------------------------------------------------------
# Command runners
# ---------------------------------------------------------------------------

async def _compare_list(
    name: str,
    gql_client: AsyncClientBase,
    grpc_client: AsyncClientBase,
    sc_cmd,
) -> None:
    """Run a pageable command on both protocols, match by object_id, compare."""
    gql_res = await gql_client.execute_for_all(command=sc_cmd)
    grpc_res = await grpc_client.execute_for_all(command=sc_cmd)

    if not gql_res.is_ok():
        print(f"\n{name}: GQL FAILED — {gql_res.result_string}")
        return
    if not grpc_res.is_ok():
        print(f"\n{name}: gRPC FAILED — {grpc_res.result_string}")
        return

    gql_objs, gql_errors = _extract_list(gql_res.result_data)
    grpc_objs, grpc_errors = _extract_list(grpc_res.result_data)
    gql_by_id = {o.object_id: o for o in gql_objs}
    grpc_by_id = {o.object_id: o for o in grpc_objs}

    common = set(gql_by_id) & set(grpc_by_id)
    gql_only = set(gql_by_id) - set(grpc_by_id)
    grpc_only = set(grpc_by_id) - set(gql_by_id)

    all_diffs: list[str] = []
    for oid in sorted(common):
        diffs = _compare_objects(gql_by_id[oid], grpc_by_id[oid])
        if diffs:
            all_diffs.append(f"  object {oid}:")
            all_diffs.extend(diffs)

    _report(name, all_diffs, len(common))
    if gql_only:
        print(f"  GQL-only ({len(gql_only)}): {sorted(gql_only)[:3]}")
    if grpc_only:
        print(f"  gRPC-only ({len(grpc_only)}): {sorted(grpc_only)[:3]}")
    for e in gql_errors:
        print(f"  GQL error: {e}")
    for e in grpc_errors:
        print(f"  gRPC error: {e}")


async def _compare_single(
    name: str,
    gql_client: AsyncClientBase,
    grpc_client: AsyncClientBase,
    sc_cmd,
    skip_reason: str = "",
) -> None:
    """Run a single-object command on both protocols and compare."""
    if skip_reason:
        _report(name, [], 0, skipped=skip_reason)
        return

    gql_res = await gql_client.execute(command=sc_cmd)
    grpc_res = await grpc_client.execute(command=sc_cmd)

    if not gql_res.is_ok():
        not_found = "NOT_FOUND" in str(gql_res.result_string) or "not found" in str(gql_res.result_string).lower()
        label = "SKIPPED (version pruned by node)" if not_found else f"GQL FAILED — {gql_res.result_string}"
        print(f"\n{name}: {label}")
        return
    if not grpc_res.is_ok():
        not_found = "NOT_FOUND" in str(grpc_res.result_string) or "not found" in str(grpc_res.result_string).lower()
        label = "SKIPPED (version pruned by node)" if not_found else f"gRPC FAILED — {grpc_res.result_string}"
        print(f"\n{name}: {label}")
        return

    gql_obj = _extract_single(gql_res.result_data)
    grpc_obj = _extract_single(grpc_res.result_data)

    if gql_obj is None or grpc_obj is None:
        print(f"\n{name}: could not extract Object from result_data")
        print(f"  GQL type: {type(gql_res.result_data)}")
        print(f"  gRPC type: {type(grpc_res.result_data)}")
        return

    _report(name, _compare_objects(gql_obj, grpc_obj), 1)


async def _compare_batch(
    name: str,
    gql_client: AsyncClientBase,
    grpc_client: AsyncClientBase,
    sc_cmd,
    skip_reason: str = "",
) -> None:
    """Run a batch-object command on both protocols, match by object_id, compare."""
    if skip_reason:
        _report(name, [], 0, skipped=skip_reason)
        return

    gql_res = await gql_client.execute(command=sc_cmd)
    grpc_res = await grpc_client.execute(command=sc_cmd)

    if not gql_res.is_ok():
        print(f"\n{name}: GQL FAILED — {gql_res.result_string}")
        return
    if not grpc_res.is_ok():
        print(f"\n{name}: gRPC FAILED — {grpc_res.result_string}")
        return

    gql_objs, gql_errors = _extract_list(gql_res.result_data)
    grpc_objs, grpc_errors = _extract_list(grpc_res.result_data)
    gql_by_id = {(o.object_id, o.version): o for o in gql_objs}
    grpc_by_id = {(o.object_id, o.version): o for o in grpc_objs}

    common = set(gql_by_id) & set(grpc_by_id)
    all_diffs: list[str] = []
    for key in sorted(common):
        diffs = _compare_objects(gql_by_id[key], grpc_by_id[key])
        if diffs:
            all_diffs.append(f"  object {key[0]} v{key[1]}:")
            all_diffs.extend(diffs)

    _report(name, all_diffs, len(common))
    for e in gql_errors:
        print(f"  GQL error: {e}")
    for e in grpc_errors:
        print(f"  gRPC error: {e}")


async def _compare_summary_batch(
    name: str,
    gql_client: AsyncClientBase,
    grpc_client: AsyncClientBase,
    sc_cmd,
) -> None:
    """Run a GetMultipleObjectSummary command on both protocols, match by objectId, compare."""
    gql_res = await gql_client.execute(command=sc_cmd)
    grpc_res = await grpc_client.execute(command=sc_cmd)

    if not gql_res.is_ok():
        print(f"\n{name}: GQL FAILED — {gql_res.result_string}")
        return
    if not grpc_res.is_ok():
        print(f"\n{name}: gRPC FAILED — {grpc_res.result_string}")
        return

    gql_items: ObjectSummaryList = gql_res.result_data
    grpc_items: ObjectSummaryList = grpc_res.result_data
    gql_by_id = {s.objectId: s for s in (gql_items.objects if gql_items else [])}
    grpc_by_id = {s.objectId: s for s in (grpc_items.objects if grpc_items else [])}

    common = set(gql_by_id) & set(grpc_by_id)
    all_diffs: list[str] = []
    for oid in sorted(common):
        gs, grs = gql_by_id[oid], grpc_by_id[oid]
        for field in ("objectId", "version", "digest", "owner", "initialSharedVersion"):
            gv, grv = getattr(gs, field), getattr(grs, field)
            if gv != grv:
                all_diffs.append(f"  object {oid}:")
                all_diffs.append(f"    {field}: gql={gv!r}  grpc={grv!r}")

    _report(name, all_diffs, len(common))
    gql_only = set(gql_by_id) - set(grpc_by_id)
    grpc_only = set(grpc_by_id) - set(gql_by_id)
    if gql_only:
        print(f"  GQL-only ({len(gql_only)}): {sorted(gql_only)[:3]}")
    if grpc_only:
        print(f"  gRPC-only ({len(grpc_only)}): {sorted(grpc_only)[:3]}")


# ---------------------------------------------------------------------------
# Epoch compare helpers
# ---------------------------------------------------------------------------


def epoch_summary(ep: "sui_prot.Epoch") -> dict:
    """Normalize Epoch proto to a flat comparable dict (committee excluded — known GQL gap)."""
    pc = ep.protocol_config
    ss = ep.system_state
    return {
        "epoch": ep.epoch,
        "reference_gas_price": ep.reference_gas_price,
        "start": ep.start,
        "end": ep.end,
        "first_checkpoint": ep.first_checkpoint,
        "last_checkpoint": ep.last_checkpoint,
        "protocol_version": pc.protocol_version if pc else None,
        "system_state_present": ss is not None,
        "system_state_epoch": ss.epoch if ss else None,
        "system_state_safe_mode": ss.safe_mode if ss else None,
    }


def _extract_epoch(result_data) -> "Optional[sui_prot.Epoch]":
    """Extract Epoch from GetEpochResponse or bare Epoch proto."""
    if isinstance(result_data, sui_prot.Epoch):
        return result_data
    if isinstance(result_data, sui_prot.GetEpochResponse):
        return result_data.epoch
    if hasattr(result_data, "epoch") and isinstance(
        getattr(result_data, "epoch"), sui_prot.Epoch
    ):
        return result_data.epoch
    return None


async def _compare_epoch(
    name: str,
    gql_client: "AsyncClientBase",
    grpc_client: "AsyncClientBase",
    epoch_id: Optional[int] = None,
) -> None:
    """Run GetEpoch on both protocols and compare Epoch scalar + system_state fields."""
    sc_cmd = cmd.GetEpoch(epoch_id=epoch_id)
    gql_res = await gql_client.execute(command=sc_cmd)
    grpc_res = await grpc_client.execute(command=sc_cmd)

    if not gql_res.is_ok():
        print(f"\n{name}: GQL FAILED — {gql_res.result_string}")
        return
    if not grpc_res.is_ok():
        print(f"\n{name}: gRPC FAILED — {grpc_res.result_string}")
        return

    gql_ep = _extract_epoch(gql_res.result_data)
    grpc_ep = _extract_epoch(grpc_res.result_data)

    if gql_ep is None or grpc_ep is None:
        print(
            f"\n{name}: could not extract Epoch — "
            f"gql={type(gql_res.result_data).__name__}  "
            f"grpc={type(grpc_res.result_data).__name__}"
        )
        return

    gd = epoch_summary(gql_ep)
    grd = epoch_summary(grpc_ep)
    diffs = []
    for k in gd:
        gv, grv = gd[k], grd[k]
        if gv != grv:
            diffs.append(f"    {k}: gql={gv!r}  grpc={grv!r}")

    _report(name, diffs, 1)
    print("  note: committee not compared — GQL returns empty ValidatorCommittee (known gap)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(profile: str, past_object_id: Optional[str] = None, past_version_arg: Optional[int] = None, past_version_extra: Optional[int] = None) -> None:
    gql_cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        profile_name=profile,
    )
    grpc_cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        profile_name=profile,
    )

    gql_client = client_factory(gql_cfg)
    grpc_client = client_factory(grpc_cfg)

    owner = gql_cfg.active_address
    print(f"Profile : {profile}")
    print(f"Owner   : {owner}")

    # Seed: fetch coins via gRPC (known-good path) to get object IDs and versions
    seed_res = await grpc_client.execute_for_all(command=cmd.GetGas(owner=owner))
    if not seed_res.is_ok():
        print(f"Seed GetGas failed: {seed_res.result_string}")
        return

    coin_objs: list[sui_prot.Object] = list(seed_res.result_data.objects)
    if not coin_objs:
        print("No gas coins found — cannot run object-specific tests")
        return

    coin_ids = [o.object_id for o in coin_objs[:5]]
    first = coin_objs[0]
    first_id = first.object_id
    first_version = first.version
    print(f"Seed    : {len(coin_objs)} coin(s)  first_id={first_id}  version={first_version}")

    # Past version for GetPastObject / GetMultiplePastObjects
    # CLI args override the seed-derived values when supplied
    if past_object_id and past_version_arg is not None:
        past_id = past_object_id
        past_version = past_version_arg
        past_skip = ""
        print(f"Past    : object_id={past_id}  version={past_version}  (from CLI)")
    else:
        past_id = first_id
        past_version = first_version - 1 if first_version and first_version > 1 else None
        past_skip = "" if past_version else f"coin version={first_version} — no prior version available"

    print("\n" + "=" * 70)

    # 1. GetGas
    await _compare_list("GetGas", gql_client, grpc_client,
                        cmd.GetGas(owner=owner))

    # 2. GetCoins (SUI)
    await _compare_list("GetCoins(SUI)", gql_client, grpc_client,
                        cmd.GetCoins(owner=owner, coin_type=SUI_COIN_TYPE))

    # 3. GetObjectsOwnedByAddress
    await _compare_list("GetObjectsOwnedByAddress", gql_client, grpc_client,
                        cmd.GetObjectsOwnedByAddress(owner=owner))

    # 4. GetObjectsForType (SUI coins)
    await _compare_list("GetObjectsForType(SUI coin)", gql_client, grpc_client,
                        cmd.GetObjectsForType(owner=owner, object_type=SUI_COIN_TYPE))

    # 5. GetObject
    await _compare_single("GetObject", gql_client, grpc_client,
                          cmd.GetObject(object_id=first_id))

    # 6. GetPastObject
    await _compare_single(
        f"GetPastObject(v{past_version})",
        gql_client, grpc_client,
        cmd.GetPastObject(object_id=past_id, version=past_version) if past_version else None,
        skip_reason=past_skip,
    )

    # 7. GetMultipleObjects
    await _compare_batch("GetMultipleObjects", gql_client, grpc_client,
                         cmd.GetMultipleObjects(object_ids=coin_ids))

    # 8. GetMultipleObjectSummary
    await _compare_summary_batch("GetMultipleObjectSummary", gql_client, grpc_client,
                                 cmd.GetMultipleObjectSummary(object_ids=coin_ids))

    # 9. GetMultiplePastObjects
    if past_version:
        batch_versions = [{"objectId": past_id, "version": past_version}]
        if past_version_extra is not None:
            batch_versions.append({"objectId": past_id, "version": past_version_extra})
        batch_label = f"GetMultiplePastObjects(v{past_version}" + (f",v{past_version_extra})" if past_version_extra else ")")
    else:
        batch_versions = None
        batch_label = f"GetMultiplePastObjects(v{past_version})"
    await _compare_batch(
        batch_label,
        gql_client, grpc_client,
        cmd.GetMultiplePastObjects(for_versions=batch_versions) if batch_versions else None,
        skip_reason=past_skip,
    )

    # 10. GetEpoch (current epoch)
    await _compare_epoch("GetEpoch(current)", gql_client, grpc_client)

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare SuiCommand shape parity across GQL and gRPC")
    parser.add_argument("--profile", default="devnet", help="Sui profile name (default: devnet)")
    parser.add_argument("--past-object-id", default=None, help="Object ID for GetPastObject tests")
    parser.add_argument("--past-version", type=int, default=None, help="Version for GetPastObject tests")
    parser.add_argument("--past-version-extra", type=int, default=None, help="Second version for GetMultiplePastObjects batch test")
    args = parser.parse_args()
    asyncio.run(main(args.profile, args.past_object_id, args.past_version, args.past_version_extra))
