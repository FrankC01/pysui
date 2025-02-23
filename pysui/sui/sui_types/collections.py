#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Collection Types."""

from abc import abstractmethod
from typing import Any, Generic, TypeVar, Union
from deprecated.sphinx import versionchanged, deprecated
from pysui.abstracts import SuiBaseType
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiString
from pysui.sui.sui_types.address import SuiAddress


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiCollection(SuiBaseType):
    """Generic Collection Type."""


AT = TypeVar("AT", SuiAddress, ObjectID, SuiInteger, SuiString)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiArray(SuiCollection, Generic[AT]):
    """Array type."""

    def __init__(self, array: list[AT]) -> None:
        """Initialize collection."""
        super().__init__(None)
        self.array = array if array else list[AT]()

    def append(self, item: AT) -> list[AT]:
        """Append and item to array."""
        self.array.append(item)
        return self.array

    def extend(self, items: list[AT]) -> list[AT]:
        """Append and item to array."""
        self.array.extend(items)
        return self.array

    @property
    def input_coins(self) -> list[ObjectID]:
        """Alias for transactions."""
        return self.array

    @property
    def coins(self) -> list[ObjectID]:
        """Alias for transactions."""
        return self.array

    @property
    def recipients(self) -> list[SuiAddress]:
        """Alias for transactions."""
        return self.array

    @property
    def amounts(self) -> list[Union[SuiInteger, SuiString]]:
        """Alias for transactions."""
        return self.array

    @property
    def amount(self) -> list[SuiInteger]:
        """Alias for transactions."""
        return self.array

    @property
    def split_amounts(self) -> list[SuiInteger]:
        """Alias for transactions."""
        return self.array

    @property
    def type_arguments(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array

    @property
    def arguments(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array

    @property
    def compiled_modules(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array

    @property
    def dependencies(self) -> list[SuiString]:
        """Alias for transactions."""
        return self.array

    @property
    def single_transaction_params(self) -> list[dict]:
        """Alias for transactions."""
        return self.array

    @property
    def digests(self) -> list[dict]:
        """Alias for transactions."""
        return self.array

    @property
    def signatures(self) -> list[dict]:
        """Alias for transactions."""
        return self.array

    @property
    def object_ids(self) -> list[dict]:
        """Alias for transactions."""
        return self.array

    @property
    def staked_sui_ids(self) -> list[dict]:
        """Alias for transactions."""
        return self.array

    @property
    def past_objects(self) -> list[dict]:
        """Alias for transactions."""
        return self.array


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiMap(SuiCollection):
    """Dictionary Type."""

    def __init__(self, key: str, value: Any) -> None:
        """Initialize collection."""
        super().__init__(None)
        self.map = {key: value}

    def add_kv_pair(self, key: str, value: Any) -> "SuiMap":
        """Add key value pair to map."""
        self.map[key] = value
        return self

    @property
    def cursor(self) -> dict:
        """Alias for query."""
        return self.map

    @property
    def recipient(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map

    @property
    def query(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map

    @property
    def filter(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map

    @property
    def name(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map

    @property
    def options(self) -> dict[str, Any]:
        """Alias for transactions."""
        return self.map

    @property
    def additional_args(self) -> dict[str, Any]:
        """Alias for transaction inspect."""
        return self.map


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class BatchParameter(SuiMap):
    """BatchParameter is abstraction for TransferObjectParams and MoveCallRequestParams."""

    @abstractmethod
    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""


@versionchanged(
    version="0.30.0", reason="event_seq and tx_seq changed from int to string"
)
@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class EventID(SuiMap):
    """Event ID specifier."""

    def __init__(self, event_seq: str, tx_seq: str):
        """Initialize EventID."""
        super().__init__("eventSeq", event_seq)
        self.map["txDigest"] = tx_seq
