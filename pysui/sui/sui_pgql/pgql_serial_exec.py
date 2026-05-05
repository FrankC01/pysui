#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Serial transaction execution for GQL."""

import asyncio
import base64
import logging
from typing import TYPE_CHECKING, Awaitable, Callable, Optional, Union

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

from pysui.sui.sui_pgql.pgql_clients import GqlProtocolClient
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
import pysui.sui.sui_common.sui_commands as cmd
import pysui.sui.sui_bcs.bcs_txne as bcst
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot

gql_ser_txn_exc_logger = logging.getLogger(__name__)


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
    """Executes transactions serially with optional gas replenishment for GQL.

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
        client: GqlProtocolClient,
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
        :type client: GqlProtocolClient
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
            Must perform the funding transaction before returning. Return the funding source
            address (for logging), or None to halt execution.
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
        """Execute a signed transaction via GQL and return common TransactionEffects.

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
            raise ValueError(f"GQL execute_transaction failed: {result.result_string}")
        if not isinstance(result.result_data, sui_prot.ExecuteTransactionResponse):
            raise TypeError(f"unexpected result type {type(result.result_data).__name__}")

        effects_bcs = bcst.TransactionEffects.deserialize(result.result_data.transaction.effects.bcs.value)
        common_effects = _gql_effects_to_common(effects_bcs)

        if common_effects.gas_object is not None:
            go = common_effects.gas_object
            try:
                await self._cache.update_gas_coins([go.object_id])
            except Exception as exc:
                gql_ser_txn_exc_logger.warning("Failed to update gas coin from effects: %s", exc)
                await self._cache.invalidate_gas_coins()
        else:
            await self._cache.invalidate_gas_coins()

        return common_effects

    async def _fetch_initial_balance(self) -> int:
        """Fetch the current gas balance for the sender via GQL.

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
        return bal.coin_balance if self._on_coins_low else bal.address_balance

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
