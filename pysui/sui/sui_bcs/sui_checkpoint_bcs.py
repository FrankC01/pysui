#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

# Hand-written BCS types for Sui Checkpoint deserialization.
# Source: crates/sui-types/src/messages_checkpoint.rs
# Targets: CheckpointSummary, CheckpointContents

"""BCS types for Sui checkpoint summary and contents deserialization."""

import canoser
import pysui.sui.sui_bcs.bcs_stnd as bcse
import pysui.sui.sui_bcs.pysui_bcs as pbcsbase

_DIGEST_LEN: int = 32
_BLS_PUBKEY_LEN: int = 96  # BLS12-381 G2 compressed authority public key


class GasCostSummaryBCS(pbcsbase.BCS_Struct):
    """BCS layout for GasCostSummary."""

    _fields = [
        ("computation_cost", bcse.U64),
        ("storage_cost", bcse.U64),
        ("storage_rebate", bcse.U64),
        ("non_refundable_storage_fee", bcse.U64),
    ]


class CheckpointDigestBCS(pbcsbase.BCS_Struct):
    """BCS layout for CheckpointDigest ([u8; 32])."""

    _fields = [("digest", canoser.ArrayT(canoser.Uint8, _DIGEST_LEN))]


class ECMHLiveObjectSetDigestBCS(pbcsbase.BCS_Struct):
    """BCS layout for ECMHLiveObjectSetDigest (struct wrapping a 32-byte ECMH hash)."""

    _fields = [("digest", canoser.ArrayT(canoser.Uint8, _DIGEST_LEN))]


class CheckpointArtifactsDigestBCS(pbcsbase.BCS_Struct):
    """BCS layout for CheckpointArtifactsDigest (struct wrapping a 32-byte digest)."""

    _fields = [("digest", canoser.ArrayT(canoser.Uint8, _DIGEST_LEN))]


class CheckpointCommitmentBCS(canoser.RustEnum):
    """BCS layout for CheckpointCommitment enum.

    Variant 0: ECMHLiveObjectSetDigest
    Variant 1: CheckpointArtifactsDigest
    """

    _enums = [
        ("ECMHLiveObjectSetDigest", ECMHLiveObjectSetDigestBCS),
        ("CheckpointArtifactsDigest", CheckpointArtifactsDigestBCS),
    ]


class CommitteeEntryBCS(pbcsbase.BCS_Struct):
    """BCS layout for (AuthorityName, StakeUnit) next-epoch committee entry."""

    _fields = [
        ("authority_name", canoser.ArrayT(canoser.Uint8, _BLS_PUBKEY_LEN)),
        ("stake", bcse.U64),
    ]


class EndOfEpochDataBCS(pbcsbase.BCS_Struct):
    """BCS layout for EndOfEpochData (present only on epoch-boundary checkpoints)."""

    _fields = [
        ("next_epoch_committee", [CommitteeEntryBCS]),
        ("next_epoch_protocol_version", bcse.U64),
        ("epoch_commitments", [CheckpointCommitmentBCS]),
    ]


class PreviousDigestOptional(pbcsbase.BCS_Optional):
    """Option<CheckpointDigest> — absent on the genesis checkpoint."""

    _type = CheckpointDigestBCS


class EndOfEpochDataOptional(pbcsbase.BCS_Optional):
    """Option<EndOfEpochData> — present only on epoch-boundary checkpoints."""

    _type = EndOfEpochDataBCS


class CheckpointSummaryBCS(pbcsbase.BCS_Struct):
    """BCS layout for CheckpointSummary.

    Field order matches crates/sui-types/src/messages_checkpoint.rs CheckpointSummary.
    Fields 8 (checkpoint_commitments) and 10 (version_specific_data) map to
    summary.commitments and summary.versionSpecificData in the gRPC proto.
    """

    _fields = [
        ("epoch", bcse.U64),
        ("sequence_number", bcse.U64),
        ("network_total_transactions", bcse.U64),
        ("content_digest", canoser.ArrayT(canoser.Uint8, _DIGEST_LEN)),
        ("previous_digest", PreviousDigestOptional),
        ("epoch_rolling_gas_cost_summary", GasCostSummaryBCS),
        ("timestamp_ms", bcse.U64),
        ("checkpoint_commitments", [CheckpointCommitmentBCS]),
        ("end_of_epoch_data", EndOfEpochDataOptional),
        ("version_specific_data", [bcse.U8]),
    ]


class ExecutionDigestsBCS(pbcsbase.BCS_Struct):
    """BCS layout for ExecutionDigests — transaction + effects digest pair."""

    _fields = [
        ("transaction", canoser.ArrayT(canoser.Uint8, _DIGEST_LEN)),
        ("effects", canoser.ArrayT(canoser.Uint8, _DIGEST_LEN)),
    ]


class CheckpointContentsV1BCS(pbcsbase.BCS_Struct):
    """BCS layout for CheckpointContentsV1.

    Only `transactions` is decoded; `user_signatures` is intentionally omitted
    because BCS parse stops after the last declared field.
    """

    _fields = [
        ("transactions", [ExecutionDigestsBCS]),
    ]


class CheckpointContentsBCS(canoser.RustEnum):
    """BCS layout for CheckpointContents versioned enum.

    Variant index (0-based) maps to CheckpointContents.version in the gRPC proto
    (proto uses 1-based, so add 1: variant 0 → version 1).
    Only V1 is currently deployed.
    """

    _enums = [
        ("V1", CheckpointContentsV1BCS),
    ]


def decode_checkpoint_contents_v2(payload: bytes) -> list:
    """Decode V2 CheckpointContents payload (after the variant byte).

    V2 stores each digest as Vec<u8> (ULEB128 length + bytes) rather than
    the fixed [u8;32] arrays used in V1.  Empirically verified against live
    devnet blobs.

    Returns list of (tx_digest_bytes, effects_digest_bytes, sig_bytes_list, alias_versions) tuples.
    sig_bytes_list is a list[bytes] of raw GenericSignature bytes per user signature.
    alias_versions is a list[Optional[int]] — None if the Option<u64> was absent, else the u64 value.
    """
    import struct

    def _uleb128(data: bytes, pos: int):
        val, shift = 0, 0
        while True:
            b = data[pos]; pos += 1
            val |= (b & 0x7F) << shift
            shift += 7
            if not (b & 0x80):
                return val, pos

    pos = 0
    count, pos = _uleb128(payload, pos)
    results = []
    for _ in range(count):
        tx_len, pos = _uleb128(payload, pos)
        tx_digest = bytes(payload[pos : pos + tx_len]); pos += tx_len
        eff_len, pos = _uleb128(payload, pos)
        eff_digest = bytes(payload[pos : pos + eff_len]); pos += eff_len
        sig_count, pos = _uleb128(payload, pos)
        sigs: list = []
        alias_versions: list = []
        for _ in range(sig_count):
            sig_len, pos = _uleb128(payload, pos)
            sig_bytes = bytes(payload[pos : pos + sig_len]); pos += sig_len
            sigs.append(sig_bytes)
            opt = payload[pos]; pos += 1
            if opt == 1:
                version = struct.unpack_from("<Q", payload, pos)[0]; pos += 8
                alias_versions.append(version)
            else:
                alias_versions.append(None)
        results.append((tx_digest, eff_digest, sigs, alias_versions))
    return results
