#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for SuiCommand ABC — all offline, no live node required.

Tests cover:
  - Cannot instantiate SuiCommand directly (abstract)
  - isinstance check works for concrete subclasses
  - is_pageable_gql defaults to False
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
    """Command that is GQL-pageable (non-cursor accumulation path)."""
    gql_class = object
    grpc_class = object
    is_pageable_gql = True
    paginated_field_path_gql = ("items",)

    package: str

    def gql_node(self):
        return self.gql_class()

    def grpc_request(self):
        return self.grpc_class()


@dataclasses.dataclass
class _GqlPageableCommand(SuiCommand):
    """GQL-pageable command with a declared field path."""
    gql_class = object
    grpc_class = object
    is_pageable_gql = True
    paginated_field_path_gql = ("objects",)

    owner: str
    next_page_token: bytes | None = None

    def gql_node(self):
        return self.gql_class()

    def grpc_request(self):
        return self.grpc_class()


@dataclasses.dataclass
class _BothPageableCommand(SuiCommand):
    """Both-protocol pageable command — single next_page_token field."""
    gql_class = object
    grpc_class = object
    is_pageable_gql = True
    is_pageable_grpc = True
    paginated_field_path_gql = ("coins",)
    paginated_field_path_grpc = ("coins",)

    owner: str
    next_page_token: bytes | None = None

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

    def test_is_pageable_gql_defaults_false(self):
        assert _FullCommand.is_pageable_gql is False
        cmd = _FullCommand(owner="0xabc")
        assert cmd.is_pageable_gql is False

    def test_is_pageable_gql_overridden(self):
        assert _PagingCommand.is_pageable_gql is True
        assert _PagingCommand.paginated_field_path_gql == ("items",)
        cmd = _PagingCommand(package="0x2")
        assert cmd.is_pageable_gql is True

    def test_classvars_absent_from_dataclass_init(self):
        fields = {f.name for f in dataclasses.fields(_FullCommand)}
        assert "gql_class" not in fields
        assert "grpc_class" not in fields
        assert "is_pageable_gql" not in fields

    def test_full_command_constructor_accepts_only_user_args(self):
        cmd = _FullCommand(owner="0xabc")
        assert cmd.owner == "0xabc"

    def test_classvars_set_on_subclass(self):
        assert _FullCommand.gql_class is object
        assert _FullCommand.grpc_class is object


class TestSuiCommandPagingContract:
    def test_is_pageable_gql_defaults_false(self):
        assert _FullCommand.is_pageable_gql is False
        assert _FullCommand(owner="0x1").is_pageable_gql is False

    def test_is_pageable_grpc_defaults_false(self):
        assert _FullCommand.is_pageable_grpc is False
        assert _FullCommand(owner="0x1").is_pageable_grpc is False

    def test_paginated_field_path_gql_defaults_none(self):
        assert _FullCommand.paginated_field_path_gql is None

    def test_paginated_field_path_grpc_defaults_none(self):
        assert _FullCommand.paginated_field_path_grpc is None

    def test_non_pageable_has_no_next_page_token_field(self):
        fields = {f.name for f in dataclasses.fields(_FullCommand)}
        assert "next_page_token" not in fields

    def test_gql_pageable_command_overrides_classvars(self):
        assert _GqlPageableCommand.is_pageable_gql is True
        assert _GqlPageableCommand.is_pageable_grpc is False
        assert _GqlPageableCommand.paginated_field_path_gql == ("objects",)
        assert _GqlPageableCommand.paginated_field_path_grpc is None

    def test_next_page_token_assignment(self):
        cmd = _GqlPageableCommand(owner="0x1")
        assert cmd.next_page_token is None
        cmd.next_page_token = b"abc"
        assert cmd.next_page_token == b"abc"

    def test_both_pageable_command_token(self):
        cmd = _BothPageableCommand(owner="0x1")
        assert cmd.next_page_token is None
        cmd.next_page_token = b"cursor"
        assert cmd.next_page_token == b"cursor"

    def test_paging_classvars_absent_from_dataclass_fields(self):
        fields = {f.name for f in dataclasses.fields(_FullCommand)}
        assert "is_pageable_gql" not in fields
        assert "is_pageable_grpc" not in fields
        assert "paginated_field_path_gql" not in fields
        assert "paginated_field_path_grpc" not in fields


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
