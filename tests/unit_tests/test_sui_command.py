#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for SuiCommand ABC — all offline, no live node required.

Tests cover:
  - Cannot instantiate SuiCommand directly (abstract)
  - isinstance check works for concrete subclasses
  - gql_requires_paging defaults to False
  - ClassVar fields are absent from dataclass __init__
  - gql_node() NotImplementedError for GQL-unsupported commands (EC-3)
  - grpc_request() NotImplementedError for gRPC-unsupported commands (EC-3)
  - Concrete subclass wires gql_class and grpc_class correctly
"""

import dataclasses
import pytest

from pysui.sui.sui_common.sui_command import SuiCommand


# ---------------------------------------------------------------------------
# Minimal concrete subclasses for testing
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _FullCommand(SuiCommand):
    """Both protocols supported."""
    gql_class = object  # stand-in; not exercised in ABC tests
    grpc_class = object

    owner: str

    def gql_node(self):
        return self.gql_class()

    def grpc_request(self):
        return self.grpc_class()


@dataclasses.dataclass
class _GqlOnlyCommand(SuiCommand):
    """GQL supported; gRPC raises NotImplementedError (EC-3)."""
    gql_class = object
    grpc_class = None

    event_type: str

    def gql_node(self):
        return self.gql_class()

    def grpc_request(self):
        raise NotImplementedError("Command not supported by gRPC")


@dataclasses.dataclass
class _GrpcOnlyCommand(SuiCommand):
    """gRPC supported; GQL raises NotImplementedError (EC-3)."""
    gql_class = None
    grpc_class = object

    digest: str

    def gql_node(self):
        raise NotImplementedError("Command not supported by GraphQL")

    def grpc_request(self):
        return self.grpc_class()


@dataclasses.dataclass
class _PagingCommand(SuiCommand):
    """Command that requires internal GQL pagination."""
    gql_class = object
    grpc_class = object
    gql_requires_paging = True

    package: str

    def gql_node(self):
        return self.gql_class()

    def grpc_request(self):
        return self.grpc_class()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSuiCommandABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            SuiCommand()

    def test_isinstance_check_passes_for_subclass(self):
        cmd = _FullCommand(owner="0xabc")
        assert isinstance(cmd, SuiCommand)

    def test_isinstance_check_fails_for_non_suicommand(self):
        assert not isinstance("not a command", SuiCommand)
        assert not isinstance(42, SuiCommand)
        assert not isinstance(None, SuiCommand)

    def test_gql_requires_paging_defaults_false(self):
        assert _FullCommand.gql_requires_paging is False
        cmd = _FullCommand(owner="0xabc")
        assert cmd.gql_requires_paging is False

    def test_gql_requires_paging_overridden(self):
        assert _PagingCommand.gql_requires_paging is True
        cmd = _PagingCommand(package="0x2")
        assert cmd.gql_requires_paging is True

    def test_classvars_absent_from_dataclass_init(self):
        fields = {f.name for f in dataclasses.fields(_FullCommand)}
        assert "gql_class" not in fields
        assert "grpc_class" not in fields
        assert "gql_requires_paging" not in fields

    def test_full_command_constructor_accepts_only_user_args(self):
        cmd = _FullCommand(owner="0xabc")
        assert cmd.owner == "0xabc"

    def test_classvars_set_on_subclass(self):
        assert _FullCommand.gql_class is object
        assert _FullCommand.grpc_class is object


class TestSuiCommandEC3:
    def test_gql_only_grpc_raises(self):
        cmd = _GqlOnlyCommand(event_type="0x2::coin::Coin")
        with pytest.raises(NotImplementedError, match="gRPC"):
            cmd.grpc_request()

    def test_gql_only_gql_succeeds(self):
        cmd = _GqlOnlyCommand(event_type="0x2::coin::Coin")
        result = cmd.gql_node()
        assert result is not None

    def test_grpc_only_gql_raises(self):
        cmd = _GrpcOnlyCommand(digest="abc123")
        with pytest.raises(NotImplementedError, match="GraphQL"):
            cmd.gql_node()

    def test_grpc_only_grpc_succeeds(self):
        cmd = _GrpcOnlyCommand(digest="abc123")
        result = cmd.grpc_request()
        assert result is not None
