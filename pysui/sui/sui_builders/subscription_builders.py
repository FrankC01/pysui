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

"""Sui Builders: For subscriptions and filters."""

from deprecated.sphinx import versionadded, deprecated
from pysui.abstracts.client_types import SuiBaseType
from pysui.sui.sui_types.event_filter import (
    _EventFilterType,
    _TransactionFilterType,
    AllFilter,
)
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_builders.base_builder import _NativeTransactionBuilder
from pysui.sui.sui_txresults.complex_tx import SubscribedEvent, SubscribedTransaction


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class SubscribeEvent(_NativeTransactionBuilder):
    """Parameter argument for suix_subscribeEvent."""

    def __init__(
        self,
        *,
        event_filter: _EventFilterType = None,
    ) -> None:
        """__init__ Initializer.

        This is the primary filter builder for event subscriptions. If event_filters argument
        is None it will default to :py:class:`.AllFilter`

        :param event_filter: The filter of type _EventFilterType, defaults to None
        :type event_filter: _EventFilterType, optional
        :raises AttributeError: If event_filters is not of type _EventFilterType
        """
        super().__init__(
            "suix_subscribeEvent", handler_cls=SubscribedEvent, handler_func="from_dict"
        )
        if event_filter:
            if isinstance(event_filter, _EventFilterType):
                self.filter = event_filter
            else:
                raise AttributeError(
                    f"Invalid argument {event_filter}. Expected subclass of _EventFilterType"
                )
        else:
            self.filter = AllFilter(filters=[])

    def set_event_filter(self, event_filter: SuiMap) -> "SubscribeEvent":
        """Update the event filter."""
        self.filter = event_filter
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Fetch parameters."""
        return [self.filter]


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class SubscribeTransaction(_NativeTransactionBuilder):
    """Parameter argument for suix_subscribeTransaction."""

    def __init__(
        self,
        *,
        txn_filter: _TransactionFilterType,
    ) -> None:
        """."""
        super().__init__(
            "suix_subscribeTransaction",
            handler_cls=SubscribedTransaction,
            handler_func="from_dict",
        )
        if txn_filter:
            if isinstance(txn_filter, _TransactionFilterType):
                self.filter = txn_filter
            else:
                raise AttributeError(
                    f"Invalid argument {txn_filter}. Expected subclass of _TransactionFilterType"
                )
        else:
            raise AttributeError("Expected 'txn_filter' not found")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Fetch parameters."""
        return [self.filter]


if __name__ == "__main__":
    pass
    # subie = SubscribeEvent(
    #     event_filter=AndFilter(
    #         lhs_filter=SenderFilter("0xdb17a242dd46de5636615e4499e507f2b3d03366"),
    #         rhs_filter=AnyFilter(filters=[EventTypeFilter("Publish"), EventTypeFilter("TransferObject")]),
    #     )
    # )
    # print(subie.params[0].filter)
