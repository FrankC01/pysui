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

"""Sui Scalar Types."""

from pysui.abstracts import SuiScalarType


class SuiNullType(SuiScalarType):
    """SuiNullType A null type.

    :param SuiBaseType: Super class
    :type SuiBaseType: _type_
    :return: _description_
    :rtype: SuiNullType
    """

    def __init__(self) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A native python type
        :type identifier: Any
        """
        super().__init__(None)

    @property
    def limit(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def version(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def cursor(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def coin_type(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def epoch(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def digest(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def descending_order(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def gas_price(self) -> None:
        """Alias for transactions."""
        return self.value


class SuiString(SuiScalarType):
    """Sui String type."""

    def __init__(self, identifier: str) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A python str
        :type identifier: str
        """
        super().__init__(identifier)

    @property
    def function(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def function_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def module(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def module_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def struct_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def arguments(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def type_arguments(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def compiled_modules(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def cursor(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def move_event_struct_name(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def digest(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def query(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def recipient(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def coin_type(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def limit(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def commitment_type(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def tx_bytes(self) -> str:
        """Alias for transactions."""
        return self.value


class SuiTxBytes(SuiString):
    """Sui Base64 tx_bytes string."""

    @property
    def tx_bytes(self) -> str:
        """Satisfy transaction verification."""
        return str(self)


class SuiSignature(SuiString):
    """Sui Base64 signature."""

    @property
    def signature(self) -> str:
        """Satisfy transaction verification."""
        return str(self)


class SuiTransactionDigest(SuiString):
    """Sui Base58 digest."""

    @property
    def digest(self) -> str:
        """Alias for transaction."""
        return str(self)


class ObjectID(SuiString):
    """Sui Object id type."""

    # def __init__(self, value: str) -> None:
    #     """Initialize with identifier."""
    #     super().__init__(value)

    @property
    def object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def object(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def package(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def package_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def parent_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def sui_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def coin_object_id(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def staked_sui(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def gas(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def input_coins(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def coins(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def delegation(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def primary_coin(self) -> str:
        """Alias over value."""
        return self.value

    @property
    def coin_to_merge(self) -> str:
        """Alias over value."""
        return self.value


class SuiBoolean(SuiScalarType):
    """Sui Bool type."""

    @property
    def descending_order(self) -> bool:
        """Alias for transactions."""
        return self.value


class SuiInteger(SuiScalarType):
    """Sui Number type."""

    def __init__(self, value: int) -> None:
        """Initialize type."""
        super().__init__(value)

    @property
    def gas_budget(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def gas_price(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def amount(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def amounts(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def split_amounts(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def count(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def limit(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def start_time(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def end_time(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def start(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def end(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def epoch(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value

    @property
    def sequence_number(self) -> int:
        """Alias for transactions."""
        return self.value

    @property
    def version(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value

    @property
    def cursor(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def split_count(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value
