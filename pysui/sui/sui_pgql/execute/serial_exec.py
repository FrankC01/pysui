#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
import base64
import logging
import time
from typing import Any, Awaitable, Callable, Optional, Union

from pysui import AsyncGqlClient
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.executors import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    SerialQueue,
)
import pysui.sui.sui_pgql.pgql_types as ptypes
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_bcs.bcs as bcs
import pysui.sui.sui_bcs.bcs_txne as bcst
from .caching_exec import AsyncCachingTransactionExecutor
from .caching_txn import CachingTransaction

ser_txn_exc_logger = logging.getLogger(__name__)


def _get_gascoin_from_effects(effects: bcst.TransactionEffects) -> bcs.ObjectReference:
    """Extract gas coin from transaction effects.

    :param effects: Transaction effects
    :type effects: bcst.TransactionEffects
    :return: Gas coin object reference
    :rtype: bcs.ObjectReference
    :raises ValueError: If effects version is not V2 or gas object not found
    """
    if effects.enum_name != "V2":
        raise ValueError(f"Expect V2 effects, found {effects.enum_name}")
    v2effects: bcst.TransactionEffectsV2 = effects.value
    gas_object_change = v2effects.changedObjects[v2effects.gasObjectIndex.value]
    if not gas_object_change:
        raise ValueError("Gas object not found in effects")

    gas_address, effchange = gas_object_change
    if effchange.outputState.enum_name != "ObjectWrite":
        raise ValueError("Unexpected gas object state")

    edigest, _eowner = effchange.outputState.value
    ser_txn_exc_logger.debug("Have gas coin from effects")
    return bcs.ObjectReference(gas_address, v2effects.lamportVersion, edigest)


class SerialTransactionExecutor:
    """Executes transactions serially with caching and optional gas replenishment.

    Gas replenishment callbacks (on_coins_low / on_balance_low) are mutually exclusive:
    - on_coins_low: used when gas is paid via Coin<SUI> objects. The callback should
      return a list of new coin IDs to inject. After a successful callback, the executor
      re-fetches the gas owner's coin_balance to re-arm threshold tracking.
    - on_balance_low: used when gas is paid via address accumulator. The callback MUST
      complete a funding transaction before returning — the returned address is the funding
      source and is used only for logging. After a successful callback, the executor
      re-fetches the gas owner's address_balance to verify funds arrived and re-arm tracking.

    Both callbacks receive an ExecutorContext. The gas_coins field of that context is a
    read-only snapshot — mutating it has no effect on the executor's internal state.

    Note: execute_transactions is not re-entrant. Concurrent calls on the same instance
    are serialized by an internal asyncio.Lock.
    """

    def __init__(
        self,
        *,
        client: AsyncGqlClient,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
        default_gas_budget: int = 50_000_000,
        min_balance_threshold: Optional[int] = None,
        on_coins_low: Optional[
            Callable[[ExecutorContext], Awaitable[list[str] | None]]
        ] = None,
        on_balance_low: Optional[
            Callable[[ExecutorContext], Awaitable[str | None]]
        ] = None,
    ):
        """Initialize SerialTransactionExecutor.

        :param client: Asynchronous GraphQL client
        :type client: AsyncGqlClient
        :param sender: Sender address or SigningMultiSig
        :type sender: Union[str, SigningMultiSig]
        :param sponsor: Optional sponsor address or SigningMultiSig, defaults to None
        :type sponsor: Optional[Union[str, SigningMultiSig]], optional
        :param default_gas_budget: Default gas budget, defaults to 50_000_000
        :type default_gas_budget: int
        :param min_balance_threshold: Minimum balance threshold that triggers a replenishment
            callback. A tracked_balance strictly less than this value triggers the callback.
            Requires either on_coins_low or on_balance_low to be provided.
        :type min_balance_threshold: Optional[int], optional
        :param on_coins_low: Async callback when coin balance drops below threshold.
            Return new coin IDs to inject, or None/[] to halt execution.
        :type on_coins_low: Optional[Callable[[ExecutorContext], Awaitable[list[str] | None]]]
        :param on_balance_low: Async callback when address balance drops below threshold.
            Must perform the funding transaction before returning. Return the funding source
            address (for logging), or None to halt execution.
        :type on_balance_low: Optional[Callable[[ExecutorContext], Awaitable[str | None]]]
        :raises ValueError: If min_balance_threshold is set without any replenishment callback
        """
        if min_balance_threshold is not None and on_coins_low is None and on_balance_low is None:
            raise ValueError(
                "min_balance_threshold requires either on_coins_low or on_balance_low callback"
            )
        self._signing_block = SignerBlock(sender=sender, sponsor=sponsor)
        self._client = client
        self._default_gas_budget: int = default_gas_budget
        self._min_balance_threshold = min_balance_threshold
        self._on_coins_low = on_coins_low
        self._on_balance_low = on_balance_low
        self._tracked_balance: Optional[int] = None
        # Prevent re-entrant execute_transactions calls on the same instance
        self._execution_lock = asyncio.Lock()
        # payer_address == sponsor if sponsor else sender
        self._cache: AsyncCachingTransactionExecutor = AsyncCachingTransactionExecutor(
            client, gas_owner=self._signing_block.payer_address
        )
        self._queue = SerialQueue()

    async def new_transaction(self) -> CachingTransaction:
        """Create a new caching transaction for transaction block building.

        :return: A new CachingTransaction
        :rtype: CachingTransaction
        """
        ser_txn_exc_logger.debug("Generate new transaction")
        return CachingTransaction(client=self._client)

    async def reset_cache(self) -> None:
        """Reset the internal cache.

        Note: this awaits the last committed transaction before clearing, which may
        involve a network poll. Do not call while holding a SerialQueue lock.
        """
        return await self._cache.reset()

    async def wait_for_last_transaction(self, poll_interval: float = 0.5) -> Any:
        """Waits for committed results of last execution.

        :param poll_interval: Polling interval in seconds, defaults to 0.5
        :type poll_interval: float
        :return: Transaction result
        :rtype: Any
        """
        return await self._cache.wait_for_last_transaction(poll_interval=poll_interval)

    def _build_executor_context(
        self, gas_coins: list[bcs.ObjectReference], tracked_balance: int
    ) -> ExecutorContext:
        """Build executor context for callbacks.

        :param gas_coins: List of gas coins (a defensive copy is made)
        :type gas_coins: list[bcs.ObjectReference]
        :param tracked_balance: Current tracked balance
        :type tracked_balance: int
        :return: Executor context
        :rtype: ExecutorContext
        """
        return ExecutorContext(
            sender=self._signing_block.sender_str,
            gas_owner=self._signing_block.payer_address,
            gas_coins=list(gas_coins),  # defensive copy — callers must not mutate cache state
            tracked_balance=tracked_balance,
        )

    async def _build_transaction(self, transaction: CachingTransaction) -> str:
        """Builds TransactionData for execution.

        :param transaction: Transaction to build
        :type transaction: CachingTransaction
        :return: Base64 encoded transaction bytes
        :rtype: str
        :raises TypeError: If the signer has no gas coins at all
        :raises ValueError: If all gas coins are in use or build otherwise fails
        """
        ser_txn_exc_logger.debug("in _build_transaction")
        transaction.set_gas_budget_if_notset(self._default_gas_budget)
        ser_txn_exc_logger.debug("Calling cache build transaction")
        return await self._cache.build_transaction(transaction, self._signing_block)

    def _sign_transaction(self, tx_str: str) -> list[str]:
        """Sign the transaction.

        :param tx_str: Base64 encoded TransactionData
        :type tx_str: str
        :return: List of base64 encoded signatures
        :rtype: list[str]

        Note: signing is synchronous CPU work. For HSM-backed or multi-sig keys with
        significant latency, consider wrapping in asyncio.to_thread.
        """
        return self._signing_block.get_signatures(
            config=self._client.config, tx_bytes=tx_str
        )

    async def _refresh_tracked_balance(self) -> Optional[int]:
        """Re-fetch and return the current tracked balance for the gas owner.

        Uses coin_balance if on_coins_low is set, address_balance otherwise.

        :return: Refreshed balance, or None if the fetch fails
        :rtype: Optional[int]
        """
        balance_result = await self._client.execute_query_node(
            with_node=qn.GetAddressCoinBalance(owner=self._signing_block.payer_address)
        )
        if not balance_result.is_ok():
            return None
        bal = balance_result.result_data.balance
        return bal.coin_balance if self._on_coins_low else bal.address_balance

    async def execute_transactions(
        self,
        transactions: list[CachingTransaction],
    ) -> list[Union[ptypes.ExecutionResultGQL, tuple[ExecutorError, Exception], ExecutionSkipped]]:
        """Serially execute one or more transactions.

        Returns a list of the same length as ``transactions``. Each element is one of:
        - ``ExecutionResultGQL``: transaction succeeded
        - ``(ExecutorError, Exception)``: transaction failed
        - ``ExecutionSkipped``: transaction was not attempted due to a prior failure

        This method may raise ValueError only on pre-flight failures (initial balance fetch)
        when replenishment is configured. All per-transaction errors are returned as tuples.

        :param transactions: The transactions to execute
        :type transactions: list[CachingTransaction]
        :return: The transaction execution results
        :rtype: list[Union[ptypes.ExecutionResultGQL, tuple[ExecutorError, Exception], ExecutionSkipped]]
        """

        async def _execute_single(
            index: int, tx: CachingTransaction
        ) -> Union[ptypes.ExecutionResultGQL, tuple[ExecutorError, Exception]]:
            """Execute one transaction; return an error tuple on failure (never raise)."""
            start_time = time.time()
            phase = "build"
            try:
                tx_str = await self._build_transaction(tx)
                phase = "sign"
                sig_list = self._sign_transaction(tx_str)
                phase = "execute"
                results = await self._cache.execute_transaction(tx_str, sig_list)
                if not isinstance(results, ptypes.ExecutionResultGQL):
                    return (ExecutorError.EXECUTING_ERROR, TypeError(
                        f"tx {index}: unexpected result type {type(results).__name__}"
                    ))

                effects = bcst.TransactionEffects.deserialize(
                    base64.b64decode(results.effects_bcs)
                )
                await self._cache.apply_effects(effects)

                # Decrement tracked balance by net gas cost from effects.
                # storageRebate in GasCostSummary is already net of nonRefundableStorageFee
                # in Sui 1.x — revisit if the protocol changes this field's semantics.
                if self._tracked_balance is not None:
                    gas_used = effects.value.gasUsed
                    self._tracked_balance -= (
                        gas_used.computationCost + gas_used.storageCost - gas_used.storageRebate
                    )

                # Update gas coin cache; on failure, invalidate so the next build fetches fresh.
                try:
                    new_gas_coin = _get_gascoin_from_effects(effects)
                    await self._cache.update_gas_coins([new_gas_coin])
                except Exception as e:
                    ser_txn_exc_logger.warning(
                        "Failed to update gas coin from effects for tx %s: %s", index, e
                    )
                    await self._cache.invalidate_gas_coins()

                ser_txn_exc_logger.info("tx %s execution time %.3fs", index, time.time() - start_time)
                return results

            except Exception as e:
                ser_txn_exc_logger.critical(
                    "tx %s [%s]: %s: %s", index, phase, type(e).__name__, e
                )
                # Classify by phase, not exception type — caching_exec raises both
                # ValueError and TypeError from build_transaction for different failure modes.
                if phase in ("build", "sign"):
                    return (ExecutorError.BUILDING_ERROR, e)
                else:
                    return (ExecutorError.EXECUTING_ERROR, e)

        async with self._execution_lock:
            # Lazy init: fetch balance once on the first call if threshold tracking is enabled.
            # min_balance_threshold == threshold value; tracked_balance < threshold triggers callback.
            if self._min_balance_threshold is not None and self._tracked_balance is None:
                try:
                    balance_result = await self._client.execute_query_node(
                        with_node=qn.GetAddressCoinBalance(owner=self._signing_block.payer_address)
                    )
                    if not balance_result.is_ok():
                        raise ValueError("Failed to fetch initial balance for threshold check")
                    bal = balance_result.result_data.balance
                    self._tracked_balance = (
                        bal.coin_balance if self._on_coins_low else bal.address_balance
                    )
                    if self._tracked_balance < self._min_balance_threshold:
                        raise ValueError(
                            f"Initial balance {self._tracked_balance} is below minimum "
                            f"threshold {self._min_balance_threshold}"
                        )
                except Exception as e:
                    exe_res: list[
                        Union[ptypes.ExecutionResultGQL, tuple[ExecutorError, Exception], ExecutionSkipped]
                    ] = [(ExecutorError.BUILDING_ERROR, e)]
                    for remaining_idx in range(1, len(transactions)):
                        exe_res.append(
                            ExecutionSkipped(
                                transaction_index=remaining_idx,
                                reason="balance initialization failed",
                            )
                        )
                    return exe_res

            exe_res = []

            for idx, tx in enumerate(transactions):
                result = await self._queue.run_task(lambda i=idx, t=tx: _execute_single(i, t))

                if isinstance(result, tuple) and result[0] in (
                    ExecutorError.BUILDING_ERROR,
                    ExecutorError.EXECUTING_ERROR,
                ):
                    # Reset cache AFTER run_task returns so we don't hold the SerialQueue
                    # lock during the (potentially long) wait_for_last_transaction poll.
                    await self.reset_cache()
                    self._tracked_balance = None  # clear stale balance so next call re-fetches
                    exe_res.append(result)
                    for remaining_idx in range(idx + 1, len(transactions)):
                        exe_res.append(
                            ExecutionSkipped(
                                transaction_index=remaining_idx,
                                reason="prior transaction failed",
                            )
                        )
                    break
                else:
                    exe_res.append(result)

                    # Check balance threshold. Strict < means exactly at the threshold is
                    # considered sufficient; the very next decrement will cross it.
                    if (
                        self._min_balance_threshold is not None
                        and self._tracked_balance < self._min_balance_threshold
                    ):
                        gas_coins = await self._cache.cache.getCustom("gasCoins")
                        ctx = self._build_executor_context(gas_coins or [], self._tracked_balance)

                        if self._on_coins_low:
                            try:
                                new_coins = await self._on_coins_low(ctx)
                            except Exception as e:
                                ser_txn_exc_logger.critical(
                                    "on_coins_low callback raised after tx %s: %s", idx, e
                                )
                                exe_res.append((ExecutorError.REPLENISHMENT_ERROR, e))
                                for remaining_idx in range(idx + 1, len(transactions)):
                                    exe_res.append(
                                        ExecutionSkipped(
                                            transaction_index=remaining_idx,
                                            reason="replenishment callback raised",
                                        )
                                    )
                                break

                            if new_coins:
                                coin_objs = await self._cache.get_sui_objects(
                                    {i: cid for i, cid in enumerate(new_coins)}
                                )
                                new_gas_coins = [
                                    bcs.ObjectReference(
                                        bcs.Address.from_str(coin.coin_object_id),
                                        coin.version,
                                        bcs.Digest.from_str(coin.object_digest),
                                    )
                                    for coin in coin_objs
                                    if isinstance(coin, ptypes.ObjectReadGQL)
                                ]
                                if new_gas_coins:
                                    await self._cache.update_gas_coins(new_gas_coins)
                                    # Re-arm tracked balance after successful replenishment.
                                    refreshed = await self._refresh_tracked_balance()
                                    if refreshed is not None:
                                        self._tracked_balance = refreshed
                                    ser_txn_exc_logger.debug(
                                        "Replenished with %s coins after tx %s; balance now %s",
                                        len(new_gas_coins), idx, self._tracked_balance,
                                    )
                                else:
                                    ser_txn_exc_logger.warning(
                                        "on_coins_low returned coin IDs after tx %s but fetch failed",
                                        idx,
                                    )
                                    for remaining_idx in range(idx + 1, len(transactions)):
                                        exe_res.append(
                                            ExecutionSkipped(
                                                transaction_index=remaining_idx,
                                                reason="coin replenishment failed",
                                            )
                                        )
                                    break
                            else:
                                ser_txn_exc_logger.debug(
                                    "on_coins_low returned None/empty after tx %s; halting", idx
                                )
                                for remaining_idx in range(idx + 1, len(transactions)):
                                    exe_res.append(
                                        ExecutionSkipped(
                                            transaction_index=remaining_idx,
                                            reason="coin replenishment declined",
                                        )
                                    )
                                break

                        elif self._on_balance_low:
                            # on_balance_low contract: the callback must complete the funding
                            # transaction before returning. The returned address is the funding
                            # source (for logging only). The executor re-verifies the gas owner's
                            # balance to confirm funds arrived.
                            try:
                                addr = await self._on_balance_low(ctx)
                            except Exception as e:
                                ser_txn_exc_logger.critical(
                                    "on_balance_low callback raised after tx %s: %s", idx, e
                                )
                                exe_res.append((ExecutorError.REPLENISHMENT_ERROR, e))
                                for remaining_idx in range(idx + 1, len(transactions)):
                                    exe_res.append(
                                        ExecutionSkipped(
                                            transaction_index=remaining_idx,
                                            reason="replenishment callback raised",
                                        )
                                    )
                                break

                            if addr:
                                ser_txn_exc_logger.debug(
                                    "on_balance_low reported funding from %s after tx %s; "
                                    "re-verifying gas owner balance",
                                    addr, idx,
                                )
                                refreshed = await self._refresh_tracked_balance()
                                if refreshed is not None:
                                    if refreshed >= self._min_balance_threshold:
                                        self._tracked_balance = refreshed
                                        ser_txn_exc_logger.debug(
                                            "Gas owner balance re-armed to %s after tx %s",
                                            refreshed, idx,
                                        )
                                    else:
                                        ser_txn_exc_logger.warning(
                                            "Gas owner balance %s still below threshold %s after "
                                            "replenishment; halting",
                                            refreshed, self._min_balance_threshold,
                                        )
                                        for remaining_idx in range(idx + 1, len(transactions)):
                                            exe_res.append(
                                                ExecutionSkipped(
                                                    transaction_index=remaining_idx,
                                                    reason="balance below threshold after replenishment",
                                                )
                                            )
                                        break
                                else:
                                    ser_txn_exc_logger.warning(
                                        "Balance re-verification failed for gas owner after tx %s",
                                        idx,
                                    )
                                    for remaining_idx in range(idx + 1, len(transactions)):
                                        exe_res.append(
                                            ExecutionSkipped(
                                                transaction_index=remaining_idx,
                                                reason="balance verification failed",
                                            )
                                        )
                                    break
                            else:
                                ser_txn_exc_logger.debug(
                                    "on_balance_low returned None after tx %s; halting", idx
                                )
                                for remaining_idx in range(idx + 1, len(transactions)):
                                    exe_res.append(
                                        ExecutionSkipped(
                                            transaction_index=remaining_idx,
                                            reason="balance replenishment declined",
                                        )
                                    )
                                break

            return exe_res
