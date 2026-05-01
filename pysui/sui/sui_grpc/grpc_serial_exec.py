#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution for gRPC."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Union

if TYPE_CHECKING:
    from pysui.sui.sui_grpc.pgrpc_async_txn import AsyncSuiTransaction

from pysui.sui.sui_grpc.pgrpc_clients import SuiGrpcClient
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.executors import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    SerialQueue,
)
from pysui.sui.sui_common.executors.base_executor import _BaseSerialExecutor
from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.types import (
    TransactionEffects, ExecutionStatus, GasCostSummary, Owner, ChangedObject
)
import pysui.sui.sui_grpc.pgrpc_requests as rn
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.sui_commands as cmd

grpc_ser_txn_exc_logger = logging.getLogger(__name__)

_OUTPUT_STATE_MAP = {
    sui_prot.ChangedObjectOutputObjectState.DOES_NOT_EXIST: "DoesNotExist",
    sui_prot.ChangedObjectOutputObjectState.OBJECT_WRITE: "ObjectWrite",
    sui_prot.ChangedObjectOutputObjectState.PACKAGE_WRITE: "PackageWrite",
}

_OWNER_KIND_MAP = {
    sui_prot.OwnerOwnerKind.ADDRESS: "AddressOwner",
    sui_prot.OwnerOwnerKind.OBJECT: "ObjectOwner",
    sui_prot.OwnerOwnerKind.SHARED: "SharedInitialVersion",
    sui_prot.OwnerOwnerKind.IMMUTABLE: "Immutable",
}


def _grpc_effects_to_common(grpc_effects: sui_prot.TransactionEffects) -> TransactionEffects:
    """Convert gRPC TransactionEffects to the protocol-agnostic common type.

    :param grpc_effects: gRPC TransactionEffects protobuf message
    :type grpc_effects: sui_prot.TransactionEffects
    :return: Protocol-agnostic TransactionEffects
    :rtype: TransactionEffects
    :raises ValueError: If required fields are missing
    """
    if grpc_effects is None:
        raise ValueError("TransactionEffects is None")

    gas_used_proto = grpc_effects.gas_used
    gas_used = GasCostSummary(
        computation_cost=gas_used_proto.computation_cost or 0,
        storage_cost=gas_used_proto.storage_cost or 0,
        storage_rebate=gas_used_proto.storage_rebate or 0,
        non_refundable_storage_fee=getattr(gas_used_proto, "non_refundable_storage_fee", None) or 0,
    ) if gas_used_proto else GasCostSummary(
        computation_cost=0, storage_cost=0, storage_rebate=0
    )

    changed_objects = []
    for co in grpc_effects.changed_objects:
        output_state_enum = co.output_state
        output_state_str = _OUTPUT_STATE_MAP.get(output_state_enum)
        if output_state_str is None:
            continue

        output_owner = None
        if co.output_owner is not None:
            kind_str = _OWNER_KIND_MAP.get(co.output_owner.kind, "Unknown")
            output_owner = Owner(
                kind=kind_str,
                address=co.output_owner.address if co.output_owner.kind in (
                    sui_prot.OwnerOwnerKind.ADDRESS, sui_prot.OwnerOwnerKind.OBJECT
                ) else None,
                initial_shared_version=co.output_owner.version if co.output_owner.kind == (
                    sui_prot.OwnerOwnerKind.SHARED
                ) else None,
            )

        changed_objects.append(ChangedObject(
            object_id=co.object_id or "",
            output_state=output_state_str,
            output_digest=co.output_digest,
            output_owner=output_owner,
        ))

    gas_object = None
    go = grpc_effects.gas_object
    if go is not None:
        go_output_state = _OUTPUT_STATE_MAP.get(go.output_state)
        if go_output_state:
            go_owner = None
            if go.output_owner is not None:
                kind_str = _OWNER_KIND_MAP.get(go.output_owner.kind, "Unknown")
                go_owner = Owner(
                    kind=kind_str,
                    address=go.output_owner.address if go.output_owner.kind in (
                        sui_prot.OwnerOwnerKind.ADDRESS, sui_prot.OwnerOwnerKind.OBJECT
                    ) else None,
                )
            gas_object = ChangedObject(
                object_id=go.object_id or "",
                output_state=go_output_state,
                output_digest=go.output_digest,
                output_owner=go_owner,
            )

    status_proto = grpc_effects.status
    success = bool(status_proto and status_proto.success)

    return TransactionEffects(
        transaction_digest=grpc_effects.transaction_digest or "",
        status=ExecutionStatus(success=success),
        gas_used=gas_used,
        lamport_version=grpc_effects.lamport_version or 0,
        changed_objects=changed_objects,
        gas_object=gas_object,
    )


class GrpcSerialTransactionExecutor(_BaseSerialExecutor):
    """Executes transactions serially with optional gas replenishment for gRPC.

    Gas replenishment callbacks (on_coins_low / on_balance_low) are mutually exclusive:

    - on_coins_low: used when gas is paid via Coin<SUI> objects. Return new coin IDs
      to signal replenishment, or None/[] to halt execution.
    - on_balance_low: used when gas is paid via address accumulator. Must complete a
      funding transaction before returning. Return the funding source address for
      logging, or None to halt execution.

    Both callbacks receive an ExecutorContext.

    Note: execute_transactions is not re-entrant. Concurrent calls on the same instance
    are serialized by an internal asyncio.Lock.
    """

    def __init__(
        self,
        *,
        client: SuiGrpcClient,
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
        :type client: SuiGrpcClient
        :param sender: Sender address or SigningMultiSig
        :type sender: Union[str, SigningMultiSig]
        :param sponsor: Optional sponsor address or SigningMultiSig, defaults to None
        :type sponsor: Optional[Union[str, SigningMultiSig]], optional
        :param default_gas_budget: Default gas budget, defaults to 50_000_000
        :type default_gas_budget: int
        :param min_balance_threshold: Minimum balance threshold that triggers replenishment
            callback. Requires either on_coins_low or on_balance_low.
        :type min_balance_threshold: Optional[int], optional
        :param on_coins_low: Async callback when coin balance drops below threshold.
            Return new coin IDs to inject, or None/[] to halt execution.
        :type on_coins_low: Optional[Callable[[ExecutorContext], Awaitable[list[str] | None]]]
        :param on_balance_low: Async callback when address balance drops below threshold.
            Return funding source address, or None to halt execution.
        :type on_balance_low: Optional[Callable[[ExecutorContext], Awaitable[str | None]]]
        :raises ValueError: If min_balance_threshold is set without any replenishment callback
        """
        if min_balance_threshold is not None and on_coins_low is None and on_balance_low is None:
            raise ValueError(
                "min_balance_threshold requires either on_coins_low or on_balance_low callback"
            )
        self._use_account_gas = on_balance_low is not None and on_coins_low is None
        super().__init__(
            client=client,
            sender=sender,
            sponsor=sponsor,
            default_gas_budget=default_gas_budget,
            min_balance_threshold=min_balance_threshold,
            on_coins_low=on_coins_low,
            on_balance_low=on_balance_low,
        )
        self._execution_lock = asyncio.Lock()
        self._queue = SerialQueue()

    def _create_caching_executor(self, client, gas_owner: str) -> _BaseCachingExecutor:
        return _BaseCachingExecutor(client=client, gas_owner=gas_owner, use_account_gas=self._use_account_gas)

    async def _execute_raw(self, tx_str: str, sigs: list[str]) -> TransactionEffects:
        """Execute a signed transaction via gRPC and return common TransactionEffects.

        :param tx_str: Base64-encoded transaction bytes
        :type tx_str: str
        :param sigs: List of base64-encoded signatures
        :type sigs: list[str]
        :return: Protocol-agnostic transaction effects
        :rtype: TransactionEffects
        :raises ValueError: If transaction execution fails or result is invalid
        :raises TypeError: If result type is unexpected
        """
        result = await self._client.execute(
            command=cmd.ExecuteTransaction(tx_bytestr=tx_str, sig_array=sigs)
        )
        if not result.is_ok():
            raise ValueError(f"gRPC execute_transaction failed: {result.result_string}")

        response: sui_prot.ExecuteTransactionResponse = result.result_data
        if response.transaction is None:
            raise ValueError("ExecuteTransactionResponse.transaction is None")

        grpc_effects = response.transaction.effects
        if grpc_effects is None:
            raise ValueError("ExecuteTransactionResponse.transaction.effects is None")

        return _grpc_effects_to_common(grpc_effects)

    async def _fetch_initial_balance(self) -> int:
        """Fetch the current gas balance for the sender via gRPC.

        :return: The gas balance
        :rtype: int
        :raises ValueError: If balance fetch fails
        """
        result = await self._client.execute(
            command=cmd.GetAddressCoinBalance(owner=self._signing_block.payer_address)
        )
        if not result.is_ok():
            raise ValueError("Failed to fetch initial balance")
        bal = result.result_data.balance
        return bal.address_balance if self._use_account_gas else bal.coin_balance

    async def reset_cache(self) -> None:
        """Reset the internal cache."""
        return await self._cache.reset()

    async def execute_transactions(
        self,
        transactions: "list[AsyncSuiTransaction]",
    ) -> list[Union[TransactionEffects, tuple[ExecutorError, Exception], ExecutionSkipped]]:
        """Serially execute one or more transactions using the base class state machine.

        Returns a list of the same length as ``transactions``. Each element is one of:
        - ``TransactionEffects``: transaction succeeded
        - ``(ExecutorError, Exception)``: transaction failed
        - ``ExecutionSkipped``: transaction was not attempted due to a prior failure

        :param transactions: The transactions to execute
        :type transactions: list[AsyncSuiTransaction]
        :return: The transaction execution results
        :rtype: list[Union[TransactionEffects, tuple[ExecutorError, Exception], ExecutionSkipped]]
        """
        async with self._execution_lock:
            return await super().execute_transactions(transactions)
