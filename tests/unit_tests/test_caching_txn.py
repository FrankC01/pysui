#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for CachingTransaction (placeholder tests for offline structure)."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestCachingTransaction:
    """Test CachingTransaction structure and basic operations."""

    def test_caching_transaction_class_exists(self):
        """CachingTransaction can be imported."""
        from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction

        assert CachingTransaction is not None

    def test_caching_transaction_requires_client(self):
        """CachingTransaction requires a client parameter."""
        from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction
        import inspect

        sig = inspect.signature(CachingTransaction.__init__)
        assert "client" in sig.parameters

    @pytest.mark.asyncio
    async def test_caching_transaction_mock_client(self):
        """CachingTransaction initialization with mock client (no network)."""
        from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction

        mock_client = MagicMock()
        mock_client.config = MagicMock()

        txn = CachingTransaction(client=mock_client)
        assert txn is not None

    def test_caching_transaction_set_gas_budget(self):
        """CachingTransaction has set_gas_budget_if_notset method."""
        from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction

        assert hasattr(CachingTransaction, "set_gas_budget_if_notset")

    @pytest.mark.asyncio
    async def test_build_txn_data_inflates_budget_for_gas_coin_draw(self):
        """_build_txn_data inflates gas_budget by gas_source_draw from _inspect_ptb_for_gas_coin."""
        from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction
        from unittest.mock import MagicMock, patch, call, AsyncMock
        import pysui.sui.sui_bcs.bcs as bcs
        from pysui.sui.sui_common.trxn_base import _TransactionBase

        mock_client = MagicMock()
        mock_client.current_gas_price = 1000
        mock_client.execute = AsyncMock()
        mock_epoch_info = MagicMock()
        mock_epoch_info.reference_gas_price = 1000
        mock_result = MagicMock()
        mock_result.is_ok.return_value = True
        mock_result.result_data = mock_epoch_info
        mock_client.execute.return_value = mock_result

        txn = CachingTransaction(client=mock_client)

        mock_signer = MagicMock()
        mock_signer.payer_address = "0x" + "ab" * 32
        mock_signer.sender_str = "0x" + "ab" * 32

        gas_ref = bcs.ObjectReference(
            bcs.Address.from_str("0x" + "01" * 32),
            1,
            bcs.Digest.from_str("11111111111111111111111111111111"),
        )

        base_budget = 5_000_000
        draw_amount = 1_000_000
        captured = {}

        real_GasData = bcs.GasData

        def capturing_GasData(payment, owner, price, budget):
            captured["budget"] = budget
            return real_GasData(payment, owner, price, budget)

        with patch.object(_TransactionBase, "_inspect_ptb_for_gas_coin", return_value=(True, draw_amount)), \
             patch("pysui.sui.sui_pgql.execute.caching_txn.bcs.GasData", side_effect=capturing_GasData):
            await txn._build_txn_data(
                gas_budget=base_budget,
                use_gas_objects=[gas_ref],
                signer_block=mock_signer,
            )

        assert captured["budget"] == base_budget + draw_amount, (
            f"Expected budget {base_budget + draw_amount}, got {captured['budget']}"
        )

    @pytest.mark.asyncio
    async def test_build_txn_data_no_inflation_when_no_gas_coin_draw(self):
        """_build_txn_data leaves budget unchanged when gas coin is not used."""
        from pysui.sui.sui_pgql.execute.caching_txn import CachingTransaction
        from unittest.mock import MagicMock, patch, AsyncMock
        import pysui.sui.sui_bcs.bcs as bcs
        from pysui.sui.sui_common.trxn_base import _TransactionBase

        mock_client = MagicMock()
        mock_client.current_gas_price = 1000
        mock_client.execute = AsyncMock()
        mock_epoch_info = MagicMock()
        mock_epoch_info.reference_gas_price = 1000
        mock_result = MagicMock()
        mock_result.is_ok.return_value = True
        mock_result.result_data = mock_epoch_info
        mock_client.execute.return_value = mock_result

        txn = CachingTransaction(client=mock_client)

        mock_signer = MagicMock()
        mock_signer.payer_address = "0x" + "ab" * 32
        mock_signer.sender_str = "0x" + "ab" * 32

        gas_ref = bcs.ObjectReference(
            bcs.Address.from_str("0x" + "01" * 32),
            1,
            bcs.Digest.from_str("11111111111111111111111111111111"),
        )

        base_budget = 5_000_000
        captured = {}

        real_GasData = bcs.GasData

        def capturing_GasData(payment, owner, price, budget):
            captured["budget"] = budget
            return real_GasData(payment, owner, price, budget)

        with patch.object(_TransactionBase, "_inspect_ptb_for_gas_coin", return_value=(False, 0)), \
             patch("pysui.sui.sui_pgql.execute.caching_txn.bcs.GasData", side_effect=capturing_GasData):
            await txn._build_txn_data(
                gas_budget=base_budget,
                use_gas_objects=[gas_ref],
                signer_block=mock_signer,
            )

        assert captured["budget"] == base_budget
