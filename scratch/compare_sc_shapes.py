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
        # presence-only fields
        "bcs_set": bool(obj.bcs),
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


def _extract_list(result_data) -> list[sui_prot.Object]:
    """Extract list of Objects from ListOwnedObjectsResponse or BatchGetObjectsResponse."""
    raw: list
    if hasattr(result_data, "objects"):
        raw = list(result_data.objects or [])
    elif isinstance(result_data, list):
        raw = result_data
    else:
        return []
    return [o for item in raw if (o := _unwrap_obj(item)) is not None]


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

    gql_by_id = {o.object_id: o for o in _extract_list(gql_res.result_data)}
    grpc_by_id = {o.object_id: o for o in _extract_list(grpc_res.result_data)}

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

    gql_by_id = {o.object_id: o for o in _extract_list(gql_res.result_data)}
    grpc_by_id = {o.object_id: o for o in _extract_list(grpc_res.result_data)}

    common = set(gql_by_id) & set(grpc_by_id)
    all_diffs: list[str] = []
    for oid in sorted(common):
        diffs = _compare_objects(gql_by_id[oid], grpc_by_id[oid])
        if diffs:
            all_diffs.append(f"  object {oid}:")
            all_diffs.extend(diffs)

    _report(name, all_diffs, len(common))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(profile: str) -> None:
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
        cmd.GetPastObject(object_id=first_id, version=past_version) if past_version else None,
        skip_reason=past_skip,
    )

    # 7. GetMultipleObjects
    await _compare_batch("GetMultipleObjects", gql_client, grpc_client,
                         cmd.GetMultipleObjects(object_ids=coin_ids))

    # 8. GetMultiplePastObjects
    await _compare_batch(
        f"GetMultiplePastObjects(v{past_version})",
        gql_client, grpc_client,
        cmd.GetMultiplePastObjects(
            for_versions=[{"objectId": first_id, "version": past_version}]
        ) if past_version else None,
        skip_reason=past_skip,
    )

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare SuiCommand shape parity across GQL and gRPC")
    parser.add_argument("--profile", default="devnet", help="Sui profile name (default: devnet)")
    args = parser.parse_args()
    asyncio.run(main(args.profile))
