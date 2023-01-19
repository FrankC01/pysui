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

"""Sui Collection Types."""

from abc import abstractmethod
from typing import Any, Generic, TypeVar
from pysui.abstracts import SuiBaseType
from pysui.sui.sui_types.scalars import ObjectID, SuiInteger, SuiString
from pysui.sui.sui_types.address import SuiAddress


class SuiCollection(SuiBaseType):
    """Generic Collection Type."""


AT = TypeVar("AT", SuiAddress, ObjectID, SuiInteger, SuiString)


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
    def recipients(self) -> list[SuiAddress]:
        """Alias for transactions."""
        return self.array

    @property
    def amounts(self) -> list[SuiInteger]:
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
    def single_transaction_params(self) -> list[dict]:
        """Alias for transactions."""
        return self.array


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


class BatchParameter(SuiMap):
    """BatchParameter is abstraction for TransferObjectParams and MoveCallRequestParams."""

    @abstractmethod
    def realize_parameters(self) -> dict:
        """Satisfied by subclasses."""


class EventID(SuiMap):
    """Event ID specifier."""

    def __init__(self, event_seq: int, tx_seq: int):
        """Initialize EventID."""
        super().__init__("eventSeq", event_seq)
        self.map["txSeq"] = tx_seq
