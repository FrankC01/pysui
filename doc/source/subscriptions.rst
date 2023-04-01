
Subscriptions
=============

General
-------
**Sui** supports subscriptions to listen for Sui Events via web-sockets.

* The Sui Events type listeners support a plethora of logical filtering capabilities that can further narrow results to exect events types.
* Interestingly enough, MystenLabs dropped support for subscribing to transactions.

SuiClient and subscription Builders
-----------------------------------

In ``pysui`` there are *two* core modules specifically defined for subscriptions:

#. :py:mod:`pysui.sui.sui_clients.subscribe` - This module contains the subscription SuiClient and a data collector class.
#. :py:mod:`pysui.sui.sui_builders.subscription_builders` - This module contains the ``Builders`` for event subscription types.

Event Filters
~~~~~~~~~~~~~

When using the :py:class:`~pysui.sui.sui_builders.subscription_builders.SubscribeEvent` bulder, you can provide an optional ``event_filter``.
If you do not provide a filter, **all** Event types will be received.

| Filters supports a logical **connective**: ``if antecedent then consequent``,
| which translates to ``if filter_criteria_met then send_event``.

Filters are those with the suffix ``Filter`` in :ref:`subscription-filters`. the special filters ``(And,Or,Any,All)`` can be used to
nest filters. For example (some details omitted):

.. code-block:: Python

    # Get all events ... default
    builder = SubscribeEvent()

    # Events from sender address
    builder = SubscribeEvent(
                    SenderFilter("0x3bcadcc8a78ec44b8765ed8a8517b82a9ee310ad"))

    # Publish events from specific sender
    builder = SubscribeEvent(
                    AndFilter(SenderFilter(...), EventTypeFilter("Publish"))
    )

Subscription Handlers
~~~~~~~~~~~~~~~~~~~~~

Handlers are python functions that are invoked whenever an event is received in the managing ``subscription proxy``. The
proxy is an internal method of the subscription client that is spawned with each subscription request.

A handler is function that takes **3 arguments** and returns something. It is typed
defined as: :code:`Callable[[Union[SubscribedEvent, SubscribedTransaction], int, int], Any]`

Where argument position:
    * **0** - The inbound data deserialized to a dataclass relavent to the subscription type.
    * **1** - The subscription identifier (int).
    * **2** - The event counter (int).

The handler can return anything, however; if `False` is returned, the subscription proxy will exit.
Anything else will be stored in a data collector and returned to the subscription caller.

Example of Event subscription
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: Python
   :linenos:

    import asyncio
    from pysui.sui.sui_clients.subscribe import SuiClient as async_subscriber
    from pysui.sui.sui_txresults.complex_tx import SubscribedEvent, EventEnvelope
    from pysui.sui.sui_builders.subscription_builders import *

    def event_handler(
        indata: SubscribedEvent,
        subscription_id: int,
        event_counter: int
    ) -> EventEnvelope:
        """Handler captures the move event type for each received."""
        event_parms: SubscribedEventParms = indata.params
        return EventEnvelope = event_parms.result

    # Asynchronous subscriber
    # use default clienti yaml at ~/.sui/sui_config/client.yaml

    client = async_subscriber(SuiConfig.default())

    # Use the explicit Event subscription service passing the
    # handler function and an optional name. A subscription proxy will be created
    # that manages listening on the websocket and delivering a value payload
    # to the handler function

    # Publish events from specific sender
    builder = SubscribeEvent(
                    AndFilter(
                        SenderFilter("0x3bcadcc8a78ec44b8765ed8a8517b82a9ee310ad"),
                        EventTypeFilter("Publish"))
    )

    subscription_result = await client.new_event_subscription(
        builder,
        event_handler, "event_handler")

    if subscription_result.is_ok():
        await asyncio.sleep(60.00)

        # Returns a tuple of results from any transaction
        # subscriptions and Sui event subscriptions that
        # were initiated.

        tx_subs_result, ev_subs_result = await client.kill_shutdown()

        if ev_subs_result:
            print("Transaction event listener results")
            for event in ev_subs_result:
                match event.result_string:

                    # Cancelled events maintain the data collected to the
                    # point of cancellation

                    case "Cancelled" | None:
                        for ev_event in event.result_data.collected
                            print(ev_event.to_json(indent=2))

                    case "General Exception":
                        print(f"Exception {event}")

                    case _:
                        print("ERROR")
    else:
        print(f"Error: {subscription_result.result_string}")
