#    Copyright Frank V. Castellucci
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
import logging
import ssl
import json
import inspect
from typing import Any, Callable, Optional, Union
import warnings
from deprecated.sphinx import versionadded, versionchanged, deprecated
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, ConnectionClosedError
from websockets.client import WebSocketClientProtocol

from pysui import SuiRpcResult, SuiConfig

from pysui.abstracts import Provider
from pysui.sui.sui_types.scalars import SuiString
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_builders.subscription_builders import (
    SubscribeEvent,
    SubscribeTransaction,
)
from pysui.sui.sui_txresults.complex_tx import (
    SubscribedEvent,
    SubscribedTransaction,
)

# Standard library logging setup
logger = logging.getLogger("pysui.subscribe")
if not logging.getLogger().handlers:
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


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


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class SuiClient(Provider):
    """A provider for managing subscriptions of Events or Transactions."""

    _ACCESS_LOCK: asyncio.Lock = asyncio.Lock()
    _ADDITIONL_HEADER: str = {"Content-Type": "application/json"}
    _PAYLOAD_TEMPLATE: dict = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": None,
        "params": [],
    }

    @versionchanged(
        version="0.20.0", reason="Added transaction subscription management."
    )
    def __init__(self, config: SuiConfig):
        """__init__ Client initializer.

        :param config: An instance of SuiConfig
        :type config: SuiConfig
        """
        super().__init__(config)
        self._event_subscriptions: dict[str, asyncio.Task] = {}
        self._txn_subscriptions: dict[str, asyncio.Task] = {}
        self._in_shutdown = False

    @versionchanged(
        version="0.20.0", reason="Added transaction subscription management."
    )
    @versionchanged(
        version="0.26.1",
        reason="Detect if handler is sync or async and invoke accordingly.",
    )
    async def _subscription_drive(
        self,
        payload_msg: dict,
        builder: Union[SubscribeEvent, SubscribeTransaction],
        websock: WebSocketClientProtocol,
        handler: Union[
            Callable[[SubscribedEvent, int, int], Any],
            Callable[[SubscribedTransaction, int, int], Any],
        ],
    ) -> SuiRpcResult:
        """_subscription_drive Iterate receiving events and calling handler function.

        :parm payload_msg: A copy of a subscription template RPC call
        :type payload_msg: dict
        :param builder: The subscription builder submitted for creating subscription filters.
        :type builder: Union[SubscribeEvent, SubscribeTransaction]
        :param websock: The live websocket connection
        :type websock: WebSocketClientProtocol
        :param handler: The function called for each received event.
        :type handler: Union[Callable[[SubscribedEvent, int, int], Any], Callable[[SubscribedTransaction, int, int], Any]]
        :return: _description_
        :rtype: SuiRpcResult
        """
        payload_msg["method"] = builder.method
        parm_arg = builder.params["filter"]
        if isinstance(parm_arg, SuiString):
            payload_msg["params"] = [parm_arg.value]
        elif isinstance(parm_arg, SuiMap):
            payload_msg["params"] = [parm_arg.filter]
        else:
            return SuiRpcResult(False, f"{parm_arg} not an accepted type")

        _is_asynch_handler = inspect.iscoroutinefunction(handler)
        logger.info(f"Handler is async -> {_is_asynch_handler}")
        logger.info("Starting listening event driver")
        await websock.send(json.dumps(payload_msg))
        # First we get a subscription ID
        response = json.loads(await websock.recv())
        if "error" in response:
            return SuiRpcResult(False, response["error"], response)
        subscription_id: int = response["result"]
        keep_running = True
        event_counter = 0
        result_data: EventData = EventData(asyncio.current_task().get_name())
        try:
            while keep_running:
                # Get an event
                the_event = await websock.recv()
                logger.debug("Subscription driver RECEIVED event")

                try:
                    if _is_asynch_handler:
                        keep_running = await handler(
                            builder.handle_return(json.loads(the_event)),
                            subscription_id,
                            event_counter,
                        )
                    else:
                        keep_running = handler(
                            builder.handle_return(json.loads(the_event)),
                            subscription_id,
                            event_counter,
                        )
                # Indicative of deserialization error
                # exit with result data
                except KeyError as kex:
                    logger.warning(
                        f"Subscription driver KeyError occured for shutdown -> {self._in_shutdown}"
                    )
                    return SuiRpcResult(False, f"KeyError on {kex}", result_data)
                # Catch anyother error and exit with result data
                except Exception as axc:
                    logger.warning(
                        f"Subscription driver Exception occured for shutdown -> {self._in_shutdown} {axc.args}"
                    )
                    return SuiRpcResult(False, f"Exception on {axc}", result_data)

                if keep_running:
                    if not isinstance(keep_running, bool):
                        result_data.add_entry(event_counter, keep_running)
                        event_counter += 1
                else:
                    logger.warning(
                        "Subscription driver Handler rquested exit from subscription events."
                    )
        except asyncio.CancelledError:
            if self._in_shutdown:
                logger.warning("Subscription cancelled by application")
            else:
                logger.warning(
                    f"asyncio.CancelledError occured for shutdown -> {self._in_shutdown}"
                )
            return SuiRpcResult(True, "Cancelled", result_data)
        return SuiRpcResult(True, None, result_data)

    @versionchanged(
        version="0.20.0", reason="Added transaction subscription management."
    )
    @versionchanged(
        version="0.28.0", reason="Socket protocol drives SSL configuration."
    )
    @versionchanged(
        version="0.29.0",
        reason="Refactored and handle connection close continuation option.",
    )
    async def _subscription_listener(
        self,
        builder: Union[SubscribeEvent, SubscribeTransaction],
        handler: Union[
            Callable[[SubscribedEvent, int, int], Any],
            Callable[[SubscribedTransaction, int, int], Any],
        ],
        continue_on_close: Optional[bool] = False,
    ) -> SuiRpcResult:
        """_subscription_listener Sets up websocket subscription and calls _subscription_drive.

        :param builder: The subscription builder submitted for creating subscription filters.
        :type builder: SubscribedEvent
        :param handler: The function called for each received event.
        :type handler: Callable[[SubscribedEvent, int], Any]
        :return: Result of subscription event handling.
        :rtype: SuiRpcResult
        """
        if self.config.socket_url.startswith("wss:"):
            logger.info("Subscription listener Connecting with SSLContext")
            warnings.simplefilter("ignore")
            async for websock in ws_connect(
                self.config.socket_url,
                extra_headers=self._ADDITIONL_HEADER,
                ssl=ssl.SSLContext(ssl.PROTOCOL_SSLv23),
            ):
                try:
                    res = await self._subscription_drive(
                        self._PAYLOAD_TEMPLATE.copy(),
                        builder,
                        websock,
                        handler,
                    )
                    logger.info(
                        f"Subscription listener returning in shutdown: {self._in_shutdown}"
                    )
                    await websock.close()
                    return res
                except (ConnectionClosed, ConnectionClosedError) as ws_cc:
                    ws_e_name = type(ws_cc).__name__
                    if continue_on_close and not self._in_shutdown:
                        logger.warning(
                            f"Subscription listener {ws_e_name}... reconnecting"
                        )
                        continue
                    else:
                        logger.error(
                            f"Subscription listener {ws_e_name} occured for shutdown -> {self._in_shutdown} {ws_cc.args}"
                        )
                        return SuiRpcResult(False, "ConnectionClosed", ws_cc)
                except Exception as exc:
                    e_name = type(exc).__name__
                    logger.error(
                        f"Subscription listener {e_name} occured in shutdown -> {self._in_shutdown} {exc.args}"
                    )
                    return SuiRpcResult(False, e_name, exc)
        else:
            logger.info("Subscription listener Connecting without SSLContext")
            async for websock in ws_connect(
                self.config.socket_url, extra_headers=self._ADDITIONL_HEADER
            ):
                try:
                    res = await self._subscription_drive(
                        self._PAYLOAD_TEMPLATE.copy(),
                        builder,
                        websock,
                        handler,
                    )
                    logger.info(
                        f"Subscription listener returning in shutdown: {self._in_shutdown}"
                    )
                    await websock.close()
                    return res
                except (ConnectionClosed, ConnectionClosedError) as ws_cc:
                    if continue_on_close and not self._in_shutdown:
                        logger.warning(
                            "Subscription listener ConnectionClosed... reconnecting"
                        )
                        continue
                    else:
                        logger.error(
                            f"Subscription listener ConnectionClosed occured for shutdown -> {self._in_shutdown} {ws_cc.args}"
                        )
                        return SuiRpcResult(False, "ConnectionClosed", ws_cc)
                except Exception as exc:
                    e_name = type(exc).__name__
                    logger.error(
                        f"Subscription listener {e_name} occured in shutdown -> {self._in_shutdown} {exc.args}"
                    )
                    return SuiRpcResult(False, e_name, exc)

    async def new_event_subscription(
        self,
        sbuilder: SubscribeEvent,
        handler: Callable[[SubscribedEvent, int, int], Any],
        task_name: str = None,
        continue_on_close: Optional[bool] = False,
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
                    self._subscription_listener(sbuilder, handler, continue_on_close),
                    name=task_name,
                )
                _task_name = new_task.get_name()
                self._event_subscriptions[_task_name] = new_task
                _result_data[_task_name] = new_task
                _sui_result = SuiRpcResult(True, None, _result_data)
            else:
                _result_data[task_name] = None
                _sui_result = SuiRpcResult(
                    False, "Not started: In shutdown mode", _result_data
                )
        return _sui_result

    @versionadded(version="0.20.0", reason="Transaction Effects Subscription")
    async def new_transaction_subscription(
        self,
        sbuilder: SubscribeTransaction,
        handler: Callable[[SubscribedTransaction, int, int], Any],
        task_name: str = None,
        continue_on_close: Optional[bool] = False,
    ) -> SuiRpcResult:
        """new_event_subscription Initiate and run a move event subscription feed.

        :param sbuilder: The subscription builder submitted for creating the transaction subscription filter.
        :type sbuilder: SubscribeTransaction
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
                    self._subscription_listener(sbuilder, handler, continue_on_close),
                    name=task_name,
                )
                _task_name = new_task.get_name()
                self._txn_subscriptions[_task_name] = new_task
                _result_data[_task_name] = new_task
                _sui_result = SuiRpcResult(True, None, _result_data)
            else:
                _result_data[task_name] = None
                _sui_result = SuiRpcResult(
                    False, "Not started: In shutdown mode", _result_data
                )
        return _sui_result

    async def wait_shutdown(self) -> list:
        """wait_shutdown Waits until all subscription tasks complete and gathers the results.

        :return: A list of Event type events results received
        :rtype: list
        """
        async with self._ACCESS_LOCK:
            self._in_shutdown = True
            ev_sub_results = await asyncio.gather(
                *self._event_subscriptions.values(), return_exceptions=True
            )
            self._in_shutdown = False
        return ev_sub_results

    async def kill_shutdown(self, wait_seconds: int = None) -> list:
        """kill_shutdown Iterates through any event subscription types, cancelling those still active.

        :param wait_seconds: Delay, if any, to perform second cancelation on tasks, defaults to None
        :type wait_seconds: int, optional
        :return: A list of Event type events results from wait_shutdown
        :rtype: list
        """
        async with self._ACCESS_LOCK:
            self._in_shutdown = True
            _results: dict[str, bool] = {}
            # First pass
            for task_name, task in self._event_subscriptions.items():
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
