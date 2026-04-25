
Transaction Executors
=====================

pysui provides high-level transaction executors for both GraphQL and gRPC transports.
All executors are asynchronous-only.

Two execution strategies are available:

- **Serial** — one transaction at a time, backed by an object cache for efficient gas and object resolution
- **Parallel** — multiple concurrent transactions, with built-in conflict tracking (owned-object serialisation), gas coin pool management, and balance monitoring

---

Gas Funding Modes
-----------------

Both serial and parallel executors support two gas funding modes:

**Coins mode**
    Gas is paid from one or more ``Coin<SUI>`` objects owned by the sender (or sponsor).
    The executor tracks which coin objects are being used and updates them from transaction effects.

    For serial executors, set ``on_coins_low`` to opt in to coin-balance threshold monitoring.
    For parallel executors, pass ``gas_mode="coins"`` and call ``seed_coin_pool`` before
    the first ``execute_transactions`` call.

**Address balance mode**
    Gas is drawn from the sender's accumulated address balance (SUI accumulator).
    No coin objects need to be managed — the node selects gas automatically.

    For serial executors, set ``on_balance_low`` to opt in to address-balance threshold monitoring.
    For parallel executors, pass ``gas_mode="addressBalance"``.

Address balance mode is the higher-throughput option: it eliminates coin check-out/check-in
overhead and pool contention, relying only on the concurrency semaphore as back-pressure.
Coins mode gives tighter control over which objects pay gas, at the cost of pool management.

For both serial executors: passing neither ``on_coins_low`` nor ``on_balance_low`` is valid —
the executor uses gas coins and works without threshold monitoring.

---

Serial Executors
----------------

Serial executors execute transactions one at a time in the order provided.
An internal object cache is primed on the first transaction (gas objects are consolidated);
subsequent transactions resolve from cache, making them significantly faster.

Note: ``execute_transactions`` is not re-entrant. Concurrent calls on the same instance are
serialized by an internal lock.

GraphQL — ``GqlSerialTransactionExecutor``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Coins gas mode** (``on_coins_low``):

.. code-block:: python

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_pgql.execute import GqlSerialTransactionExecutor, CachingTransaction
    from pysui.sui.sui_common.executors import ExecutorContext

    async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
        # return new coin IDs to continue, or None/[] to halt
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = GqlSerialTransactionExecutor(
            client=client,
            sender=cfg.active_address,
            default_gas_budget=5_000_000,
            min_balance_threshold=100_000_000,
            on_coins_low=on_coins_low,
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
                print(r)

**Address balance gas mode** (``on_balance_low``):

.. code-block:: python

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_pgql.execute import GqlSerialTransactionExecutor, CachingTransaction
    from pysui.sui.sui_common.executors import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        # perform top-up, return funding address for logging, or None to halt
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = GqlSerialTransactionExecutor(
            client=client,
            sender=cfg.active_address,
            default_gas_budget=5_000_000,
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
                print(r)

gRPC — ``GrpcSerialTransactionExecutor``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The gRPC serial executor has the same interface as the GraphQL one; only the client type differs.

**Coins gas mode**:

.. code-block:: python

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_grpc.grpc_serial_exec import GrpcSerialTransactionExecutor
    from pysui.sui.sui_common.executors import ExecutorContext

    async def on_coins_low(ctx: ExecutorContext) -> list[str] | None:
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)
        executor = GrpcSerialTransactionExecutor(
            client=client,
            sender=cfg.active_address,
            default_gas_budget=5_000_000,
            min_balance_threshold=100_000_000,
            on_coins_low=on_coins_low,
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
                print(r)

**Address balance gas mode**:

.. code-block:: python

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_grpc.grpc_serial_exec import GrpcSerialTransactionExecutor
    from pysui.sui.sui_common.executors import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)
        executor = GrpcSerialTransactionExecutor(
            client=client,
            sender=cfg.active_address,
            default_gas_budget=5_000_000,
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
                print(r)

---

Parallel Executors
------------------

Parallel executors run transactions concurrently using ``asyncio.gather``. They include:

- **Conflict tracking** — owned objects are serialised automatically across concurrent transactions to prevent equivocation
- **Coins mode** — a pool of dedicated gas coins; each in-flight transaction holds one exclusively, returned after effects apply
- **Address balance mode** — no coin pool; the node selects gas from the sender's balance; concurrency bounded by ``max_tasks``

GraphQL — ``GqlParallelTransactionExecutor``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Coins mode** — requires seeding the pool before the first call.
``seed_coin_pool`` is mandatory: ``checkout()`` blocks until a coin is available, so an empty
pool at the start of ``execute_transactions`` will deadlock. Auto-refill maintains the pool
during execution but cannot start it from zero.

.. code-block:: python

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_pgql.execute import GqlParallelTransactionExecutor
    from pysui.sui.sui_common.executors import GasCoin

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = GqlParallelTransactionExecutor(
            client=client,
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

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_pgql.execute import GqlParallelTransactionExecutor
    from pysui.sui.sui_common.executors import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        # top up balance and return truthy to continue, or None/falsy to halt
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        executor = GqlParallelTransactionExecutor(
            client=client,
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

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_grpc.grpc_parallel_exec import GrpcParallelTransactionExecutor
    from pysui.sui.sui_common.executors import GasCoin

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)
        executor = GrpcParallelTransactionExecutor(
            client=client,
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

    from pysui import PysuiConfiguration
    from pysui.sui.sui_common.factory import client_factory
    from pysui.sui.sui_grpc.grpc_parallel_exec import GrpcParallelTransactionExecutor
    from pysui.sui.sui_common.executors import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> str | None:
        return None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GRPC_GROUP)
        client = client_factory(cfg)
        executor = GrpcParallelTransactionExecutor(
            client=client,
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

**Serial executors** return ``TransactionEffects | (ExecutorError, Exception) | ExecutionSkipped``.
``ExecutionSkipped`` is returned for transactions after a halt (e.g. replenishment declined).

.. code-block:: python

    from pysui.sui.sui_common.executors import ExecutorError
    from pysui.sui.sui_common.types import TransactionEffects

    results = await executor.execute_transactions(txns)
    for r in results:
        if isinstance(r, tuple):
            err, exc = r
            print(f"{err.name}: {exc}")
        else:
            print(r)

---

Constructor Parameters
-----------------------

Serial executors (``GqlSerialTransactionExecutor``, ``GrpcSerialTransactionExecutor``):

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
   * - ``client``
     - Async protocol client (``AsyncGqlClient`` or ``SuiGrpcClient``)
   * - ``sender``
     - Sender address string or ``SigningMultiSig``
   * - ``sponsor``
     - Optional sponsor address or ``SigningMultiSig``
   * - ``default_gas_budget``
     - Gas budget per transaction (default: ``50_000_000``)
   * - ``min_balance_threshold``
     - Balance level that triggers the replenishment callback; requires one of the callbacks below
   * - ``on_coins_low``
     - Async callback for coins mode; return new coin IDs or ``None``/``[]`` to halt
   * - ``on_balance_low``
     - Async callback for address balance mode; return funding address or ``None`` to halt

Parallel executors (``GqlParallelTransactionExecutor``, ``GrpcParallelTransactionExecutor``) add:

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
