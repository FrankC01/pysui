#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Offline unit tests for Phase 1-3 deprecation warnings and shared-type contracts.

All tests in this module run without a network connection or live Sui node.
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# TransactionConstraints backwards-compat re-export
# ---------------------------------------------------------------------------


def test_transaction_constraints_reexport():
    """TransactionConstraints imported from pgql_types resolves to the same class
    as the canonical location in sui_common.types."""
    from pysui.sui.sui_pgql.pgql_types import TransactionConstraints as FromPgql
    from pysui.sui.sui_common.types import TransactionConstraints as Canonical

    assert FromPgql is Canonical


# ---------------------------------------------------------------------------
# PysuiClient ABC contract
# ---------------------------------------------------------------------------


def test_pysuiclient_abc_requires_transaction():
    """A concrete subclass that omits transaction() must raise TypeError."""
    from pysui.sui.sui_common.client import PysuiClient

    class IncompleteClient(PysuiClient):
        pass  # no abstract methods implemented

    with pytest.raises(TypeError, match="transaction"):
        IncompleteClient()


def test_pysuiclient_abc_satisfied():
    """A concrete subclass implementing all abstract methods can be instantiated."""
    from pysui.sui.sui_common.client import PysuiClient

    class MinimalClient(PysuiClient):
        @property
        def current_gas_price(self) -> int:
            return 0

        def protocol(self, for_version=None):
            return MagicMock()

        def transaction(self, **kwargs):
            return MagicMock()

    client = MinimalClient(pysui_config=MagicMock())
    assert client is not None


# ---------------------------------------------------------------------------
# Deprecation warnings — no network required
# ---------------------------------------------------------------------------


def test_sui_config_deprecated():
    """SuiConfig emits DeprecationWarning on instantiation."""
    from pysui.sui.sui_config import SuiConfig

    with patch.object(SuiConfig, "__init__", return_value=None):
        with pytest.warns(DeprecationWarning, match="SuiConfig"):
            SuiConfig()


def test_sync_json_rpc_client_deprecated():
    """JSON-RPC synchronous SuiClient emits DeprecationWarning on instantiation.

    The @deprecated decorator fires before __init__ body runs; init itself
    fails without a real config, which is expected and suppressed here.
    """
    from pysui.sui.sui_clients.sync_client import SuiClient

    with pytest.warns(DeprecationWarning, match="JSON-RPC SuiClient.*synchronous"):
        try:
            SuiClient(config=MagicMock())
        except Exception:
            pass  # init cannot complete without a real config; warning already emitted


def test_async_json_rpc_client_deprecated():
    """JSON-RPC asynchronous SuiClient emits DeprecationWarning on instantiation.

    The @deprecated decorator fires before __init__ body runs; init itself
    fails without a real config, which is expected and suppressed here.
    """
    from pysui.sui.sui_clients.async_client import SuiClient

    with pytest.warns(DeprecationWarning, match="JSON-RPC SuiClient.*asynchronous"):
        try:
            SuiClient(config=MagicMock())
        except Exception:
            pass  # init cannot complete without a real config; warning already emitted


def test_sync_gql_client_deprecated():
    """Synchronous SuiGQLClient emits DeprecationWarning on instantiation."""
    from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
    import pysui.sui.sui_pgql.pgql_clients as pgql_clients

    with patch.object(pgql_clients.scm, "Schema", return_value=MagicMock()), \
         patch("pysui.sui.sui_pgql.pgql_clients.BaseSuiGQLClient.__init__", return_value=None):
        with pytest.warns(DeprecationWarning, match="SuiGQLClient.*synchronous"):
            SuiGQLClient(pysui_config=MagicMock())


def test_sync_sui_transaction_deprecated():
    """Synchronous SuiTransaction emits DeprecationWarning; frame guard then raises
    ValueError since the caller is not SuiGQLClient.transaction()."""
    from pysui.sui.sui_pgql.pgql_sync_txn import SuiTransaction

    with pytest.warns(DeprecationWarning, match="SuiTransaction.*synchronous"):
        with pytest.raises(ValueError, match="SuiTransaction must be created"):
            SuiTransaction()
