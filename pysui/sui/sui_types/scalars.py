#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui Scalar Types."""

import math
from typing import Union
from deprecated.sphinx import deprecated
from pysui.abstracts import SuiScalarType


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
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

    @property
    def gas(self) -> None:
        """Alias for transactions."""
        return self.value

    @property
    def at_checkpoint(self) -> None:
        """Alias for transactions."""
        return self.value


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiString(SuiScalarType):
    """Sui String type."""

    def __init__(self, identifier: str) -> None:
        """__init__ Native string initializing SuiString.

        :param identifier: A python str
        :type identifier: str
        """
        super().__init__(identifier)

    @property
    def id(self) -> str:
        """Alias for transactions."""
        return self.value

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

    @property
    def amounts(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def transaction_digest(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def gas_budget(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def amount(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def split_count(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def epoch(self) -> str:
        """Alias for transactions."""
        return self.value


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiTxBytes(SuiString):
    """Sui Base64 tx_bytes string."""

    @property
    def tx_bytes(self) -> str:
        """Satisfy transaction verification."""
        return str(self)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiSignature(SuiString):
    """Sui Base64 signature."""

    @property
    def signature(self) -> str:
        """Satisfy transaction verification."""
        return str(self)

    @property
    def signatures(self) -> str:
        """Satisfy transaction verification."""
        return str(self)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiTransactionDigest(SuiString):
    """Sui Base58 digest."""

    @property
    def digest(self) -> str:
        """Alias for transaction."""
        return str(self)


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
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
    def object_ids(self) -> str:
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
    def staked_sui_ids(self) -> str:
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


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
class SuiBoolean(SuiScalarType):
    """Sui Bool type."""

    @property
    def descending_order(self) -> bool:
        """Alias for transactions."""
        return self.value


@deprecated(
    version="0.65.0", reason="Transition to pysui GraphQL SuiClients and QueryNodes"
)
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
    def id(self) -> int:
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
    def arguments(self) -> str:
        """Alias for transactions."""
        return self.value

    @property
    def split_count(self) -> int:
        """Alias for transactions."""
        if self.value is None:
            return 0
        return self.value


# pylint:disable=too-few-public-methods
class SuiIntegerType:
    """."""

    def to_bytes(self) -> bytes:
        """."""
        value: int = getattr(self, "value")
        maxer: int = getattr(self, "_BYTE_COUNT")
        return value.to_bytes(maxer, "little")

    @property
    def type_tag_name(self) -> str:
        """."""
        return getattr(self, "_TYPE_TAG_NAME")

    @classmethod
    def to_best_fit_integer_type(cls, value: int) -> "SuiIntegerType":
        """."""
        byte_count = math.ceil(value.bit_count() / 8)
        for sclz in cls.__subclasses__():
            if getattr(sclz, "_BYTE_COUNT") == byte_count:
                return sclz(value)
        raise ValueError(f"Unable to resolve type to hold {byte_count} bytes")

    @classmethod
    def byte_count(clz) -> int:
        """Return count of bytes for class"""
        return getattr(clz, "_BYTE_COUNT")


class SuiU8(SuiIntegerType):
    """."""

    _MAX_VAL: int = 0xFF
    _BYTE_COUNT: int = 1
    _TYPE_TAG_NAME: str = "U8"

    def __init__(self, val: Union[int, str]):
        """."""
        assert int(val) <= self._MAX_VAL
        self.value = int(val)


class SuiU16(SuiIntegerType):
    """."""

    _MAX_VAL: int = 0xFFFF
    _BYTE_COUNT: int = 2
    _TYPE_TAG_NAME: str = "U16"

    def __init__(self, val: Union[int, str]):
        """."""
        assert int(val) <= self._MAX_VAL
        self.value = int(val)


class SuiU32(SuiIntegerType):
    """."""

    _MAX_VAL: int = 0xFFFFFFFF
    _BYTE_COUNT: int = 4
    _TYPE_TAG_NAME: str = "U32"

    def __init__(self, val: Union[int, str]):
        """."""
        assert int(val) <= self._MAX_VAL
        self.value = int(val)


class SuiU64(SuiIntegerType):
    """."""

    _MAX_VAL: int = 0xFFFFFFFFFFFFFFFF
    _BYTE_COUNT: int = 8
    _TYPE_TAG_NAME: str = "U64"

    def __init__(self, val: Union[int, str]):
        """."""
        assert int(val) <= self._MAX_VAL
        self.value = int(val)


class SuiU128(SuiIntegerType):
    """."""

    _MAX_VAL: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    _BYTE_COUNT: int = 16
    _TYPE_TAG_NAME: str = "U128"

    def __init__(self, val: Union[int, str]):
        """."""
        assert int(val) <= self._MAX_VAL
        self.value = int(val)


class SuiU256(SuiIntegerType):
    """."""

    _MAX_VAL: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    _BYTE_COUNT: int = 32
    _TYPE_TAG_NAME: str = "U256"

    def __init__(self, val: Union[int, str]):
        """."""
        assert int(val) <= self._MAX_VAL
        self.value = int(val)
