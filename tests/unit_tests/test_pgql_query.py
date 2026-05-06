#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.sui.sui_pgql.pgql_query — all offline, no live node required.

Tests cover:
  - Constructor attribute storage
  - encode_fn() static method wiring to the correct result type
  - Deprecation warnings (DryRunTransaction, GetAllCoinBalances)
  - PGQL_NoOp short-circuit when a paging cursor is exhausted
  - GetGas subclass invariants
"""

import warnings
import pytest

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pt
from pysui.sui.sui_pgql.pgql_clients import PGQL_NoOp

# Reusable constants
_ADDR = "0x" + "a" * 64
_ADDR2 = "0x" + "b" * 64
_SUI_COIN = "0x2::coin::Coin<0x2::sui::SUI>"
_EXHAUSTED_CURSOR = pt.PagingCursor(hasNextPage=False, endCursor=None)
_LIVE_CURSOR = pt.PagingCursor(hasNextPage=True, endCursor="tok1")


# ---------------------------------------------------------------------------
# TestConstruction — __init__ stores args correctly
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_get_coin_metadata_default_coin_type(self):
        obj = qn.GetCoinMetaData()
        assert obj.coin_type == "0x2::sui::SUI"

    def test_get_coin_metadata_custom_coin_type(self):
        obj = qn.GetCoinMetaData(coin_type="0x2::usdc::USDC")
        assert obj.coin_type == "0x2::usdc::USDC"

    def test_get_address_coin_balance_stores_owner(self):
        obj = qn.GetAddressCoinBalance(owner=_ADDR)
        assert obj.owner == _ADDR
        assert obj.coin_type == "0x2::sui::SUI"

    def test_get_address_coin_balance_custom_coin_type(self):
        obj = qn.GetAddressCoinBalance(owner=_ADDR, coin_type="0xdead::beef::COIN")
        assert obj.coin_type == "0xdead::beef::COIN"

    def test_get_coins_defaults(self):
        obj = qn.GetCoins(owner=_ADDR)
        assert obj.owner == _ADDR
        assert obj.coin_type == _SUI_COIN
        assert obj.next_page is None

    def test_get_coins_with_all_args(self):
        obj = qn.GetCoins(owner=_ADDR, coin_type="0xfoo::bar::BAZ", next_page=_LIVE_CURSOR)
        assert obj.coin_type == "0xfoo::bar::BAZ"
        assert obj.next_page.hasNextPage is True

    def test_get_epoch_defaults(self):
        obj = qn.GetEpoch()
        assert obj.epoch_id is None

    def test_get_epoch_with_id(self):
        obj = qn.GetEpoch(epoch_id=42)
        assert obj.epoch_id == 42

    def test_get_checkpoint_by_sequence_stores_number(self):
        obj = qn.GetCheckpointBySequence(sequence_number=99)
        assert obj.sequence_number == 99

    def test_get_package_versions_stores_address(self):
        obj = qn.GetPackageVersions(package_address="0x2")
        assert obj.package_address == "0x2"

    def test_get_package_versions_with_next_page(self):
        obj = qn.GetPackageVersions(package_address="0x2", next_page=_LIVE_CURSOR)
        assert obj.next_page.endCursor == "tok1"

    def test_get_tx_stores_digest(self):
        obj = qn.GetTx(digest="FakeTxDigest123")
        assert obj.digest == "FakeTxDigest123"

    def test_get_events_stores_filter(self):
        filt = {"type": "0x3::validator::StakingRequestEvent"}
        obj = qn.GetEvents(event_filter=filt)
        assert obj.event_filter == filt
        assert obj.next_page is None

    def test_get_object_validates_and_stores_id(self):
        obj = qn.GetObject(object_id=_ADDR)
        assert obj.object_id == _ADDR

    def test_get_multiple_gas_objects_stores_ids(self):
        obj = qn.GetMultipleGasObjects(coin_object_ids=[_ADDR, _ADDR2])
        assert len(obj.coin_ids) == 2

    def test_simulate_transaction_bytes_stores_data(self):
        obj = qn.SimulateTransaction(tx_bytestr=b"\x00\x01\x02")
        assert obj.tx_data == b"\x00\x01\x02"

    def test_simulate_transaction_base64_stores_data(self):
        import base64
        b64 = base64.b64encode(b"\x10\x20\x30").decode()
        obj = qn.SimulateTransaction(tx_bytestr=b64)
        assert obj.tx_data == b64

    def test_get_reference_gas_price_constructs(self):
        obj = qn.GetReferenceGasPrice()
        assert isinstance(obj, qn.GetReferenceGasPrice)

    def test_get_basic_current_epoch_info_constructs(self):
        obj = qn.GetBasicCurrentEpochInfo()
        assert isinstance(obj, qn.GetBasicCurrentEpochInfo)

    def test_get_name_service_address_stores_name(self):
        obj = qn.GetNameServiceAddress(name="example.sui")
        assert obj.name == "example.sui"

    def test_get_name_service_names_stores_owner(self):
        obj = qn.GetNameServiceNames(owner=_ADDR)
        assert obj.owner == _ADDR


# ---------------------------------------------------------------------------
# TestGetGas — subclass invariants
# ---------------------------------------------------------------------------

class TestGetGas:
    def test_get_gas_is_get_coins_subclass(self):
        assert issubclass(qn.GetGas, qn.GetCoins)

    def test_get_gas_fixes_coin_type(self):
        obj = qn.GetGas(owner=_ADDR)
        assert obj.coin_type == _SUI_COIN

    def test_get_gas_inherits_encode_fn(self):
        assert qn.GetGas.encode_fn() == pt.SuiCoinObjectsGQL.from_query

    def test_get_gas_with_next_page(self):
        obj = qn.GetGas(owner=_ADDR, next_page=_LIVE_CURSOR)
        assert obj.next_page.hasNextPage is True


# ---------------------------------------------------------------------------
# TestEncodeFn — encode_fn() wired to correct result type (no instantiation needed)
# ---------------------------------------------------------------------------

class TestEncodeFn:
    def test_get_coin_metadata_encode_fn(self):
        assert qn.GetCoinMetaData.encode_fn() == pt.SuiCoinMetadataGQL.from_query

    def test_get_address_coin_balance_encode_fn(self):
        assert qn.GetAddressCoinBalance.encode_fn() == pt.AddressBalanceGQL.from_query

    def test_get_all_coin_balances_encode_fn(self):
        assert qn.GetAllCoinBalances.encode_fn() == pt.BalancesGQL.from_query

    def test_get_address_coin_balances_encode_fn(self):
        assert qn.GetAddressCoinBalances.encode_fn() == pt.BalancesGQL.from_query

    def test_get_coin_summary_encode_fn(self):
        assert qn.GetCoinSummary.encode_fn() == pt.SuiCoinObjectSummaryGQL.from_query

    def test_get_coins_encode_fn(self):
        assert qn.GetCoins.encode_fn() == pt.SuiCoinObjectsGQL.from_query

    def test_get_multiple_gas_objects_encode_fn(self):
        assert qn.GetMultipleGasObjects.encode_fn() == pt.SuiCoinFromObjectsGQL.from_query

    def test_get_multiple_objects_encode_fn(self):
        assert qn.GetMultipleObjects.encode_fn() == pt.ObjectReadsGQL.from_query

    def test_get_object_encode_fn(self):
        assert qn.GetObject.encode_fn() == pt.ObjectReadGQL.from_query

    def test_get_past_object_encode_fn(self):
        assert qn.GetPastObject.encode_fn() == pt.ObjectReadGQL.from_query

    def test_get_tx_encode_fn(self):
        assert qn.GetTx.encode_fn() == pt.TransactionResultGQL.from_query

    def test_get_multiple_tx_encode_fn(self):
        assert qn.GetMultipleTx.encode_fn() == pt.TransactionSummariesGQL.from_query

    def test_get_basic_current_epoch_info_encode_fn(self):
        assert qn.GetBasicCurrentEpochInfo.encode_fn() == pt.BasicCurrentEpochInfoGQL.from_query

    def test_get_epoch_encode_fn(self):
        assert qn.GetEpoch.encode_fn() == pt.EpochGQL.from_query

    def test_get_latest_checkpoint_encode_fn(self):
        assert qn.GetLatestCheckpointSequence.encode_fn() == pt.CheckpointGQL.from_last_checkpoint

    def test_get_checkpoint_by_sequence_encode_fn(self):
        assert qn.GetCheckpointBySequence.encode_fn() == pt.CheckpointGQL.from_query

    def test_get_checkpoints_encode_fn(self):
        assert qn.GetCheckpoints.encode_fn() == pt.CheckpointsGQL.from_query

    def test_get_reference_gas_price_encode_fn(self):
        assert qn.GetReferenceGasPrice.encode_fn() == pt.ReferenceGasPriceGQL.from_query

    def test_get_package_versions_encode_fn(self):
        assert qn.GetPackageVersions.encode_fn() == pt.PackageVersionsGQL.from_query

    def test_dry_run_transaction_encode_fn(self):
        assert qn.DryRunTransaction.encode_fn() == pt.DryRunResultGQL.from_query

    def test_dry_run_transaction_kind_encode_fn(self):
        assert qn.DryRunTransactionKind.encode_fn() == pt.DryRunResultGQL.from_query

    def test_simulate_transaction_encode_fn(self):
        assert qn.SimulateTransaction.encode_fn() == pt.DryRunResultGQL.from_query

    def test_simulate_transaction_kind_encode_fn(self):
        assert qn.SimulateTransactionKind.encode_fn() == pt.DryRunResultGQL.from_query

    def test_execute_transaction_encode_fn(self):
        assert qn.ExecuteTransaction.encode_fn() == pt.ExecutionResultGQL.from_query


# ---------------------------------------------------------------------------
# TestDeprecationWarnings
# ---------------------------------------------------------------------------

class TestDeprecationWarnings:
    def test_dry_run_transaction_warns(self):
        with pytest.warns(DeprecationWarning, match="DryRunTransaction is deprecated"):
            qn.DryRunTransaction(tx_bytestr=b"\x00\x01\x02")

    def test_dry_run_transaction_suggests_simulate(self):
        with pytest.warns(DeprecationWarning, match="SimulateTransaction"):
            qn.DryRunTransaction(tx_bytestr=b"\xff")

    def test_get_all_coin_balances_warns(self):
        with pytest.warns(DeprecationWarning):
            qn.GetAllCoinBalances(owner=_ADDR)

    def test_simulate_transaction_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            qn.SimulateTransaction(tx_bytestr=b"\x00\x01")
        dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(dep_warnings) == 0


# ---------------------------------------------------------------------------
# TestNoopShortCircuit — as_document_node returns PGQL_NoOp before touching schema
# ---------------------------------------------------------------------------

class TestNoopShortCircuit:
    """When next_page.hasNextPage is False, the query returns PGQL_NoOp immediately.

    We pass schema=None to confirm the guard fires before schema access.
    """

    def test_get_coins_exhausted_cursor(self):
        obj = qn.GetCoins(owner=_ADDR, next_page=_EXHAUSTED_CURSOR)
        assert obj.as_document_node(None) is PGQL_NoOp

    def test_get_gas_exhausted_cursor(self):
        obj = qn.GetGas(owner=_ADDR, next_page=_EXHAUSTED_CURSOR)
        assert obj.as_document_node(None) is PGQL_NoOp

    def test_get_objects_owned_exhausted_cursor(self):
        obj = qn.GetObjectsOwnedByAddress(owner=_ADDR, next_page=_EXHAUSTED_CURSOR)
        assert obj.as_document_node(None) is PGQL_NoOp

    def test_get_checkpoints_exhausted_cursor(self):
        obj = qn.GetCheckpoints(next_page=_EXHAUSTED_CURSOR)
        assert obj.as_document_node(None) is PGQL_NoOp

    def test_get_package_versions_exhausted_cursor(self):
        obj = qn.GetPackageVersions(package_address="0x2", next_page=_EXHAUSTED_CURSOR)
        assert obj.as_document_node(None) is PGQL_NoOp

    def test_get_all_coin_balances_exhausted_cursor(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            obj = qn.GetAllCoinBalances(owner=_ADDR, next_page=_EXHAUSTED_CURSOR)
        assert obj.as_document_node(None) is PGQL_NoOp

    def test_live_cursor_does_not_short_circuit(self):
        """A live cursor should NOT trigger the PGQL_NoOp guard."""
        obj = qn.GetCoins(owner=_ADDR, next_page=_LIVE_CURSOR)
        # We cannot call as_document_node without a schema when cursor is live,
        # but we can assert the guard condition is false.
        assert obj.next_page.hasNextPage is True


# ---------------------------------------------------------------------------
# TestSCSiblings — encode_fn() output shapes for SC sibling classes
# ---------------------------------------------------------------------------

import datetime
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot


class TestSCSiblings:
    """Verify each SC sibling's encode_fn produces the correct proto shape."""

    def test_get_coin_metadata_sc_inherits_parent_coin_type(self):
        obj = qn.GetCoinMetaDataSC(coin_type="0x2::sui::SUI")
        assert obj.coin_type == "0x2::sui::SUI"

    def test_get_coin_metadata_sc_encode_fn_returns_callable(self):
        fn = qn.GetCoinMetaDataSC.encode_fn()
        assert callable(fn)

    def test_get_coin_metadata_sc_encode_maps_fields(self):
        raw = {
            "coinMetadata": {
                "decimals": 9,
                "name": "Sui",
                "symbol": "SUI",
                "description": "The Sui token",
                "iconUrl": "https://sui.io/icon.png",
                "supply": "10000000000",
                "address": _ADDR,
            }
        }
        result = qn.GetCoinMetaDataSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.GetCoinInfoResponse)
        meta = result.metadata
        assert isinstance(meta, sui_prot.CoinMetadata)
        assert meta.id == _ADDR
        assert meta.decimals == 9
        assert meta.name == "Sui"
        assert meta.symbol == "SUI"
        assert meta.description == "The Sui token"
        assert meta.icon_url == "https://sui.io/icon.png"

    def test_get_address_coin_balance_sc_encode_maps_fields(self):
        raw = {
            "address": {
                "balance": {
                    "coinType": {"coinType": "0x2::sui::SUI"},
                    "addressBalance": "1000",
                    "coinBalance": "2000",
                    "totalBalance": "3000",
                }
            }
        }
        result = qn.GetAddressCoinBalanceSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.GetBalanceResponse)
        bal = result.balance
        assert isinstance(bal, sui_prot.Balance)
        assert bal.coin_type == "0x2::sui::SUI"
        assert bal.balance == 3000
        assert bal.address_balance == 1000
        assert bal.coin_balance == 2000

    def test_get_address_coin_balances_sc_encode_maps_fields(self):
        raw = {
            "qres": {
                "owner_address": _ADDR,
                "balances": {
                    "cursor": {"hasNextPage": True, "endCursor": "tok42"},
                    "type_balances": [
                        {
                            "addressBalance": "500",
                            "coinBalance": "1500",
                            "totalBalance": "2000",
                            "coinType": {"coin_type": "0x2::sui::SUI"},
                        }
                    ],
                },
            }
        }
        result = qn.GetAddressCoinBalancesSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ListBalancesResponse)
        assert len(result.balances) == 1
        bal = result.balances[0]
        assert bal.coin_type == "0x2::sui::SUI"
        assert bal.balance == 2000
        assert bal.address_balance == 500
        assert bal.coin_balance == 1500
        assert result.next_page_token == b"tok42"

    def test_get_address_coin_balances_sc_no_next_page(self):
        raw = {
            "qres": {
                "owner_address": _ADDR,
                "balances": {
                    "cursor": {"hasNextPage": False, "endCursor": None},
                    "type_balances": [],
                },
            }
        }
        result = qn.GetAddressCoinBalancesSC.encode_fn()(raw)
        assert result.next_page_token is None
        assert result.balances == []

    def test_get_epoch_sc_encode_maps_fields(self):
        raw = {
            "epoch": {
                "epochId": 42,
                "startTimestamp": "2024-01-15T00:00:00+00:00",
                "endTimestamp": "2024-01-16T00:00:00+00:00",
                "referenceGasPrice": "750",
                "totalCheckpoints": "1000",
                "totalTransactions": "5000",
            }
        }
        result = qn.GetEpochSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.GetEpochResponse)
        ep = result.epoch
        assert isinstance(ep, sui_prot.Epoch)
        assert ep.epoch == 42
        assert ep.reference_gas_price == 750
        assert ep.start == datetime.datetime.fromisoformat("2024-01-15T00:00:00+00:00")
        assert ep.end == datetime.datetime.fromisoformat("2024-01-16T00:00:00+00:00")

    def test_get_epoch_sc_no_end_timestamp(self):
        raw = {
            "epoch": {
                "epochId": 5,
                "startTimestamp": "2024-03-01T00:00:00+00:00",
                "endTimestamp": None,
                "referenceGasPrice": "1000",
            }
        }
        result = qn.GetEpochSC.encode_fn()(raw)
        assert result.epoch.end is None

    def test_get_package_versions_sc_encode_maps_fields(self):
        raw = {
            "packageVersions": {
                "cursor": {"hasNextPage": False, "endCursor": None},
                "versions": [
                    {"address": _ADDR, "version": 1, "digest": "aaa"},
                    {"address": _ADDR2, "version": 2, "digest": "bbb"},
                ],
            }
        }
        result = qn.GetPackageVersionsSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ListPackageVersionsResponse)
        assert len(result.versions) == 2
        assert result.versions[0].package_id == _ADDR
        assert result.versions[0].version == 1
        assert result.versions[1].package_id == _ADDR2
        assert result.versions[1].version == 2
        assert result.next_page_token is None

    def test_get_package_versions_sc_with_next_page(self):
        raw = {
            "packageVersions": {
                "cursor": {"hasNextPage": True, "endCursor": "pageX"},
                "versions": [{"address": _ADDR, "version": 3, "digest": "ccc"}],
            }
        }
        result = qn.GetPackageVersionsSC.encode_fn()(raw)
        assert result.next_page_token == b"pageX"

    def test_get_name_service_address_sc_encode_maps_fields(self):
        raw = {
            "suinsName": {
                "address": _ADDR,
                "defaultSuinsName": "example.sui",
            }
        }
        result = qn.GetNameServiceAddressSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.LookupNameResponse)
        rec = result.record
        assert isinstance(rec, sui_prot.NameRecord)
        assert rec.name == "example.sui"
        assert rec.target_address == _ADDR

    def test_get_name_service_address_sc_encode_returns_empty_on_no_match(self):
        result = qn.GetNameServiceAddressSC.encode_fn()({"suinsName": None})
        assert isinstance(result, sui_prot.LookupNameResponse)
        assert result.record is None

    def test_get_name_service_names_sc_encode_maps_fields(self):
        raw = {
            "address": {
                "address": _ADDR,
                "defaultSuinsName": "example.sui",
            }
        }
        result = qn.GetNameServiceNamesSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ReverseLookupNameResponse)
        rec = result.record
        assert isinstance(rec, sui_prot.NameRecord)
        assert rec.name == "example.sui"
        assert rec.target_address == _ADDR

    def test_get_name_service_names_sc_encode_returns_empty_on_no_name(self):
        raw = {"address": {"address": _ADDR, "defaultSuinsName": None}}
        result = qn.GetNameServiceNamesSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ReverseLookupNameResponse)
        assert result.record is None

    def test_get_name_service_names_sc_encode_returns_empty_on_null_address(self):
        result = qn.GetNameServiceNamesSC.encode_fn()({"address": None})
        assert isinstance(result, sui_prot.ReverseLookupNameResponse)
        assert result.record is None

    def test_get_basic_current_epoch_info_sc_encode_maps_fields(self):
        raw = {
            "epoch": {
                "epochId": 42,
                "referenceGasPrice": "1000",
                "startTimestamp": "2024-01-01T00:00:00+00:00",
                "endTimestamp": "2024-01-02T00:00:00+00:00",
            }
        }
        result = qn.GetBasicCurrentEpochInfoSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.Epoch)
        assert result.epoch == 42
        assert result.reference_gas_price == 1000

    def test_get_basic_current_epoch_info_sc_encode_handles_missing_end(self):
        raw = {
            "epoch": {
                "epochId": 7,
                "referenceGasPrice": "750",
                "startTimestamp": "2024-06-01T00:00:00+00:00",
                "endTimestamp": None,
            }
        }
        result = qn.GetBasicCurrentEpochInfoSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.Epoch)
        assert result.epoch == 7
        assert result.reference_gas_price == 750
        assert result.end is None


# ---------------------------------------------------------------------------
# TestTransactionSCEncode — GetTransactionSC / GetTransactionsSC / GetTransactionKindSC
# ---------------------------------------------------------------------------

import base64


def _minimal_tx_dict(digest: str = "FakeDigest1111") -> dict:
    """Build a minimal but structurally complete GQL SC transaction dict.

    Keys mirror what _encode_executed_tx reads from a live GQL SC response:
    - transactionJson: proto-format JSON blob (camelCase); parsed via Transaction.from_dict()
    - transactionBcs: base64 raw BCS for the Transaction
    - signatures: list of {signatureBytes: base64} from the GQL query
    - effects: dict of typed GQL fields + proto JSON blobs read by _encode_executed_tx
      - effectsJson parsed via TransactionEffects.from_dict()
      - balanceChangesJson parsed via BalanceChange.from_dict() per element
      - checkpoint.sequenceNumber and timestamp are typed GQL fields (not in JSON blobs)
    """
    return {
        "transactionJson": {
            "digest": digest,
            "sender": _ADDR,
            "kind": {"programmableTransaction": {}},
            "gasPayment": {
                "objects": [{"objectId": "0x" + "c" * 64}],
                "price": "1000",
                "budget": "1000000",
            },
        },
        "transactionBcs": base64.b64encode(b"txbcsbytes").decode(),
        "signatures": [
            {"signatureBytes": base64.b64encode(b"fakesig").decode()}
        ],
        "effects": {
            "effectsJson": {
                "status": {"success": True},
                "epoch": "3",
                "gasUsed": {
                    "computationCost": "100",
                    "storageCost": "200",
                    "storageRebate": "50",
                    "nonRefundableStorageFee": "10",
                },
            },
            "balanceChangesJson": [
                {
                    "address": _ADDR,
                    "coinType": "0x2::sui::SUI",
                    "amount": "-1000",
                }
            ],
            "effectsBcs": base64.b64encode(b"effectsbcsbytes").decode(),
            "checkpoint": {"sequenceNumber": 42},
            "timestamp": "2024-01-15T12:00:00Z",
        },
    }


class TestTransactionSCEncode:
    """Verify encode_fn shapes for GetTransactionSC, GetTransactionsSC, GetTransactionKindSC."""

    # --- GetTransactionSC ---

    def test_get_transaction_sc_encode_fn_is_callable(self):
        assert callable(qn.GetTransactionSC.encode_fn())

    def test_get_transaction_sc_encode_null_transaction_returns_none(self):
        result = qn.GetTransactionSC.encode_fn()({"transaction": None})
        assert result is None

    def test_get_transaction_sc_encode_missing_digest_returns_none(self):
        result = qn.GetTransactionSC.encode_fn()({"transaction": {}})
        assert result is None

    def test_get_transaction_sc_encode_missing_key_returns_none(self):
        result = qn.GetTransactionSC.encode_fn()({})
        assert result is None

    def test_get_transaction_sc_encode_returns_executed_transaction(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ExecutedTransaction)

    def test_get_transaction_sc_encode_digest(self):
        raw = {"transaction": _minimal_tx_dict("MyDigestABC")}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.digest == "MyDigestABC"

    def test_get_transaction_sc_encode_sender(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.transaction.sender == _ADDR

    def test_get_transaction_sc_encode_signatures(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert len(result.signatures) == 1
        assert isinstance(result.signatures[0], sui_prot.UserSignature)
        assert result.signatures[0].bcs.value == b"fakesig"

    def test_get_transaction_sc_encode_transaction_bcs(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.transaction.bcs.value == b"txbcsbytes"

    def test_get_transaction_sc_encode_effects_bcs(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.effects.bcs.value == b"effectsbcsbytes"

    def test_get_transaction_sc_encode_effects_success(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.effects.status.success is True

    def test_get_transaction_sc_encode_effects_failure(self):
        tx = _minimal_tx_dict()
        tx["effects"]["effectsJson"]["status"] = {"success": False}
        result = qn.GetTransactionSC.encode_fn()({"transaction": tx})
        assert result.effects.status.success is False

    def test_get_transaction_sc_encode_gas_summary(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        gs = result.effects.gas_used
        assert isinstance(gs, sui_prot.GasCostSummary)
        assert gs.computation_cost == 100
        assert gs.storage_cost == 200
        assert gs.storage_rebate == 50
        assert gs.non_refundable_storage_fee == 10

    def test_get_transaction_sc_encode_checkpoint(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.checkpoint == 42

    def test_get_transaction_sc_encode_epoch(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.effects.epoch == 3

    def test_get_transaction_sc_encode_timestamp_parsed(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert isinstance(result.timestamp, datetime.datetime)

    def test_get_transaction_sc_encode_balance_changes(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert len(result.balance_changes) == 1
        bc = result.balance_changes[0]
        assert isinstance(bc, sui_prot.BalanceChange)
        assert bc.coin_type == "0x2::sui::SUI"
        assert bc.amount == "-1000"
        assert bc.address == _ADDR

    def test_get_transaction_sc_encode_gas_payment_fields(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        gp = result.transaction.gas_payment
        assert isinstance(gp, sui_prot.GasPayment)
        assert gp.price == 1000
        assert gp.budget == 1000000
        assert len(gp.objects) == 1
        assert gp.objects[0].object_id == "0x" + "c" * 64

    def test_get_transaction_sc_encode_kind_programmable(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        tk = result.transaction.kind
        assert isinstance(tk, sui_prot.TransactionKind)
        assert tk.programmable_transaction is not None

    def test_get_transaction_sc_encode_expiration_none(self):
        raw = {"transaction": _minimal_tx_dict()}
        result = qn.GetTransactionSC.encode_fn()(raw)
        assert result.transaction.expiration is None

    def test_get_transaction_sc_encode_expiration_epoch(self):
        tx = _minimal_tx_dict()
        tx["transactionJson"]["expiration"] = {"epoch": "99"}
        result = qn.GetTransactionSC.encode_fn()({"transaction": tx})
        exp = result.transaction.expiration
        assert exp is not None
        assert exp.epoch == 99

    # --- GetTransactionsSC ---

    def test_get_transactions_sc_encode_fn_is_callable(self):
        assert callable(qn.GetTransactionsSC.encode_fn())

    def test_get_transactions_sc_uses_correct_key(self):
        raw = {"transactions": [_minimal_tx_dict()]}
        result = qn.GetTransactionsSC.encode_fn()(raw)
        # "transactions" key is wrong — SC uses "multiGetTransactions"
        assert result == []

    def test_get_transactions_sc_correct_key_returns_list(self):
        raw = {"multiGetTransactions": [_minimal_tx_dict("D1"), _minimal_tx_dict("D2")]}
        result = qn.GetTransactionsSC.encode_fn()(raw)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_transactions_sc_returns_executed_transaction_items(self):
        raw = {"multiGetTransactions": [_minimal_tx_dict("D1")]}
        result = qn.GetTransactionsSC.encode_fn()(raw)
        assert isinstance(result[0], sui_prot.ExecutedTransaction)
        assert result[0].digest == "D1"

    def test_get_transactions_sc_none_slot_propagates(self):
        raw = {"multiGetTransactions": [_minimal_tx_dict("D1"), None, _minimal_tx_dict("D3")]}
        result = qn.GetTransactionsSC.encode_fn()(raw)
        assert len(result) == 3
        assert result[0].digest == "D1"
        assert result[1] is None
        assert result[2].digest == "D3"

    def test_get_transactions_sc_empty_list(self):
        raw = {"multiGetTransactions": []}
        result = qn.GetTransactionsSC.encode_fn()(raw)
        assert result == []

    def test_get_transactions_sc_missing_key_returns_empty(self):
        result = qn.GetTransactionsSC.encode_fn()({})
        assert result == []

    # --- GetTransactionKindSC ---

    def test_get_transaction_kind_sc_encode_fn_is_callable(self):
        assert callable(qn.GetTransactionKindSC.encode_fn())

    def test_get_transaction_kind_sc_null_transaction_returns_none(self):
        result = qn.GetTransactionKindSC.encode_fn()({"transaction": None})
        assert result is None

    def test_get_transaction_kind_sc_missing_key_returns_none(self):
        result = qn.GetTransactionKindSC.encode_fn()({})
        assert result is None

    def test_get_transaction_kind_sc_returns_transaction_kind(self):
        raw = {
            "transaction": {
                "kind": {
                    "tx_kind": "ProgrammableTransaction",
                    "inputs": {"nodes": []},
                    "commands": {"nodes": []},
                }
            }
        }
        result = qn.GetTransactionKindSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.TransactionKind)

    def test_get_transaction_kind_sc_programmable_transaction_populated(self):
        raw = {
            "transaction": {
                "kind": {
                    "tx_kind": "ProgrammableTransaction",
                    "inputs": {"nodes": []},
                    "commands": {"nodes": []},
                }
            }
        }
        result = qn.GetTransactionKindSC.encode_fn()(raw)
        assert result.programmable_transaction is not None
        assert isinstance(result.programmable_transaction, sui_prot.ProgrammableTransaction)

    def test_get_transaction_kind_sc_empty_kind_returns_empty_proto(self):
        raw = {"transaction": {"kind": {}}}
        result = qn.GetTransactionKindSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.TransactionKind)

    def test_get_transaction_kind_sc_change_epoch_kind(self):
        raw = {
            "transaction": {
                "kind": {
                    "tx_kind": "ChangeEpochTransaction",
                    "epoch": {"epochId": 5},
                    "protocolConfigs": {"protocolVersion": 3},
                    "storageCharge": "100",
                    "computationCharge": "200",
                    "storageRebate": "50",
                    "nonRefundableStorageFee": "0",
                    "epochStartTimestamp": None,
                }
            }
        }
        result = qn.GetTransactionKindSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.TransactionKind)
        assert result.change_epoch is not None
        assert result.change_epoch.epoch == 5
