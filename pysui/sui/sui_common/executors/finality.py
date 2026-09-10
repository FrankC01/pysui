#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Transaction finality polling for executors.

Finality and indexing are distinct on Sui: a transaction can be final while the node
serving reads has not yet indexed it. An executor that caches post-execution object
versions must wait for indexing before publishing those versions for a later
transaction to use, or that transaction builds against state the node cannot serve.

Three layers are kept strictly apart here, because conflating them is what let an
earlier version of this module poll for its full timeout on conditions that could
never resolve, then report the result as an ordinary timeout:

* protocol -- ``result.is_ok()``: whether the RPC itself worked. Says nothing about
  the chain, and no amount of polling changes it.
* chain -- the transaction's own execution status, success or failure. Terminal.
* indexing -- ``checkpoint`` present and not None: whether the read-serving node can
  answer for this transaction yet. This is the only condition worth waiting on.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import TYPE_CHECKING

import pysui.sui.sui_common.sui_commands as cmd
from pysui.sui.sui_common.instrumentation import count, instrumented

if TYPE_CHECKING:
    from pysui import AsyncClientBase

logger = logging.getLogger(__name__)


class FinalityOutcome(Enum):
    """Why a finality wait ended.

    Only INDEXED means the read-serving node can answer for the transaction's objects.
    On every other member the caller must not publish those versions, and should treat
    any version it already seeded for the same objects as untrustworthy.
    """

    INDEXED = "indexed"
    TIMED_OUT = "timed_out"
    FAILED_ON_CHAIN = "failed_on_chain"
    PROTOCOL_ERROR = "protocol_error"


def _ended(outcome: FinalityOutcome, digest: str, detail: str) -> FinalityOutcome:
    """Count and log a non-INDEXED outcome, then return it.

    Every early exit routes through here so a skipped registry publish can never be
    silent again. The absence of exactly this signal is what let a stale registry take
    a whole batch down with no indication of why.
    """
    count(f"executor.finality.{outcome.value}")
    logger.warning(
        "wait_for_finality: %s for digest %s: %s", outcome.value, digest, detail
    )
    return outcome


@instrumented("executor.finality.wait_for_finality")
async def wait_for_finality(
    *,
    client: "AsyncClientBase",
    digest: str,
    timeout: float = 60.0,
    poll_interval: float = 0.5,
) -> FinalityOutcome:
    """Poll until the read-serving node has indexed the transaction.

    Returns INDEXED once GetTransaction reports a checkpoint that is present and not
    None. GetTransaction is a SuiCommand returning the same ExecutedTransaction proto
    on every protocol, so this check is protocol agnostic.

    PROTOCOL_ERROR and FAILED_ON_CHAIN return immediately rather than polling: neither
    is a condition waiting can change. They are returned rather than raised because the
    executor's contract is that every submitted item resolves its future, and an
    exception escaping here would kill the execute task and leave that future pending
    forever.

    TIMED_OUT means the transaction is genuinely still unindexed after ``timeout``.

    :param client: Async protocol client used to issue GetTransaction
    :type client: AsyncClientBase
    :param digest: Digest of the transaction to wait for
    :type digest: str
    :param timeout: Seconds to keep polling before giving up, defaults to 60.0
    :type timeout: float, optional
    :param poll_interval: Seconds between polls, defaults to 0.5
    :type poll_interval: float, optional
    :return: Which condition ended the wait
    :rtype: FinalityOutcome
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        result = await client.execute(command=cmd.GetTransaction(digest=digest))

        if not result.is_ok():
            return _ended(FinalityOutcome.PROTOCOL_ERROR, digest, result.result_string)

        executed = result.result_data
        status = getattr(getattr(executed, "effects", None), "status", None)
        if status is not None and status.success is False:
            return _ended(
                FinalityOutcome.FAILED_ON_CHAIN,
                digest,
                str(getattr(status, "error", "")),
            )

        if getattr(executed, "checkpoint", None) is not None:
            return FinalityOutcome.INDEXED

        if loop.time() >= deadline:
            return _ended(
                FinalityOutcome.TIMED_OUT, digest, f"not indexed after {timeout}s"
            )

        await asyncio.sleep(poll_interval)
