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

"""Sui builders for subscription filtering."""

from typing import Union
from pysui.abstracts.client_types import SuiBaseType
from pysui.sui.sui_types.scalars import ObjectID, SuiString
from pysui.sui.sui_types.address import SuiAddress, valid_sui_address
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_builders.base_builder import _NativeTransactionBuilder
from pysui.sui.sui_txresults.complex_tx import SubscribedEvent, SubscribedTransaction


class _EventFilterType:
    """Base class for identifying valid filters."""


class SenderFilter(_EventFilterType, SuiMap):
    """Filter events by Sender address."""

    def __init__(self, sender: Union[str, SuiAddress]):
        """Initialize filter parameter."""
        if isinstance(sender, str) and valid_sui_address(sender):
            super().__init__("SenderAddress", sender)
        elif isinstance(sender, SuiAddress):
            super().__init__("SenderAddress", sender.value.value)
        else:
            raise AttributeError(f"Invalid argument {sender}. Expect python str or SuiAddress")


class PackageFilter(_EventFilterType, SuiMap):
    """Filter events by Package address."""

    def __init__(self, package: Union[str, ObjectID]):
        """Initialize filter parameter."""
        if isinstance(package, str):
            super().__init__("Package", package)
        elif isinstance(package, ObjectID):
            super().__init__("Package", package.value)
        else:
            raise AttributeError(f"Invalid argument {package}. Expect python str or ObjectID")


class ModuleFilter(_EventFilterType, SuiMap):
    """Filter events by Module name."""

    def __init__(self, module: Union[str, SuiString]):
        """Initialize filter parameter."""
        if isinstance(module, str):
            super().__init__("Module", module)
        elif isinstance(module, SuiString):
            super().__init__("Module", module.value)
        else:
            raise AttributeError(f"Invalid argument {module}. Expect python str or SuiString")


class MoveEventTypeFilter(_EventFilterType, SuiMap):
    """Filter events by move event name."""

    def __init__(self, event_name: Union[str, SuiString]):
        """Initialize filter parameter."""
        if isinstance(event_name, str):
            super().__init__("MoveEventType", event_name)
        elif isinstance(event_name, SuiString):
            super().__init__("MoveEventType", event_name.value)
        else:
            raise AttributeError(f"Invalid argument {event_name}. Expect python str or SuiString")


class MoveEventFieldFilter(_EventFilterType, SuiMap):
    """Filter events by Move event field path."""

    def __init__(self, path_name: Union[str, SuiString]):
        """Initialize filter parameter."""
        if isinstance(path_name, str):
            super().__init__("MoveEventField", path_name)
        elif isinstance(path_name, SuiString):
            super().__init__("MoveEventField", path_name.value)
        else:
            raise AttributeError(f"Invalid argument {path_name}. Expect python str or SuiString")


class EventTypeFilter(_EventFilterType, SuiMap):
    """Filter events by event name."""

    _event_type_set: set = {
        "MoveEvent",
        "Publish",
        "CoinBalanceChange",
        "EpochChange",
        "Checkpoint",
        "TransferObject",
        "MutateObject",
        "DeleteObject",
        "NewObject",
    }

    def __init__(self, event_name: Union[str, SuiString]):
        """Initialize filter parameter."""
        if isinstance(event_name, str) and event_name in self._event_type_set:
            super().__init__("EventType", event_name)
        elif isinstance(event_name, SuiString) and event_name.value in self._event_type_set:
            super().__init__("EventType", event_name.value)
        else:
            raise AttributeError(f"Invalid argument {event_name}. Expect python str or SuiString")


class ObjectFilter(_EventFilterType, SuiMap):
    """Filter events by object address."""

    def __init__(self, object_id: Union[str, SuiString]):
        """Initialize filter parameter."""
        if isinstance(object_id, str):
            super().__init__("ObjectId", object_id)
        elif isinstance(object_id, ObjectID):
            super().__init__("ObjectId", object_id.value)
        else:
            raise AttributeError(f"Invalid argument {object_id}. Expect python str or ObjectID")


class SubscribeEvent(_NativeTransactionBuilder):
    """Parameter argument for sui_subscribeEvent."""

    def __init__(
        self,
        *,
        event_filter: _EventFilterType = None,
    ) -> None:
        """."""
        super().__init__("sui_subscribeEvent", handler_cls=SubscribedEvent, handler_func="from_dict")
        if event_filter:
            if isinstance(event_filter, _EventFilterType):

                self.filter = event_filter
            else:
                raise AttributeError(f"Invalid argument {event_filter}. Expected subclass of _EventFilterType")
        else:
            self.filter = SuiMap("All", [])

    def set_event_filter(self, event_filter: SuiMap) -> "SubscribeEvent":
        """."""
        self.filter = event_filter
        return self

    def _collect_parameters(self) -> list[SuiBaseType]:
        """."""
        return [self.filter]


class SubscribeTransaction(_NativeTransactionBuilder):
    """Parameter argument for sui_subscribeTransaction."""

    def __init__(
        self,
    ) -> None:
        """."""
        super().__init__("sui_subscribeTransaction", handler_cls=SubscribedTransaction, handler_func="from_dict")
        self.filter = SuiString("Any")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """."""
        return [self.filter]
