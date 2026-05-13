Transaction Executors
=====================

pysui provides high-level transaction executors for both GraphQL and gRPC transports.
All executors are asynchronous-only.

Two execution strategies are available:

- **Serial** — one transaction at a time, or one batch of transactions with each transaction execution serialized, backed by an object cache for efficient gas and object resolution
- **Parallel** — multiple concurrent transactions, with built-in conflict tracking (owned-object serialisation), gas coin pool management, and balance monitoring

---

Gas Funding Modes
-----------------

Both serial and parallel executors support two gas funding modes:

**Coins mode**
    Gas is paid from one or more ``Coin<SUI>`` objects owned by the sender.
    The executor tracks which coin objects are being used and updates them from transaction effects.

    For serial executors, use :meth:`serial_executor_with_coins` and optionally set
    ``on_coins_low`` to opt in to coin-balance threshold monitoring.
    For parallel executors, pass ``gas_mode="coins"`` and call ``seed_coin_pool`` before
    the first ``execute_transactions`` call.

**Address balance mode**
    Gas is drawn from the sender's accumulated address balance (SUI accumulator).
    No coin objects need to be managed — the node selects gas automatically.

    For serial executors, use :meth:`serial_executor_with_account` and optionally set
    ``on_balance_low`` to opt in to address-balance threshold monitoring.
    For parallel executors, pass ``gas_mode="addressBalance"``.

Address balance mode is the higher-throughput option: it eliminates coin check-out/check-in
overhead and pool contention, relying only on the concurrency semaphore as back-pressure.
Coins mode gives tighter control over which objects pay gas, at the cost of pool management.

For serial executors: passing neither ``on_coins_low`` nor ``on_balance_low`` is valid —
the executor uses gas coins and works without threshold monitoring.

---

Serial Executors
----------------

Serial executors execute transactions in the order provided; multiple transactions can be
batched into a list and submitted in a single ``execute_transactions`` call, where each is
executed serially in sequence. An internal object cache is primed on the first transaction
(gas objects are consolidated); subsequent transactions resolve from cache, making them
significantly faster.

``PysuiSerialExecutor`` is the single concrete serial executor class, shared across both
GraphQL and gRPC transports. Only the :func:`client_factory` group name differs between
transports — the executor interface is identical.

Obtain an instance via :meth:`serial_executor_with_coins` (coins gas mode) or
:meth:`serial_executor_with_account` (address balance gas mode).

Restrictions
~~~~~~~~~~~~

- **Not re-entrant** — submissions to ``execute_transactions()`` must be serialized by
  the user. Concurrent calls on the same instance will result in conflicting gas coin
  versions and undefined object cache state.

- **No sponsored transactions** — only the sender's gas coin is used. Sponsor-pays
  patterns are not supported by the serial executor.

- **Gas coin threshold with** ``txn.gas`` **references** — if the transactions being
  submitted reference ``txn.gas`` directly (e.g.
  ``txn.split_coin(coin=txn.gas, amounts=[...])``) the gas coin balance is consumed by
  both gas fees *and* the PTB operation. In this case ``min_balance_threshold`` may need
  a significantly higher starting value than the default.

**Coins gas mode** (``serial_executor_with_coins``):

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory

    async def run():
        # Use SUI_GQL_RPC_GROUP for GraphQL or SUI_GRPC_GROUP for gRPC
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor, primary_coin_id = await client.serial_executor_with_coins(
            sender=cfg.active_address,
            min_balance_threshold=100_000_000,
        )

        txn = await executor.new_transaction()
        coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
        await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)

        results = await executor.execute_transactions([txn])
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r.to_json(indent=2))

``serial_executor_with_coins`` parameters:

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - ``sender``
     - Sender address string or ``SigningMultiSig``
   * - ``coins``
     - Optional list of coin object IDs (``list[str]``) or pre-fetched ``sui_prot.Object``
       instances. If ``None``, fetches enough SUI coins owned by ``sender`` to cover
       ``min_balance_threshold`` — not all SUI coins.
   * - ``min_balance_threshold``
     - Minimum MIST balance the managed gas coin must maintain before ``on_coins_low``
       fires (default: ``10_000_000``). The default may be too low for workloads that
       submit many transactions or transactions with high gas consumption — increase it
       accordingly.
   * - ``on_coins_low``
     - Async callback invoked when the gas coin balance drops below
       ``min_balance_threshold``. Receives an ``ExecutorContext``. Return a list of
       additional coins to merge into the gas coin, or ``None``/``[]`` to halt the
       executor. See the example below.
   * - ``on_failure``
     - Controls behavior when a transaction fails (e.g. no SUI coins available) with
       remaining transactions still queued. ``"continue"`` (default) processes remaining
       transactions; ``"exit"`` halts the batch immediately.

Returns ``(PysuiSerialExecutor, str)`` — the configured executor and the object ID of
the primary gas coin for the ``SerialExecutor`` to pay for transactions from. The object
ID is returned to ensure this coin is not used outside of the executor.

**Using** ``on_coins_low`` **— class-based pattern:**

The callback is invoked after the managed gas coin balance drops below
``min_balance_threshold``. A common pattern is a small class that holds a reference to
the primary coin object ID (returned by the factory) so the callback can exclude it from
the replenishment list:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors.exec_types import ExecutorContext
    import pysui.sui.sui_common.sui_commands as cmd

    class CoinManager:
        def __init__(self, client, sender: str):
            self._client = client
            self._sender = sender
            self._avoid_use: str = None

        def set_in_use(self, coin_id: str):
            self._avoid_use = coin_id

        async def on_coins_low(self, ctx: ExecutorContext) -> list | None:
            result = await self._client.execute_for_all(
                cmd.GetGas(owner=self._sender)
            )
            if result.is_err():
                return None
            coins = result.result_data.objects
            # Exclude the coin currently managed by the executor
            available = [c for c in coins if c.object_id != self._avoid_use]
            return available if available else None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)

        cm = CoinManager(client, cfg.active_address)

        executor, primary_coin_id = await client.serial_executor_with_coins(
            sender=cfg.active_address,
            min_balance_threshold=100_000_000,
            on_coins_low=cm.on_coins_low,
        )
        # Set after factory returns — the callback captures self (cm) by reference,
        # so it will see the updated value when it fires during execution.
        cm.set_in_use(primary_coin_id)

        txn = await executor.new_transaction()
        coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
        await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)

        results = await executor.execute_transactions([txn])
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r.to_json(indent=2))

**Address balance gas mode** (``serial_executor_with_account``):

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors.exec_types import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        # perform top-up, return funding address for logging, or None to halt
        return None

    async def run():
        # Use SUI_GQL_RPC_GROUP for GraphQL or SUI_GRPC_GROUP for gRPC
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = await client.serial_executor_with_account(
            sender=cfg.active_address,
            min_balance_threshold=100_000_000,
            on_balance_low=on_balance_low,
        )

        txn = await executor.new_transaction()
        coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
        await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)

        results = await executor.execute_transactions([txn])
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r.to_json(indent=2))

---

Parallel Executors
------------------

Parallel executors run transactions concurrently using ``asyncio.gather``. They include:

- **Conflict tracking** — owned objects are serialised automatically across concurrent transactions to prevent equivocation
- **Coins mode** — a pool of dedicated gas coins; each in-flight transaction holds one exclusively, returned after effects apply
- **Address balance mode** — no coin pool; the node selects gas from the sender's balance; concurrency bounded by ``max_tasks``

GraphQL — ``GqlParallelTransactionExecutor``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Coins mode** — requires seeding the pool before the first call.
``seed_coin_pool`` is mandatory: ``checkout()`` blocks until a coin is available, so an empty
pool at the start of ``execute_transactions`` will deadlock. Auto-refill maintains the pool
during execution but cannot start it from zero.

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import GasCoin

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = await client.parallel_executor(
            sender=cfg.active_address,
            gas_mode="coins",
            max_tasks=4,
            default_gas_budget=50_000_000,
            low_water_mark=5,
        )

        # Must seed the pool before calling execute_transactions
        await executor.seed_coin_pool([
            GasCoin(object_id="0xABC...", version="1", digest="...", balance=10_000_000),
        ])

        txns = []
        for _ in range(8):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        results = await executor.execute_transactions(txns)
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r)

**Address balance mode** — no pool required; optional low-balance callback:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors.exec_types import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        # top up balance and return truthy to continue, or None/falsy to halt
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = await client.parallel_executor(
            sender=cfg.active_address,
            gas_mode="addressBalance",
            max_tasks=4,
            default_gas_budget=50_000_000,
            min_balance_threshold=100_000_000,
            on_balance_low=on_balance_low,
        )

        txns = []
        for _ in range(8):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        results = await executor.execute_transactions(txns)
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r)

gRPC — ``GrpcParallelTransactionExecutor``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same interface as the GraphQL parallel executor; only the client type and import differ.

**Coins mode**:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import GasCoin

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)
        executor = await client.parallel_executor(
            sender=cfg.active_address,
            gas_mode="coins",
            max_tasks=4,
            default_gas_budget=50_000_000,
        )

        # Must seed the pool before calling execute_transactions
        await executor.seed_coin_pool([
            GasCoin(object_id="0xABC...", version="1", digest="...", balance=10_000_000),
        ])

        txns = []
        for _ in range(4):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        results = await executor.execute_transactions(txns)
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r)

**Address balance mode**:

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors.exec_types import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)
        executor = await client.parallel_executor(
            sender=cfg.active_address,
            gas_mode="addressBalance",
            max_tasks=4,
            default_gas_budget=50_000_000,
        )

        txns = []
        for _ in range(4):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        results = await executor.execute_transactions(txns)
        for r in results:
            if isinstance(r, tuple):
                err, exc = r
                print(f"Error: {err.name} — {exc}")
            else:
                print(r)

---

Result Handling
---------------

All ``execute_transactions`` calls return a list of the same length as the input list.
Each element is either a success value or a failure tuple:

**Parallel executors** return ``TransactionEffects | (ExecutorError, Exception)``.

**Serial executors** return ``sui_prot.ExecutedTransaction | (ExecutorError, Exception) | ExecutionSkipped``.
``ExecutionSkipped`` is returned for transactions after a halt (e.g. replenishment declined).

.. code-block:: python

    from pysui.sui.sui_common.executors import ExecutorError, ExecutionSkipped

    def print_result(r):
        if isinstance(r, ExecutionSkipped):
            print(f"Skipped tx {r.transaction_index}: {r.reason}")
        elif isinstance(r, tuple):
            err, exc = r
            print(f"Error: {err.name} — {exc}")
        else:
            # ExecutedTransaction — serialise as needed
            print(r.to_json(indent=2))

    results = await executor.execute_transactions(txns)
    for r in results:
        print_result(r)

---

Constructor Parameters
-----------------------

Parallel executors (``GqlParallelTransactionExecutor``, ``GrpcParallelTransactionExecutor``):

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - ``gas_mode``
     - ``"coins"`` or ``"addressBalance"``
   * - ``max_tasks``
     - Maximum concurrent in-flight transactions (default: ``4``)
   * - ``low_water_mark``
     - Pool size below which an auto-refill is triggered (coins mode, default: ``5``)
   * - ``coin_split_amount``
     - MIST per gas coin in auto-refill splits (default: ``10_000_000``)
   * - ``min_balance_per_coin``
     - Retire a coin when its balance falls below this value
   * - ``min_balance_threshold``
     - Balance level that triggers ``on_balance_low`` (addressBalance mode)
   * - ``on_balance_low``
     - Async callback fired when balance is low (required if ``min_balance_threshold`` set)
   * - ``registry``
     - Shared ``AbstractObjectRegistry``; defaults to the process-wide singleton
