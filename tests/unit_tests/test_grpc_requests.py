#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for pysui.sui.sui_grpc.pgrpc_requests — all offline, no live node required.

Tests cover:
  - Constructor attribute storage
  - Service type assignment (LEDGER, STATE, TRANSACTION, MOVEPACKAGE, SUBSCRIPTION, SIGNATURE, NAMESERVICE)
  - Subclass/alias relationships
  - RESULT_TYPE declarations
  - Input validation (GetMultipleObjects >50 limit)
  - Default coin types for GetCoins and GetGas
"""

import pytest

import pysui.sui.sui_grpc.pgrpc_requests as gr
import pysui.sui.sui_grpc.pgrpc_absreq as absreq
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.shared_types as shared_types


# ---------------------------------------------------------------------------
# TestCheckpointRequests
# ---------------------------------------------------------------------------

class TestCheckpointRequests:
    def test_get_checkpoint_default_constructs(self):
        obj = gr.GetCheckpoint()
        assert obj.sequence is None
        assert obj.digest is None
        assert obj.service == absreq.Service.LEDGER

    def test_get_checkpoint_with_sequence(self):
        obj = gr.GetCheckpoint(sequence=42)
        assert obj.sequence == 42
        assert obj.digest is None

    def test_get_checkpoint_with_digest(self):
        obj = gr.GetCheckpoint(digest="abc123")
        assert obj.digest == "abc123"
        assert obj.sequence is None

    def test_get_latest_checkpoint_is_get_checkpoint(self):
        assert issubclass(gr.GetLatestCheckpoint, gr.GetCheckpoint)

    def test_get_latest_checkpoint_no_args(self):
        obj = gr.GetLatestCheckpoint()
        assert obj.sequence is None
        assert obj.digest is None
        assert obj.service == absreq.Service.LEDGER

    def test_get_checkpoint_by_sequence_stores_number(self):
        obj = gr.GetCheckpointBySequence(sequence_number=99)
        assert obj.sequence == 99
        assert obj.service == absreq.Service.LEDGER

    def test_get_checkpoint_by_digest_stores_digest(self):
        obj = gr.GetCheckpointByDigest(digest="deadbeef")
        assert obj.digest == "deadbeef"
        assert obj.service == absreq.Service.LEDGER

    def test_get_checkpoint_result_type(self):
        assert gr.GetCheckpoint.RESULT_TYPE is sui_prot.GetCheckpointResponse


# ---------------------------------------------------------------------------
# TestEpochRequests
# ---------------------------------------------------------------------------

class TestEpochRequests:
    def test_get_epoch_default_constructs(self):
        obj = gr.GetEpoch()
        assert obj.epoch_number is None
        assert obj.service == absreq.Service.LEDGER

    def test_get_epoch_with_number(self):
        obj = gr.GetEpoch(epoch_number=10)
        assert obj.epoch_number == 10

    def test_get_latest_sui_system_state_is_get_epoch(self):
        assert issubclass(gr.GetLatestSuiSystemState, gr.GetEpoch)

    def test_get_latest_sui_system_state_service(self):
        obj = gr.GetLatestSuiSystemState()
        assert obj.service == absreq.Service.LEDGER

    def test_get_current_validators_is_get_epoch(self):
        assert issubclass(gr.GetCurrentValidators, gr.GetEpoch)

    def test_get_current_validators_service(self):
        obj = gr.GetCurrentValidators()
        assert obj.service == absreq.Service.LEDGER


# ---------------------------------------------------------------------------
# TestObjectRequests
# ---------------------------------------------------------------------------

class TestObjectRequests:
    _OID = "0xabcdef"
    _OID2 = "0x123456"

    def test_get_object_stores_id(self):
        obj = gr.GetObject(object_id=self._OID)
        assert obj.object_id == self._OID
        assert obj.service == absreq.Service.LEDGER

    def test_get_object_default_field_mask(self):
        obj = gr.GetObject(object_id=self._OID)
        assert obj.field_mask is not None

    def test_get_object_custom_field_mask(self):
        obj = gr.GetObject(object_id=self._OID, field_mask=["version"])
        assert obj.field_mask is not None

    def test_get_past_object_stores_id_and_version(self):
        obj = gr.GetPastObject(object_id=self._OID, version=5)
        assert obj.object_id == self._OID
        assert obj.version == 5
        assert obj.service == absreq.Service.LEDGER

    def test_get_multiple_objects_stores_ids(self):
        obj = gr.GetMultipleObjects(object_ids=[self._OID, self._OID2])
        assert len(obj.objects) == 2
        assert obj.service == absreq.Service.LEDGER

    def test_get_multiple_objects_over_50_raises(self):
        with pytest.raises(ValueError, match="Max object ids 50"):
            gr.GetMultipleObjects(object_ids=[f"0x{i:04x}" for i in range(51)])

    def test_get_multiple_past_objects_over_50_raises(self):
        entries = [{"objectId": f"0x{i:04x}", "version": i} for i in range(51)]
        with pytest.raises(ValueError, match="Max object ids 50"):
            gr.GetMultiplePastObjects(for_versions=entries)

    def test_get_service_info_service(self):
        obj = gr.GetServiceInfo()
        assert obj.service == absreq.Service.LEDGER


# ---------------------------------------------------------------------------
# TestOwnedObjectRequests
# ---------------------------------------------------------------------------

class TestOwnedObjectRequests:
    _ADDR = "0xowner"
    _SUI_COIN = "0x2::coin::Coin<0x2::sui::SUI>"

    def test_get_objects_owned_by_address_stores_owner(self):
        obj = gr.GetObjectsOwnedByAddress(owner=self._ADDR)
        assert obj.owner == self._ADDR
        assert obj.service == absreq.Service.STATE

    def test_get_objects_owned_optional_type(self):
        obj = gr.GetObjectsOwnedByAddress(owner=self._ADDR, object_type="0x2::token::T")
        assert obj.object_type == "0x2::token::T"

    def test_get_staked_is_owned_objects(self):
        assert issubclass(gr.GetStaked, gr.GetObjectsOwnedByAddress)

    def test_get_staked_object_type(self):
        obj = gr.GetStaked(owner=self._ADDR)
        assert obj.object_type == "0x3::staking_pool::StakedSui"

    def test_get_delegated_stakes_is_get_staked(self):
        assert issubclass(gr.GetDelegatedStakes, gr.GetStaked)


# ---------------------------------------------------------------------------
# TestCoinBalanceRequests
# ---------------------------------------------------------------------------

class TestCoinBalanceRequests:
    _ADDR = "0xowner"

    def test_get_coin_metadata_default_coin_type(self):
        obj = gr.GetCoinMetaData()
        assert obj.coin_type == "0x2::sui::SUI"
        assert obj.service == absreq.Service.STATE

    def test_get_coin_metadata_custom_coin_type(self):
        obj = gr.GetCoinMetaData(coin_type="0xdead::token::T")
        assert obj.coin_type == "0xdead::token::T"

    def test_get_address_coin_balance_stores_owner(self):
        obj = gr.GetAddressCoinBalance(owner=self._ADDR)
        assert obj.owner == self._ADDR
        assert obj.coin_type == "0x2::sui::SUI"
        assert obj.service == absreq.Service.STATE

    def test_get_address_coin_balance_custom_coin_type(self):
        obj = gr.GetAddressCoinBalance(owner=self._ADDR, coin_type="0xfoo::bar::BAZ")
        assert obj.coin_type == "0xfoo::bar::BAZ"

    def test_get_address_coin_balances_stores_owner(self):
        obj = gr.GetAddressCoinBalances(owner=self._ADDR)
        assert obj.owner == self._ADDR
        assert obj.service == absreq.Service.STATE

    def test_get_address_coin_balances_paging_args(self):
        obj = gr.GetAddressCoinBalances(owner=self._ADDR, page_size=10, page_token=b"tok")
        assert obj.page_size == 10
        assert obj.page_token == b"tok"


# ---------------------------------------------------------------------------
# TestTransactionRequests
# ---------------------------------------------------------------------------

class TestTransactionRequests:
    def test_get_transaction_stores_digest(self):
        obj = gr.GetTransaction(digest="txdigest")
        assert obj.digest == "txdigest"
        assert obj.service == absreq.Service.LEDGER

    def test_get_transaction_default_field_mask(self):
        obj = gr.GetTransaction(digest="txdigest")
        assert obj.field_mask is not None

    def test_get_transactions_stores_list(self):
        obj = gr.GetTransactions(transactions=["d1", "d2", "d3"])
        assert obj.transactions == ["d1", "d2", "d3"]
        assert obj.service == absreq.Service.LEDGER

    def test_get_transaction_sc_is_get_transaction(self):
        assert issubclass(gr.GetTransactionSC, gr.GetTransaction)

    def test_get_transaction_sc_has_render(self):
        assert hasattr(gr.GetTransactionSC, "render")

    def test_get_transaction_sc_render_returns_transaction(self):
        obj = gr.GetTransactionSC(digest="abc")
        tx = sui_prot.ExecutedTransaction()
        response = sui_prot.GetTransactionResponse(transaction=tx)
        assert obj.render(response) is tx

    def test_get_transaction_sc_render_none_for_missing(self):
        obj = gr.GetTransactionSC(digest="abc")
        response = sui_prot.GetTransactionResponse()
        assert obj.render(response) is None

    def test_get_transactions_sc_is_get_transactions(self):
        assert issubclass(gr.GetTransactionsSC, gr.GetTransactions)

    def test_get_transactions_sc_has_render(self):
        assert hasattr(gr.GetTransactionsSC, "render")

    def test_get_transactions_sc_render_returns_list(self):
        obj = gr.GetTransactionsSC(transactions=["d1", "d2"])
        tx1 = sui_prot.ExecutedTransaction()
        tx2 = sui_prot.ExecutedTransaction()
        response = sui_prot.BatchGetTransactionsResponse(
            transactions=[
                sui_prot.GetTransactionResult(transaction=tx1),
                sui_prot.GetTransactionResult(transaction=tx2),
            ]
        )
        result = obj.render(response)
        assert result == [tx1, tx2]

    def test_get_transactions_sc_render_preserves_none_slot(self):
        obj = gr.GetTransactionsSC(transactions=["d1", "fake", "d2"])
        tx1 = sui_prot.ExecutedTransaction()
        tx2 = sui_prot.ExecutedTransaction()
        response = sui_prot.BatchGetTransactionsResponse(
            transactions=[
                sui_prot.GetTransactionResult(transaction=tx1),
                sui_prot.GetTransactionResult(),
                sui_prot.GetTransactionResult(transaction=tx2),
            ]
        )
        result = obj.render(response)
        assert len(result) == 3
        assert result[0] is tx1
        assert result[1] is None
        assert result[2] is tx2

    def test_get_transaction_kind_sc_is_get_transaction(self):
        assert issubclass(gr.GetTransactionKindSC, gr.GetTransaction)

    def test_get_transaction_kind_sc_has_render(self):
        assert hasattr(gr.GetTransactionKindSC, "render")

    def test_get_transaction_kind_sc_field_mask(self):
        obj = gr.GetTransactionKindSC(digest="abc")
        assert obj.field_mask is not None

    def test_get_transaction_kind_sc_render_returns_kind(self):
        obj = gr.GetTransactionKindSC(digest="abc")
        kind = sui_prot.TransactionKind()
        tx = sui_prot.Transaction(kind=kind)
        executed = sui_prot.ExecutedTransaction(transaction=tx)
        response = sui_prot.GetTransactionResponse(transaction=executed)
        assert obj.render(response) is kind

    def test_get_transaction_kind_sc_render_none_for_missing(self):
        obj = gr.GetTransactionKindSC(digest="abc")
        response = sui_prot.GetTransactionResponse()
        assert obj.render(response) is None

    def test_execute_transaction_bytes_tx(self):
        obj = gr.ExecuteTransaction(tx_bytestr=b"\x00\x01", sig_array=[b"\x02"])
        assert obj.service == absreq.Service.TRANSACTION
        assert isinstance(obj.transaction, sui_prot.Transaction)

    def test_execute_transaction_multiple_sigs(self):
        obj = gr.ExecuteTransaction(tx_bytestr=b"\x00", sig_array=[b"\x01", b"\x02"])
        assert len(obj.signatures) == 2

    def test_simulate_transaction_bytes(self):
        obj = gr.SimulateTransaction(transaction=b"\x00\x01\x02")
        assert obj.service == absreq.Service.TRANSACTION
        assert isinstance(obj.transaction, sui_prot.Transaction)

    def test_simulate_transaction_defaults(self):
        obj = gr.SimulateTransaction(transaction=b"\x00")
        assert obj.gas_selection is True


# ---------------------------------------------------------------------------
# TestPackageRequests
# ---------------------------------------------------------------------------

class TestPackageRequests:
    def test_get_package_versions_stores_id(self):
        obj = gr.GetPackageVersions(package_storage_id="0x2")
        assert obj.package_storage_id == "0x2"
        assert obj.service == absreq.Service.MOVEPACKAGE

    def test_get_package_versions_paging(self):
        obj = gr.GetPackageVersions(package_storage_id="0x2", page_size=5, page_token=b"tok")
        assert obj.page_size == 5
        assert obj.page_token == b"tok"

    def test_get_package_stores_id(self):
        obj = gr.GetPackage(package="0x2")
        assert obj.package_id == "0x2"
        assert obj.service == absreq.Service.MOVEPACKAGE

    def test_get_move_data_type_stores_args(self):
        obj = gr.GetMoveDataType(package="0x2", module_name="coin", type_name="Coin")
        assert obj.package == "0x2"
        assert obj.module_name == "coin"
        assert obj.type_name == "Coin"
        assert obj.service == absreq.Service.MOVEPACKAGE

    def test_get_structure_is_get_move_data_type(self):
        assert issubclass(gr.GetStructure, gr.GetMoveDataType)

    def test_get_structure_maps_structure_name(self):
        obj = gr.GetStructure(package="0x2", module_name="coin", structure_name="Coin")
        assert obj.type_name == "Coin"

    def test_get_structures_is_get_package(self):
        assert issubclass(gr.GetStructures, gr.GetPackage)

    def test_get_function_stores_args(self):
        obj = gr.GetFunction(package="0x2", module_name="coin", function_name="transfer")
        assert obj.package == "0x2"
        assert obj.module_name == "coin"
        assert obj.function_name == "transfer"
        assert obj.service == absreq.Service.MOVEPACKAGE

    def test_get_functions_is_get_package(self):
        assert issubclass(gr.GetFunctions, gr.GetPackage)

    def test_get_module_is_get_package(self):
        assert issubclass(gr.GetModule, gr.GetPackage)


# ---------------------------------------------------------------------------
# TestNameServiceRequests
# ---------------------------------------------------------------------------

class TestNameServiceRequests:
    def test_get_name_service_address_stores_name(self):
        obj = gr.GetNameServiceAddress(name="example.sui")
        assert obj.name == "example.sui"
        assert obj.service == absreq.Service.NAMESERVICE

    def test_get_name_service_address_none_default(self):
        obj = gr.GetNameServiceAddress()
        assert obj.name is None

    def test_get_name_service_names_stores_address(self):
        obj = gr.GetNameServiceNames(address="0xabc")
        assert obj.address == "0xabc"
        assert obj.service == absreq.Service.NAMESERVICE


# ---------------------------------------------------------------------------
# TestMiscRequests
# ---------------------------------------------------------------------------

class TestMiscRequests:
    def test_get_dynamic_fields_stores_parent(self):
        obj = gr.GetDynamicFields("0xparent")
        assert obj.parent == "0xparent"
        assert obj.service == absreq.Service.STATE

    def test_get_dynamic_fields_paging(self):
        obj = gr.GetDynamicFields("0xparent", page_size=20, page_token=b"cursor")
        assert obj.page_size == 20
        assert obj.page_token == b"cursor"

    def test_subscribe_checkpoint_service(self):
        obj = gr.SubscribeCheckpoint()
        assert obj.service == absreq.Service.SUBSCRIPTION

    def test_verify_signature_stores_message_and_sig(self):
        obj = gr.VerifySignature(
            message_type="PersonalMessage",
            message=b"\x00\x01",
            signature=b"\x02\x03",
        )
        assert obj.service == absreq.Service.SIGNATURE
        assert isinstance(obj.message, sui_prot.Bcs)
        assert isinstance(obj.signature, sui_prot.UserSignature)

    def test_verify_signature_optional_address(self):
        obj = gr.VerifySignature(
            message_type="PersonalMessage",
            message=b"\x00",
            signature=b"\x01",
            address="0xsender",
        )
        assert obj.address == "0xsender"


# ---------------------------------------------------------------------------
# TestRenderMethods — render() output for gRPC SC variants (epoch, object, misc)
# ---------------------------------------------------------------------------

class TestRenderMethods:
    """Verify render() transformations for gRPC SC subclasses."""

    # --- GetChainIdentifierSC ---

    def test_get_chain_identifier_sc_render_returns_chain_id(self):
        response = sui_prot.GetServiceInfoResponse(chain_id="mainnet-abc")
        obj = gr.GetChainIdentifierSC()
        assert obj.render(response) == "mainnet-abc"

    def test_get_chain_identifier_sc_render_empty_chain_id(self):
        response = sui_prot.GetServiceInfoResponse()
        obj = gr.GetChainIdentifierSC()
        assert obj.render(response) == ""

    # --- GetLatestSuiSystemState ---

    def test_get_latest_sui_system_state_render_returns_system_state(self):
        ss = sui_prot.SystemState()
        epoch = sui_prot.Epoch(system_state=ss)
        response = sui_prot.GetEpochResponse(epoch=epoch)
        obj = gr.GetLatestSuiSystemState()
        result = obj.render(response)
        assert result is ss

    # --- GetCurrentValidatorsSC ---

    def test_get_current_validators_sc_render_returns_active_validators(self):
        v1 = sui_prot.Validator()
        v2 = sui_prot.Validator()
        vs = sui_prot.ValidatorSet(active_validators=[v1, v2])
        ss = sui_prot.SystemState(validators=vs)
        epoch = sui_prot.Epoch(system_state=ss)
        response = sui_prot.GetEpochResponse(epoch=epoch)
        obj = gr.GetCurrentValidatorsSC()
        result = obj.render(response)
        assert result.validators == [v1, v2]

    # --- GetBasicCurrentEpochInfo ---

    def test_get_basic_current_epoch_info_render_returns_epoch(self):
        epoch = sui_prot.Epoch(epoch=7, reference_gas_price=1000)
        response = sui_prot.GetEpochResponse(epoch=epoch)
        obj = gr.GetBasicCurrentEpochInfo()
        result = obj.render(response)
        assert result is epoch
        assert result.epoch == 7
        assert result.reference_gas_price == 1000

    # --- GetProtocolConfig ---

    def test_get_protocol_config_render_returns_protocol_config(self):
        pc = sui_prot.ProtocolConfig(protocol_version=42)
        epoch = sui_prot.Epoch(protocol_config=pc)
        response = sui_prot.GetEpochResponse(epoch=epoch)
        obj = gr.GetProtocolConfig()
        result = obj.render(response)
        assert result is pc
        assert result.protocol_version == 42

    # --- GetObjectSC ---

    def test_get_object_sc_render_returns_inner_object(self):
        inner = sui_prot.Object(object_id="0xabc", version=3)
        response = sui_prot.GetObjectResponse(object=inner)
        obj = gr.GetObjectSC(object_id="0xabc")
        assert obj.render(response) is inner

    def test_get_object_sc_render_none_when_missing(self):
        response = sui_prot.GetObjectResponse()
        obj = gr.GetObjectSC(object_id="0xabc")
        assert obj.render(response) is None

    # --- GetPastObjectSC ---

    def test_get_past_object_sc_render_returns_inner_object(self):
        inner = sui_prot.Object(object_id="0xdef", version=7)
        response = sui_prot.GetObjectResponse(object=inner)
        obj = gr.GetPastObjectSC(object_id="0xdef", version=7)
        assert obj.render(response) is inner

    # --- GetObjectSummarySC ---

    def test_get_object_summary_sc_render_address_owner(self):
        owner = sui_prot.Owner(kind=sui_prot.OwnerOwnerKind.ADDRESS, address="0xowner")
        inner = sui_prot.Object(object_id="0x1", version=5, digest="dg1", owner=owner)
        response = sui_prot.GetObjectResponse(object=inner)
        obj = gr.GetObjectSummarySC(object_id="0x1")
        result = obj.render(response)
        assert isinstance(result, shared_types.ObjectSummary)
        assert result.objectId == "0x1"
        assert result.version == "5"
        assert result.digest == "dg1"
        assert result.owner == "0xowner"
        assert result.initialSharedVersion is None

    def test_get_object_summary_sc_render_shared_owner(self):
        owner = sui_prot.Owner(kind=sui_prot.OwnerOwnerKind.SHARED, version=100)
        inner = sui_prot.Object(object_id="0x2", version=2, digest="dg2", owner=owner)
        response = sui_prot.GetObjectResponse(object=inner)
        obj = gr.GetObjectSummarySC(object_id="0x2")
        result = obj.render(response)
        assert result.owner is None
        assert result.initialSharedVersion == "100"

    # --- GetMultipleObjectsSummarySC ---

    def test_get_multiple_objects_summary_sc_render_address_owner(self):
        owner = sui_prot.Owner(kind=sui_prot.OwnerOwnerKind.ADDRESS, address="0xaddr")
        obj1 = sui_prot.Object(object_id="0x1", version=1, digest="d1", owner=owner)
        response = sui_prot.BatchGetObjectsResponse(
            objects=[sui_prot.GetObjectResult(object=obj1)]
        )
        sc = gr.GetMultipleObjectsSummarySC(object_ids=["0x1"])
        result = sc.render(response)
        assert isinstance(result, shared_types.ObjectSummaryList)
        assert len(result.objects) == 1
        assert result.objects[0].owner == "0xaddr"

    def test_get_multiple_objects_summary_sc_render_shared_owner(self):
        owner = sui_prot.Owner(kind=sui_prot.OwnerOwnerKind.SHARED, version=55)
        obj1 = sui_prot.Object(object_id="0x2", version=3, digest="d2", owner=owner)
        response = sui_prot.BatchGetObjectsResponse(
            objects=[sui_prot.GetObjectResult(object=obj1)]
        )
        sc = gr.GetMultipleObjectsSummarySC(object_ids=["0x2"])
        result = sc.render(response)
        assert result.objects[0].initialSharedVersion == "55"
        assert result.objects[0].owner is None

    def test_get_multiple_objects_summary_sc_render_empty(self):
        response = sui_prot.BatchGetObjectsResponse(objects=[])
        sc = gr.GetMultipleObjectsSummarySC(object_ids=[])
        result = sc.render(response)
        assert isinstance(result, shared_types.ObjectSummaryList)
        assert result.objects == []

    # --- GetObjectsOwnedByAddress (base class render filters coin reservations) ---

    def test_get_objects_owned_by_address_render_filters_version_zero(self):
        real_obj = sui_prot.Object(object_id="0x1", version=3, digest=None)
        coin_res = sui_prot.Object(object_id="0x2", version=0)  # version==0 → coin reservation
        response = sui_prot.ListOwnedObjectsResponse(objects=[real_obj, coin_res])
        obj = gr.GetObjectsOwnedByAddress(owner="0xowner")
        result = obj.render(response)
        assert len(result.objects) == 1
        assert result.objects[0].object_id == "0x1"

    def test_get_objects_owned_by_address_render_preserves_real_objects(self):
        obj1 = sui_prot.Object(object_id="0x1", version=1, digest="d1")
        obj2 = sui_prot.Object(object_id="0x2", version=2, digest="d2")
        response = sui_prot.ListOwnedObjectsResponse(objects=[obj1, obj2])
        sc = gr.GetObjectsOwnedByAddress(owner="0xowner")
        result = sc.render(response)
        assert len(result.objects) == 2
