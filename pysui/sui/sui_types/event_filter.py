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

"""Sui query and get event filter types."""


from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_types.scalars import SuiInteger


class _EventFilterType:
    """Base class for identifying valid filters."""


class SenderEventQuery(_EventFilterType, SuiMap):
    """Query events for Sender address."""

    def __init__(self, sender: SuiAddress):
        """Initialize query parameter."""
        super().__init__("Sender", sender.value.value)


class TransactionEventQuery(_EventFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, txid: str):
        """Initialize query parameter."""
        super().__init__("Transaction", txid)


class PackageEventQuery(_EventFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, package_id: str):
        """Initialize query parameter."""
        super().__init__("Package", package_id)


class MoveModuleEventQuery(_EventFilterType, SuiMap):
    """Query events for Move Module."""

    def __init__(self, module: str, package: str) -> None:
        """Initialize query parameter."""
        sdict = {"module": module, "package": package}
        super().__init__("MoveModule", sdict)


class MoveEventTypeQuery(_EventFilterType, SuiMap):
    """Query events for Move Event on Struct type."""

    def __init__(self, struct: str):
        """Initialize query parameter."""
        super().__init__("MoveEventType", struct)


class MoveEventField(_EventFilterType, SuiMap):
    """Query events for Move Event fields."""

    def __init__(self, field_path: dict[str, str]):
        """Initialize query parameter.

        field_path argument is dict with {'path':PATH_TO_FILE,'value':true}
        """
        super().__init__("MoveEventField", field_path)


class TimeRangeEventQuery(_EventFilterType, SuiMap):
    """Query events for Time Range."""

    def __init__(self, start_time: SuiInteger, end_time: SuiInteger):
        """Initialize query parameter."""
        sdict = {"startTime": start_time.value, "endTime": end_time.value}
        super().__init__("TimeRange", sdict)


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
