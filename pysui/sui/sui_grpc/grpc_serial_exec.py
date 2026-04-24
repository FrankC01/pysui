#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution for gRPC."""

import asyncio
import base64
import logging
import time
from typing import Any, Awaitable, Callable, Optional, Union

grpc_ser_txn_exc_logger = logging.getLogger(__name__)

from pysui import AsyncGrpcClient
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.executors import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    SerialQueue,
)
import pysui.sui.sui_bcs.bcs as bcs
import pysui.sui.sui_bcs.bcs_txne as bcst
from pysui.sui.sui_grpc.pgrpc_async_txn import AsyncSuiTransaction


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
    grpc_ser_txn_exc_logger.debug("Have gas coin from effects")
    return bcs.ObjectReference(gas_address, v2effects.lamportVersion, edigest)


class GrpcSerialTransactionExecutor:
    """Executes transactions serially with caching and optional gas replenishment for gRPC."""

    def __init__(
        self,
        *,
        client: AsyncGrpcClient,
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
        """Initialize GrpcSerialTransactionExecutor.

        :param client: Asynchronous gRPC client
        :type client: AsyncGrpcClient
        :param sender: Sender address or SigningMultiSig
        :type sender: Union[str, SigningMultiSig]
        :param sponsor: Optional sponsor address or SigningMultiSig, defaults to None
        :type sponsor: Optional[Union[str, SigningMultiSig]], optional
        :param default_gas_budget: Default gas budget, defaults to 50_000_000
        :type default_gas_budget: int
        :param min_balance_threshold: Minimum balance threshold for replenishment trigger, defaults to None
        :type min_balance_threshold: Optional[int], optional
        :param on_coins_low: Async callback when gas coins are low, defaults to None
        :type on_coins_low: Optional[Callable[[ExecutorContext], Awaitable[list[str] | None]]], optional
        :param on_balance_low: Async callback when account balance is low, defaults to None
        :type on_balance_low: Optional[Callable[[ExecutorContext], Awaitable[str | None]]], optional
        """
        self._signing_block = SignerBlock(sender=sender, sponsor=sponsor)
        self._client = client
        self._default_gas_budget: int = default_gas_budget
        self._min_balance_threshold = min_balance_threshold
        self._on_coins_low = on_coins_low
        self._on_balance_low = on_balance_low
        self._queue = SerialQueue()
        # TODO: Implement gRPC caching executor similar to GraphQL version
        # self._cache: AsyncGrpcCachingTransactionExecutor = AsyncGrpcCachingTransactionExecutor(
        #     client, gas_owner=self._signing_block.payer_address
        # )

    async def new_transaction(self, **kwargs) -> AsyncSuiTransaction:
        """Create a new transaction for transaction block building.

        :return: A new AsyncSuiTransaction
        :rtype: AsyncSuiTransaction
        """
        grpc_ser_txn_exc_logger.debug("Generate new transaction")
        kwargs["client"] = self._client
        return await self._client.transaction(**kwargs)

    def _build_executor_context(
        self, gas_coins: list[bcs.ObjectReference], tracked_balance: int
    ) -> ExecutorContext:
        """Build executor context for callbacks.

        :param gas_coins: List of gas coins
        :type gas_coins: list[bcs.ObjectReference]
        :param tracked_balance: Current tracked balance
        :type tracked_balance: int
        :return: Executor context
        :rtype: ExecutorContext
        """
        return ExecutorContext(
            sender=self._signing_block.sender_str,
            gas_owner=self._signing_block.payer_address,
            gas_coins=gas_coins,
            tracked_balance=tracked_balance,
        )

    def _sign_transaction(self, tx_bytes: bytes) -> list[str]:
        """Sign the transaction.

        :param tx_bytes: Transaction bytes
        :type tx_bytes: bytes
        :return: List of base64 encoded signatures
        :rtype: list[str]
        :raises ValueError: If signing fails
        """
        # Convert bytes to base64 for signing interface
        tx_str = base64.b64encode(tx_bytes).decode("utf-8")
        return self._signing_block.get_signatures(
            config=self._client.config, tx_bytes=tx_str
        )

    async def execute_transactions(
        self,
        transactions: list[AsyncSuiTransaction],
    ) -> list[Union[Any, tuple[ExecutorError, Exception], ExecutionSkipped]]:
        """Serially execute one or more transactions.

        :param transactions: The transactions to execute
        :type transactions: list[AsyncSuiTransaction]
        :return: The transaction execution results
        :rtype: list[Union[Any, tuple[ExecutorError, Exception], ExecutionSkipped]]
        """

        async def _execute_single(
            index: int, tx: AsyncSuiTransaction
        ) -> Union[Any, tuple[ExecutorError, Exception], ExecutionSkipped]:
            """Execute a single transaction with error handling."""
            start_time = time.time()
            phase = "build"
            try:
                grpc_ser_txn_exc_logger.debug("Building transaction %s", index)
                tx_bytes = await tx.build(
                    sender=self._signing_block.sender_str,
                    sponsor=self._signing_block.sponsor_str,
                )
                phase = "sign"
                grpc_ser_txn_exc_logger.debug("Signing transaction %s", index)
                sig_list = self._sign_transaction(tx_bytes)

                phase = "execute"
                grpc_ser_txn_exc_logger.debug("Executing transaction %s", index)
                # TODO: Execute transaction via gRPC client
                # result = await self._client.execute_transaction(tx_bytes, sig_list)

                grpc_ser_txn_exc_logger.info(
                    "tx %s execution time %.3fs", index, time.time() - start_time
                )
                return None  # Placeholder for actual result

            except Exception as e:
                grpc_ser_txn_exc_logger.critical(
                    "tx %s [%s]: %s: %s", index, phase, type(e).__name__, e
                )
                if phase in ("build", "sign"):
                    return (ExecutorError.BUILDING_ERROR, e)
                else:
                    return (ExecutorError.EXECUTING_ERROR, e)

        exe_res: list[Union[Any, tuple[ExecutorError, Exception], ExecutionSkipped]] = []

        for idx, tx in enumerate(transactions):
            # Wire SerialQueue to serialize execution
            result = await self._queue.run_task(lambda idx=idx, tx=tx: _execute_single(idx, tx))

            # Check for error and decide whether to continue or halt
            if isinstance(result, tuple) and result[0] in (
                ExecutorError.BUILDING_ERROR,
                ExecutorError.EXECUTING_ERROR,
            ):
                exe_res.append(result)
                # Halt on first error - fill remaining slots with ExecutionSkipped
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

                # Check balance threshold if replenishment is enabled
                if self._min_balance_threshold is not None:
                    # TODO: Fetch balance from gRPC client
                    tracked_balance = 0

                    # Check if we need replenishment
                    if tracked_balance < self._min_balance_threshold:
                        ctx = self._build_executor_context([], tracked_balance)

                        # Try coins_low callback first
                        if self._on_coins_low:
                            grpc_ser_txn_exc_logger.debug(
                                "Calling on_coins_low callback after tx %s", idx
                            )
                            new_coins = await self._on_coins_low(ctx)
                            if new_coins:
                                # TODO: Handle coin replenishment
                                grpc_ser_txn_exc_logger.debug(
                                    "Replenished with %s coins", len(new_coins)
                                )
                            else:
                                # No coins returned, halt
                                grpc_ser_txn_exc_logger.debug(
                                    "on_coins_low returned None/empty after tx %s", idx
                                )
                                for remaining_idx in range(idx + 1, len(transactions)):
                                    exe_res.append(
                                        ExecutionSkipped(
                                            transaction_index=remaining_idx,
                                            reason="coin replenishment declined",
                                        )
                                    )
                                break

                        # Try balance_low callback if coins_low didn't provide coins
                        elif self._on_balance_low:
                            grpc_ser_txn_exc_logger.debug(
                                "Calling on_balance_low callback after tx %s", idx
                            )
                            addr = await self._on_balance_low(ctx)
                            if addr:
                                # TODO: Verify balance using gRPC GetBalance
                                grpc_ser_txn_exc_logger.debug("Balance checked at %s", addr)
                            else:
                                # Balance low callback returned None, halt
                                grpc_ser_txn_exc_logger.debug(
                                    "on_balance_low returned None after tx %s", idx
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
