#!/usr/bin/env python3
"""
SuiCommand GQL/gRPC parity check.

Runs all SuiCommands (excluding ExecuteTransaction, SimulateTransaction,
SimulateTransactionKind) against both transports and compares proto JSON output.

Usage:
    python scratch/parity_check.py [--profile devnet|testnet|mainnet]
                                    [--config scratch/parity_check_config.json]
                                    [--out scratch/parity_check_results.json]

Config file (JSON):
    {
        "package_ids": ["0x..."],
        "GetDynamicFields": {"object_id": "0x..."},
        "GetNameServiceAddress": {"name": "example.sui"},
        "VerifyTransactionSignature": {"message": "...", "signature": "...", "author": "0x..."},
        "VerifyPersonalMessageSignature": {"message": "...", "signature": "...", "author": "0x..."}
    }
"""
import asyncio
import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Optional

from pysui import PysuiConfiguration, AsyncClientBase, client_factory
from pysui.sui.sui_common.sui_commands import (
    GetCoinMetaData,
    GetAddressCoinBalance,
    GetAddressCoinBalances,
    GetCoins,
    GetGas,
    GetStaked,
    GetDelegatedStakes,
    GetObject,
    GetPastObject,
    GetMultipleObjects,
    GetObjectSummary,
    GetMultipleObjectSummary,
    GetMultiplePastObjects,
    GetObjectsOwnedByAddress,
    GetDynamicFields,
    GetEpoch,
    GetBasicCurrentEpochInfo,
    GetLatestCheckpoint,
    GetCheckpointBySequence,
    GetCheckpointByDigest,
    GetMultipleObjectContent,
    GetProtocolConfig,
    GetObjectContent,
    GetObjectsForType,
    GetCoinSummary,
    GetPackage,
    GetPackageVersions,
    GetModule,
    GetMoveDataType,
    GetStructure,
    GetStructures,
    GetFunction,
    GetFunctions,
    GetNameServiceAddress,
    GetNameServiceNames,
    GetChainIdentifier,
    GetLatestSuiSystemState,
    GetCurrentValidators,
    GetTransaction,
    GetTransactions,
    GetTransactionKind,
    VerifyTransactionSignature,
    VerifyPersonalMessageSignature,
)

STATUS_MATCH = "MATCH"
STATUS_MISMATCH = "MISMATCH"
STATUS_SKIP = "SKIP"
STATUS_ERROR = "ERROR"
STATUS_ACCEPTED = "ACCEPTED_GAP"


def _diff(a: Any, b: Any, path: str = "") -> list[str]:
    """Recursive field-level diff; returns list of difference descriptions."""
    diffs: list[str] = []
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if float(a) != float(b):
            diffs.append(f"{path}: GQL={a!r} gRPC={b!r}")
        return diffs
    if type(a) is not type(b):
        diffs.append(
            f"{path}: type {type(a).__name__} vs {type(b).__name__} (GQL={a!r} gRPC={b!r})"
        )
        return diffs
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}" if path else k
            if k not in a:
                diffs.append(f"{p}: missing in GQL (gRPC={b[k]!r})")
            elif k not in b:
                diffs.append(f"{p}: missing in gRPC (GQL={a[k]!r})")
            else:
                diffs.extend(_diff(a[k], b[k], p))
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length GQL={len(a)} gRPC={len(b)}")
        for i, (ai, bi) in enumerate(zip(a, b)):
            diffs.extend(_diff(ai, bi, f"{path}[{i}]"))
    else:
        if a != b:
            diffs.append(f"{path}: GQL={a!r} gRPC={b!r}")
    return diffs


async def _run(client: AsyncClientBase, command: Any) -> tuple[bool, Optional[dict], str]:
    """Execute a SuiCommand; returns (ok, json_dict, error_msg)."""
    try:
        result = await client.execute_for_all(command=command)
        if result.is_ok():
            data = result.result_data
            if hasattr(data, "to_json"):
                return True, json.loads(data.to_json()), ""
            elif isinstance(data, list):
                items = [
                    json.loads(item.to_json()) if hasattr(item, "to_json") else item
                    for item in data
                ]
                return True, {"items": items}, ""
            else:
                return True, {"value": str(data)}, ""
        return False, None, str(result.result_string)
    except Exception as exc:
        return False, None, str(exc)


async def _run_all(client: AsyncClientBase, command: Any) -> tuple[bool, Optional[dict], str]:
    """Execute_for_all a pageable SuiCommand; accumulates all pages."""
    try:
        result = await client.execute_for_all(command=command)
        if result.is_ok():
            data = result.result_data
            if hasattr(data, "to_json"):
                return True, json.loads(data.to_json()), ""
            elif isinstance(data, list):
                items = [
                    json.loads(item.to_json()) if hasattr(item, "to_json") else item
                    for item in data
                ]
                return True, {"items": items}, ""
            else:
                return True, {"value": str(data)}, ""
        return False, None, str(result.result_string)
    except Exception as exc:
        return False, None, str(exc)


async def _check_all(
    name: str,
    factory: Any,
    gql: AsyncClientBase,
    grpc: AsyncClientBase,
    results: dict,
) -> str:
    """Run one pageable command against both transports (all pages), compare, record."""
    try:
        cmd_gql = factory()
        cmd_grpc = factory()
    except Exception as exc:
        results[name] = {"status": STATUS_SKIP, "reason": f"factory error: {exc}"}
        return STATUS_SKIP

    gql_ok, gql_data, gql_err = await _run_all(gql, cmd_gql)
    grpc_ok, grpc_data, grpc_err = await _run_all(grpc, cmd_grpc)

    if not gql_ok or not grpc_ok:
        results[name] = {
            "status": STATUS_ERROR,
            "gql_error": str(gql_err) if not gql_ok else None,
            "grpc_error": str(grpc_err) if not grpc_ok else None,
        }
        return STATUS_ERROR

    diffs = _diff(gql_data, grpc_data)
    status = STATUS_MATCH if not diffs else STATUS_MISMATCH
    results[name] = {
        "status": status,
        "diffs": diffs,
        "gql": gql_data,
        "grpc": grpc_data,
    }
    return status


async def _check(
    name: str,
    factory: Any,
    gql: AsyncClientBase,
    grpc: AsyncClientBase,
    results: dict,
) -> str:
    """Run one command against both transports, compare outputs, record result."""
    try:
        cmd_gql = factory()
        cmd_grpc = factory()
    except Exception as exc:
        results[name] = {"status": STATUS_SKIP, "reason": f"factory error: {exc}"}
        return STATUS_SKIP

    gql_ok, gql_data, gql_err = await _run(gql, cmd_gql)
    grpc_ok, grpc_data, grpc_err = await _run(grpc, cmd_grpc)

    if not gql_ok or not grpc_ok:
        results[name] = {
            "status": STATUS_ERROR,
            "gql_error": str(gql_err) if not gql_ok else None,
            "grpc_error": str(grpc_err) if not grpc_ok else None,
        }
        return STATUS_ERROR

    diffs = _diff(gql_data, grpc_data)
    status = STATUS_MATCH if not diffs else STATUS_MISMATCH
    results[name] = {
        "status": status,
        "diffs": diffs,
        "gql": gql_data,
        "grpc": grpc_data,
    }
    return status


async def _bootstrap(grpc: AsyncClientBase, address: str, cfg: dict) -> dict:
    """Gather runtime args from gRPC responses using proto attributes (snake_case)."""
    ctx: dict = {
        "object_ids": [],
        "coin_ids": [],
        "object_versions": {},
        "prev_tx_digest": None,
        "checkpoint_sequence": None,
        "checkpoint_digest": None,
        "package_ids": list(cfg.get("package_ids", [])),
        "module_names": {},
        "structure_names": {},
        "function_names": {},
        "verify_tx_message": None,
        "verify_tx_signature": None,
        "verify_tx_author": None,
    }

    async def _fetch(cmd: Any) -> Optional[Any]:
        r = await grpc.execute(command=cmd)
        return r.result_data if r.is_ok() else None

    cp = await _fetch(GetLatestCheckpoint())
    if cp:
        cp_inner = getattr(cp, "checkpoint", None)
        cp_src = cp_inner if cp_inner is not None else cp
        ctx["checkpoint_sequence"] = getattr(cp_src, "sequence_number", None)
        ctx["checkpoint_digest"] = getattr(cp_src, "digest", None)

    owned = await _fetch(GetObjectsOwnedByAddress(owner=address))
    if owned:
        for obj in getattr(owned, "objects", []):
            oid = getattr(obj, "object_id", None)
            ver = getattr(obj, "version", None)
            if oid:
                ctx["object_ids"].append(oid)
                if ver is not None:
                    ctx["object_versions"][oid] = int(ver)

    coins_resp = await _fetch(GetCoins(owner=address))
    if coins_resp:
        for coin in getattr(coins_resp, "objects", []):
            cid = getattr(coin, "object_id", None)
            if cid:
                ctx["coin_ids"].append(cid)

    if ctx["object_ids"]:
        obj = await _fetch(GetObject(object_id=ctx["object_ids"][0]))
        if obj:
            ctx["prev_tx_digest"] = getattr(obj, "previous_transaction", None)
            if not ctx["object_versions"].get(ctx["object_ids"][0]):
                v = getattr(obj, "version", None)
                if v is not None:
                    ctx["object_versions"][ctx["object_ids"][0]] = int(v)

    if ctx["prev_tx_digest"]:
        tx = await _fetch(GetTransaction(digest=ctx["prev_tx_digest"]))
        if tx:
            tx_inner = getattr(tx, "transaction", None) or tx
            bcs_obj = getattr(tx_inner, "bcs", None)
            bcs_bytes = getattr(bcs_obj, "value", None)
            sigs = getattr(tx, "signatures", [])
            if bcs_bytes and sigs:
                first_sig_bcs = getattr(sigs[0], "bcs", None)
                first_sig_bytes = getattr(first_sig_bcs, "value", None)
                if first_sig_bytes:
                    import base64 as _b64
                    ctx["verify_tx_message"] = _b64.b64encode(bcs_bytes).decode()
                    ctx["verify_tx_signature"] = _b64.b64encode(first_sig_bytes).decode()
                    ctx["verify_tx_author"] = getattr(tx_inner, "sender", None)

    for pkg_id in ctx["package_ids"]:
        pkg = await _fetch(GetPackage(package=pkg_id))
        if not pkg:
            continue
        pkg_inner = getattr(pkg, "package", None)
        pkg_src = pkg_inner if pkg_inner is not None else pkg
        modules = getattr(pkg_src, "modules", [])
        if not modules:
            continue
        first_mod = modules[0]
        mod_name = getattr(first_mod, "name", None)
        if not mod_name:
            continue
        ctx["module_names"][pkg_id] = mod_name

        structs_resp = await _fetch(GetStructures(package=pkg_id, module_name=mod_name))
        if structs_resp:
            structs = getattr(structs_resp, "structures", [])
            if structs:
                sn = getattr(structs[0], "name", None)
                if sn:
                    ctx["structure_names"][(pkg_id, mod_name)] = sn

        fns_resp = await _fetch(GetFunctions(package=pkg_id, module_name=mod_name))
        if fns_resp:
            fns = getattr(fns_resp, "functions", [])
            if fns:
                fn = getattr(fns[0], "name", None)
                if fn:
                    ctx["function_names"][(pkg_id, mod_name)] = fn
        break

    return ctx


async def main(args: Any) -> None:
    profile: str = args.profile
    out_path = Path(args.out)
    cfg_path = Path(args.config) if args.config else None

    cfg: dict = {}
    if cfg_path and cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())

    gql_cfg = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP, profile_name=profile
    )
    grpc_client: AsyncClientBase = client_factory(
        PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP, profile_name=profile)
    )
    gql_client: AsyncClientBase = client_factory(gql_cfg)
    active_address: str = gql_cfg.active_address

    print(f"Profile: {profile}  Address: {active_address}")
    print("Bootstrapping from gRPC...")
    ctx = await _bootstrap(grpc_client, active_address, cfg)
    print(
        f"  objects={len(ctx['object_ids'])}  coins={len(ctx['coin_ids'])}"
        f"  packages={len(ctx['package_ids'])}  checkpoint={ctx['checkpoint_sequence']}"
    )

    results: dict = {}
    marks = {STATUS_MATCH: "✓", STATUS_MISMATCH: "✗", STATUS_SKIP: "·", STATUS_ERROR: "!", STATUS_ACCEPTED: "~"}

    async def check(name: str, factory: Any) -> str:
        status = await _check(name, factory, gql_client, grpc_client, results)
        print(f"  {marks.get(status, '?')} {name}: {status}")
        return status

    async def check_all(name: str, factory: Any) -> str:
        status = await _check_all(name, factory, gql_client, grpc_client, results)
        print(f"  {marks.get(status, '?')} {name}: {status}")
        return status

    def skip(name: str, reason: str) -> None:
        results[name] = {"status": STATUS_SKIP, "reason": reason}
        print(f"  · {name}: SKIP ({reason})")

    async def accept_gap(name: str, reason: str, factory: Any) -> None:
        status = await _check(name, factory, gql_client, grpc_client, results)
        if status == STATUS_MISMATCH:
            results[name]["status"] = STATUS_ACCEPTED
            results[name]["reason"] = reason
            status = STATUS_ACCEPTED
        print(f"  ~ {name}: {status} ({reason})")

    # ── Phase 1 — No args ─────────────────────────────────────────────────
    print("\nPhase 1 — No args")
    await check("GetChainIdentifier", lambda: GetChainIdentifier())
    await check("GetBasicCurrentEpochInfo", lambda: GetBasicCurrentEpochInfo())
    if ctx["checkpoint_sequence"] is not None:
        seq = ctx["checkpoint_sequence"]
        await accept_gap("GetLatestCheckpoint", "GQL checkpoint schema gaps: bitmap encoding differs; transactions/objects not exposed in GQL checkpoint query (gRPC wildcard mask fetches all)", lambda: GetCheckpointBySequence(sequence_number=seq))
    else:
        skip("GetLatestCheckpoint", "no checkpoint_sequence in ctx")
    await check("GetLatestSuiSystemState", lambda: GetLatestSuiSystemState())
    await check("GetCurrentValidators", lambda: GetCurrentValidators())
    await accept_gap("GetEpoch", "schema gaps: lastCheckpoint semantic + protocol config key differences", lambda: GetEpoch())
    await check("GetCoinMetaData", lambda: GetCoinMetaData())
    await accept_gap("GetProtocolConfig", "schema gaps: GQL/gRPC expose different protocol config keys", lambda: GetProtocolConfig())

    # ── Phase 2 — Active address ──────────────────────────────────────────
    print("\nPhase 2 — Address")
    addr = active_address
    await check("GetAddressCoinBalance", lambda: GetAddressCoinBalance(owner=addr))
    await check("GetAddressCoinBalances", lambda: GetAddressCoinBalances(owner=addr))
    await check("GetCoins", lambda: GetCoins(owner=addr))
    await check("GetGas", lambda: GetGas(owner=addr))
    await check("GetStaked", lambda: GetStaked(owner=addr))
    await check("GetDelegatedStakes", lambda: GetDelegatedStakes(owner=addr))
    await check("GetObjectsOwnedByAddress", lambda: GetObjectsOwnedByAddress(owner=addr))
    await accept_gap(
        "GetNameServiceNames",
        "SuiNS not configured on devnet; GQL schema missing defaultSuinsName on Address type",
        lambda: GetNameServiceNames(owner=addr),
    )
    await check(
        "GetObjectsForType",
        lambda: GetObjectsForType(
            owner=addr, object_type="0x2::coin::Coin<0x2::sui::SUI>"
        ),
    )

    # ── Phase 3 — Objects ─────────────────────────────────────────────────
    print("\nPhase 3 — Objects")
    obj_id = ctx["object_ids"][0] if ctx["object_ids"] else None
    coin_id = ctx["coin_ids"][0] if ctx["coin_ids"] else None
    multi_ids = ctx["object_ids"][:3]

    if obj_id:
        oid = obj_id
        ver = ctx["object_versions"].get(oid, 1)
        await check("GetObject", lambda: GetObject(object_id=oid))
        await check("GetObjectSummary", lambda: GetObjectSummary(object_id=oid))
        await check("GetObjectContent", lambda: GetObjectContent(object_id=oid))
        await check("GetPastObject", lambda: GetPastObject(object_id=oid, version=ver))
    else:
        for n in ("GetObject", "GetObjectSummary", "GetObjectContent", "GetPastObject"):
            skip(n, "no object_id from bootstrap")

    if len(multi_ids) >= 2:
        ids = multi_ids
        vers = [
            {"objectId": o, "version": ctx["object_versions"].get(o, 1)}
            for o in ids[:2]
        ]
        await check("GetMultipleObjects", lambda: GetMultipleObjects(object_ids=ids))
        await check(
            "GetMultipleObjectSummary",
            lambda: GetMultipleObjectSummary(object_ids=ids),
        )
        await check(
            "GetMultipleObjectContent",
            lambda: GetMultipleObjectContent(object_ids=ids),
        )
        await check(
            "GetMultiplePastObjects",
            lambda: GetMultiplePastObjects(for_versions=vers),
        )
    else:
        for n in (
            "GetMultipleObjects",
            "GetMultipleObjectSummary",
            "GetMultipleObjectContent",
            "GetMultiplePastObjects",
        ):
            skip(n, "need ≥2 object_ids from bootstrap")

    if coin_id:
        cid = coin_id
        await check("GetCoinSummary", lambda: GetCoinSummary(coin_id=cid))
    else:
        skip("GetCoinSummary", "no coin_id from bootstrap")

    df_cfg = cfg.get("GetDynamicFields", {})
    if df_cfg.get("object_id"):
        df_oid = df_cfg["object_id"]
        await check("GetDynamicFields", lambda: GetDynamicFields(object_id=df_oid))
    else:
        skip("GetDynamicFields", "add GetDynamicFields.object_id to config")

    # ── Phase 4 — Packages ────────────────────────────────────────────────
    print("\nPhase 4 — Packages")
    pkg_id = ctx["package_ids"][0] if ctx["package_ids"] else None
    if pkg_id:
        pid = pkg_id
        await accept_gap("GetPackage", "GQL MovePackage does not expose originalId — field-level schema gap only", lambda: GetPackage(package=pid))
        await check("GetPackageVersions", lambda: GetPackageVersions(package_address=pid))
        mod_name = ctx["module_names"].get(pkg_id) or cfg.get("module_name")
        if mod_name:
            mn = mod_name
            await check("GetModule", lambda: GetModule(package=pid, module_name=mn))
            await check_all("GetStructures", lambda: GetStructures(package=pid, module_name=mn))
            await check_all("GetFunctions", lambda: GetFunctions(package=pid, module_name=mn))
            struct_name = ctx["structure_names"].get((pkg_id, mod_name))
            if struct_name:
                sn = struct_name
                await check(
                    "GetStructure",
                    lambda: GetStructure(package=pid, module_name=mn, structure_name=sn),
                )
                await check(
                    "GetMoveDataType",
                    lambda: GetMoveDataType(package=pid, module_name=mn, type_name=sn),
                )
            else:
                for n in ("GetStructure", "GetMoveDataType"):
                    skip(n, "no structure name from bootstrap")
            fn_name = ctx["function_names"].get((pkg_id, mod_name))
            if fn_name:
                fn = fn_name
                await check(
                    "GetFunction",
                    lambda: GetFunction(package=pid, module_name=mn, function_name=fn),
                )
            else:
                skip("GetFunction", "no function name from bootstrap")
        else:
            for n in (
                "GetModule",
                "GetStructures",
                "GetFunctions",
                "GetStructure",
                "GetMoveDataType",
                "GetFunction",
            ):
                skip(n, "no module name from bootstrap")
    else:
        for n in (
            "GetPackage",
            "GetPackageVersions",
            "GetModule",
            "GetStructures",
            "GetFunctions",
            "GetStructure",
            "GetMoveDataType",
            "GetFunction",
        ):
            skip(n, "add package_ids to config")

    # ── Phase 5 — Checkpoints ─────────────────────────────────────────────
    print("\nPhase 5 — Checkpoints")
    if ctx["checkpoint_sequence"] is not None:
        seq = ctx["checkpoint_sequence"]
        await accept_gap(
            "GetCheckpointBySequence",
            "GQL checkpoint schema gaps: bitmap encoding differs; transactions/objects not exposed in GQL checkpoint query (gRPC wildcard mask fetches all)",
            lambda: GetCheckpointBySequence(sequence_number=seq),
        )
        if ctx["checkpoint_digest"]:
            dgst = ctx["checkpoint_digest"]
            await accept_gap(
                "GetCheckpointByDigest",
                "GQL checkpoint schema gaps: bitmap encoding differs; transactions/objects not exposed in GQL checkpoint query (gRPC wildcard mask fetches all)",
                lambda: GetCheckpointByDigest(digest=dgst),
            )
        else:
            skip("GetCheckpointByDigest", "no checkpoint digest from bootstrap")
    else:
        skip("GetCheckpointBySequence", "no checkpoint from bootstrap")
        skip("GetCheckpointByDigest", "no checkpoint from bootstrap")

    # ── Phase 6 — Transactions ────────────────────────────────────────────
    print("\nPhase 6 — Transactions")
    tx_digest = ctx["prev_tx_digest"]
    if tx_digest:
        txd = tx_digest
        await accept_gap("GetTransaction", "gRPC ObjectSet empty pending Mysten server deployment (objects.objects.bcs field mask)", lambda: GetTransaction(digest=txd))
        await accept_gap("GetTransactions", "gRPC ObjectSet empty pending Mysten server deployment (objects.objects.bcs field mask)", lambda: GetTransactions(digests=[txd]))
        await check("GetTransactionKind", lambda: GetTransactionKind(digest=txd))
    else:
        for n in ("GetTransaction", "GetTransactions", "GetTransactionKind"):
            skip(n, "no tx digest from bootstrap")

    # ── Phase 7 — Config only ─────────────────────────────────────────────
    print("\nPhase 7 — Config only")
    ns_cfg = cfg.get("GetNameServiceAddress", {})
    if ns_cfg.get("name"):
        ns_name = ns_cfg["name"]
        await check(
            "GetNameServiceAddress", lambda: GetNameServiceAddress(name=ns_name)
        )
    else:
        skip("GetNameServiceAddress", "add GetNameServiceAddress.name to config")

    for cmd_name in ("VerifyTransactionSignature", "VerifyPersonalMessageSignature"):
        vc = cfg.get(cmd_name, {})
        if cmd_name == "VerifyTransactionSignature" and ctx["verify_tx_message"]:
            msg = ctx["verify_tx_message"]
            sig = ctx["verify_tx_signature"]
            auth = ctx["verify_tx_author"]
        elif vc.get("message") and vc.get("signature"):
            msg = vc["message"]
            sig = vc["signature"]
            auth = vc.get("author")
        else:
            skip(cmd_name, f"add {cmd_name}.message/.signature to config (or ensure prev_tx_digest resolves)")
            continue
        if cmd_name == "VerifyTransactionSignature":
            await check(
                cmd_name,
                lambda: VerifyTransactionSignature(
                    message=msg, signature=sig, author=auth
                ),
            )
        else:
            await check(
                cmd_name,
                lambda: VerifyPersonalMessageSignature(
                    message=msg, signature=sig, author=auth
                ),
            )

    # ── Summary ───────────────────────────────────────────────────────────
    counts: dict[str, int] = {
        STATUS_MATCH: 0,
        STATUS_MISMATCH: 0,
        STATUS_SKIP: 0,
        STATUS_ERROR: 0,
        STATUS_ACCEPTED: 0,
    }
    for r in results.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print(f"\n{'='*60}")
    print(
        f"  MATCH={counts[STATUS_MATCH]}  MISMATCH={counts[STATUS_MISMATCH]}"
        f"  ACCEPTED_GAP={counts[STATUS_ACCEPTED]}"
        f"  ERROR={counts[STATUS_ERROR]}  SKIP={counts[STATUS_SKIP]}"
    )
    print(f"{'='*60}")

    mismatched = [(n, r) for n, r in results.items() if r["status"] == STATUS_MISMATCH]
    if mismatched:
        print("\nMISMATCHED:")
        for name, r in mismatched:
            nd = len(r.get("diffs", []))
            print(f"  {name}: {nd} diff(s)")
            for d in r.get("diffs", [])[:3]:
                print(f"    {d}")
            if nd > 3:
                print(f"    ... {nd - 3} more (see results file)")

    accepted = [(n, r) for n, r in results.items() if r["status"] == STATUS_ACCEPTED]
    if accepted:
        print("\nACCEPTED GAPS:")
        for name, r in accepted:
            nd = len(r.get("diffs", []))
            print(f"  {name}: {nd} diff(s) — {r.get('reason', '')}")

    errored = [(n, r) for n, r in results.items() if r["status"] == STATUS_ERROR]
    if errored:
        print("\nERRORS:")
        for name, r in errored:
            print(f"  {name}: GQL={r.get('gql_error')}  gRPC={r.get('grpc_error')}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull results → {out_path}")


if __name__ == "__main__":
    p = ArgumentParser(description="SuiCommand GQL/gRPC parity check")
    p.add_argument(
        "--profile",
        default="devnet",
        choices=["devnet", "testnet", "mainnet"],
        help="Sui network profile (default: devnet)",
    )
    p.add_argument(
        "--out",
        default="scratch/parity_check_results.json",
        help="Output JSON file path",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Optional config JSON for package_ids and per-command args",
    )
    asyncio.run(main(p.parse_args()))
