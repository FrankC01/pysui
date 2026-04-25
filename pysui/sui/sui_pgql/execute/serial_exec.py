#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution."""

import asyncio
import base64
import logging
import time
from typing import Awaitable, Callable, Optional, Union

from pysui import AsyncGqlClient
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.executors import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    SerialQueue,
)
from pysui.sui.sui_common.executors.base_executor import _BaseSerialExecutor
from pysui.sui.sui_common.types import (
    TransactionEffects, ExecutionStatus, GasCostSummary, Owner, ChangedObject
)
import pysui.sui.sui_pgql.pgql_types as ptypes
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_bcs.bcs as bcs
import pysui.sui.sui_bcs.bcs_txne as bcst
from .caching_exec import GqlCachingTransactionExecutor
from .caching_txn import CachingTransaction

ser_txn_exc_logger = logging.getLogger(__name__)


def _gql_effects_to_common(effects: bcst.TransactionEffects) -> TransactionEffects:
    """Convert GQL BCS TransactionEffects to the protocol-agnostic common type.

    :param effects: BCS-deserialized transaction effects from GraphQL
    :type effects: bcst.TransactionEffects
    :return: Protocol-agnostic TransactionEffects
    :rtype: TransactionEffects
    :raises ValueError: If effects version is not V2
    """
    if effects.enum_name != "V2":
        raise ValueError(f"Expect V2 effects, found {effects.enum_name}")
    v2 = effects.value

    changed_objects = []
    for addr, change in v2.changedObjects:
        obj_id = addr.to_address_str()
        out = change.outputState
        if out.enum_name == "NotExist":
            changed_objects.append(ChangedObject(object_id=obj_id, output_state="DoesNotExist"))
        elif out.enum_name in ("ObjectWrite", "PackageWrite"):
            digest, owner = out.value
            owner_kind = owner.enum_name
            output_owner = Owner(
                kind=owner_kind,
                address=owner.value.to_address_str() if owner_kind == "AddressOwner" else None,
                initial_shared_version=owner.value if owner_kind == "SharedInitialVersion" else None,
            )
            changed_objects.append(ChangedObject(
                object_id=obj_id,
                output_state=out.enum_name,
                output_digest=digest.to_digest_str(),
                output_owner=output_owner,
            ))

    gas_used = GasCostSummary(
        computation_cost=v2.gasUsed.computationCost,
        storage_cost=v2.gasUsed.storageCost,
        storage_rebate=v2.gasUsed.storageRebate,
        non_refundable_storage_fee=getattr(v2.gasUsed, 'nonRefundableStorageFee', 0),
    )

    # Gas object
    gas_object = None
    try:
        gas_idx = v2.gasObjectIndex.value
        if gas_idx < len(v2.changedObjects):
            gas_addr, gas_change = v2.changedObjects[gas_idx]
            if gas_change.outputState.enum_name == "ObjectWrite":
                gas_digest, gas_owner = gas_change.outputState.value
                gas_object = ChangedObject(
                    object_id=gas_addr.to_address_str(),
                    output_state="ObjectWrite",
                    output_digest=gas_digest.to_digest_str(),
                    output_owner=Owner(
                        kind=gas_owner.enum_name,
                        address=gas_owner.value.to_address_str() if gas_owner.enum_name == "AddressOwner" else None,
                    ),
                )
    except Exception:
        pass

    return TransactionEffects(
        transaction_digest=v2.transactionDigest.to_digest_str(),
        status=ExecutionStatus(success=True),
        gas_used=gas_used,
        lamport_version=v2.lamportVersion,
        changed_objects=changed_objects,
        gas_object=gas_object,
    )


class GqlSerialTransactionExecutor(_BaseSerialExecutor):
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
        """Initialize GqlSerialTransactionExecutor.

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
        super().__init__(
            client=client,
            sender=sender,
            sponsor=sponsor,
            default_gas_budget=default_gas_budget,
            min_balance_threshold=min_balance_threshold,
            on_coins_low=on_coins_low,
            on_balance_low=on_balance_low,
        )
        # Prevent re-entrant execute_transactions calls on the same instance
        self._execution_lock = asyncio.Lock()
        self._queue = SerialQueue()

    def _create_caching_executor(self, client, gas_owner: str) -> "GqlCachingTransactionExecutor":
        """Create a protocol-specific caching executor.

        :param client: The GraphQL client
        :param gas_owner: Address of the gas owner
        :return: The caching executor
        :rtype: GqlCachingTransactionExecutor
        """
        return GqlCachingTransactionExecutor(client, gas_owner=gas_owner)

    async def _execute_raw(self, tx_str: str, sigs: list[str]) -> TransactionEffects:
        """Execute a signed transaction and return common TransactionEffects.

        :param tx_str: Base64-encoded transaction bytes
        :type tx_str: str
        :param sigs: List of base64-encoded signatures
        :type sigs: list[str]
        :return: Protocol-agnostic transaction effects
        :rtype: TransactionEffects
        :raises ValueError: If transaction execution fails or result is invalid
        :raises TypeError: If result type is unexpected
        """
        results = await self._cache.execute_transaction(tx_str, sigs)
        if not isinstance(results, ptypes.ExecutionResultGQL):
            raise TypeError(f"unexpected result type {type(results).__name__}")
        effects_bcs = bcst.TransactionEffects.deserialize(base64.b64decode(results.effects_bcs))
        common_effects = _gql_effects_to_common(effects_bcs)

        # Update gas coin cache from effects
        if common_effects.gas_object is not None:
            go = common_effects.gas_object
            try:
                new_gas_coin = bcs.ObjectReference(
                    bcs.Address.from_str(go.object_id),
                    common_effects.lamport_version,
                    bcs.Digest.from_str(go.output_digest),
                )
                await self._cache.update_gas_coins([new_gas_coin])
            except Exception as e:
                ser_txn_exc_logger.warning("Failed to update gas coin from effects: %s", e)
                await self._cache.invalidate_gas_coins()
        else:
            await self._cache.invalidate_gas_coins()

        return common_effects

    async def _fetch_initial_balance(self) -> int:
        """Fetch the current gas balance for the sender.

        :return: The gas balance
        :rtype: int
        :raises ValueError: If balance fetch fails
        """
        balance_result = await self._client.execute_query_node(
            with_node=qn.GetAddressCoinBalance(owner=self._signing_block.payer_address)
        )
        if not balance_result.is_ok():
            raise ValueError("Failed to fetch initial balance")
        bal = balance_result.result_data.balance
        return bal.coin_balance if self._on_coins_low else bal.address_balance

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
    ) -> list[Union[TransactionEffects, tuple[ExecutorError, Exception], ExecutionSkipped]]:
        """Serially execute one or more transactions using the base class state machine.

        Returns a list of the same length as ``transactions``. Each element is one of:
        - ``TransactionEffects``: transaction succeeded
        - ``(ExecutorError, Exception)``: transaction failed
        - ``ExecutionSkipped``: transaction was not attempted due to a prior failure

        This method may raise ValueError only on pre-flight failures (initial balance fetch)
        when replenishment is configured. All per-transaction errors are returned as tuples.

        :param transactions: The transactions to execute
        :type transactions: list[CachingTransaction]
        :return: The transaction execution results
        :rtype: list[Union[TransactionEffects, tuple[ExecutorError, Exception], ExecutionSkipped]]
        """
        async with self._execution_lock:
            return await super().execute_transactions(transactions)
