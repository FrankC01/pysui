#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Integration tests: move_call argument type encoding (parms.move contract).

SERIAL EXECUTION REQUIRED — do not run with -n / --dist flags.
Sui equivocation: parallel txns on the same non-shared object lock those
objects until the next epoch.

Tests verify that all parms.move function signatures can be called through
both the GQL and gRPC transports with correct argument encoding.

Ordered after test_core_commands.py — tests here start at order 100 to
avoid conflicts with core command test order numbers.
"""

import asyncio

import pytest
import pytest_asyncio

import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_grpc.pgrpc_requests as rn
from pysui import AsyncGqlClient, SuiGrpcClient
from pysui.sui.sui_grpc.pgrpc_utils import (
    async_get_all_owned_objects as grpc_get_all_objects,
    async_get_all_owned_gas_objects as grpc_get_coins,
)
from pysui.sui.sui_pgql.pgql_utils import (
    async_get_all_owned_objects as gql_get_all_objects,
)

from tests.integration_tests.conftest import (
    SETTLE_SECS,
    PublishedPackage,
    json_faucet,
    _faucet_url_for,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.xdist_group(name="sui_integration"),
]

# Bytes used for vector<uN> arguments (reused from sample files).
_SAMP_HEX = "f87900820102dc8d63656e7472616c697a65642d318d63656e7472616c697a65642d32f856aa637863666463323730656464326131663130303336666131326132616231646134666231323632393633aa637838313532306438643439373635316632633035306334613130616166353131373666333732333064"
_SAMP_BYTES = bytes.fromhex(_SAMP_HEX)

# Two placeholder addresses for vector<address> / vector<ID> tests.
_ADDR_A = "0x645de330536a27a537b876142b90d9d559f1caab1a4e66a2e816078ed9b85022"
_ADDR_B = "0xa9e2db385f055cc0215a3cde268b76270535b9443807514f183be86926c219f4"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_gql_success(result, label: str) -> None:
    assert result.is_ok(), f"{label} transport error: {result.result_string}"
    assert result.result_data.status == "SUCCESS", (
        f"{label} on-chain failure: {result.result_data.execution_error}"
    )


def _assert_grpc_success(result, label: str) -> None:
    assert result.is_ok(), f"{label} transport error: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        f"{label} on-chain execution failed"
    )


# ---------------------------------------------------------------------------
# Session fixtures: Phoney object lifecycle helpers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def phoney_gql_id(
    gql_session_client: AsyncGqlClient,
    published_gql: PublishedPackage,
) -> str:
    """Create a Phoney object via GQL and return its object ID."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr
    addr = str(gql_session_client.config.active_address)

    txer = gql_session_client.transaction()
    await txer.move_call(
        target=f"{pkg_addr}::parms::create_phoney",
        arguments=[],
    )
    result = await gql_session_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    assert result.is_ok(), f"create_phoney GQL transport error: {result.result_string}"
    assert result.result_data.status == "SUCCESS", (
        f"create_phoney GQL on-chain failure: {result.result_data.execution_error}"
    )
    await asyncio.sleep(SETTLE_SECS)

    # Fetch the Phoney object ID from owned objects filtered by type.
    all_objs = await gql_get_all_objects(owner=addr, client=gql_session_client)
    phoney = next(
        (
            o
            for o in all_objs
            if o.object_type and "Phoney" in o.object_type
        ),
        None,
    )
    assert phoney is not None, "Could not find Phoney object in GQL owned objects"
    return phoney.object_id


@pytest_asyncio.fixture(scope="session")
async def phoney_grpc_id(
    grpc_session_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
) -> str:
    """Create a Phoney object via gRPC and return its object ID."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr
    addr = str(grpc_session_client.config.active_address)

    txer = await grpc_session_client.transaction()
    await txer.move_call(
        target=f"{pkg_addr}::parms::create_phoney",
        arguments=[],
    )
    result = await grpc_session_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    assert result.is_ok(), f"create_phoney gRPC transport error: {result.result_string}"
    assert result.result_data.transaction.effects.status.success, (
        "create_phoney gRPC on-chain execution failed"
    )
    await asyncio.sleep(SETTLE_SECS)

    # Fetch the Phoney object via type-filtered query.
    phoney_result = await grpc_session_client.execute(
        request=rn.GetObjectsOwnedByAddress(
            owner=addr,
            object_type=f"{pkg_addr}::parms::Phoney",
        )
    )
    assert phoney_result.is_ok(), (
        f"GetObjectsOwnedByAddress(Phoney) failed: {phoney_result.result_string}"
    )
    objects = phoney_result.result_data.objects
    assert objects, "Could not find Phoney object in gRPC owned objects"
    return objects[0].object_id


# ---------------------------------------------------------------------------
# 1. check_uints
# ---------------------------------------------------------------------------


@pytest.mark.order(100)
async def test_check_uints_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_uints (GQL): u16, u32, u64, u128, u256 as Python ints."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_uints",
        arguments=[1, 2, 3, 4, 5],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_uints")


@pytest.mark.order(101)
async def test_check_uints_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_uints (gRPC): u16, u32, u64, u128, u256 as Python ints."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_uints",
        arguments=[1, 2, 3, 4, 5],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_uints")


# ---------------------------------------------------------------------------
# 2. check_optional_uints
# ---------------------------------------------------------------------------


@pytest.mark.order(102)
async def test_check_optional_uints_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_optional_uints (GQL): mix of ints and None for Option<uN>."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_optional_uints",
        arguments=[1, 2, 3, None, 5],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_optional_uints")


@pytest.mark.order(103)
async def test_check_optional_uints_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_optional_uints (gRPC): mix of ints and None for Option<uN>."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_optional_uints",
        arguments=[1, 2, 3, None, 5],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_optional_uints")


# ---------------------------------------------------------------------------
# 3. check_uints_vectors
# ---------------------------------------------------------------------------


@pytest.mark.order(104)
async def test_check_uints_vectors_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_uints_vectors (GQL): vector<uN> passed as bytes slices."""
    await asyncio.sleep(SETTLE_SECS)
    alen = len(_SAMP_HEX)
    args = [_SAMP_BYTES[: int(alen / r)] for r in range(1, 6)]
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_uints_vectors",
        arguments=args,
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_uints_vectors")


@pytest.mark.order(105)
async def test_check_uints_vectors_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_uints_vectors (gRPC): vector<uN> passed as bytes slices."""
    await asyncio.sleep(SETTLE_SECS)
    alen = len(_SAMP_HEX)
    args = [_SAMP_BYTES[: int(alen / r)] for r in range(1, 6)]
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_uints_vectors",
        arguments=args,
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_uints_vectors")


# ---------------------------------------------------------------------------
# 4. check_optional_uint_vectors
# ---------------------------------------------------------------------------


@pytest.mark.order(106)
async def test_check_optional_uint_vectors_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_optional_uint_vectors (GQL): Option<vector<uN>> with mix of None/bytes."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_optional_uint_vectors",
        arguments=[None, _SAMP_BYTES, None, None, None],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_optional_uint_vectors")


@pytest.mark.order(107)
async def test_check_optional_uint_vectors_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_optional_uint_vectors (gRPC): Option<vector<uN>> with mix of None/bytes."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_optional_uint_vectors",
        arguments=[None, _SAMP_BYTES, None, None, None],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_optional_uint_vectors")


# ---------------------------------------------------------------------------
# 5. check_vec_u8
# ---------------------------------------------------------------------------


@pytest.mark.order(108)
async def test_check_vec_u8_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_vec_u8 (GQL): vector<u8> passed as a Python string."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_vec_u8",
        arguments=["Foo"],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_vec_u8")


@pytest.mark.order(109)
async def test_check_vec_u8_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_vec_u8 (gRPC): vector<u8> passed as a Python string."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_vec_u8",
        arguments=["Foo"],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_vec_u8")


# ---------------------------------------------------------------------------
# 6. check_vec_optional_u8
# ---------------------------------------------------------------------------


@pytest.mark.order(110)
async def test_check_vec_optional_u8_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_vec_optional_u8 (GQL): Option<vector<u8>> passed as None."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_vec_optional_u8",
        arguments=[None],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_vec_optional_u8")


@pytest.mark.order(111)
async def test_check_vec_optional_u8_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_vec_optional_u8 (gRPC): Option<vector<u8>> passed as None."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_vec_optional_u8",
        arguments=[None],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_vec_optional_u8")


# ---------------------------------------------------------------------------
# 7. check_vec_deep_u8
# ---------------------------------------------------------------------------


@pytest.mark.order(112)
async def test_check_vec_deep_u8_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_vec_deep_u8 (GQL): vector<vector<vector<u8>>> via nested list of bytes."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_vec_deep_u8",
        arguments=[[_SAMP_BYTES]],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_vec_deep_u8")


@pytest.mark.order(113)
@pytest.mark.skip(reason="Known bug: gRPC deeply nested vector encoding - see issue #376")
async def test_check_vec_deep_u8_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_vec_deep_u8 (gRPC): vector<vector<vector<u8>>> via nested list of bytes."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_vec_deep_u8",
        arguments=[[_SAMP_BYTES]],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_vec_deep_u8")


# ---------------------------------------------------------------------------
# 8. check_address_vec
# ---------------------------------------------------------------------------


@pytest.mark.order(114)
async def test_check_address_vec_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_address_vec (GQL): vector<address> as list of hex address strings."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_address_vec",
        arguments=[[_ADDR_A, _ADDR_B]],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_address_vec")


@pytest.mark.order(115)
async def test_check_address_vec_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_address_vec (gRPC): vector<address> as list of hex address strings."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_address_vec",
        arguments=[[_ADDR_A, _ADDR_B]],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_address_vec")


# ---------------------------------------------------------------------------
# 9. check_id_vec
# ---------------------------------------------------------------------------


@pytest.mark.order(116)
async def test_check_id_vec_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_id_vec (GQL): vector<ID> as list of hex address strings."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_id_vec",
        arguments=[[_ADDR_A, _ADDR_B]],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_id_vec")


@pytest.mark.order(117)
async def test_check_id_vec_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_id_vec (gRPC): vector<ID> as list of hex address strings."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_id_vec",
        arguments=[[_ADDR_A, _ADDR_B]],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_id_vec")


# ---------------------------------------------------------------------------
# 10. check_string
# ---------------------------------------------------------------------------


@pytest.mark.order(118)
async def test_check_string_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_string (GQL): &String passed as Python str."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_string",
        arguments=["foo"],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_string")


@pytest.mark.order(119)
async def test_check_string_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_string (gRPC): &String passed as Python str."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_string",
        arguments=["foo"],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_string")


# ---------------------------------------------------------------------------
# 11. check_string_option
# ---------------------------------------------------------------------------


@pytest.mark.order(120)
async def test_check_string_option_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_string_option (GQL): Option<String> passed as None."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_string_option",
        arguments=[None],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_string_option")


@pytest.mark.order(121)
async def test_check_string_option_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_string_option (gRPC): Option<String> passed as None."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_string_option",
        arguments=[None],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_string_option")


# ---------------------------------------------------------------------------
# 12. check_string_vec
# ---------------------------------------------------------------------------


@pytest.mark.order(122)
async def test_check_string_vec_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_string_vec (GQL): vector<String> passed as list of Python strs."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_string_vec",
        arguments=[["foo", "bar"]],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_string_vec")


@pytest.mark.order(123)
async def test_check_string_vec_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_string_vec (gRPC): vector<String> passed as list of Python strs."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_string_vec",
        arguments=[["foo", "bar"]],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_string_vec")


# ---------------------------------------------------------------------------
# 13. check_vec_option_string
# ---------------------------------------------------------------------------


@pytest.mark.order(124)
async def test_check_vec_option_string_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_vec_option_string (GQL): vector<Option<String>> with mixed str/None."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_vec_option_string",
        arguments=[["foo", None, "Bar"]],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_vec_option_string")


@pytest.mark.order(125)
async def test_check_vec_option_string_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_vec_option_string (gRPC): vector<Option<String>> with mixed str/None."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_vec_option_string",
        arguments=[["foo", None, "Bar"]],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_vec_option_string")


# ---------------------------------------------------------------------------
# 14. check_bool
# ---------------------------------------------------------------------------


@pytest.mark.order(126)
async def test_check_bool_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_bool (GQL): bool passed as Python True."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_bool",
        arguments=[True],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_bool")


@pytest.mark.order(127)
async def test_check_bool_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_bool (gRPC): bool passed as Python True."""
    await asyncio.sleep(SETTLE_SECS)
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_bool",
        arguments=[True],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_bool")


# ---------------------------------------------------------------------------
# 15. get_sender → transfer_objects (address return value)
# ---------------------------------------------------------------------------


@pytest.mark.order(128)
async def test_get_sender_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """get_sender (GQL): address return value used as recipient in transfer_objects."""
    await asyncio.sleep(SETTLE_SECS)
    txer = gql_client.transaction()
    split_res = await txer.split_coin(coin=txer.gas, amounts=[1_000_000, 1_000_000])
    addr_result = await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::get_sender",
        arguments=[],
    )
    await txer.transfer_objects(transfers=split_res, recipient=addr_result)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL get_sender")


@pytest.mark.order(129)
async def test_get_sender_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """get_sender (gRPC): address return value used as recipient in transfer_objects."""
    await asyncio.sleep(SETTLE_SECS)
    addr = str(grpc_client.config.active_address)
    coins = await grpc_get_coins(owner=addr, client=grpc_client)
    assert len(coins) >= 1, "Need at least 1 coin for get_sender split"
    source_coin = coins[0].object_id
    txer = await grpc_client.transaction()
    split_res = await txer.split_coin(coin=source_coin, amounts=[1_000_000])
    addr_result = await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::get_sender",
        arguments=[],
    )
    await txer.transfer_objects(transfers=split_res, recipient=addr_result)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC get_sender")


# ---------------------------------------------------------------------------
# 16. create_parm_object → transfer_objects
# ---------------------------------------------------------------------------


@pytest.mark.order(130)
async def test_create_parm_object_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """create_parm_object (GQL): returns ParmObject transferred to self via transfer_objects."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr
    addr = str(gql_client.config.active_address)
    txer = gql_client.transaction()
    parm_obj = await txer.move_call(
        target=f"{pkg_addr}::parms::create_parm_object",
        arguments=[],
    )
    await txer.transfer_objects(transfers=[parm_obj], recipient=addr)
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL create_parm_object")


@pytest.mark.order(131)
async def test_create_parm_object_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """create_parm_object (gRPC): returns ParmObject transferred to self via transfer_objects."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr
    addr = str(grpc_client.config.active_address)
    txer = await grpc_client.transaction()
    parm_obj = await txer.move_call(
        target=f"{pkg_addr}::parms::create_parm_object",
        arguments=[],
    )
    await txer.transfer_objects(transfers=[parm_obj], recipient=addr)
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC create_parm_object")


# ---------------------------------------------------------------------------
# 17. check_phoney (optional object pattern)
# ---------------------------------------------------------------------------


@pytest.mark.order(132)
async def test_check_phoney_gql(
    gql_session_client: AsyncGqlClient,
    published_gql: PublishedPackage,
    phoney_gql_id: str,
) -> None:
    """check_phoney (GQL): wrap Phoney in optional_object, check, destroy_some, transfer back."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr
    addr = str(gql_session_client.config.active_address)

    txer = gql_session_client.transaction()
    opt_result = await txer.optional_object(
        optional_object=phoney_gql_id,
        type_arguments=[f"{pkg_addr}::parms::Phoney"],
    )
    await txer.move_call(
        target=f"{pkg_addr}::parms::check_phoney",
        arguments=[opt_result],
    )
    popped = await txer.move_call(
        target="0x1::option::destroy_some",
        arguments=[opt_result],
        type_arguments=[f"{pkg_addr}::parms::Phoney"],
    )
    await txer.transfer_objects(transfers=[popped], recipient=addr)
    result = await gql_session_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_phoney")


@pytest.mark.order(133)
async def test_check_phoney_grpc(
    grpc_session_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
    phoney_grpc_id: str,
) -> None:
    """check_phoney (gRPC): wrap Phoney in optional_object, check, destroy_some, transfer back."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr
    addr = str(grpc_session_client.config.active_address)

    txer = await grpc_session_client.transaction()
    opt_result = await txer.optional_object(
        optional_object=phoney_grpc_id,
        type_arguments=[f"{pkg_addr}::parms::Phoney"],
    )
    await txer.move_call(
        target=f"{pkg_addr}::parms::check_phoney",
        arguments=[opt_result],
    )
    popped = await txer.move_call(
        target="0x1::option::destroy_some",
        arguments=[opt_result],
        type_arguments=[f"{pkg_addr}::parms::Phoney"],
    )
    await txer.transfer_objects(transfers=[popped], recipient=addr)
    result = await grpc_session_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_phoney")


# ---------------------------------------------------------------------------
# 18. burn_phoney (lifecycle completion)
# ---------------------------------------------------------------------------


@pytest.mark.order(134)
async def test_burn_phoney_gql(
    gql_session_client: AsyncGqlClient,
    published_gql: PublishedPackage,
    phoney_gql_id: str,
) -> None:
    """burn_phoney (GQL): consume and delete the Phoney object created in this session."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_gql.pkg_addr

    txer = gql_session_client.transaction()
    await txer.move_call(
        target=f"{pkg_addr}::parms::burn_phoney",
        arguments=[phoney_gql_id],
    )
    result = await gql_session_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL burn_phoney")


@pytest.mark.order(135)
async def test_burn_phoney_grpc(
    grpc_session_client: SuiGrpcClient,
    published_grpc: PublishedPackage,
    phoney_grpc_id: str,
) -> None:
    """burn_phoney (gRPC): consume and delete the Phoney object created in this session."""
    await asyncio.sleep(SETTLE_SECS)
    pkg_addr = published_grpc.pkg_addr

    txer = await grpc_session_client.transaction()
    await txer.move_call(
        target=f"{pkg_addr}::parms::burn_phoney",
        arguments=[phoney_grpc_id],
    )
    result = await grpc_session_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC burn_phoney")


# ---------------------------------------------------------------------------
# 19. check_all (xfail — ParmScalars is an embedded struct field of ParmObject,
#     not a standalone on-chain object; no direct PTB path to pass &ParmScalars)
# ---------------------------------------------------------------------------


@pytest.mark.order(136)
@pytest.mark.xfail(
    reason=(
        "check_all requires &ParmScalars, an embedded field of ParmObject. "
        "PTB cannot borrow a struct field from an object; no direct call path."
    ),
    strict=True,
)
async def test_check_all_gql(
    gql_client: AsyncGqlClient, published_gql: PublishedPackage
) -> None:
    """check_all (GQL): expected to fail — ParmScalars is not callable directly."""
    txer = gql_client.transaction()
    await txer.move_call(
        target=f"{published_gql.pkg_addr}::parms::check_all",
        type_arguments=["u8"],
        arguments=[True, 1, 256, "hello", None, b"bytes", ["a", "b"], None, []],
    )
    result = await gql_client.execute_query_node(
        with_node=qn.ExecuteTransaction(**await txer.build_and_sign())
    )
    _assert_gql_success(result, "GQL check_all")


@pytest.mark.order(137)
@pytest.mark.xfail(
    reason=(
        "check_all requires &ParmScalars, an embedded field of ParmObject. "
        "PTB cannot borrow a struct field from an object; no direct call path."
    ),
    strict=True,
)
async def test_check_all_grpc(
    grpc_client: SuiGrpcClient, published_grpc: PublishedPackage
) -> None:
    """check_all (gRPC): expected to fail — ParmScalars is not callable directly."""
    txer = await grpc_client.transaction()
    await txer.move_call(
        target=f"{published_grpc.pkg_addr}::parms::check_all",
        type_arguments=["u8"],
        arguments=[True, 1, 256, "hello", None, b"bytes", ["a", "b"], None, []],
    )
    result = await grpc_client.execute(
        request=rn.ExecuteTransaction(**await txer.build_and_sign(use_account_for_gas=True))
    )
    _assert_grpc_success(result, "gRPC check_all")
