#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sample module for gRPC and GraphQL subscription examples for Pysui 1.3.0.

Subscriptions are NOT SuiCommand/UCI-compatible (the uniform-ask premise
behind ``encode_fn`` breaks down for streaming: gRPC's read_mask is a
runtime FieldMask value, GraphQL's equivalent is the query's static
selection set). Each protocol's native subscription path is demonstrated
separately:

- gRPC: ``client.execute_grpc_request()`` against the three ``Subscribe*``
  request classes in ``pysui.sui.sui_grpc.pgrpc_requests``. Requires a
  ``GrpcProtocolClient`` (``PysuiConfiguration.SUI_GRPC_GROUP``).
- GraphQL: raw ``httpx`` + ``httpx-sse`` against the GraphQL subscriptions
  endpoint. This bypasses pysui's GQL client entirely — the client has no
  native subscription support. Takes a ``PysuiConfiguration`` directly, not a
  client.

All subscription functions here are a bare single-shot: no reconnect
logic is implemented. Mysten's public gRPC load balancer resets filtered
streams after ~30s (``grpclib.exceptions.StreamTerminatedError``) — this
is expected common-good-server behavior, not an error, and a production
consumer should reconnect and resume from the last watermark cursor via
the paired List API. Whether GraphQL subscriptions are subject to a
similar timeout is unconfirmed — the ~30s figure is specific to Mysten's
free public gRPC load balancer and should not be assumed to apply
universally or to other providers, so no artificial cap is imposed here
either; the GQL functions rely on the same bare exception handler.
"""

import asyncio
import json

import httpx
from httpx_sse import aconnect_sse
from grpclib.exceptions import StreamTerminatedError

from pysui import PysuiConfiguration, client_factory
from pysui.sui.sui_grpc.pgrpc_clients import GrpcProtocolClient
import pysui.sui.sui_grpc.pgrpc_requests as rn
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot

import pysui.sui.sui_grpc.pgrpc_filters as pgf


async def do_grpc_subscribe_checkpoints(client: GrpcProtocolClient) -> None:
    """Stream checkpoints via gRPC SubscribeCheckpoints.

    See module docstring for the stream-termination note.
    """
    fields = ["sequence_number", "digest", "summary.timestamp"]
    # Example filter — uncomment and adjust the predicate as needed:
    # cp_filter = pgf.build_transaction_filter(
    #     terms=[[pgf.Literal(predicate="sender", value="0x...")]]
    # )
    request = rn.SubscribeCheckpoints(field_mask=fields, tx_filter=None)
    result = await client.execute_grpc_request(request=request)
    if not result.is_ok():
        print(result.result_string)
        return
    count = 0
    try:
        async for checkpoint in result.result_data:
            print(checkpoint.to_json(indent=2))
            count += 1
    except StreamTerminatedError:
        print(
            f"Stream terminated by remote after {count} message(s) "
            "(expected ~30s public-node load-balancer timeout, not an "
            "error). Reconnect and resume from the last watermark cursor "
            "via the paired List API to continue."
        )


async def do_grpc_subscribe_transactions(client: GrpcProtocolClient) -> None:
    """Stream finalized transactions via gRPC SubscribeTransactions, filtered by sender.

    Filters on the configured active address (client.config.active_address).
    Change this to any valid Sui address you want to watch instead. Once
    this is running, fire off a transaction from the watched address (e.g.
    from another terminal/session) to see a matching message printed —
    otherwise nothing prints until the load-balancer terminates the stream
    (see module docstring). On termination, backfills any transactions
    missed during the gap via ListTransactions (resuming from the last
    watermark cursor), then reconnects the subscription once to
    demonstrate the reconnect/resume pattern documented in
    subscriptions.rst.
    """
    max_reconnects = 1
    fields = ["digest", "checkpoint"]
    tx_filter = pgf.build_transaction_filter(
        terms=[[pgf.Literal(predicate="sender", value=client.config.active_address)]]
    )
    last_cursor = None
    reconnects_used = 0
    while True:
        request = rn.SubscribeTransactions(field_mask=fields, tx_filter=tx_filter)
        result = await client.execute_grpc_request(request=request)
        if not result.is_ok():
            print(result.result_string)
            return
        print(
            f"Subscribed (attempt {reconnects_used + 1}) — fire a "
            "transaction now to see it picked up."
        )
        count = 0
        try:
            async for txn in result.result_data:
                if txn.watermark:
                    last_cursor = txn.watermark.cursor
                print(txn.to_json(indent=2))
                count += 1
        except StreamTerminatedError:
            print(
                f"Stream terminated by remote after {count} message(s) "
                "(expected ~30s public-node load-balancer timeout, not an "
                "error)."
            )
            if reconnects_used >= max_reconnects:
                print(f"Max reconnects ({max_reconnects}) reached. Stopping.")
                return
            reconnects_used += 1
            print(
                "Backfilling via ListTransactions from last watermark "
                f"cursor (reconnect {reconnects_used}/{max_reconnects})..."
            )
            backfill_request = rn.ListTransactions(
                field_mask=fields,
                tx_filter=tx_filter,
                options=sui_prot.QueryOptions(after=last_cursor),
            )
            backfill_result = await client.execute_grpc_request(
                request=backfill_request
            )
            if not backfill_result.is_ok():
                print(backfill_result.result_string)
                return
            async for msg in backfill_result.result_data:
                if msg.watermark:
                    last_cursor = msg.watermark.cursor
                print(msg.to_json(indent=2))
            print("Resuming live subscription...")


async def do_grpc_subscribe_events(client: GrpcProtocolClient) -> None:
    """Stream emitted events via gRPC SubscribeEvents.

    See module docstring for the stream-termination note.
    """
    fields = ["timestamp", "transaction_module"]
    # Example filter — uncomment and adjust the predicate as needed:
    # ev_filter = pgf.build_event_filter(
    #     terms=[[pgf.Literal(predicate="event_type", value="0x...")]]
    # )
    request = rn.SubscribeEvents(field_mask=fields, event_filter=None)
    result = await client.execute_grpc_request(request=request)
    if not result.is_ok():
        print(result.result_string)
        return
    count = 0
    try:
        async for event in result.result_data:
            print(event.to_json(indent=2))
            count += 1
    except StreamTerminatedError:
        print(
            f"Stream terminated by remote after {count} message(s) "
            "(expected ~30s public-node load-balancer timeout, not an "
            "error). Reconnect and resume from the last watermark cursor "
            "via the paired List API to continue."
        )


async def do_gql_subscribe_checkpoints(config: PysuiConfiguration) -> None:
    """Stream checkpoints via raw GraphQL SSE subscription.

    See module docstring: bypasses pysui's GQL client entirely.
    """
    sub_url = f"{config.url}/subscriptions"
    query = (
        "subscription { checkpoints { cursor node { sequenceNumber "
        "timestamp networkTotalTransactions } } }"
    )
    payload = {"query": query}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    timeout = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            async with aconnect_sse(
                http_client, "POST", sub_url, json=payload, headers=headers
            ) as source:
                async for event in source.aiter_sse():
                    if event.data:
                        print(json.dumps(json.loads(event.data), indent=2))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")


async def do_gql_subscribe_transactions(config: PysuiConfiguration) -> None:
    """Stream transactions via raw GraphQL SSE subscription, filtered by sender.

    Filters on the configured active address (config.active_address). Change
    this to any valid Sui address you want to watch instead. Once this is
    running, fire off a transaction from the watched address (e.g. from
    another terminal/session) to see a matching message printed.

    See module docstring: bypasses pysui's GQL client entirely.
    """
    sub_url = f"{config.url}/subscriptions"
    query = (
        "subscription($filter: TransactionFilter) { "
        "transactions(filter: $filter) { cursor node { digest "
        "sender { address } } } }"
    )
    payload = {
        "query": query,
        "variables": {"filter": {"sentAddress": config.active_address}},
    }
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    timeout = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            async with aconnect_sse(
                http_client, "POST", sub_url, json=payload, headers=headers
            ) as source:
                async for event in source.aiter_sse():
                    if event.data:
                        print(json.dumps(json.loads(event.data), indent=2))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")


async def do_gql_subscribe_events(config: PysuiConfiguration) -> None:
    """Stream events via raw GraphQL SSE subscription.

    See module docstring: bypasses pysui's GQL client entirely.
    """
    sub_url = f"{config.url}/subscriptions"
    query = (
        "subscription { events { cursor node { timestamp "
        "sender { address } transactionModule { name } } } }"
    )
    payload = {"query": query}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    timeout = httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            async with aconnect_sse(
                http_client, "POST", sub_url, json=payload, headers=headers
            ) as source:
                async for event in source.aiter_sse():
                    if event.data:
                        print(json.dumps(json.loads(event.data), indent=2))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")


async def main_gql():
    """Run subscriptions using GraphQL.

    GraphQL functions take a PysuiConfiguration directly on SUI_GQL_RPC_GROUP
    or user defined group for GraphQL.
    """
    try:
        ## GraphQL subscriptions
        gql_config = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
            profile_name="devnet",
            # profile_name="testnet",
            # profile_name="mainnet",
        )
        # await do_gql_subscribe_checkpoints(gql_config)
        await do_gql_subscribe_transactions(gql_config)
        # await do_gql_subscribe_events(gql_config)
    except (ValueError, NotImplementedError) as ve:
        print(ve)


async def main_grpc():
    """Run subscriptions using gRPC.

    gRPC functions require a GrpcProtocolClient built from a
    PysuiConfiguration on SUI_GRPC_GROUP or user defined group for gRPC.
    """
    grpc_client: GrpcProtocolClient = None
    try:
        grpc_config = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP,
            profile_name="devnet",
            # profile_name="testnet",
            # profile_name="mainnet",
        )
        grpc_client = client_factory(grpc_config)

        ## gRPC subscriptions
        # await do_grpc_subscribe_checkpoints(grpc_client)
        await do_grpc_subscribe_transactions(grpc_client)
        # await do_grpc_subscribe_events(grpc_client)

    except (ValueError, NotImplementedError) as ve:
        print(ve)
    finally:
        if grpc_client:
            await grpc_client.close()


async def main():
    """Run subscription example functions against a live Sui node.

    To switch which example runs, comment/uncomment the calls below.
    """
    try:
        await main_grpc()
        # await main_gql()

    except (ValueError, NotImplementedError) as ve:
        print(ve)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, asyncio.CancelledError, Exception) as rte:
        print(rte)
