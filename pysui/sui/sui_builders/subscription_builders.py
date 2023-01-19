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

"""Sui Builders: For subscriptions and filters."""

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
        """__init__ Filter initializer.

        :param sender: This is the SuiAddress to use as the sender in filtering
        :type sender: Union[str, SuiAddress]
        :raises AttributeError: If sender is neither a string or SuiAddress
        """
        if isinstance(sender, str) and valid_sui_address(sender):
            super().__init__("SenderAddress", sender)
        elif isinstance(sender, SuiAddress):
            super().__init__("SenderAddress", sender.value.value)
        else:
            raise AttributeError(f"Invalid argument {sender}. Expect python str or SuiAddress")


class PackageFilter(_EventFilterType, SuiMap):
    """Filter events by Package address."""

    def __init__(self, package: Union[str, ObjectID]):
        """__init__ Filter initializer.

        :param package: This is the package id to use in filtering
        :type package: Union[str, ObjectID]
        :raises AttributeError: If package is neither a string or ObjectID
        """
        if isinstance(package, str):
            super().__init__("Package", package)
        elif isinstance(package, ObjectID):
            super().__init__("Package", package.value)
        else:
            raise AttributeError(f"Invalid argument {package}. Expect python str or ObjectID")


class ModuleFilter(_EventFilterType, SuiMap):
    """Filter events by Module name."""

    def __init__(self, module: Union[str, SuiString]):
        """__init__ Filter initializer.

        :param module: This is the module name to use in filtering
        :type module: Union[str, SuiString]
        :raises AttributeError: If module is neither a string or SuiString
        """
        if isinstance(module, str):
            super().__init__("Module", module)
        elif isinstance(module, SuiString):
            super().__init__("Module", module.value)
        else:
            raise AttributeError(f"Invalid argument {module}. Expect python str or SuiString")


class MoveEventTypeFilter(_EventFilterType, SuiMap):
    """Filter events by move event name."""

    def __init__(self, event_name: Union[str, SuiString]):
        """__init__ Filter initializer.

        :param event_name: This is the evemt name to use in filtering
        :type event_name: Union[str, SuiString]
        :raises AttributeError: If event_name is neither a string or a SuiString
        """
        if isinstance(event_name, str):
            super().__init__("MoveEventType", event_name)
        elif isinstance(event_name, SuiString):
            super().__init__("MoveEventType", event_name.value)
        else:
            raise AttributeError(f"Invalid argument {event_name}. Expect python str or SuiString")


class MoveEventFieldFilter(_EventFilterType, SuiMap):
    """Filter events by Move event field path."""

    def __init__(self, path_name: Union[str, SuiString]):
        """__init__ Filter initializer.

        :param path_name: This is the path name to use in filtering
        :type path_name: Union[str, SuiString]
        :raises AttributeError: If path_name is neither a string or SuiString
        """
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
        """__init__ Filter initializer.

        :param event_name: The event type name to use in filtering
        :type event_name: Union[str, SuiString]
        :raises AttributeError: If event_name neither a string or SuiString
        :raises AttributeError: If event_name not in _event_type_set
        """
        if isinstance(event_name, (str, SuiString)):
            if isinstance(event_name, str) and event_name in self._event_type_set:
                super().__init__("EventType", event_name)
            elif isinstance(event_name, SuiString) and event_name.value in self._event_type_set:
                super().__init__("EventType", event_name.value)
            else:
                raise AttributeError(f"Invalid argument {event_name}. Expect to be one of {self._event_type_set}")
        else:
            raise AttributeError(f"Invalid argument {event_name}. Expects a python str or SuiString")


class ObjectFilter(_EventFilterType, SuiMap):
    """Filter events by object address."""

    def __init__(self, object_id: Union[str, ObjectID]):
        """__init__ Filter initializer.

        :param object_id: The object to use in filtering
        :type object_id: Union[str, ObjectID]
        :raises AttributeError: If object_id is neither a string or ObjectID
        """
        if isinstance(object_id, str):
            super().__init__("ObjectId", object_id)
        elif isinstance(object_id, ObjectID):
            super().__init__("ObjectId", object_id.value)
        else:
            raise AttributeError(f"Invalid argument {object_id}. Expect python str or ObjectID")


class AndFilter(_EventFilterType, SuiMap):
    """AndFilter joins two _EventFilterTypes."""

    def __init__(self, *, lhs_filter: _EventFilterType, rhs_filter: _EventFilterType) -> None:
        """__init__ Filter initializer.

        Where event must be of type lhs_filter AND rhs_filter.

        :param lhs_filter: The primary filter used in conjunction with rhs_filter
        :type lhs_filter: _EventFilterType
        :param rhs_filter: The secondary filter used in conjunction with lhs_filter
        :type rhs_filter: _EventFilterType
        :raises AttributeError: If either lhs_filter or rhs_filter not of type _EventFilterType
        """
        if isinstance(lhs_filter, _EventFilterType) and isinstance(rhs_filter, _EventFilterType):
            super().__init__("And", [lhs_filter.filter, rhs_filter.filter])
        else:
            raise AttributeError("AndFilter constuctor requires arguments to be of type _EventFilterType")


class OrFilter(_EventFilterType, SuiMap):
    """AndFilter joins two _EventFilterTypes."""

    def __init__(self, *, lhs_filter: _EventFilterType, rhs_filter: _EventFilterType) -> None:
        """__init__ Filter initializer.

        Where event may be of type lhs_filter OR rhs_filter.

        :param lhs_filter: The primary filter used in conjunction with rhs_filter
        :type lhs_filter: _EventFilterType
        :param rhs_filter: The secondary filter used in conjunction with lhs_filter
        :type rhs_filter: _EventFilterType
        :raises AttributeError: If either lhs_filter or rhs_filter not of type _EventFilterType
        """
        if isinstance(lhs_filter, _EventFilterType) and isinstance(rhs_filter, _EventFilterType):
            super().__init__("Or", [lhs_filter.filter, rhs_filter.filter])
        else:
            raise AttributeError("OrFilter constuctor requires arguments to be of type _EventFilterType")


class AllFilter(_EventFilterType, SuiMap):
    """AllFilter will alllow all events in filter(s) criteria to be delivered."""

    def __init__(self, *, filters: list[_EventFilterType] = None) -> None:
        """__init__ Filter initializer.

        :param filters: A list of _EventFilterType, defaults to None
        :type filters: list[_EventFilterType], optional
        """
        filters = filters if filters else []
        super().__init__("All", [x.filter for x in filters])


class AnyFilter(_EventFilterType, SuiMap):
    """AnyFilter will alllow any events in filter(s) criteria to be delivered."""

    def __init__(self, *, filters: list[_EventFilterType] = None) -> None:
        """__init__ Filter initializer.

        :param filters: A list of _EventFilterType, defaults to None
        :type filters: list[_EventFilterType], optional
        """
        filters = filters if filters else []
        super().__init__("Any", [x.filter for x in filters])


class SubscribeEvent(_NativeTransactionBuilder):
    """Parameter argument for sui_subscribeEvent."""

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
        super().__init__("sui_subscribeEvent", handler_cls=SubscribedEvent, handler_func="from_dict")
        if event_filter:
            if isinstance(event_filter, _EventFilterType):
                self.filter = event_filter
            else:
                raise AttributeError(f"Invalid argument {event_filter}. Expected subclass of _EventFilterType")
        else:
            self.filter = AllFilter(filters=[])

    def set_event_filter(self, event_filter: SuiMap) -> "SubscribeEvent":
        """Update the event filter."""
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
        # self.filter = AnyFilter(filters=[])
        self.filter = SuiString("Any")

    def _collect_parameters(self) -> list[SuiBaseType]:
        """."""
        return [self.filter]


if __name__ == "__main__":
    subie = SubscribeEvent(
        event_filter=AndFilter(
            lhs_filter=SenderFilter("0xdb17a242dd46de5636615e4499e507f2b3d03366"),
            rhs_filter=AnyFilter(filters=[EventTypeFilter("Publish"), EventTypeFilter("TransferObject")]),
        )
    )
    print(subie.params[0].filter)
