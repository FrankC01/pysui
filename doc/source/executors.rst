Transaction Executors
=====================

pysui provides high-level transaction executors for both GraphQL and gRPC transports.
All executors are asynchronous-only.

Two execution strategies are available:

- **Serial** — one transaction at a time, or one batch of transactions with each transaction execution serialized, backed by an object cache for efficient gas and object resolution
- **Parallel** — multiple concurrent transactions, with built-in conflict tracking (owned-object serialisation), gas coin pool management, and balance monitoring

Gas Funding Modes
-----------------

Both serial and parallel executors support two gas funding modes:

**Coins mode**
    Gas is paid from one or more ``Coin<SUI>`` objects owned by the sender.
    The executor tracks which coin objects are being used and updates them from transaction effects.

**Address balance mode**
    Gas is drawn from the sender's accumulated address balance (SUI accumulator).
    No coin objects need to be managed — the node selects gas automatically.

Address balance mode is the higher-throughput option: it eliminates coin check-out/check-in
overhead and pool contention, relying only on the concurrency semaphore as back-pressure.
Coins mode gives tighter control over which objects pay gas, at the cost of pool management.

Serial Executors
----------------

Serial executors execute transactions in the order provided; multiple transactions can be
batched and submitted together via ``submit()``, where each is executed serially in
sequence. An internal object cache accumulates object versions as transactions execute;
subsequent transactions that reuse the same objects resolve from cache, avoiding redundant
network fetches.

``SerialExecutor`` is the single concrete serial executor class, shared across both
GraphQL and gRPC transports. Only the :func:`client_factory` group name differs between
transports — the executor interface is identical.

Obtain an instance via :meth:`serial_executor`, passing a fully configured
:class:`ExecutorOptions` instance.

Restrictions
~~~~~~~~~~~~

- **No sponsored transactions** — only the sender's gas coin is used. Sponsor-pays
  patterns are not supported by the serial executor.

- **Gas coin threshold with** ``txn.gas`` **references** — if the transactions being
  submitted reference ``txn.gas`` directly (e.g.
  ``txn.split_coin(coin=txn.gas, amounts=[...])``) the gas coin balance is consumed by
  both gas fees *and* the PTB operation. In this case ``min_threshold_balance`` may need
  a significantly higher starting value than the default.

**Coins gas mode** (``SerialGasMode.COINS``):

``ExecutorOptions`` parameters:

+----------------------------+--------------------------------------------------------------+
| Parameter                  | Description                                                  |
+============================+==============================================================+
| ``sender``                 | Sender address string or ``SigningMultiSig``                 |
+----------------------------+--------------------------------------------------------------+
| ``gas_mode``               | ``SerialGasMode.COINS`` or                                   |
|                            | ``SerialGasMode.ADDRESS_BALANCE``                            |
+----------------------------+--------------------------------------------------------------+
| ``initial_coins``          | List of coin object IDs (``list[str]``) or pre-fetched coin  |
|                            | objects. An empty list triggers automatic coin selection via |
|                            | ``GetGas``. In COINS mode, selected coins are merged into a  |
|                            | single gas coin. In ADDRESS_BALANCE mode, selected coins are |
|                            | sent to the sender's address accumulator when the existing   |
|                            | balance is below ``min_threshold_balance``.                  |
+----------------------------+--------------------------------------------------------------+
| ``min_threshold_balance``  | Minimum MIST balance before ``on_balance_low`` fires. In     |
|                            | COINS mode, tracks the managed gas coin balance; in          |
|                            | ADDRESS_BALANCE mode, tracks the address accumulator.        |
|                            | Default: ``10_000_000``. Increase for workloads with high    |
|                            | gas consumption or that reference ``txn.gas`` in PTB         |
|                            | operations.                                                  |
+----------------------------+--------------------------------------------------------------+
| ``on_balance_low``         | Optional async callback invoked when balance drops below     |
|                            | ``min_threshold_balance``. Receives a                        |
|                            | ``SerialExecutorContext``. In COINS mode, return a list of   |
|                            | additional coins to merge in, or ``None``/``[]`` to halt.    |
|                            | In ADDRESS_BALANCE mode, return any truthy value to          |
|                            | continue or ``None`` to halt.                                |
+----------------------------+--------------------------------------------------------------+
| ``max_retries``            | Number of replenishment attempts before halting              |
|                            | (default: ``1``)                                             |
+----------------------------+--------------------------------------------------------------+
| ``on_failure``             | Controls behavior when a transaction fails with remaining    |
|                            | transactions still queued. ``"continue"`` (default)          |
|                            | processes remaining transactions; ``"exit"`` halts the       |
|                            | batch immediately.                                           |
+----------------------------+--------------------------------------------------------------+

Returns a ``SerialExecutor`` — initialized and ready to use.

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import ExecutorOptions, SerialGasMode

    async def run():
        # Use SUI_GQL_RPC_GROUP for GraphQL or SUI_GRPC_GROUP for gRPC
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        options = ExecutorOptions(
            sender=cfg.active_address,
            gas_mode=SerialGasMode.COINS,
            initial_coins=[],            # empty → auto-fetch from sender's SUI coins
            min_threshold_balance=100_000_000,
        )
        executor = await client.serial_executor(options=options)

        txn = await executor.new_transaction()
        coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
        await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)

        future = executor.submit(txn)
        result = await future
        if isinstance(result, tuple):
            err, exc = result
            print(f"Error: {err.name} — {exc}")
        else:
            print(result.to_json(indent=2))

**Using** ``on_balance_low`` **(coins mode):**

The callback is invoked when the managed gas coin balance drops below
``min_threshold_balance``. It receives a :class:`SerialExecutorContext` with ``sender``,
``tracked_balance``, ``min_threshold_balance``, and ``client``. Return additional coins
to merge in, or ``None``/``[]`` to halt:

.. code-block:: python

    import asyncio
    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import ExecutorOptions, SerialGasMode, SerialExecutorContext
    import pysui.sui.sui_common.sui_commands as cmd

    async def on_balance_low(ctx: SerialExecutorContext) -> list | None:
        result = await ctx.client.execute_for_all(
            cmd.GetGas(owner=ctx.sender)
        )
        if result.is_err():
            return None
        coins = result.result_data.objects
        return coins if coins else None

    async def run():
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        options = ExecutorOptions(
            sender=cfg.active_address,
            gas_mode=SerialGasMode.COINS,
            initial_coins=[],
            min_threshold_balance=100_000_000,
            on_balance_low=on_balance_low,
        )
        executor = await client.serial_executor(options=options)

        txns = []
        for _ in range(3):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        futures = executor.submit(txns)
        results = await asyncio.gather(*futures)
        for result in results:
            if isinstance(result, tuple):
                err, exc = result
                print(f"Error: {err.name} — {exc}")
            else:
                print(result.to_json(indent=2))

**Address balance gas mode** (``SerialGasMode.ADDRESS_BALANCE``):

.. code-block:: python

    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import ExecutorOptions, SerialGasMode, SerialExecutorContext

    async def on_balance_low(ctx: SerialExecutorContext) -> list | None:
        # perform top-up; return truthy to continue, or None to halt
        return None

    async def run():
        # Use SUI_GQL_RPC_GROUP for GraphQL or SUI_GRPC_GROUP for gRPC
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        options = ExecutorOptions(
            sender=cfg.active_address,
            gas_mode=SerialGasMode.ADDRESS_BALANCE,
            initial_coins=[],
            min_threshold_balance=100_000_000,
            on_balance_low=on_balance_low,
        )
        executor = await client.serial_executor(options=options)

        txn = await executor.new_transaction()
        coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000_000])
        await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)

        future = executor.submit(txn)
        result = await future
        if isinstance(result, tuple):
            err, exc = result
            print(f"Error: {err.name} — {exc}")
        else:
            print(result.to_json(indent=2))

Parallel Executors
------------------

``ParallelExecutor`` is the single concrete parallel executor, shared across both
GraphQL and gRPC transports. It runs transactions concurrently with:

- **Conflict tracking** — owned-object inputs are serialised automatically across concurrent
  transactions to prevent equivocation
- **Coins mode** — a dedicated gas coin pool; each in-flight transaction holds one coin
  exclusively, returned after effects are applied
- **Address balance mode** — no coin pool; the node selects gas from the sender's address
  accumulator; throughput is bounded only by ``max_concurrent``

Obtain an instance via :meth:`parallel_executor`, passing a fully configured
:class:`ExecutorOptions` instance.

``ExecutorOptions`` parameters:

+----------------------------+--------------------------------------------------------------+
| Parameter                  | Description                                                  |
+============================+==============================================================+
| ``sender``                 | Sender address string or ``SigningMultiSig``                 |
+----------------------------+--------------------------------------------------------------+
| ``gas_mode``               | ``GasMode.COINS`` or ``GasMode.ADDRESS_BALANCE``             |
+----------------------------+--------------------------------------------------------------+
| ``initial_coins``          | List of coin object IDs (``list[str]``) or pre-fetched coin  |
|                            | objects. An empty list triggers automatic coin selection via |
|                            | ``GetGas``. In COINS mode, selected coins are added to the   |
|                            | gas coin pool. In ADDRESS_BALANCE mode, selected coins are   |
|                            | sent to the sender's address accumulator when the existing   |
|                            | balance is below ``min_threshold_balance``.                  |
+----------------------------+--------------------------------------------------------------+
| ``min_threshold_balance``  | Minimum MIST balance before ``on_balance_low`` fires.        |
|                            | Default: ``10_000_000``.                                     |
+----------------------------+--------------------------------------------------------------+
| ``max_concurrent``         | Maximum number of in-flight transactions at once             |
|                            | (default: ``10``). Controls the concurrency semaphore that   |
|                            | bounds all submitted tasks.                                  |
+----------------------------+--------------------------------------------------------------+
| ``on_balance_low``         | Optional async callback invoked when tracked balance drops   |
|                            | below ``min_threshold_balance``. Receives an                 |
|                            | :class:`ExecutorContext`. Return a list of coins to add, or  |
|                            | ``None``/``[]`` to halt.                                     |
+----------------------------+--------------------------------------------------------------+
| ``max_retries``            | Number of replenishment attempts on gas error before halting |
|                            | (default: ``1``).                                            |
+----------------------------+--------------------------------------------------------------+
| ``on_failure``             | Controls behavior when a transaction fails with remaining    |
|                            | transactions still queued. ``"continue"`` (default)          |
|                            | continues; ``"exit"`` halts the executor immediately.        |
+----------------------------+--------------------------------------------------------------+

**Coins mode:**

.. code-block:: python

    import asyncio
    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import ExecutorOptions, GasMode

    async def run():
        # Use SUI_GQL_RPC_GROUP for GraphQL or SUI_GRPC_GROUP for gRPC
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        options = ExecutorOptions(
            sender=cfg.active_address,
            gas_mode=GasMode.COINS,
            initial_coins=[],            # empty → auto-fetch from sender's SUI coins
            min_threshold_balance=100_000_000,
            max_concurrent=4,
        )
        executor = await client.parallel_executor(options=options)

        txns = []
        for _ in range(8):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        futures = executor.submit(txns)
        results = await asyncio.gather(*futures)
        for result in results:
            if isinstance(result, tuple):
                err, exc = result
                print(f"Error: {err.name} — {exc}")
            else:
                print(result.to_json(indent=2))

        await executor.close()

**Address balance mode:**

.. code-block:: python

    import asyncio
    from pysui import PysuiConfiguration, client_factory
    from pysui.sui.sui_common.executors import ExecutorOptions, GasMode
    from pysui.sui.sui_common.executors.exec_types import ExecutorContext

    async def on_balance_low(ctx: ExecutorContext) -> list | None:
        # top up and return coins, or None to halt
        return None

    async def run():
        # Use SUI_GQL_RPC_GROUP for GraphQL or SUI_GRPC_GROUP for gRPC
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        client = client_factory(cfg)
        options = ExecutorOptions(
            sender=cfg.active_address,
            gas_mode=GasMode.ADDRESS_BALANCE,
            initial_coins=[],
            min_threshold_balance=100_000_000,
            on_balance_low=on_balance_low,
            max_concurrent=4,
        )
        executor = await client.parallel_executor(options=options)

        txns = []
        for _ in range(8):
            txn = await executor.new_transaction()
            coin = await txn.split_coin(coin=txn.gas, amounts=[1_000_000])
            await txn.transfer_objects(transfers=[coin], recipient=cfg.active_address)
            txns.append(txn)

        futures = executor.submit(txns)
        results = await asyncio.gather(*futures)
        for result in results:
            if isinstance(result, tuple):
                err, exc = result
                print(f"Error: {err.name} — {exc}")
            else:
                print(result.to_json(indent=2))

        await executor.close()

Result Handling
---------------

``submit()`` returns a single ``asyncio.Future`` for one transaction, or a list of
``asyncio.Future`` objects when passed a list. Await futures individually or gather them:

.. code-block:: python

    import asyncio
    from pysui.sui.sui_common.executors import ExecutorError, ExecutionSkipped

    # Single transaction
    future = executor.submit(txn)
    result = await future

    # Batch
    futures = executor.submit([txn1, txn2, txn3])
    results = await asyncio.gather(*futures)

Each resolved value is one of:

- ``sui_prot.ExecutedTransaction`` — success
- ``(ExecutorError, Exception)`` — build or execution failure
- ``ExecutionSkipped`` — transaction was not attempted (executor halted before reaching it)

**Serial executors** use the same result types. ``ExecutionSkipped`` is returned for
transactions that were queued after a halt (e.g. replenishment declined).

.. code-block:: python

    def print_result(r):
        if isinstance(r, ExecutionSkipped):
            print(f"Skipped: {r.reason}")
        elif isinstance(r, tuple):
            err, exc = r
            print(f"Error: {err.name} — {exc}")
        else:
            print(r.to_json(indent=2))

    for r in results:
        print_result(r)
