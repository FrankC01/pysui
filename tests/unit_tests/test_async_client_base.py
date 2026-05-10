#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Unit tests for AsyncClientBase.execute_for_all() — all offline, no live node.

Covers:
  - _protocol ClassVar defaults on AsyncClientBase and concrete subclasses
  - Non-pageable command delegates directly to execute()
  - Single-page pageable command (cursor None on first call) returns immediately
  - Multi-page accumulation: items list extended; next_page_token cleared
  - Transport error on first page propagates immediately
  - Transport error on subsequent page propagates immediately
"""

import dataclasses
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from pysui import SuiRpcResult
from pysui.abstracts.async_client import AsyncClientBase
from pysui.sui.sui_common.sui_command import SuiCommand


# ---------------------------------------------------------------------------
# Minimal concrete AsyncClientBase for testing
# ---------------------------------------------------------------------------

class _MockClient(AsyncClientBase):
    """Minimal concrete client — execute() is replaced per test via mock."""

    _protocol: str = "gql"

    async def transaction(self, **kwargs):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def execute(self, *, command, timeout=None, headers=None):
        raise NotImplementedError("replace with mock")


class _MockGrpcClient(_MockClient):
    _protocol: str = "grpc"


# ---------------------------------------------------------------------------
# Minimal SuiCommand stubs
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _NonPageableCmd(SuiCommand):
    gql_class = object
    grpc_class = object

    owner: str

    def gql_node(self):
        return object()

    def grpc_request(self):
        return object()


@dataclasses.dataclass
class _PageableCmd(SuiCommand):
    gql_class = object
    grpc_class = object
    is_pageable_gql = True
    paginated_field_path_gql = ("coins",)

    owner: str
    next_page_token: bytes | None = None

    def gql_node(self):
        return object()

    def grpc_request(self):
        return object()


# ---------------------------------------------------------------------------
# Minimal proto-shaped result object
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _CoinPage:
    coins: list
    next_page_token: bytes | None = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestProtocolClassVar:
    def test_base_protocol_default_is_empty(self):
        assert AsyncClientBase._protocol == ""

    def test_gql_client_protocol(self):
        assert _MockClient._protocol == "gql"

    def test_grpc_client_protocol(self):
        assert _MockGrpcClient._protocol == "grpc"


@pytest.mark.asyncio
class TestExecuteForAllNonPageable:
    async def test_non_pageable_delegates_to_execute(self):
        client = _MockClient()
        cmd = _NonPageableCmd(owner="0x1")
        expected = SuiRpcResult(True, "", {"result": 42})
        client.execute = AsyncMock(return_value=expected)

        result = await client.execute_for_all(command=cmd)

        client.execute.assert_awaited_once_with(command=cmd, timeout=None, headers=None)
        assert result is expected

    async def test_non_pageable_passes_timeout_and_headers(self):
        client = _MockClient()
        cmd = _NonPageableCmd(owner="0x1")
        expected = SuiRpcResult(True, "", {})
        client.execute = AsyncMock(return_value=expected)

        await client.execute_for_all(command=cmd, timeout=5.0, headers={"x": "y"})

        client.execute.assert_awaited_once_with(command=cmd, timeout=5.0, headers={"x": "y"})


@pytest.mark.asyncio
class TestExecuteForAllSinglePage:
    async def test_single_page_returns_immediately(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        page = _CoinPage(coins=["c1", "c2"], next_page_token=None)
        client.execute = AsyncMock(return_value=SuiRpcResult(True, "", page))

        result = await client.execute_for_all(command=cmd)

        assert result.is_ok()
        assert result.result_data.coins == ["c1", "c2"]
        assert result.result_data.next_page_token is None
        client.execute.assert_awaited_once()

    async def test_empty_page_returns_immediately(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        page = _CoinPage(coins=[], next_page_token=None)
        client.execute = AsyncMock(return_value=SuiRpcResult(True, "", page))

        result = await client.execute_for_all(command=cmd)

        assert result.is_ok()
        assert result.result_data.coins == []
        client.execute.assert_awaited_once()


@pytest.mark.asyncio
class TestExecuteForAllMultiPage:
    async def test_two_pages_accumulated(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        page1 = _CoinPage(coins=["c1", "c2"], next_page_token=b"cursor1")
        page2 = _CoinPage(coins=["c3"], next_page_token=None)
        client.execute = AsyncMock(side_effect=[
            SuiRpcResult(True, "", page1),
            SuiRpcResult(True, "", page2),
        ])

        result = await client.execute_for_all(command=cmd)

        assert result.is_ok()
        assert result.result_data.coins == ["c1", "c2", "c3"]
        assert result.result_data.next_page_token is None
        assert client.execute.await_count == 2

    async def test_three_pages_accumulated(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        pages = [
            SuiRpcResult(True, "", _CoinPage(coins=["a"], next_page_token=b"c1")),
            SuiRpcResult(True, "", _CoinPage(coins=["b"], next_page_token=b"c2")),
            SuiRpcResult(True, "", _CoinPage(coins=["c"], next_page_token=None)),
        ]
        client.execute = AsyncMock(side_effect=pages)

        result = await client.execute_for_all(command=cmd)

        assert result.result_data.coins == ["a", "b", "c"]
        assert client.execute.await_count == 3

    async def test_caller_command_not_mutated(self):
        """execute_for_all must not mutate the caller's command instance."""
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        client.execute = AsyncMock(side_effect=[
            SuiRpcResult(True, "", _CoinPage(coins=["c1"], next_page_token=b"tok")),
            SuiRpcResult(True, "", _CoinPage(coins=["c2"], next_page_token=None)),
        ])

        await client.execute_for_all(command=cmd)

        assert cmd.next_page_token is None

    async def test_final_next_page_token_is_none(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        client.execute = AsyncMock(side_effect=[
            SuiRpcResult(True, "", _CoinPage(coins=["c1"], next_page_token=b"tok")),
            SuiRpcResult(True, "", _CoinPage(coins=["c2"], next_page_token=None)),
        ])

        result = await client.execute_for_all(command=cmd)

        assert result.result_data.next_page_token is None


@pytest.mark.asyncio
class TestExecuteForAllErrors:
    async def test_error_on_first_page_propagates(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        error = SuiRpcResult(False, "transport error", None)
        client.execute = AsyncMock(return_value=error)

        result = await client.execute_for_all(command=cmd)

        assert not result.is_ok()
        assert result.result_string == "transport error"
        client.execute.assert_awaited_once()

    async def test_error_on_second_page_propagates(self):
        client = _MockClient()
        cmd = _PageableCmd(owner="0x1")
        client.execute = AsyncMock(side_effect=[
            SuiRpcResult(True, "", _CoinPage(coins=["c1"], next_page_token=b"tok")),
            SuiRpcResult(False, "timeout", None),
        ])

        result = await client.execute_for_all(command=cmd)

        assert not result.is_ok()
        assert result.result_string == "timeout"
        assert client.execute.await_count == 2
