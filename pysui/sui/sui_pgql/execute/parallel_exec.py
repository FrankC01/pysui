#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""GraphQL parallel transaction execution."""

from __future__ import annotations

import base64
import logging
from typing import Awaitable, Callable, Optional, Union

from pysui import AsyncGqlClient
from pysui.sui.sui_common.executors.base_caching_executor import _BaseCachingExecutor
from pysui.sui.sui_common.executors.base_parallel_executor import _BaseParallelExecutor
from pysui.sui.sui_common.executors.exec_types import ExecutorContext
from pysui.sui.sui_common.executors.gas_pool import GasCoin
from pysui.sui.sui_common.executors.object_registry import AbstractObjectRegistry
from pysui.sui.sui_common.txb_signing import SignerBlock, SigningMultiSig
from pysui.sui.sui_common.types import TransactionEffects

import pysui.sui.sui_bcs.bcs as bcs
import pysui.sui.sui_bcs.bcs_txne as bcst
import pysui.sui.sui_pgql.pgql_query as qn
import pysui.sui.sui_pgql.pgql_types as ptypes
from .caching_exec import GqlCachingTransactionExecutor
from .caching_txn import CachingTransaction
from .serial_exec import _gql_effects_to_common

par_txn_exc_logger = logging.getLogger(__name__)


class GqlParallelTransactionExecutor(_BaseParallelExecutor):
    """Executes transactions in parallel using GraphQL transport.

    Supports two gas modes:

    **coins mode** (default):
        A pool of dedicated gas coins is managed by the executor. Each
        in-flight transaction checks out one coin exclusively and returns it
        (at its updated version) after effects are applied. The pool is
        replenished automatically when it drops to the low-water mark.

        Seed the pool before executing:

        .. code-block:: python

            await executor.seed_coin_pool(coins)

        Or let the first call to ``execute_transactions`` trigger an automatic
        refill via ``_refill_coin_pool``.

    **addressBalance mode**:
        No coin pool. The Sui node selects gas from the sender's accumulated
        address balance. Concurrency is bounded only by ``max_tasks``.
        An optional ``on_balance_low`` callback fires when the tracked balance
        drops below ``min_balance_threshold``.

    Both modes support ``SigningMultiSig`` for sender and sponsor.

    :param client: Asynchronous GraphQL client
    :param sender: Sender address or ``SigningMultiSig``
    :param sponsor: Optional sponsor address or ``SigningMultiSig``
    :param gas_mode: ``"coins"`` or ``"addressBalance"``
    :param max_tasks: Maximum concurrent transactions
    :param default_gas_budget: Per-transaction gas budget
    :param min_balance_threshold: Balance level that triggers ``on_balance_low``
    :param coin_split_amount: Amount in MIST to allocate to each refill coin
    :param low_water_mark: Pool size at or below which a refill is triggered
    :param min_balance_per_coin: Retire a coin when its balance drops below this
    :param on_balance_low: Async callback fired when balance is low (addressBalance mode)
    :param registry: Shared object registry; defaults to the process-wide singleton
    """

    DEFAULT_COIN_SPLIT_AMOUNT: int = 10_000_000  # 0.01 SUI per gas coin

    def __init__(
        self,
        *,
        client: AsyncGqlClient,
        sender: Union[str, SigningMultiSig],
        sponsor: Optional[Union[str, SigningMultiSig]] = None,
        gas_mode: str = "coins",
        max_tasks: int = 4,
        default_gas_budget: int = 50_000_000,
        min_balance_threshold: Optional[int] = None,
        coin_split_amount: int = DEFAULT_COIN_SPLIT_AMOUNT,
        low_water_mark: int = 5,
        min_balance_per_coin: Optional[int] = None,
        on_balance_low: Optional[Callable[[ExecutorContext], Awaitable[Optional[str]]]] = None,
        registry: Optional[AbstractObjectRegistry] = None,
    ) -> None:
        super().__init__(
            client=client,
            sender=sender,
            sponsor=sponsor,
            gas_mode=gas_mode,
            max_tasks=max_tasks,
            default_gas_budget=default_gas_budget,
            min_balance_threshold=min_balance_threshold,
            low_water_mark=low_water_mark,
            min_balance_per_coin=min_balance_per_coin,
            on_balance_low=on_balance_low,
            registry=registry,
        )
        self._coin_split_amount = coin_split_amount

    # ------------------------------------------------------------------
    # _BaseParallelExecutor implementation
    # ------------------------------------------------------------------

    def _create_caching_executor(self) -> GqlCachingTransactionExecutor:
        return GqlCachingTransactionExecutor(self._client, gas_owner=self._gas_owner)

    async def _execute_single(
        self,
        tx_str: str,
        sigs: list[str],
        caching_exec: _BaseCachingExecutor,
    ) -> TransactionEffects:
        gql_exec: GqlCachingTransactionExecutor = caching_exec  # type: ignore[assignment]
        result = await gql_exec.execute_transaction(tx_str, sigs)
        if not isinstance(result, ptypes.ExecutionResultGQL):
            raise TypeError(f"unexpected result type {type(result).__name__}")
        effects_bcs = bcst.TransactionEffects.deserialize(base64.b64decode(result.effects_bcs))
        common_effects = _gql_effects_to_common(effects_bcs)

        # Update the per-tx caching executor's gas coins from effects
        if common_effects.gas_object is not None:
            go = common_effects.gas_object
            try:
                digest_str = go.output_digest or ""
                new_ref = bcs.ObjectReference(
                    bcs.Address.from_str(go.object_id),
                    common_effects.lamport_version,
                    bcs.Digest.from_str(digest_str),
                )
                await gql_exec.update_gas_coins([new_ref])
            except Exception as exc:
                par_txn_exc_logger.warning("Failed to update gas coin from effects: %s", exc)
                await gql_exec.invalidate_gas_coins()
        else:
            await gql_exec.invalidate_gas_coins()

        return common_effects

    async def _refill_coin_pool(self, n: int) -> list[GasCoin]:
        """Split n new gas coins from the gas owner's balance.

        Builds and executes a one-off CachingTransaction that splits the gas
        coin into n equal parts. The resulting coins are returned as GasCoin
        objects. This path does NOT go through the parallel executor to avoid
        a circular dependency.
        """
        par_txn_exc_logger.info(
            "parallel_exec: refilling pool with %d coins @ %d MIST each",
            n, self._coin_split_amount,
        )
        # Use a fresh one-off caching executor+transaction (outside the executor pool)
        one_off_cache = GqlCachingTransactionExecutor(
            self._client, gas_owner=self._gas_owner
        )
        txn = CachingTransaction(client=self._client)

        amounts = [self._coin_split_amount] * n
        split_result = await txn.split_coin(coin=txn.gas, amounts=amounts)

        # Transfer each split coin back to the gas owner (keeps them as individual objects)
        await txn.transfer_objects(transfers=split_result, recipient=self._gas_owner)

        tx_str = await one_off_cache.build_transaction(
            txn, self._signing_block, self._default_gas_budget
        )
        sigs = self._signing_block.get_signatures(
            config=self._client.config, tx_bytes=tx_str
        )

        result = await one_off_cache.execute_transaction(tx_str, sigs)
        if not isinstance(result, ptypes.ExecutionResultGQL):
            raise TypeError(f"refill: unexpected result type {type(result).__name__}")

        effects_bcs = bcst.TransactionEffects.deserialize(base64.b64decode(result.effects_bcs))
        common_effects = _gql_effects_to_common(effects_bcs)
        await one_off_cache.apply_effects(common_effects)

        # Extract newly created coin objects from effects
        new_coins: list[GasCoin] = []
        for obj in common_effects.changed_objects:
            if (
                obj.output_state == "ObjectWrite"
                and obj.output_owner is not None
                and obj.output_owner.kind == "AddressOwner"
                and obj.output_owner.address == self._gas_owner
                and obj.object_id != (common_effects.gas_object.object_id if common_effects.gas_object else None)
            ):
                new_coins.append(GasCoin(
                    object_id=obj.object_id,
                    version=str(common_effects.lamport_version),
                    digest=obj.output_digest or "",
                    balance=self._coin_split_amount,
                ))
            if len(new_coins) >= n:
                break

        par_txn_exc_logger.info(
            "parallel_exec: refill produced %d coins", len(new_coins)
        )
        return new_coins

    async def _fetch_balance(self) -> int:
        result = await self._client.execute_query_node(
            with_node=qn.GetAddressCoinBalance(owner=self._gas_owner)
        )
        if not result.is_ok():
            raise ValueError(f"Failed to fetch balance for {self._gas_owner}")
        bal = result.result_data.balance
        return bal.coin_balance if self._gas_mode == "coins" else bal.address_balance

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def new_transaction(self) -> CachingTransaction:
        """Create a new CachingTransaction for building transaction blocks.

        :return: A new CachingTransaction
        :rtype: CachingTransaction
        """
        return CachingTransaction(client=self._client)
