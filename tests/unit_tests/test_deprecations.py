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



