#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.sui.sui_pgql.pgql_types — all offline, no live node required."""

import pytest
import pysui.sui.sui_pgql.pgql_types as pt
from helpers import (
    mock_paging_cursor,
    mock_owner_address,
    mock_owner_shared,
    mock_owner_object,
    mock_owner_immutable,
    mock_coin_object,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cursor_dict(*, has_next: bool = False, end_cursor: str = None) -> dict:
    return {"hasNextPage": has_next, "endCursor": end_cursor}


# ---------------------------------------------------------------------------
# TestNoop
# ---------------------------------------------------------------------------

class TestNoop:
    def test_noop_from_query_returns_noop(self):
        result = pt.NoopGQL.from_query()
        assert isinstance(result, pt.NoopGQL)
        assert result.data == []
        assert result.next_cursor.hasNextPage is False

    def test_error_gql_from_query(self):
        result = pt.ErrorGQL.from_query(errors=["something went wrong"])
        assert isinstance(result, pt.ErrorGQL)
        assert result.errors == ["something went wrong"]
        assert result.data == []

    def test_noop_next_cursor_defaults(self):
        result = pt.NoopGQL.from_query()
        assert result.next_cursor.endCursor is None or result.next_cursor.endCursor == ""

    def test_error_gql_empty_errors(self):
        result = pt.ErrorGQL.from_query(errors=[])
        assert isinstance(result, pt.ErrorGQL)
        assert result.errors == []


# ---------------------------------------------------------------------------
# TestSuiCoinObjectGQL
# ---------------------------------------------------------------------------

class TestSuiCoinObjectGQL:
    def _make(self, owner: dict) -> dict:
        return mock_coin_object(owner=owner)

    def test_address_owner(self):
        data = self._make(mock_owner_address("0xabc"))
        result = pt.SuiCoinObjectGQL.from_query(data)
        assert isinstance(result, pt.SuiCoinObjectGQL)
        assert result.coin_object_id == "0xcoin"
        assert result.balance == "1000000000"
        assert isinstance(result.object_owner, pt.SuiObjectOwnedAddress)
        assert result.object_owner.address_id == "0xabc"

    def test_shared_owner(self):
        data = self._make(mock_owner_shared())
        result = pt.SuiCoinObjectGQL.from_query(data)
        assert isinstance(result.object_owner, pt.SuiObjectOwnedShared)

    def test_object_owner(self):
        data = self._make(mock_owner_object("0xparent"))
        result = pt.SuiCoinObjectGQL.from_query(data)
        assert isinstance(result.object_owner, pt.SuiObjectOwnedParent)
        assert result.object_owner.parent_id == "0xparent"

    def test_immutable_owner(self):
        data = self._make(mock_owner_immutable())
        result = pt.SuiCoinObjectGQL.from_query(data)
        assert isinstance(result.object_owner, pt.SuiObjectOwnedImmutable)

    def test_object_id_property(self):
        data = self._make(mock_owner_address())
        result = pt.SuiCoinObjectGQL.from_query(data)
        assert result.object_id == result.coin_object_id

    def test_version_and_digest(self):
        data = mock_coin_object(version=42, object_digest="ddd", owner=mock_owner_address())
        result = pt.SuiCoinObjectGQL.from_query(data)
        assert result.version == 42
        assert result.object_digest == "ddd"


# ---------------------------------------------------------------------------
# TestSuiCoinCollections
# ---------------------------------------------------------------------------

class TestSuiCoinCollections:
    def test_sui_coin_from_objects_gql(self):
        node = {
            "asMoveObject": mock_coin_object(owner=mock_owner_address("0xowner"))
        }
        in_data = {"multiGetObjects": [node]}
        result = pt.SuiCoinFromObjectsGQL.from_query(in_data)
        assert isinstance(result, pt.SuiCoinFromObjectsGQL)
        assert len(result.data) == 1
        assert result.data[0].coin_object_id == "0xcoin"

    def test_sui_coin_from_objects_empty_returns_noop(self):
        result = pt.SuiCoinFromObjectsGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)

    def test_sui_coin_objects_gql(self):
        coin = mock_coin_object(owner=mock_owner_address())
        in_data = {
            "qres": {
                "coins": {
                    "cursor": _cursor_dict(has_next=True, end_cursor="tok1"),
                    "coin_objects": [coin],
                }
            }
        }
        result = pt.SuiCoinObjectsGQL.from_query(in_data)
        assert isinstance(result, pt.SuiCoinObjectsGQL)
        assert len(result.data) == 1
        assert result.next_cursor.hasNextPage is True
        assert result.next_cursor.endCursor == "tok1"

    def test_sui_coin_object_summary_gql(self):
        in_data = {
            "id": "someid",
            "coin_object_id": "0xcoin",
            "object_digest": "dgst",
            "version": 5,
            "balance": "500",
        }
        result = pt.SuiCoinObjectSummaryGQL.from_query(in_data)
        assert isinstance(result, pt.SuiCoinObjectSummaryGQL)
        assert result.coin_object_id == "0xcoin"
        assert result.version == 5
        assert result.object_id == "0xcoin"

    def test_sui_coin_object_summary_object_id_property(self):
        in_data = {
            "id": "x",
            "coin_object_id": "0xtest",
            "object_digest": "d",
            "version": 1,
            "balance": "100",
        }
        result = pt.SuiCoinObjectSummaryGQL.from_query(in_data)
        assert result.object_id == "0xtest"


# ---------------------------------------------------------------------------
# TestEpochTypes
# ---------------------------------------------------------------------------

class TestEpochTypes:
    def test_basic_current_epoch_info(self):
        in_data = {
            "epoch": {
                "epochId": 10,
                "referenceGasPrice": "750",
                "startTimestamp": "2024-01-01T00:00:00Z",
                "endTimestamp": None,
            }
        }
        result = pt.BasicCurrentEpochInfoGQL.from_query(in_data)
        assert isinstance(result, pt.BasicCurrentEpochInfoGQL)
        assert result.epoch_id == 10
        assert result.reference_gas_price == 750
        assert result.start_timestamp == "2024-01-01T00:00:00Z"

    def test_basic_current_epoch_info_empty_returns_noop(self):
        result = pt.BasicCurrentEpochInfoGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)

    def test_epoch_gql_full(self):
        in_data = {
            "epoch": {
                "epochId": 42,
                "startTimestamp": "2024-06-01T00:00:00Z",
                "endTimestamp": "2024-06-02T00:00:00Z",
                "referenceGasPrice": "1000",
                "totalCheckpoints": 100,
                "totalTransactions": 5000,
                "totalGasFees": "9999",
                "totalStakeRewards": "12345",
            }
        }
        result = pt.EpochGQL.from_query(in_data)
        assert isinstance(result, pt.EpochGQL)
        assert result.epoch_id == 42
        assert result.total_checkpoints == 100
        assert result.total_transactions == 5000
        assert result.total_gas_fees == "9999"

    def test_epoch_gql_empty_returns_noop(self):
        result = pt.EpochGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)

    def test_epoch_gql_optional_fields_none(self):
        in_data = {
            "epoch": {
                "epochId": 1,
                "startTimestamp": "2024-01-01T00:00:00Z",
            }
        }
        result = pt.EpochGQL.from_query(in_data)
        assert isinstance(result, pt.EpochGQL)
        assert result.end_timestamp is None
        assert result.total_checkpoints is None

    def test_epoch_gql_current_epoch_no_end(self):
        in_data = {
            "epoch": {
                "epochId": 99,
                "startTimestamp": "2024-12-01T00:00:00Z",
                "endTimestamp": None,
                "referenceGasPrice": "800",
            }
        }
        result = pt.EpochGQL.from_query(in_data)
        assert result.end_timestamp is None
        assert result.reference_gas_price == "800"


# ---------------------------------------------------------------------------
# TestCheckpointTypes
# ---------------------------------------------------------------------------

class TestCheckpointTypes:
    def _make_checkpoint_dict(self, seq: int = 10) -> dict:
        return {
            "digest": "cp_digest",
            "sequence_number": seq,
            "timestamp": "2024-01-01T00:00:00Z",
            "networkTotalTransactions": 1000,
            "transaction_blocks": {
                "cursor": {"hasNextPage": False, "endCursor": None},
                "tx_digests": [],
            },
            "previous_checkpoint_digest": None,
        }

    def test_checkpoint_gql_from_query(self):
        in_data = {"checkpoint": self._make_checkpoint_dict(5)}
        result = pt.CheckpointGQL.from_query(in_data)
        assert isinstance(result, pt.CheckpointGQL)
        assert result.sequence_number == 5
        assert result.digest == "cp_digest"

    def test_checkpoint_gql_from_query_no_wrapper(self):
        # from_query also accepts unwrapped dict
        result = pt.CheckpointGQL.from_query(self._make_checkpoint_dict(7))
        assert isinstance(result, pt.CheckpointGQL)
        assert result.sequence_number == 7

    def test_checkpoint_gql_from_last_checkpoint(self):
        in_data = {
            "checkpoints": {
                "nodes": [self._make_checkpoint_dict(99)]
            }
        }
        result = pt.CheckpointGQL.from_last_checkpoint(in_data)
        assert isinstance(result, pt.CheckpointGQL)
        assert result.sequence_number == 99

    def test_checkpoints_gql_from_query(self):
        in_data = {
            "checkpoints": {
                "cursor": _cursor_dict(has_next=False),
                "checkpoints": [self._make_checkpoint_dict(1), self._make_checkpoint_dict(2)],
            }
        }
        result = pt.CheckpointsGQL.from_query(in_data)
        assert isinstance(result, pt.CheckpointsGQL)
        assert len(result.data) == 2
        assert result.next_cursor.hasNextPage is False

    def test_checkpoints_gql_with_next_page(self):
        in_data = {
            "checkpoints": {
                "cursor": _cursor_dict(has_next=True, end_cursor="next_tok"),
                "checkpoints": [self._make_checkpoint_dict(3)],
            }
        }
        result = pt.CheckpointsGQL.from_query(in_data)
        assert result.next_cursor.hasNextPage is True
        assert result.next_cursor.endCursor == "next_tok"

    def test_checkpoint_transaction_blocks_parsed(self):
        cp = self._make_checkpoint_dict()
        result = pt.CheckpointGQL.from_query({"checkpoint": cp})
        assert hasattr(result, "transaction_blocks")


# ---------------------------------------------------------------------------
# TestBalanceTypes
# ---------------------------------------------------------------------------

class TestBalanceTypes:
    def _make_balance_dict(self) -> dict:
        return {
            "coinType": "0x2::sui::SUI",
            "addressBalance": "500",
            "coinBalance": "400",
            "totalBalance": "900",
        }

    def test_balance_gql_from_query(self):
        result = pt.BalanceGQL.from_query(self._make_balance_dict())
        assert isinstance(result, pt.BalanceGQL)
        assert result.address_balance == 500
        assert result.coin_balance == 400
        assert result.total_balance == 900

    def test_balance_gql_coin_type(self):
        result = pt.BalanceGQL.from_query(self._make_balance_dict())
        assert result.coin_type == "0x2::sui::SUI"

    def test_address_balance_gql_from_query(self):
        in_data = {
            "address": self._make_balance_dict()
        }
        result = pt.AddressBalanceGQL.from_query(in_data)
        assert isinstance(result, pt.AddressBalanceGQL)
        assert isinstance(result.balance, pt.BalanceGQL)
        assert result.balance.total_balance == 900

    def test_balances_gql_from_query(self):
        in_data = {
            "owner_address": "0xowner",
            "balances": {
                "cursor": _cursor_dict(),
                "type_balances": [self._make_balance_dict()],
            }
        }
        result = pt.BalancesGQL.from_query(in_data)
        assert isinstance(result, pt.BalancesGQL)
        assert result.owner_address == "0xowner"
        assert len(result.data) == 1

    def test_balances_gql_paging(self):
        in_data = {
            "owner_address": "0xowner",
            "balances": {
                "cursor": _cursor_dict(has_next=True, end_cursor="tok"),
                "type_balances": [],
            }
        }
        result = pt.BalancesGQL.from_query(in_data)
        assert result.next_cursor.hasNextPage is True


# ---------------------------------------------------------------------------
# TestCoinMetadata
# ---------------------------------------------------------------------------

class TestCoinMetadata:
    def test_coin_metadata_from_query(self):
        in_data = {
            "decimals": 9,
            "name": "Sui",
            "symbol": "SUI",
            "description": "The Sui token",
            "supply": {"value": "10000000000000000"},
            "address": "0x2::sui::SUI",
            "iconUrl": None,
        }
        result = pt.SuiCoinMetadataGQL.from_query(in_data)
        assert isinstance(result, pt.SuiCoinMetadataGQL)
        assert result.decimals == 9
        assert result.symbol == "SUI"

    def test_coin_metadata_optional_fields_none(self):
        in_data = {"decimals": 6, "name": "USDC", "symbol": "USDC"}
        result = pt.SuiCoinMetadataGQL.from_query(in_data)
        assert result.icon_url is None
        assert result.supply is None

    def test_coin_metadata_supply_flattened(self):
        in_data = {
            "decimals": 9,
            "name": "Sui",
            "symbol": "SUI",
            "supply": {"value": "999"},
        }
        result = pt.SuiCoinMetadataGQL.from_query(in_data)
        # _fast_flat flattens supply.value → value; supply field itself is gone
        assert result.supply is None or result.supply == "999"


# ---------------------------------------------------------------------------
# TestTransactionTypes
# ---------------------------------------------------------------------------

class TestTransactionTypes:
    def test_dry_run_result_gql_empty_returns_noop(self):
        result = pt.DryRunResultGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)

    def test_dry_run_result_gql_no_dry_run_key_returns_noop(self):
        result = pt.DryRunResultGQL.from_query({"other": "data"})
        assert isinstance(result, pt.NoopGQL)

    def test_dry_run_result_gql_with_data(self):
        in_data = {
            "dryRun": {
                "results": [{"returnValues": []}],
                "transactionBlock": {
                    "status": "success",
                    "gasEffects": {},
                    "balanceChanges": {},
                    "objectChanges": {"nodes": []},
                },
            }
        }
        result = pt.DryRunResultGQL.from_query(in_data)
        assert isinstance(result, pt.DryRunResultGQL)
        assert result.results == [{"returnValues": []}]

    def test_simulate_result_gql_is_dry_run_result_gql(self):
        assert pt.SimulateResultGQL is pt.DryRunResultGQL

    def test_execution_result_gql_empty_returns_noop(self):
        result = pt.ExecutionResultGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)

    def test_transaction_result_gql_empty_returns_noop(self):
        result = pt.TransactionResultGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)


# ---------------------------------------------------------------------------
# TestPackageVersions
# ---------------------------------------------------------------------------

class TestPackageVersions:
    def test_package_version_gql_fields(self):
        pv = pt.PackageVersionGQL(package_id="0x2", version=3, digest="dgst")
        assert pv.package_id == "0x2"
        assert pv.version == 3
        assert pv.digest == "dgst"

    def test_package_version_gql_digest_optional(self):
        pv = pt.PackageVersionGQL(package_id="0x2", version=1)
        assert pv.digest is None

    def test_package_versions_gql_from_query(self):
        in_data = {
            "packageVersions": {
                "cursor": _cursor_dict(has_next=False),
                "versions": [
                    {"address": "0x2", "version": 1, "digest": "d1"},
                    {"address": "0x2", "version": 2, "digest": "d2"},
                ],
            }
        }
        result = pt.PackageVersionsGQL.from_query(in_data)
        assert isinstance(result, pt.PackageVersionsGQL)
        assert len(result.versions) == 2
        assert result.versions[0].package_id == "0x2"
        assert result.versions[1].version == 2

    def test_package_versions_gql_empty_returns_noop(self):
        result = pt.PackageVersionsGQL.from_query({})
        assert isinstance(result, pt.NoopGQL)

    def test_package_versions_gql_with_next_cursor(self):
        in_data = {
            "packageVersions": {
                "cursor": _cursor_dict(has_next=True, end_cursor="tok"),
                "versions": [],
            }
        }
        result = pt.PackageVersionsGQL.from_query(in_data)
        assert isinstance(result, pt.PackageVersionsGQL)
        assert result.next_cursor.hasNextPage is True


# ---------------------------------------------------------------------------
# TestReferenceGasPrice
# ---------------------------------------------------------------------------

class TestReferenceGasPrice:
    def test_reference_gas_price_from_query(self):
        in_data = {"epoch": {"referenceGasPrice": "750"}}
        result = pt.ReferenceGasPriceGQL.from_query(in_data)
        assert isinstance(result, pt.ReferenceGasPriceGQL)
        assert result.reference_gas_price == "750"

    def test_reference_gas_price_passthrough(self):
        # Also accepts unwrapped dict (pop falls back to in_data itself)
        in_data = {"referenceGasPrice": "1000"}
        result = pt.ReferenceGasPriceGQL.from_query(in_data)
        assert isinstance(result, pt.ReferenceGasPriceGQL)
        assert result.reference_gas_price == "1000"

    def test_reference_gas_price_type_is_str(self):
        in_data = {"epoch": {"referenceGasPrice": "999"}}
        result = pt.ReferenceGasPriceGQL.from_query(in_data)
        assert isinstance(result.reference_gas_price, str)
