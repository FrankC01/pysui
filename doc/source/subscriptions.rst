
Subscriptions
=============

General
-------
**Sui** supports subscriptions to listen for Sui Events and Sui Transactions via web-sockets.

* The Sui Events type listeners support a plethora of logical filtering capabilities that can further narrow results to exact events types.
* The Sui Transaction type listeners support a number of simple filter options to focus on specific effect context.

SuiClient and subscription Builders
-----------------------------------

In ``pysui`` there are *two* core modules specifically defined for subscriptions:

#. :py:mod:`pysui.sui.sui_clients.subscribe` - This module contains the subscription SuiClient and a data collector class.
#. :py:mod:`pysui.sui.sui_builders.subscription_builders` - This module contains the ``Builders`` for event and transation subscription types.

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
    builder = SubscribeEvent(event_filter=SenderFilter("0x3bcadcc8a78ec44b8765ed8a8517b82a9ee310ad"))

    # Publish events from specific sender
    builder = SubscribeEvent(event_filter=AndFilter(SenderFilter(...), EventTypeFilter("Publish")))

Transaction Filters
~~~~~~~~~~~~~~~~~~~

When using the :py:class:`~pysui.sui.sui_builders.subscription_builders.SubscribeTransaction` bulder, you must provide a ``transaction_filter``.

Filters are those with the suffix ``Filter`` in :ref:`subscription-filters`. For example (some details omitted):


.. code-block:: Python

    # Effects included are those when a SuiAddress is the sender
    builder = SubscribeTransaction(txn_filter=FromAddressEvent("0xf0f14d5806df6071b8147319705bcf6e90b9b40963ab22d72e517ab613f40c80"))


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

Examples of subscription
~~~~~~~~~~~~~~~~~~~~~~~~

Source code in ``samples/`` folder include:
    * **0** - `async_sub`       # Subscribes to move events
    * **1** - `async_sub_txn`   # Subscribes to transaction events
