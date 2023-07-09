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

"""Testing transaction subscriptions."""

import os
import sys
import pathlib
import asyncio
from typing import Any


PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui import SuiConfig
from pysui.sui.sui_clients.subscribe import SuiClient as subscriber
from pysui.sui.sui_txresults.complex_tx import (
    SubscribedTransaction,
    SubscribedEventParms,
    Effects,
)
from pysui.sui.sui_types.event_filter import FromAddressEvent

from pysui.sui.sui_builders.subscription_builders import (
    SubscribeTransaction,
)


def test_txn_handler(
    indata: SubscribedTransaction, subscription_id: int, event_counter: int
) -> Any:
    """Handler captures the move event type for each received."""
    event_parms: SubscribedEventParms = indata.params
    result_class: Effects = event_parms.result
    print(result_class)
    return {"func": result_class.transaction_digest}


async def main_run(sub_manager: subscriber):
    """Main async loop to run subscriptions."""
    print()
    # With Sui 0.28.0, the only events sent to listeners are those that are 'emitted' by
    # a module during some operations. The filters apply primarily to that context
    # This will get all transaction events
    subscribe_event_for = SubscribeTransaction(
        txn_filter=FromAddressEvent(sub_manager.config.active_address)
    )
    # Start listening
    print("Start event type listener")
    thing = await sub_manager.new_event_subscription(
        subscribe_event_for, test_txn_handler, "test_txn_handler"
    )
    if thing.is_ok():
        print("Sleeping for 60 seconds")
        await asyncio.sleep(60.00)
        print("Killing listeners")
        ev_subs_result = await sub_manager.kill_shutdown()
        if ev_subs_result:
            print("Event listener results")
            for event in ev_subs_result:
                match event.result_string:
                    case "Cancelled" | None:
                        res_finish = event.result_string or "Normal Exit"
                        print(
                            f"    {event.result_data.name} task state: {res_finish}"
                        )
                        print(
                            f"    Processed events: {len(event.result_data.collected)}"
                        )
                    case "General Exception":
                        print(f"Exception {event}")
                    case _:
                        print("ERROR")
                        print(event.result_data)

    else:
        print(thing.result_string)


def main():
    """Setup asynch loop and run."""
    arg_line = sys.argv[1:].copy()
    # Handle a different client.yaml than default
    if arg_line and arg_line[0] == "--local":
        cfg = SuiConfig.sui_base_config()
    else:
        cfg = SuiConfig.default_config()
    asyncio.run(main_run(subscriber(cfg)))
    print("Done")


if __name__ == "__main__":
    main()
