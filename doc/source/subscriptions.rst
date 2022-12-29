
Subscriptions
=============

General
-------
``Sui`` supports subscriptions to listen for Sui and Transaction events vis-a-vis web-sockets.

* The Sui events type listeners support a plethora of logical filtering capabilities that can further narrow results to exect events types.
* Interestingly enough, filtering transactions are supported at this time. You will receive all transactions from the fullnode if you subscribe to it.

SuiClient and subscription Builders
-----------------------------------

In ``pysui`` there are *two* modules specifically defined for subscriptions:

#. :py:mod:`pysui.sui.sui_clients.subscribe` - This module contains the subscription SuiClient and a data collector class.
#. :py:mod:`pysui.sui.sui_builders.subscription_builders` - This module contains the ``Builders`` for both subscription types noted above.

Brief example of Transaction subscription
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: Python
   :linenos:

    import asyncio
    from pysui.sui.sui_clients.subscribe import SuiClient as async_subscriber
    from pysui.sui.sui_txresults.complex_tx import SubscribedTransaction
    from pysui.sui.sui_builders.subscription_builders import SubscribeTransaction

    def tx_handler(indata: SubscribedTransaction, subscription_id: int, event_counter: int) -> Any:
        """Handler captures entire transaction event for each received."""
        print(f"Received event {event_counter} for subscription {subscription_id}")
        return indata

    # Asynchronous subscriber
    # use default clienti yaml at ~/.sui/sui_config/client.yaml

    client = async_subscriber(SuiConfig.default())

    # Use the explicit Transaction subscription service passing the
    # handler function and an optional name. A subscription proxy will be created
    # that manages listening on the websocket and delivering a value payload
    # to the handler function

    subscription_result = await client.new_txn_subscription(SubscribeTransaction(), tx_handler, "tx_handler")

    # If successful subscription wait for 1 minutes then force it to shut down
    # We force kill it as the tx_handler will run endlessley. If a handler
    # returns False it will shut down the subscription proxy associated with it.

    if subscription_result.is_ok():
        await asyncio.sleep(60.00)

        # Returns a tuple of results from any transaction
        # subscriptions and Sui event subscriptions that
        # were initiated.

        tx_subs_result, ev_subs_result = await client.kill_shutdown()

        if tx_subs_result:
            print("Transaction event listener results")
            for event in tx_subs_result:
                match event.result_string:

                    # Cancelled events maintain the data collected to the
                    # point of cancellation

                    case "Cancelled" | None:
                        for tx_event in event.result_data.collected
                            print(tx_event.to_json(indent=2))

                    case "General Exception":
                        print(f"Exception {event}")

                    case _:
                        print("ERROR")
    else:
        print(f"Error: {subscription_result.result_string}")
