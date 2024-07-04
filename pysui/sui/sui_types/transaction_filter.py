#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui transaction filter types."""


from typing import Final, Optional, Union
from deprecated.sphinx import versionadded, deprecated

from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import SuiMap
from pysui.sui.sui_types.scalars import ObjectID


DEFAULT_GET_TX_OPTIONS: Final[dict] = {
    "showEffects": True,
    "showEvents": True,
    "showBalanceChanges": True,
    "showObjectChanges": True,
    "showRawInput": True,
    "showInput": True,
}


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
def _validate_options(options: dict) -> Union[dict, None]:
    """."""
    if options:
        standard_set = set(DEFAULT_GET_TX_OPTIONS.keys())
        inbound_set = set(options.keys())
        diff_set = inbound_set - standard_set
        if diff_set:
            raise ValueError(f"Options are not valid for QueryTransaction {diff_set}")
    return options


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class _TransactionFilterType:
    """Base class for identifying valid filters."""


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class CheckpointQuery(_TransactionFilterType, SuiMap):
    """Query by checkpoint."""

    def __init__(self, check_point: int, options: Optional[dict] = None):
        """Initialize query parameter."""
        super().__init__("filter", {"Checkpoint": check_point})
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class MoveFunctionQuery(_TransactionFilterType, SuiMap):
    """Query by move function."""

    def __init__(
        self,
        package: str,
        module: str = None,
        function: str = None,
        options: Optional[dict] = None,
    ):
        """Initialize query parameter."""
        super().__init__(
            "filter",
            {
                "MoveFunction": {
                    "module": module,
                    "package": package,
                    "function": function,
                }
            },
        )
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class InputObjectQuery(_TransactionFilterType, SuiMap):
    """Query by input object."""

    def __init__(self, object_id: Union[str, ObjectID], options: Optional[dict] = None):
        """Initialize query parameter."""
        object_id = object_id if isinstance(object_id, str) else object_id.value
        super().__init__("filter", {"InputObject": object_id})
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class ChangedObjectQuery(_TransactionFilterType, SuiMap):
    """Query by changed object, including created, mutated and unwrapped objects."""

    def __init__(
        self, object_id: Union[str, ObjectID], options: Optional[dict] = None
    ) -> None:
        """Initialize query parameter."""
        object_id = object_id if isinstance(object_id, str) else object_id.value
        super().__init__("filter", {"ChangedObject": object_id})
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class FromAddressQuery(_TransactionFilterType, SuiMap):
    """Query by sender address."""

    def __init__(self, address: Union[str, SuiAddress], options: Optional[dict] = None):
        """Initialize query parameter."""
        address = address if isinstance(address, str) else address.address
        super().__init__("filter", {"FromAddress": address})
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class ToAddressQuery(_TransactionFilterType, SuiMap):
    """Query by recipient address."""

    def __init__(self, address: Union[str, SuiAddress], options: Optional[dict] = None):
        """Initialize query parameter."""
        address = address if isinstance(address, str) else address.address
        super().__init__("filter", {"ToAddress": address})
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class FromAndToAddressQuery(_TransactionFilterType, SuiMap):
    """Query by sender and recipient address."""

    def __init__(
        self,
        from_address: Union[str, SuiAddress],
        to_address: Union[str, SuiAddress],
        options: Optional[dict] = None,
    ):
        """Initialize query parameter."""
        from_address = (
            from_address if isinstance(from_address, str) else from_address.address
        )
        to_address = to_address if isinstance(to_address, str) else to_address.address
        super().__init__(
            "filter",
            {"FromAndToAddress": {"from": from_address, "to": to_address}},
        )
        self.map["options"] = _validate_options(options)


@versionadded(version="0.31.0", reason="New filter supported in Sui RPC API 1.5.0")
@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class FromOrToAddressQuery(_TransactionFilterType, SuiMap):
    """Query by sender or recipient address, requires indexer."""

    def __init__(self, address: Union[str, SuiAddress], options: Optional[dict] = None):
        """Initialize query parameter."""
        address = address if isinstance(address, str) else address.address
        super().__init__("filter", {"FromOrToAddress": {"addr": address}})
        self.map["options"] = _validate_options(options)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class TransactionKindQuery(_TransactionFilterType, SuiMap):
    """Query by transaction kind."""

    def __init__(self, tx_kind: str, options: Optional[dict] = None):
        """Initialize query parameter."""
        super().__init__("filter", {"TransactionKind": tx_kind})
        self.map["options"] = _validate_options(options)


@versionadded(version="0.31.0", reason="New filter supported in Sui RPC API 1.6.0")
@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class TransactionKindInQuery(_TransactionFilterType, SuiMap):
    """Query by transactions of any given kind in the input, requires indexer."""

    def __init__(self, tx_kinds: list, options: Optional[dict] = None):
        """Initialize query parameter."""
        super().__init__("filter", {"TransactionKindIn": tx_kinds})
        self.map["options"] = _validate_options(options)
