=============
Subscriptions
=============

Subscriptions deliver a live feed of checkpoints, transactions, or events
as they are finalized or emitted, without polling. Subscriptions are
**not** SuiCommand/UCI-compatible: gRPC's read mask is a runtime
``FieldMask`` value, while GraphQL's equivalent is the query's static
selection set — these aren't expressible as a single uniform parameter,
so subscriptions fall outside the SuiCommand model. Each protocol's
native subscription path is used directly, as shown below.

See ``ucs_subscription_examples.py`` in the project root for runnable
examples of all six subscription functions (three gRPC, three GraphQL).

gRPC Subscriptions
-------------------

The gRPC transport supports native server-side streaming via three request
classes in :py:mod:`pysui.sui.sui_grpc.pgrpc_requests`:

.. list-table::
   :header-rows: 1

   * - RPC
     - Request class
     - Filter field
   * - ``SubscribeCheckpoints``
     - :py:class:`~pysui.sui.sui_grpc.pgrpc_requests.SubscribeCheckpoints`
     - ``tx_filter`` (``TransactionFilter``)
   * - ``SubscribeTransactions``
     - :py:class:`~pysui.sui.sui_grpc.pgrpc_requests.SubscribeTransactions`
     - ``tx_filter`` (``TransactionFilter``)
   * - ``SubscribeEvents``
     - :py:class:`~pysui.sui.sui_grpc.pgrpc_requests.SubscribeEvents`
     - ``event_filter`` (``EventFilter``)

Subscriptions execute via ``client.execute_grpc_request()`` — **not**
``client.execute(command=...)`` — since these requests are not
``SuiCommand`` instances. The result's ``result_data`` is a raw async
generator yielding decoded protobuf response objects (e.g.
``SubscribeTransactionsResponse``) — call ``.to_json()`` on each to
inspect it, as shown below.

.. note::

    Mysten Labs servers impose rate limits on subscription endpoints.

.. code-block:: python
   :linenos:

    import asyncio
    from pysui import PysuiConfiguration, client_factory
    import pysui.sui.sui_grpc.pgrpc_requests as rn
    import pysui.sui.sui_grpc.pgrpc_filters as pgf
    from grpclib.exceptions import StreamTerminatedError

    async def stream_transactions():
        """Stream transactions sent by the active address, via gRPC subscription."""
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GRPC_GROUP, profile_name="devnet"
        )
        client = client_factory(cfg)  # returns GrpcProtocolClient

        tx_filter = pgf.build_transaction_filter(
            terms=[[pgf.Literal(predicate="sender", value=cfg.active_address)]]
        )
        request = rn.SubscribeTransactions(
            field_mask=["digest", "checkpoint"], tx_filter=tx_filter
        )
        result = await client.execute_grpc_request(request=request)

        count = 0
        try:
            async for txn in result.result_data:
                print(txn.to_json(indent=2))
                count += 1
        except StreamTerminatedError:
            # Mysten's public gRPC load balancer resets filtered streams
            # after ~30s (HTTP/2 RST_STREAM) — expected behavior, not an
            # error. See "Stream termination and reconnect" below.
            print(f"Stream terminated after {count} message(s) — see docs.")

        await client.close()

    if __name__ == "__main__":
        asyncio.run(stream_transactions())

See ``ucs_subscription_examples.py`` in the project root for runnable
versions of all three gRPC subscription functions.

Filtering (gRPC)
~~~~~~~~~~~~~~~~~

:py:mod:`pysui.sui.sui_grpc.pgrpc_filters` builds the DNF (disjunctive
normal form) filter protos consumed by ``tx_filter``/``event_filter``, as
used in the example above. The filter grammar, in EBNF:

.. code-block:: text

    filter     = term , { "OR" , term } ;
    term       = literal , { "AND" , literal } ;
    literal    = [ "NOT" ] , predicate , "=" , value ;
    predicate  = tx-predicate | event-predicate ;
    tx-predicate    = "sender" | "affected_address" | "affected_object"
                     | "move_call" | "emit_module" | "event_type"
                     | "event_stream_head" | "package_write" ;
    event-predicate = "sender" | "emit_module" | "event_type"
                     | "event_stream_head" ;

``build_transaction_filter`` accepts the full ``tx-predicate`` set;
``build_event_filter`` accepts only ``event-predicate``. In the Python
API, ``filter`` maps to the outer ``terms`` list (ORed), ``term`` maps to
one inner list of :py:class:`~pysui.sui.sui_grpc.pgrpc_filters.Literal`
values (ANDed), and ``NOT`` maps to ``Literal(..., negated=True)``. For
example, "sent by address A, OR calls module M and was NOT written by
package P":

.. code-block:: python

    pgf.build_transaction_filter(
        terms=[
            [pgf.Literal(predicate="sender", value="0xA...")],
            [
                pgf.Literal(predicate="move_call", value="0xM...::mod"),
                pgf.Literal(predicate="package_write", value="0xP...", negated=True),
            ],
        ]
    )

Progress frames and cursor semantics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The server periodically sends cursor-only "progress" (watermark) frames —
no ``checkpoint``/``transaction``/``event`` payload — when no filter match
has occurred since the last message. A genuine match produces a full
payload alongside the watermark. Don't mistake cursor-only output for a
broken filter.

.. note::

    ``SubscribeCheckpointsResponse.cursor`` is the checkpoint **sequence
    number** (``uint64``), not a digest.

Stream termination and reconnect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mysten's public gRPC common-good servers enforce a load-balancer timeout
(~30 seconds) on subscription streams, terminating the connection with
``grpclib.exceptions.StreamTerminatedError`` (HTTP/2 ``RST_STREAM``), as
caught in the example above. This is expected, periodic behavior on
public infrastructure — not an error condition, and not specific to
whether a filter has matched. A production consumer should catch this
exception and reconnect, resuming from the last watermark cursor.

Resumption is intended to work via the paired List RPCs on
``LedgerService`` (``ListCheckpoints``, ``ListTransactions``,
``ListEvents`` — unary-stream, filterable, orderable by sequence),
passing the last watermark cursor as the resume point. The examples in
``ucs_subscription_examples.py`` catch and report the stream termination
but do not implement reconnect.

GraphQL Subscriptions
-----------------------

The GraphQL schema exposes a ``Subscription`` type with ``checkpoints``,
``transactions``, and ``events`` fields on any network whose schema
includes it — but **pysui's GraphQL client has no native subscription
support**; subscriptions are not reachable through
:py:class:`~pysui.sui.sui_pgql.pgql_clients.GqlProtocolClient`. This is
because GraphQL subscriptions use Server-Sent Events (SSE) rather than
the client's request/response transport. Use raw ``httpx`` + ``httpx-sse``
against the network's GraphQL subscriptions endpoint instead
(``{graphql_url}/subscriptions``).

.. code-block:: python
   :linenos:

    import asyncio
    import json
    import httpx
    from httpx_sse import aconnect_sse
    from pysui import PysuiConfiguration

    async def stream_transactions():
        """Stream transactions sent by the active address, via GraphQL SSE."""
        cfg = PysuiConfiguration(
            group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP, profile_name="devnet"
        )
        sub_url = f"{cfg.url}/subscriptions"
        query = (
            "subscription($filter: TransactionFilter) { "
            "transactions(filter: $filter) { cursor node { digest sender { address } } } }"
        )
        payload = {
            "query": query,
            "variables": {"filter": {"sentAddress": cfg.active_address}},
        }
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}

        async with httpx.AsyncClient() as http_client:
            async with aconnect_sse(
                http_client, "POST", sub_url, json=payload, headers=headers
            ) as source:
                async for event in source.aiter_sse():
                    if event.data:
                        print(json.dumps(json.loads(event.data), indent=2))

    if __name__ == "__main__":
        asyncio.run(stream_transactions())

See ``ucs_subscription_examples.py`` in the project root for runnable
versions of all three GraphQL subscription functions.

Filtering (GraphQL)
~~~~~~~~~~~~~~~~~~~~

``transactions`` and ``events`` accept an optional ``filter`` argument
(``TransactionFilter`` / ``EventFilter`` respectively), passed as a
GraphQL variable — as shown in the example above using ``sentAddress`` —
rather than interpolated into the query string.

``TransactionFilter`` fields include ``sentAddress`` (sender),
``affectedAddress``, ``affectedObject``, ``function`` (move call target),
``kind``, ``atCheckpoint``, ``afterCheckpoint``, ``beforeCheckpoint``.
Consult the active network's GraphQL schema for the full field set and
the ``EventFilter`` shape, as these evolve independently of pysui.

``checkpoints`` does not currently accept a filter — only cursor-based
pagination (``after``/``afterCheckpoint``).

Response shape and cursor semantics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Events are framed per the ``graphql-sse`` protocol: each matching item
arrives as a ``next``-type SSE event carrying a JSON payload shaped like a
Relay edge — ``{"data": {"<field>": {"cursor": ..., "node": {...}}}}``.

Stream termination
~~~~~~~~~~~~~~~~~~~~

Whether GraphQL subscriptions are subject to a load-balancer timeout
similar to gRPC's ~30 second limit is unconfirmed — that figure is
specific to Mysten's free public gRPC load balancer and should not be
assumed to apply to GraphQL or to other providers. The examples in
``ucs_subscription_examples.py`` use a bare exception handler with no
artificial cap.
