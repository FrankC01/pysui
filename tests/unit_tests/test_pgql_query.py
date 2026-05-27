#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.sui.sui_pgql.pgql_query — all offline, no live node required.

Tests cover:
  - Constructor attribute storage
  - encode_fn() static method wiring to the correct result type
  - Deprecation warnings (DryRunTransaction, GetAllCoinBalances)
  - PGQL_NoOp short-circuit when a paging cursor is exhausted
"""

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as pt

# Reusable constants
_ADDR = "0x" + "a" * 64
_ADDR2 = "0x" + "b" * 64
_SUI_COIN = "0x2::coin::Coin<0x2::sui::SUI>"


# ---------------------------------------------------------------------------
# TestConstruction — __init__ stores args correctly
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_get_coin_metadata_default_coin_type(self):
        obj = qn.GetCoinMetaDataSC()
        assert obj.coin_type == "0x2::sui::SUI"

    def test_get_coin_metadata_custom_coin_type(self):
        obj = qn.GetCoinMetaDataSC(coin_type="0x2::usdc::USDC")
        assert obj.coin_type == "0x2::usdc::USDC"

    def test_get_epoch_defaults(self):
        obj = qn.GetEpochSC()
        assert obj.epoch_id is None

    def test_get_epoch_with_id(self):
        obj = qn.GetEpochSC(epoch_id=42)
        assert obj.epoch_id == 42

    def test_get_package_versions_stores_address(self):
        obj = qn.GetPackageVersionsSC(package_address="0x2")
        assert obj.package_address == "0x2"

    def test_get_package_versions_with_next_page(self):
        obj = qn.GetPackageVersionsSC(package_address="0x2", next_page_token=b"tok1")
        assert obj.next_page_token == b"tok1"

    def test_get_basic_current_epoch_info_constructs(self):
        obj = qn.GetBasicCurrentEpochInfoSC()
        assert isinstance(obj, qn.GetBasicCurrentEpochInfoSC)

    def test_get_name_service_address_stores_name(self):
        obj = qn.GetNameServiceAddressSC(name="example.sui")
        assert obj.name == "example.sui"

    def test_get_name_service_names_stores_owner(self):
        obj = qn.GetNameServiceNamesSC(owner=_ADDR)
        assert obj.owner == _ADDR



# ---------------------------------------------------------------------------
# TestNoopShortCircuit — as_document_node returns PGQL_NoOp before touching schema
# ---------------------------------------------------------------------------

class TestNoopShortCircuit:
    """PagingCursor-based classes short-circuit to PGQL_NoOp when hasNextPage is False.

    next_page_token-based classes (added in 0.99.0) use bytes | None — there is no
    exhausted-cursor concept; None simply means no more pages.
    """

    def test_get_package_versions_no_token_is_none(self):
        obj = qn.GetPackageVersionsSC(package_address="0x2")
        assert obj.next_page_token is None

# ---------------------------------------------------------------------------
# TestSCSiblings — encode_fn() output shapes for SC sibling classes
# ---------------------------------------------------------------------------

import datetime
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_grpc.pgrpc_requests as _pgrpc_rn
import pysui.sui.sui_common.shared_types as shared_types


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
                "protocolConfigs": {"protocolVersion": 99},
                "first_checkpoint": {"nodes": [{"sequenceNumber": "1000"}]},
                "last_checkpoint": {"nodes": [{"sequenceNumber": "1999"}]},
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
        assert ep.protocol_config is not None
        assert ep.protocol_config.protocol_version == 99
        assert ep.first_checkpoint == 1000
        assert ep.last_checkpoint == 1999
        assert ep.committee is not None

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
        assert result.epoch.system_state is None
        assert result.epoch.protocol_config is None
        assert result.epoch.first_checkpoint is None
        assert result.epoch.last_checkpoint is None

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


# ---------------------------------------------------------------------------
# TestObjectSCSiblings — encode_fn() shapes for object-oriented SC classes
# ---------------------------------------------------------------------------


def _min_obj(object_id: str = _ADDR, version: int = 5, digest: str = "SomeDigest") -> dict:
    """Minimal GQL object dict consumable by _encode_object_from_raw."""
    return {"object_id": object_id, "version": version, "object_digest": digest}


class TestObjectSCSiblings:
    """encode_fn output shapes for GetObjectSC, GetCoinsSC, GetGasSC, etc."""

    # --- GetObjectSC ---

    def test_get_object_sc_encode_fn_is_callable(self):
        assert callable(qn.GetObjectSC.encode_fn())

    def test_get_object_sc_encode_returns_object_with_fields(self):
        raw = {"object": _min_obj()}
        result = qn.GetObjectSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.Object)
        assert result.object_id == _ADDR
        assert result.version == 5
        assert result.digest == "SomeDigest"

    def test_get_object_sc_encode_empty_object_returns_empty(self):
        result = qn.GetObjectSC.encode_fn()({"object": {}})
        assert isinstance(result, sui_prot.Object)

    def test_get_object_sc_encode_missing_key_returns_empty(self):
        result = qn.GetObjectSC.encode_fn()({})
        assert isinstance(result, sui_prot.Object)

    # --- GetPastObjectSC ---

    def test_get_past_object_sc_encode_returns_object_with_fields(self):
        raw = {"object": _min_obj(_ADDR2, version=3, digest="PastDigest")}
        result = qn.GetPastObjectSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.Object)
        assert result.object_id == _ADDR2
        assert result.version == 3
        assert result.digest == "PastDigest"

    # --- GetCoinsSC ---

    def test_get_coins_sc_encode_fn_is_callable(self):
        assert callable(qn.GetCoinsSC.encode_fn())

    def test_get_coins_sc_encode_empty_list_no_next_page(self):
        raw = {"objects": {"cursor": {"hasNextPage": False, "endCursor": None}, "objects_data": []}}
        result = qn.GetCoinsSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ListOwnedObjectsResponse)
        assert result.objects == []
        assert result.next_page_token is None

    def test_get_coins_sc_encode_with_objects_and_next_page(self):
        raw = {
            "objects": {
                "cursor": {"hasNextPage": True, "endCursor": "cursorABC"},
                "objects_data": [_min_obj()],
            }
        }
        result = qn.GetCoinsSC.encode_fn()(raw)
        assert len(result.objects) == 1
        assert result.next_page_token == b"cursorABC"

    # --- GetGasSC ---

    def test_get_gas_sc_encode_fn_is_callable(self):
        assert callable(qn.GetGasSC.encode_fn())

    def test_get_gas_sc_encode_empty_list_no_next_page(self):
        raw = {"objects": {"cursor": {"hasNextPage": False, "endCursor": None}, "objects_data": []}}
        result = qn.GetGasSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ListOwnedObjectsResponse)
        assert result.objects == []
        assert result.next_page_token is None

    def test_get_gas_sc_encode_with_paging(self):
        raw = {
            "objects": {
                "cursor": {"hasNextPage": True, "endCursor": "gasPage2"},
                "objects_data": [_min_obj(_ADDR2, version=7, digest="GasDig")],
            }
        }
        result = qn.GetGasSC.encode_fn()(raw)
        assert len(result.objects) == 1
        assert result.next_page_token == b"gasPage2"

    # --- GetObjectsOwnedByAddressSC ---

    def test_get_objects_owned_by_address_sc_encode_fn_is_callable(self):
        assert callable(qn.GetObjectsOwnedByAddressSC.encode_fn())

    def test_get_objects_owned_by_address_sc_filters_coin_reservation(self):
        raw = {
            "objects": {
                "cursor": {"hasNextPage": False, "endCursor": None},
                "objects_data": [
                    _min_obj(_ADDR, version=1, digest=None),
                    _min_obj(_ADDR2, version=0, digest=None),  # version==0 → coin reservation
                ],
            }
        }
        result = qn.GetObjectsOwnedByAddressSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.ListOwnedObjectsResponse)
        assert len(result.objects) == 1
        assert result.objects[0].object_id == _ADDR

    def test_get_objects_owned_by_address_sc_no_next_page(self):
        raw = {"objects": {"cursor": {"hasNextPage": False, "endCursor": None}, "objects_data": []}}
        result = qn.GetObjectsOwnedByAddressSC.encode_fn()(raw)
        assert result.next_page_token is None

    def test_get_objects_owned_by_address_sc_with_next_page(self):
        raw = {"objects": {"cursor": {"hasNextPage": True, "endCursor": "ownPage"}, "objects_data": []}}
        result = qn.GetObjectsOwnedByAddressSC.encode_fn()(raw)
        assert result.next_page_token == b"ownPage"

    # --- GetMultipleObjectsSC ---

    def test_get_multiple_objects_sc_encode_fn_is_callable(self):
        assert callable(qn.GetMultipleObjectsSC.encode_fn())

    def test_get_multiple_objects_sc_encode_returns_batch_response(self):
        raw = {
            "multiGetObjects": [
                _min_obj(_ADDR, version=1, digest="d1"),
                _min_obj(_ADDR2, version=2, digest="d2"),
            ]
        }
        result = qn.GetMultipleObjectsSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.BatchGetObjectsResponse)
        assert len(result.objects) == 2
        assert result.objects[0].object.object_id == _ADDR
        assert result.objects[1].object.object_id == _ADDR2

    def test_get_multiple_objects_sc_encode_empty_list(self):
        result = qn.GetMultipleObjectsSC.encode_fn()({"multiGetObjects": []})
        assert isinstance(result, sui_prot.BatchGetObjectsResponse)
        assert result.objects == []

    # --- GetMultipleVersionedObjectsSC ---

    def test_get_multiple_versioned_objects_sc_encode_returns_batch_response(self):
        raw = {"multiGetObjects": [_min_obj(_ADDR, version=3, digest="v3dig")]}
        result = qn.GetMultipleVersionedObjectsSC.encode_fn()(raw)
        assert isinstance(result, sui_prot.BatchGetObjectsResponse)
        assert len(result.objects) == 1
        assert result.objects[0].object.version == 3

    # --- GetMultipleObjectsSummarySC ---

    def test_get_multiple_objects_summary_sc_encode_fn_is_callable(self):
        assert callable(qn.GetMultipleObjectsSummarySC.encode_fn())

    def test_get_multiple_objects_summary_sc_address_owner(self):
        raw = {
            "multiGetObjects": [
                {
                    "object_id": _ADDR,
                    "version": 10,
                    "object_digest": "dg1",
                    "owner": {"obj_owner_kind": "AddressOwner", "address_id": {"address": _ADDR2}},
                }
            ]
        }
        result = qn.GetMultipleObjectsSummarySC.encode_fn()(raw)
        assert isinstance(result, shared_types.ObjectSummaryList)
        assert len(result.objects) == 1
        obj = result.objects[0]
        assert obj.objectId == _ADDR
        assert obj.version == "10"
        assert obj.owner == _ADDR2
        assert obj.initialSharedVersion is None

    def test_get_multiple_objects_summary_sc_shared_owner(self):
        raw = {
            "multiGetObjects": [
                {
                    "object_id": _ADDR2,
                    "version": 5,
                    "object_digest": "dg2",
                    "owner": {"obj_owner_kind": "Shared", "initial_version": 42},
                }
            ]
        }
        result = qn.GetMultipleObjectsSummarySC.encode_fn()(raw)
        assert len(result.objects) == 1
        obj = result.objects[0]
        assert obj.owner is None
        assert obj.initialSharedVersion == "42"

    def test_get_multiple_objects_summary_sc_skips_none_entries(self):
        raw = {"multiGetObjects": [None]}
        result = qn.GetMultipleObjectsSummarySC.encode_fn()(raw)
        assert result.objects == []

    # --- GetLatestSuiSystemStateSC ---

    def test_get_latest_sui_system_state_sc_encode_fn_is_callable(self):
        assert callable(qn.GetLatestSuiSystemStateSC.encode_fn())

    def test_get_latest_sui_system_state_sc_missing_epoch_returns_empty(self):
        result = qn.GetLatestSuiSystemStateSC.encode_fn()({})
        assert isinstance(result, sui_prot.SystemState)

    def test_get_latest_sui_system_state_sc_no_bcs_returns_empty(self):
        result = qn.GetLatestSuiSystemStateSC.encode_fn()({"epoch": {"systemState": {}}})
        assert isinstance(result, sui_prot.SystemState)

    # --- GetCurrentValidatorsSC ---

    def test_get_current_validators_sc_encode_fn_is_callable(self):
        assert callable(qn.GetCurrentValidatorsSC.encode_fn())

    def test_get_current_validators_sc_empty_nodes_returns_empty_list(self):
        raw = {
            "epoch": {
                "validatorSet": {
                    "activeValidators": {
                        "cursor": {"hasNextPage": False, "endCursor": None},
                        "nodes": [],
                    }
                }
            }
        }
        result = qn.GetCurrentValidatorsSC.encode_fn()(raw)
        assert result.validators == []
        assert result.next_page_token is None

    def test_get_current_validators_sc_sets_next_page_token(self):
        raw = {
            "epoch": {
                "validatorSet": {
                    "activeValidators": {
                        "cursor": {"hasNextPage": True, "endCursor": "validPage2"},
                        "nodes": [],
                    }
                }
            }
        }
        result = qn.GetCurrentValidatorsSC.encode_fn()(raw)
        assert result.next_page_token == b"validPage2"

    def test_get_current_validators_sc_missing_epoch_returns_empty(self):
        result = qn.GetCurrentValidatorsSC.encode_fn()({})
        assert result.validators == []
        assert result.next_page_token is None
