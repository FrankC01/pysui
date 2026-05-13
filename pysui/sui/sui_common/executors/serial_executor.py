#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Concrete serial transaction executor — protocol-agnostic."""

import asyncio
import logging
from typing import TYPE_CHECKING, Awaitable, Callable, Literal, Optional, Type, Union

if TYPE_CHECKING:
    from pysui.sui.sui_common.async_txn import AsyncSuiTransaction

from pysui.sui.sui_common.txb_signing import SigningMultiSig
from pysui.sui.sui_common.executors.exec_types import (
    ExecutorContext,
    ExecutionSkipped,
    ExecutorError,
    GasSummary,
)
from pysui.sui.sui_common.executors.base_executor import _BaseSerialExecutor
from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
import pysui.sui.sui_grpc.suimsgs.sui.rpc.v2 as sui_prot
import pysui.sui.sui_common.sui_commands as cmd

logger = logging.getLogger(__name__)

_SUI_COIN_TYPE = "0x0000000000000000000000000000000000000000000000000000000000000002::coin::Coin<0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI>"


class PysuiSerialExecutor(_BaseSerialExecutor):
    """Protocol-agnostic serial transaction executor.

    Executes transactions serially with optional gas replenishment.

    Gas replenishment callbacks (on_coins_low / on_balance_low) are mutually exclusive:

    - on_coins_low: used when gas is paid via Coin<SUI> objects. Return new coin IDs
      to signal replenishment, or None/[] to halt execution.
    - on_balance_low: used when gas is paid via address accumulator. Must complete a
      funding transaction before returning. Return the funding source address for
      logging, or None to halt execution.

    Both callbacks receive an ExecutorContext.

    Obtain an instance via client.serial_executor() or PysuiSerialExecutor.with_coins().

    Note: execute_transactions is not re-entrant. Concurrent calls on the same instance
    are serialized by an internal asyncio.Lock.
    """

    def __init__(
        self,
        *,
        client,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
        min_balance_threshold: Optional[int] = None,
        on_coins_low: Optional[
            Callable[[ExecutorContext], Awaitable["list[str] | list[sui_prot.Object] | None"]]
        ] = None,
        on_balance_low: Optional[
            Callable[[ExecutorContext], Awaitable["str | None"]]
        ] = None,
        on_failure: Literal["continue", "exit"] = "continue",
    ):
        super().__init__(
            client=client,
            sender=sender,
            sponsor=sponsor,
            min_balance_threshold=min_balance_threshold,
            on_coins_low=on_coins_low,
            on_balance_low=on_balance_low,
            on_failure=on_failure,
        )
        self._execution_lock = asyncio.Lock()

    def _create_caching_executor(self, client, gas_owner: str, use_account_gas: bool = False) -> _BaseCachingExecutor:
        return _BaseCachingExecutor(client=client, gas_owner=gas_owner, use_account_gas=use_account_gas)

    async def _execute_raw(self, tx_str: str, sigs: list[str]) -> sui_prot.ExecutedTransaction:
        result = await self._client.execute(
            command=cmd.ExecuteTransaction(tx_bytestr=tx_str, sig_array=sigs)
        )
        if not result.is_ok():
            raise ValueError(f"execute_transaction failed: {result.result_string}")

        response: "sui_prot.ExecutedTransaction | None" = result.result_data
        if response is None:
            raise ValueError("ExecuteTransaction returned None")

        self._update_gas_summary(response)

        effects = response.effects
        if effects is None:
            raise ValueError("ExecutedTransaction.effects is None")

        if effects.gas_object is not None:
            try:
                await self._cache.update_gas_coins([effects.gas_object.object_id])
            except Exception as exc:
                logger.warning("Failed to update gas coin from effects: %s", exc)
                await self._cache.invalidate_gas_coins()
        else:
            await self._cache.invalidate_gas_coins()
        return response

    async def _fetch_initial_balance(self) -> int:
        result = await self._client.execute(
            command=cmd.GetAddressCoinBalance(owner=self._signing_block.payer_address)
        )
        if not result.is_ok():
            raise ValueError("Failed to fetch initial balance")
        bal = result.result_data.balance
        return bal.coin_balance if not self._use_account_gas else bal.address_balance

    @classmethod
    async def with_coins(
        cls: Type["PysuiSerialExecutor"],
        client,
        sender: Union[str, SigningMultiSig],
        coins: Optional[Union[list[str], "list[sui_prot.Object]"]] = None,
        min_balance_threshold: int = 10_000_000,
        on_coins_low: Optional[
            Callable[
                ["ExecutorContext"],
                Awaitable["list[str] | list[sui_prot.Object] | None"],
            ]
        ] = None,
        on_failure: Literal["continue", "exit"] = "continue",
    ) -> "tuple[PysuiSerialExecutor, str]":
        """Factory: create an executor pre-seeded with gas coins.

        :param client: Async protocol client (GQL or gRPC)
        :param sender: Sender address or SigningMultiSig
        :param coins: Optional coin IDs or Object list; if None fetches all sender gas coins
        :param min_balance_threshold: Minimum gas balance before on_coins_low fires; defaults to 10_000_000
        :param on_coins_low: Callback returning new coins to merge; None means halt on low balance
        :param on_failure: "continue" processes all txns; "exit" halts at first failure
        :return: (executor instance, primary gas coin objectId)
        :raises ValueError: If coin fetch fails, no coins found, or balance below threshold

        Note: on_balance_low (account-gas replenishment) is not available via this factory.
        Use the constructor directly and manage gas replenishment via on_balance_low callback.
        """
        sender_str = sender if isinstance(sender, str) else sender.signing_address
        se = cls(
            client=client,
            sender=sender,
            on_coins_low=on_coins_low,
            on_failure=on_failure,
            min_balance_threshold=min_balance_threshold,
        )
        if coins is None:
            result = await client.execute_for_all(command=cmd.GetGas(owner=sender_str))
            if not result.is_ok():
                raise ValueError(
                    f"with_coins: failed to fetch gas coins: {result.result_string}"
                )
            obj_list: list[sui_prot.Object] = result.result_data.objects
            if not obj_list:
                raise ValueError("with_coins: no gas coins found for sender")
        elif len(coins) == 0:
            raise ValueError("with_coins: coins must not be empty")
        elif isinstance(coins[0], str):
            result = await client.execute(
                command=cmd.GetMultipleObjects(object_ids=list(coins))
            )
            if not result.is_ok():
                raise ValueError(
                    f"with_coins: failed to fetch coin objects: {result.result_string}"
                )
            obj_list = [
                o for o in result.result_data if o.object_type == _SUI_COIN_TYPE
            ]
            if not obj_list:
                raise ValueError("with_coins: no coin objects returned")
        else:
            obj_list = list(coins)

        primary_obj = max(obj_list, key=lambda o: o.balance or 0)
        rest_objs = [o for o in obj_list if o is not primary_obj]
        primary = GasSummary(
            objectId=primary_obj.object_id,
            version=str(primary_obj.version),
            digest=primary_obj.digest,
            balance=primary_obj.balance or 0,
        )
        se._gas_summary = primary

        if primary.balance >= min_balance_threshold:
            se._tracked_balance = primary.balance
        else:
            to_merge = []
            running = primary.balance
            for obj in sorted(rest_objs, key=lambda o: o.balance or 0, reverse=True):
                to_merge.append(obj)
                running += obj.balance or 0
                if running >= min_balance_threshold:
                    break
            if running < min_balance_threshold:
                raise ValueError(
                    f"with_coins: insufficient balance {running} < {min_balance_threshold}"
                )
            merge_tx = await se.new_transaction()
            await merge_tx.merge_coins(merge_to=merge_tx.gas, merge_from=to_merge)
            gas_objects = [
                sui_prot.Object(
                    object_id=primary.objectId,
                    version=int(primary.version),
                    digest=primary.digest,
                    balance=primary.balance,
                )
            ]
            build_dict = await merge_tx.build_and_sign(use_gas_objects=gas_objects)
            result = await client.execute(command=cmd.ExecuteTransaction(**build_dict))
            if not result.is_ok():
                raise ValueError(
                    f"with_coins: failed to build merge transaction: {result.result_string}"
                )
            se._update_gas_summary(result.result_data)
            se._tracked_balance = se._gas_summary.balance
        return se, se._gas_summary.objectId

    async def execute_transactions(
        self,
        transactions: "list[AsyncSuiTransaction]",
    ) -> "list[Union[sui_prot.ExecutedTransaction, tuple[ExecutorError, Exception], ExecutionSkipped]]":
        """Serially execute one or more transactions using the base class state machine.

        Returns a list of the same length as ``transactions``. Each element is one of:
        - ``ExecutedTransaction``: transaction succeeded
        - ``(ExecutorError, Exception)``: transaction failed
        - ``ExecutionSkipped``: transaction was not attempted due to a prior failure

        :param transactions: The transactions to execute
        :type transactions: list[AsyncSuiTransaction]
        :return: The transaction execution results
        :rtype: list[Union[ExecutedTransaction, tuple[ExecutorError, Exception], ExecutionSkipped]]
        """
        async with self._execution_lock:
            return await super().execute_transactions(transactions)
