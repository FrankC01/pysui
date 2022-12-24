#    Copyright 2022 Frank V. Castellucci
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# -*- coding: utf-8 -*-

"""Sui Asynchronous subscription module."""

import asyncio
import ssl
import json
from typing import Any, Callable, Tuple, Union
import warnings
from websockets.client import connect as ws_connect

from pysui.abstracts import Provider
from pysui.sui.sui_types.scalars import SuiString
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_builders.subscription_builders import SubscribeEvent, SubscribeTransaction
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_txresults.complex_tx import SubscribedEvent, SubscribedTransaction


class Subscribe(Provider):
    """."""

    _ACCESS_LOCK = asyncio.Lock()

    def __init__(self, config: SuiConfig):
        """."""
        super().__init__(config)
        self._event_subscriptions: dict[str, asyncio.Task] = {}
        self._txn_subscriptions: dict[str, asyncio.Task] = {}
        self._header = {"Content-Type": "application/json"}
        self._in_shutdown = False

    async def _subscription_listener(
        self,
        builder: Union[SubscribeEvent, SubscribeTransaction],
        handler: Callable[[Union[SubscribedEvent, SubscribedEvent], int], Any],
    ):
        """."""
        # Filter the warning about deprecated SSL context
        warnings.simplefilter("ignore")
        _txsub = {"jsonrpc": "2.0", "id": 1, "method": None, "params": []}
        async with ws_connect(
            self.config.socket_url, extra_headers=self._header, ssl=ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        ) as websock:
            _txsub["method"] = builder.method
            parm_arg = builder.params[0]
            if isinstance(parm_arg, SuiString):
                _txsub["params"].append(parm_arg.value)
            elif isinstance(parm_arg, SuiMap):
                _txsub["params"].append(parm_arg.filter)
            else:
                raise AttributeError(f"{parm_arg} not an accepted type")
            print(_txsub)
            await websock.send(json.dumps(_txsub))
            # First we get a subscription ID
            response = json.loads(await websock.recv())
            if "error" in response:
                print(response)
                return SuiRpcResult(False, response["error"])
            subscription_id: int = response["result"]
            keep_running = True
            event_counter = 0
            result_data: dict[int, Any] = {}
            try:
                while keep_running:
                    # Get an event
                    the_event = await websock.recv()
                    try:
                        keep_running = handler(
                            builder.handle_return(json.loads(the_event)), subscription_id, event_counter
                        )
                    # Indicative of deserialization error
                    except KeyError as kex:
                        print(f"KeyError on {kex}")
                        print(f"from ... {the_event}")
                        keep_running = False
                    if keep_running:
                        result_data[event_counter] = keep_running
                        event_counter += 1
            except asyncio.CancelledError:
                return SuiRpcResult(True, "Cancelled", result_data)
        return SuiRpcResult(True, None, result_data)

    async def new_event_subscription(
        self,
        sbuilder: SubscribeEvent,
        handler: Callable[[SubscribedEvent, int], Any],
        task_name: str = None,
    ) -> SuiRpcResult:
        """."""
        _result_data: dict[str, asyncio.Task] = {}
        async with self._ACCESS_LOCK:
            if not self._in_shutdown:
                new_task: asyncio.Task = asyncio.create_task(
                    self._subscription_listener(sbuilder, handler), name=task_name
                )
                _task_name = new_task.get_name()
                print(f"{_task_name} created {new_task}")
                self._event_subscriptions[_task_name] = new_task
                _result_data[_task_name] = new_task
                _sui_result = SuiRpcResult(True, None, _result_data)
            else:
                _result_data[task_name] = None
                _sui_result = SuiRpcResult(False, "Not started: In shutdown mode", _result_data)
        return _sui_result

    async def new_txn_subscription(
        self,
        tbuilder: SubscribeTransaction,
        handler: Callable[[SubscribedTransaction, int], Union[Any, bool]],
        task_name: str = None,
    ) -> SuiRpcResult:
        """."""
        _result_data: dict[str, asyncio.Task] = {}
        async with self._ACCESS_LOCK:
            if not self._in_shutdown:
                new_task: asyncio.Task = asyncio.create_task(
                    self._subscription_listener(tbuilder, handler), name=task_name
                )
                _task_name = new_task.get_name()
                self._txn_subscriptions[_task_name] = new_task
                _result_data[_task_name] = new_task
                _sui_result = SuiRpcResult(True, None, _result_data)
            else:
                _result_data[task_name] = None
                _sui_result = SuiRpcResult(False, "Not started: In shutdown mode", _result_data)
        return _sui_result

    async def wait_shutdown(self) -> Tuple[list, list]:
        """."""
        async with self._ACCESS_LOCK:
            self._in_shutdown = True
            tx_sub_results = await asyncio.gather(*self._txn_subscriptions.values(), return_exceptions=True)
            ev_sub_results = await asyncio.gather(*self._event_subscriptions.values(), return_exceptions=True)
            self._in_shutdown = False
        return (tx_sub_results, ev_sub_results)

    async def kill_shutdown(self, wait_seconds: int = None) -> dict:
        """."""
        async with self._ACCESS_LOCK:
            self._in_shutdown = True
            _results: dict[str, bool] = {}
            # First pass
            for task_name, task in self._event_subscriptions.items():
                print(f"Cancelling event subscription {task_name} -> {task}")
                state = task.cancel()
                if state:
                    _results[task.get_name()] = task
            for task_name, task in self._txn_subscriptions.items():
                print(f"Cancelling transaction subscription {task_name}")
                state = task.cancel()
                if state:
                    _results[task.get_name()] = task
            # If we have results and are asked to wait for themm to complete
            if _results and wait_seconds:
                print(f"Waiting {wait_seconds} seconds for straglers {len(_results)}")
                await asyncio.sleep(float(wait_seconds))
                for task_name, task in _results.items():
                    print(f"Cancelling {task_name}")
                    state = task.cancel()
            self._in_shutdown = False
        return _results
