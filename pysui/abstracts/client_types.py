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


"""Type Client Abstractions."""
from abc import ABC

from types import NoneType
from typing import Any


class AbstractType(ABC):
    """Base most abstraction."""

    def __init__(self, identifier: "AbstractType") -> None:
        """Initialize type."""
        self.value = identifier

    @property
    def identifier(self) -> Any:
        """Return underlying value."""
        return self.value

    # @property
    # def value(self) -> Any:
    #     """Return underlying value."""
    #     return self.value

    def __eq__(self, other: "AbstractType") -> bool:
        """Equality check."""
        return str(self) == str(other)

    def __hash__(self) -> int:
        """Hashability."""
        return hash(str(self))

    def __str__(self) -> str:
        """Convert value to string using formatting."""
        if isinstance(self.value, str):
            return self.value
        if isinstance(self.value, bytes):
            return self.value.decode()
        if isinstance(self.value, int):
            return self.value
        if isinstance(self.value, AbstractType):
            return str(self.value.value)
        if isinstance(self.value, NoneType):
            return ""
        raise NotImplementedError


class SuiBaseType(AbstractType):
    """Base most SUI object type."""

    def __init__(self, identifier: Any) -> None:
        """__init__ Initialize type with identifier.

        :param identifier: A native python type
        :type identifier: Any
        """
        super().__init__(identifier)


class SuiScalarType(SuiBaseType):
    """Base most SUI scalar type."""
