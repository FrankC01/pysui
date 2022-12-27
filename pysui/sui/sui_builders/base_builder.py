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

"""Sui Builders: Common types."""

from abc import abstractmethod
from enum import IntEnum
from typing import Type, Union
from pysui.abstracts.client_types import SuiBaseType
from pysui.abstracts.client_rpc import Builder


class SuiRequestType(IntEnum):
    """SuiRequestType Defines the type of request being made when invoking `sui_executeTransaction`.

    :param IntEnum: Base enumeration type
    :type IntEnum: _type_
    :raises TypeError: _description_
    """

    IMMEDIATERETURN = 0
    WAITFORTXCERT = 1
    WAITFOREFFECTSCERT = 2
    WAITFORLOCALEXECUTION = 3

    def as_str(self) -> str:
        """Get scheme as string."""
        if self is SuiRequestType.IMMEDIATERETURN:
            return "ImmediateReturn"
        if self is SuiRequestType.WAITFORTXCERT:
            return "WaitForTxCert"
        if self is SuiRequestType.WAITFOREFFECTSCERT:
            return "WaitForEffectsCert"
        if self is SuiRequestType.WAITFORLOCALEXECUTION:
            return "WaitForLocalExecution"
        raise TypeError(f"Unknown request type {self.name}")

    @property
    def request_type(self) -> str:
        """Satisfy transaction verification."""
        return self.as_str()


class SuiBaseBuilder(Builder):
    """Base Sui API Builder Class.

    Subclasses must identify public vars that are
    required by Sui RPC API.
    """

    def __init__(
        self, method: str, txn_required: bool, handler_cls: Type[SuiBaseType] = None, handler_func: str = None
    ) -> None:
        """__init__ Initialize builder.

        :param method: The SUI RPC API method
        :type method: str
        :param txn_required: Indicate that this is a complex request or simple transaction
        :type txn_required: bool
        :param handler_cls: Designate factor class for receipt data, defaults to None
        :type handler_cls: Type[SuiBaseType], optional
        :param handler_func:
            Name of function (either on class or regular function) to convert receipt data, defaults to None
        :type handler_func: str, optional
        """
        super().__init__()
        self._method = method
        self._txn_required = txn_required
        self._handler_cls: Type[SuiBaseType] = handler_cls
        self._handler_func: str = handler_func

    def _pull_vars(self) -> list[SuiBaseType]:
        """Filter out private/protected var elements."""
        var_map = vars(self)
        return [val for key, val in var_map.items() if key[0] != "_"]

    @abstractmethod
    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        return self._pull_vars()

    @property
    def params(self) -> list[SuiBaseType]:
        """Return parameters list."""
        return self._collect_parameters()

    @property
    def header(self) -> dict:
        """Return copy of the current header."""
        return self._header

    @property
    def method(self) -> str:
        """Return method."""
        return self._method

    @property
    def txn_required(self) -> bool:
        """Get transaction required flag."""
        return self._txn_required

    # Experimental
    def _has_return_handler_cls(self) -> bool:
        """Query presence of return handler."""
        return self._handler_cls is not None

    def _has_return_handler_func(self) -> bool:
        """Query presence of return handler."""
        return self._handler_func is not None

    # Experimental
    def handle_return(self, indata: dict) -> Union[dict, SuiBaseType]:
        """Handle the expected return."""
        if self._handler_cls and self._handler_func:
            return getattr(self._handler_cls, self._handler_func)(indata)
        if self._handler_cls and self._handler_func is None:
            return self._handler_cls(indata)
        if self._handler_cls is None and self._handler_func:
            return self._handler_func(indata)
        return indata


class _NativeTransactionBuilder(SuiBaseBuilder):
    """Builders for simple single parameter transactions."""

    def __init__(self, method: str, handler_cls: Type[SuiBaseType] = None, handler_func: str = None) -> None:
        """Initialize builder."""
        super().__init__(method, False, handler_cls, handler_func)
