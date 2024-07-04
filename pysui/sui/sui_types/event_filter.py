#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui query and get event filter types."""

from typing import Optional, Union
from deprecated.sphinx import versionadded, deprecated
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiString


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class _EventFilterType:
    """Base class for identifying valid filters."""


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class SenderEventQuery(_EventFilterType, SuiMap):
    """Query events for Sender address."""

    def __init__(self, sender: SuiAddress):
        """Initialize query parameter."""
        super().__init__("Sender", sender.value.value)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class TransactionEventQuery(_EventFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, txid: str):
        """Initialize query parameter."""
        super().__init__("Transaction", txid)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class PackageEventQuery(_EventFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, package_id: str):
        """Initialize query parameter."""
        super().__init__("Package", package_id)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class MoveEventModuleQuery(_EventFilterType, SuiMap):
    """Query events with the given move event module name."""

    def __init__(self, module: str, package_id: str):
        """Initialize query parameter."""
        sdict = {"module": module, "package": package_id}
        super().__init__("MoveEventModule", sdict)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class MoveModuleEventQuery(_EventFilterType, SuiMap):
    """Query events emitted in a specified Move module."""

    def __init__(self, module: str, package: str) -> None:
        """Initialize query parameter."""
        sdict = {"module": module, "package": package}
        super().__init__("MoveModule", sdict)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class MoveEventTypeQuery(_EventFilterType, SuiMap):
    """Query events for Move Event on Struct type."""

    def __init__(self, struct: str):
        """Initialize query parameter."""
        super().__init__("MoveEventType", struct)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class MoveEventFieldQuery(_EventFilterType, SuiMap):
    """Query events for Move Event fields."""

    def __init__(self, field_path: dict[str, str]):
        """Initialize query parameter.

        field_path argument is dict with {'path':PATH_TO_FILE,'value':true}
        """
        super().__init__("MoveEventField", field_path)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class TimeRangeEventQuery(_EventFilterType, SuiMap):
    """Query events for Time Range."""

    def __init__(self, start_time: SuiInteger, end_time: SuiInteger):
        """Initialize query parameter."""
        sdict = {"startTime": start_time.value, "endTime": end_time.value}
        super().__init__("TimeRange", sdict)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class AndFilter(_EventFilterType, SuiMap):
    """AndFilter joins two _EventFilterTypes."""

    def __init__(
        self, *, lhs_filter: _EventFilterType, rhs_filter: _EventFilterType
    ) -> None:
        """__init__ Filter initializer.

        Where event must be of type lhs_filter AND rhs_filter.

        :param lhs_filter: The primary filter used in conjunction with rhs_filter
        :type lhs_filter: _EventFilterType
        :param rhs_filter: The secondary filter used in conjunction with lhs_filter
        :type rhs_filter: _EventFilterType
        :raises AttributeError: If either lhs_filter or rhs_filter not of type _EventFilterType
        """
        if isinstance(lhs_filter, _EventFilterType) and isinstance(
            rhs_filter, _EventFilterType
        ):
            super().__init__("And", [lhs_filter.filter, rhs_filter.filter])
        else:
            raise AttributeError(
                "AndFilter constuctor requires arguments to be of type _EventFilterType"
            )


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class OrFilter(_EventFilterType, SuiMap):
    """AndFilter joins two _EventFilterTypes."""

    def __init__(
        self, *, lhs_filter: _EventFilterType, rhs_filter: _EventFilterType
    ) -> None:
        """__init__ Filter initializer.

        Where event may be of type lhs_filter OR rhs_filter.

        :param lhs_filter: The primary filter used in conjunction with rhs_filter
        :type lhs_filter: _EventFilterType
        :param rhs_filter: The secondary filter used in conjunction with lhs_filter
        :type rhs_filter: _EventFilterType
        :raises AttributeError: If either lhs_filter or rhs_filter not of type _EventFilterType
        """
        if isinstance(lhs_filter, _EventFilterType) and isinstance(
            rhs_filter, _EventFilterType
        ):
            super().__init__("Or", [lhs_filter.filter, rhs_filter.filter])
        else:
            raise AttributeError(
                "OrFilter constuctor requires arguments to be of type _EventFilterType"
            )


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class AllFilter(_EventFilterType, SuiMap):
    """AllFilter will alllow all events in filter(s) criteria to be delivered."""

    def __init__(self, *, filters: list[_EventFilterType] = None) -> None:
        """__init__ Filter initializer.

        :param filters: A list of _EventFilterType, defaults to None
        :type filters: list[_EventFilterType], optional
        """
        filters = filters if filters else []
        super().__init__("All", [x.filter for x in filters])


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class AnyFilter(_EventFilterType, SuiMap):
    """AnyFilter will alllow any events in filter(s) criteria to be delivered."""

    def __init__(self, *, filters: list[_EventFilterType] = None) -> None:
        """__init__ Filter initializer.

        :param filters: A list of _EventFilterType, defaults to None
        :type filters: list[_EventFilterType], optional
        """
        filters = filters if filters else []
        super().__init__("Any", [x.filter for x in filters])


@versionadded(version="0.20.0", reason="Added from Sui RPC API 1.0.0")
@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class _TransactionFilterType:
    """Base class for identifying valid transaction filters."""


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class CheckpointEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, checkpoint_id: str):
        """Initialize query parameter."""
        super().__init__("Checkpoint", checkpoint_id)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class MoveFunctionEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(
        self,
        package_id: Union[str, ObjectID],
        module_name: Optional[Union[str, SuiString]] = None,
        function_name: Optional[Union[str, SuiString]] = None,
    ):
        """Initialize query parameter."""
        package_id = package_id if isinstance(package_id, str) else package_id.value
        module_name = module_name if isinstance(module_name, str) else module_name.value
        function_name = (
            function_name if isinstance(function_name, str) else function_name
        )
        sdict = {
            "package": package_id,
            "module": module_name,
            "function": function_name,
        }
        super().__init__("MoveFunction", sdict)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class InputObjectEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, object_id: Union[str, ObjectID]):
        """Initialize query parameter."""
        object_id = object_id if isinstance(object_id, str) else object_id.vaule
        super().__init__("InputObject", object_id)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class ChangedObjectEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, object_id: Union[str, ObjectID]):
        """Initialize query parameter."""
        object_id = object_id if isinstance(object_id, str) else object_id.vaule
        super().__init__("ChangedObject", object_id)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class FromAddressEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, address_id: Union[str, SuiAddress]):
        """Initialize query parameter."""
        address_id = address_id if isinstance(address_id, str) else address_id.address
        super().__init__("FromAddress", address_id)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class ToAddressEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, address_id: Union[str, SuiAddress]):
        """Initialize query parameter."""
        address_id = address_id if isinstance(address_id, str) else address_id.address
        super().__init__("ToAddress", address_id)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class FromAndToAddressEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(
        self,
        from_address_id: Union[str, SuiAddress],
        to_address_id: Union[str, SuiAddress],
    ):
        """Initialize query parameter."""
        from_address_id = (
            from_address_id
            if isinstance(from_address_id, str)
            else from_address_id.address
        )
        to_address_id = (
            to_address_id if isinstance(to_address_id, str) else to_address_id.address
        )
        sdict = {"from": from_address_id, "to": to_address_id}
        super().__init__("FromAndToAddress", sdict)


@deprecated(version="0.65.0", reason="Sui dropping JSON RPC subscriptions.")
class TransactionKindEvent(_TransactionFilterType, SuiMap):
    """Query events for Transaction."""

    def __init__(self, transaction_kind: Union[str, SuiString]):
        """Initialize query parameter."""
        transaction_kind = (
            transaction_kind
            if isinstance(transaction_kind, str)
            else transaction_kind.value
        )
        super().__init__("TransactionKindEvent", transaction_kind)
