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
from websockets.client import WebSocketClientProtocol

from pysui.abstracts import Provider
from pysui.sui.sui_types.scalars import SuiString
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_clients.common import SuiRpcResult
from pysui.sui.sui_builders.subscription_builders import SubscribeEvent, SubscribeTransaction
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_txresults.complex_tx import SubscribedEvent, SubscribedTransaction


class EventData:
    """Container for subscription data returned from subscription handler."""

    def __init__(self, tx_name: str):
        """Initialie container."""
        self._name = tx_name
        self._collected: dict[int, Any] = {}

    def add_entry(self, event_index: int, data: Any) -> None:
        """Add a data entry to container."""
        self._collected[event_index] = data

    @property
    def collected(self) -> dict[int, Any]:
        """Get the data collection dictionary."""
        return self._collected

    @property
    def name(self) -> str:
        """Get the name of the task associated to this container and it's content."""
        return self._name


class SuiClient(Provider):
    """A provider for managing subscriptions of Events or Transactions."""

    _ACCESS_LOCK: asyncio.Lock = asyncio.Lock()
    _ADDITIONL_HEADER: str = {"Content-Type": "application/json"}
    _PAYLOAD_TEMPLATE: dict = {"jsonrpc": "2.0", "id": 1, "method": None, "params": []}

    def __init__(self, config: SuiConfig):
        """__init__ Client initializer.

        :param config: An instance of SuiConfig
        :type config: SuiConfig
        """
        super().__init__(config)
        self._event_subscriptions: dict[str, asyncio.Task] = {}
        self._txn_subscriptions: dict[str, asyncio.Task] = {}
        self._in_shutdown = False

    async def _subscription_drive(
        self,
        payload_msg: dict,
        builder: Union[SubscribedEvent, SubscribeTransaction],
        websock: WebSocketClientProtocol,
        handler: Callable[[Union[SubscribedEvent, SubscribedTransaction], int, int], Any],
    ) -> SuiRpcResult:
        """_subscription_drive Iterate receiving events and calling handler function.

        :parm payload_msg: A copy of a subscription template RPC call
        :type payload_msg: dict
        :param builder: The subscription builder submitted for creating subscription filters.
        :type builder: Union[SubscribedEvent, SubscribeTransaction]
        :param websock: The live websocket connection
        :type websock: WebSocketClientProtocol
        :param handler: The function called for each received event.
        :type handler: Callable[[Union[SubscribedEvent, SubscribedEvent], int], Any]
        :return: _description_
        :rtype: SuiRpcResult
        """
        payload_msg["method"] = builder.method
        parm_arg = builder.params[0]
        if isinstance(parm_arg, SuiString):
            payload_msg["params"] = [parm_arg.value]
        elif isinstance(parm_arg, SuiMap):
            payload_msg["params"] = [parm_arg.filter]
        else:
            return SuiRpcResult(False, f"{parm_arg} not an accepted type")

        await websock.send(json.dumps(payload_msg))
        # First we get a subscription ID
        response = json.loads(await websock.recv())
        if "error" in response:
            return SuiRpcResult(False, response["error"], response)
        subscription_id: int = response["result"]
        # print(f"Subscription ID = {subscription_id}")
        keep_running = True
        event_counter = 0
        result_data: EventData = EventData(asyncio.current_task().get_name())
        try:
            while keep_running:
                # Get an event
                the_event = await websock.recv()
                try:
                    keep_running = handler(builder.handle_return(json.loads(the_event)), subscription_id, event_counter)
                # Indicative of deserialization error
                except KeyError as kex:
                    return SuiRpcResult(False, f"KeyError on {kex}", the_event)
                if keep_running:
                    if not isinstance(keep_running, bool):
                        result_data.add_entry(event_counter, keep_running)
                        event_counter += 1
        except asyncio.CancelledError:
            return SuiRpcResult(True, "Cancelled", result_data)
        return SuiRpcResult(True, None, result_data)

    async def _subscription_listener(
        self,
        builder: Union[SubscribeEvent, SubscribeTransaction],
        handler: Callable[[Union[SubscribedEvent, SubscribedTransaction], int, int], Any],
    ) -> SuiRpcResult:
        """_subscription_listener Sets up websocket subscription and calls _subscription_drive.

        :param builder: The subscription builder submitted for creating subscription filters.
        :type builder: Union[SubscribedEvent, SubscribeTransaction]
        :param handler: The function called for each received event.
        :type handler: Callable[[Union[SubscribedEvent, SubscribedEvent], int], Any]
        :return: Result of subscription event handling.
        :rtype: SuiRpcResult
        """
        try:
            if self.config.local_config:
                async with ws_connect(
                    self.config.socket_url,
                    extra_headers=self._ADDITIONL_HEADER,
                ) as websock:
                    return await self._subscription_drive(self._PAYLOAD_TEMPLATE.copy(), builder, websock, handler)
            else:
                # Filter the warning about deprecated SSL context
                warnings.simplefilter("ignore")
                async with ws_connect(
                    self.config.socket_url,
                    extra_headers=self._ADDITIONL_HEADER,
                    ssl=ssl.SSLContext(ssl.PROTOCOL_SSLv23),
                ) as websock:
                    warnings.simplefilter("default")
                    return await self._subscription_drive(self._PAYLOAD_TEMPLATE.copy(), builder, websock, handler)
        except AttributeError as axc:
            return SuiRpcResult(False, "Attribute Error", axc)
        except Exception as axc:
            return SuiRpcResult(False, "Exception", axc)

    async def new_event_subscription(
        self,
        sbuilder: SubscribeEvent,
        handler: Callable[[SubscribedEvent, int, int], Any],
        task_name: str = None,
    ) -> SuiRpcResult:
        """new_event_subscription Initiate and run a move event subscription feed.

        :param sbuilder: The subscription builder submitted for creating the event subscription filter.
        :type sbuilder: SubscribeEvent
        :param handler: The function called for each received move event.
        :type handler: Callable[[SubscribedEvent, int], Any]
        :param task_name: A name to assign to the listener task, defaults to None
        :type task_name: str, optional
        :return: Result of subscribed move event handling
        :rtype: SuiRpcResult
        """
        _result_data: dict[str, asyncio.Task] = {}
        async with self._ACCESS_LOCK:
            if not self._in_shutdown:
                new_task: asyncio.Task = asyncio.create_task(
                    self._subscription_listener(sbuilder, handler), name=task_name
                )
                _task_name = new_task.get_name()
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
        handler: Callable[[SubscribedTransaction, int, int], Any],
        task_name: str = None,
    ) -> SuiRpcResult:
        """new_txn_subscription Initiate and run a transaction event subscription feed.

        :param tbuilder: The subscription builder submitted for creating the transaction subscription filter.
        :type tbuilder: SubscribeEvent
        :param handler: The function called for each received transaction event.
        :type handler: Callable[[SubscribedTransaction, int], Any]
        :param task_name: A name to assign to the listener task, defaults to None
        :type task_name: str, optional
        :return: Result of subscribed transaction event handling
        :rtype: SuiRpcResult
        """
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
        """wait_shutdown Waits until all subscription tasks complete and gathers the results.

        :return: A tuple of (Tranaction type events result list,Event type events result list)
        :rtype: Tuple[list, list]
        """
        async with self._ACCESS_LOCK:
            self._in_shutdown = True
            tx_sub_results = await asyncio.gather(*self._txn_subscriptions.values(), return_exceptions=True)
            ev_sub_results = await asyncio.gather(*self._event_subscriptions.values(), return_exceptions=True)
            self._in_shutdown = False
        return (tx_sub_results, ev_sub_results)

    async def kill_shutdown(self, wait_seconds: int = None) -> Tuple[list, list]:
        """kill_shutdown Iterates through any event subscription types, cancelling those still active.

        :param wait_seconds: Delay, if any, to perform second cancelation on tasks, defaults to None
        :type wait_seconds: int, optional
        :return: A tuple of (Tranaction type events result list,Event type events result list) from wait_shutdown
        :rtype: Tuple[list, list]
        """
        async with self._ACCESS_LOCK:
            self._in_shutdown = True
            _results: dict[str, bool] = {}
            # First pass
            for task_name, task in self._event_subscriptions.items():
                state = task.cancel()
                if state:
                    _results[task_name] = task
            for task_name, task in self._txn_subscriptions.items():
                state = task.cancel()
                if state:
                    _results[task_name] = task
            # If we have results and are asked to wait for themm to complete
            if _results and wait_seconds:
                await asyncio.sleep(float(wait_seconds))
                for _task_name, task in _results.items():
                    state = task.cancel()
            self._in_shutdown = False
        # Wait and gather task results
        return await self.wait_shutdown()
