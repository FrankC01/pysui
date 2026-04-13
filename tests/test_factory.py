#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Tests for client_factory dispatch logic."""

from unittest.mock import MagicMock, patch
import pytest

from pysui import client_factory, GroupProtocol
from pysui.sui.sui_pgql.pgql_clients import AsyncSuiGQLClient
from pysui.sui.sui_grpc.pgrpc_clients import SuiGrpcClient


def _make_config(protocol: GroupProtocol) -> MagicMock:
    """Build a minimal PysuiConfiguration mock for the given protocol."""
    cfg = MagicMock()
    cfg.active_group.group_protocol = protocol
    return cfg


# ---------------------------------------------------------------------------
# Error cases — no network required
# ---------------------------------------------------------------------------


def test_group_name_without_protocol_raises():
    """Providing group_name without protocol must raise ValueError."""
    cfg = _make_config(GroupProtocol.GRAPHQL)
    with pytest.raises(ValueError, match="protocol is required"):
        client_factory(cfg, group_name="custom_group")


def test_other_protocol_raises():
    """GroupProtocol.OTHER (or any unrecognised value) must raise NotImplementedError."""
    cfg = _make_config(GroupProtocol.OTHER)
    with pytest.raises(NotImplementedError):
        client_factory(cfg)


# ---------------------------------------------------------------------------
# Dispatch — mocked constructors, no network required
# ---------------------------------------------------------------------------


@patch("pysui.sui.sui_pgql.pgql_clients.AsyncSuiGQLClient", autospec=True)
def test_active_graphql_group_returns_gql_client(mock_gql):
    """Active group with GRAPHQL protocol returns AsyncSuiGQLClient."""
    cfg = _make_config(GroupProtocol.GRAPHQL)
    result = client_factory(cfg)
    mock_gql.assert_called_once_with(pysui_config=cfg)
    assert result is mock_gql.return_value


@patch("pysui.sui.sui_grpc.pgrpc_clients.SuiGrpcClient", autospec=True)
def test_active_grpc_group_returns_grpc_client(mock_grpc):
    """Active group with GRPC protocol returns SuiGrpcClient."""
    cfg = _make_config(GroupProtocol.GRPC)
    result = client_factory(cfg)
    mock_grpc.assert_called_once_with(pysui_config=cfg)
    assert result is mock_grpc.return_value


@patch("pysui.sui.sui_pgql.pgql_clients.AsyncSuiGQLClient", autospec=True)
def test_explicit_group_graphql(mock_gql):
    """Explicit group_name + GRAPHQL protocol activates group and returns GQL client."""
    cfg = _make_config(GroupProtocol.OTHER)
    result = client_factory(cfg, group_name="my_provider", protocol=GroupProtocol.GRAPHQL)
    cfg.make_active.assert_called_once_with(group_name="my_provider", persist=False)
    mock_gql.assert_called_once_with(pysui_config=cfg)
    assert result is mock_gql.return_value


@patch("pysui.sui.sui_grpc.pgrpc_clients.SuiGrpcClient", autospec=True)
def test_explicit_group_grpc(mock_grpc):
    """Explicit group_name + GRPC protocol activates group and returns gRPC client."""
    cfg = _make_config(GroupProtocol.OTHER)
    result = client_factory(cfg, group_name="my_provider", protocol=GroupProtocol.GRPC)
    cfg.make_active.assert_called_once_with(group_name="my_provider", persist=False)
    mock_grpc.assert_called_once_with(pysui_config=cfg)
    assert result is mock_grpc.return_value
