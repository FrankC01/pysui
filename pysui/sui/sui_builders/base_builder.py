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

import inspect
import functools


from enum import IntEnum
from typing import Type, Union, get_args
import typing_utils
from pysui.abstracts.client_types import SuiBaseType
from pysui.abstracts.client_rpc import Builder
from pysui.sui.sui_utils import COERCION_FROM_TO_SETS, COERCION_FN_MAP, COERCION_TO_FROM_SETS


class SuiRequestType(IntEnum):
    """SuiRequestType Defines the type of request being made when invoking `sui_executeTransaction`.

    :param IntEnum: Base enumeration type
    :type IntEnum: IntEnum
    :raises TypeError: If request type enum not known
    """

    WAITFOREFFECTSCERT = 0
    WAITFORLOCALEXECUTION = 1

    def as_str(self) -> str:
        """Get scheme as string."""
        if self is SuiRequestType.WAITFOREFFECTSCERT:
            return "WaitForEffectsCert"
        if self is SuiRequestType.WAITFORLOCALEXECUTION:
            return "WaitForLocalExecution"
        raise TypeError(f"Unknown request type {self.name}")

    @property
    def request_type(self) -> str:
        """Satisfy transaction verification."""
        return self.as_str()


class SuiTransactionBuilderMode(IntEnum):
    """SuiTransactionBuilderMode Defines the mode of the transaction.

    :param IntEnum: Base enumeration type
    :type IntEnum: IntEnum
    :raises TypeError: If request type enum not known
    """

    COMMIT = 0
    DEVINSPECT = 1

    def as_str(self) -> str:
        """Get scheme as string."""
        if self is SuiTransactionBuilderMode.COMMIT:
            return "Commit"
        if self is SuiTransactionBuilderMode.DEVINSPECT:
            return "DevInspect"
        raise TypeError(f"Unknown builder mode type {self.name}")

    @property
    def transactio_buid_type(self) -> str:
        """Satisfy transaction verification."""
        return self.as_str()

    @property
    def txn_builder_mode(self) -> str:
        """Satisfy transaction verification."""
        return self.as_str()

    @property
    def execution_mode(self) -> str:
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

    def _collect_parameters(self) -> list[SuiBaseType]:
        """Collect the call parameters."""
        # TODO: Merge with `params` method when refactored or just remove abstract decl
        return self._pull_vars()

    @property
    def params(self) -> list[SuiBaseType]:
        """Return parameters list."""
        return self._pull_vars()

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

    def handle_return(self, indata: dict) -> Union[dict, SuiBaseType]:
        """Handle the expected return."""
        if self._handler_cls and self._handler_func:
            return getattr(self._handler_cls, self._handler_func)(indata)
        if self._handler_cls and self._handler_func is None:
            return self._handler_cls(indata)
        if self._handler_cls is None and self._handler_func:
            return self._handler_func(indata)
        return indata

    # EXPERIMENTAL
    @classmethod
    def value_type_validator(cls, base_class_name: str, args: dict, builder_types: dict) -> Union[dict, TypeError]:
        """value_type_validator Aligns and or coerces expected arg type from input arg value.

        :param base_class_name: Class of type
        :type base_class_name: str
        :param args: Arguments passed to constructor
        :type args: dict
        :param builder_types: Expected types for builder
        :type builder_types: dict
        :raises TypeError: If missing or unresolvable coercion function
        :raises ValueError: If unresolvable type
        :return: Dictionary of argname to coerced argvalue
        :rtype: Union[dict, TypeError]
        """
        result_dict = {}
        for ctype_key, ctype_value in builder_types.items():
            # Get the type of value from args of same name
            has_type = type(args[ctype_key])
            # if hastype is equal to expected type (ctype_value)
            if has_type == ctype_value:
                result_dict[ctype_key] = args[ctype_key]
            elif args[ctype_key] and typing_utils.issubtype(
                has_type, ctype_value
            ):  # issubclass(has_type, ctype_value):
                result_dict[ctype_key] = args[ctype_key]
            # if intype has cross-reference, call the converter
            elif has_type in COERCION_FROM_TO_SETS and ctype_value in COERCION_FROM_TO_SETS[has_type]:
                result_dict[ctype_key] = COERCION_FN_MAP[ctype_value](args[ctype_key])
            # If no value in argument but type supports Optional
            elif not args[ctype_key]:
                if has_type in COERCION_FN_MAP:
                    result_dict[ctype_key] = COERCION_FN_MAP[has_type](ctype_key)
                else:
                    raise TypeError(f"{ctype_key} has no value and no coercion function. In {has_type}")
            elif has_type in COERCION_TO_FROM_SETS:
                result_dict[ctype_key] = COERCION_FN_MAP[has_type](args[ctype_key])
            else:
                # We get here if we can't coerce type
                raise ValueError(f"{ctype_key} expects {ctype_value} but args {ctype_key} is {type(args[ctype_key])}")
        return result_dict


def sui_builder(*includes, **kwargs):
    """sui_builder Decorator to use in Builders."""

    def _autoargs(func):
        """_autoargs Function that wraps decorator behavior.

        :param func: Function that is being wrapped
        :type func: CallOnce
        :raises ValueError: If function being wrapped is not __init__
        :raises AttributeError: If variable args are declared in __init__
        :return: The wrapper function for __init__
        :rtype: CallOnce
        """
        __host_class, __host_func = func.__qualname__.split(".")
        if __host_func != "__init__":
            raise ValueError(f"@sui_builder is decorator for class __init__, but found {__host_func}")
        spec: inspect.FullArgSpec = inspect.getfullargspec(func)
        # handle varargs is an exception for builders
        if spec.varargs:
            raise AttributeError(f"Builder initializers do not accept variable args {spec.varargs}")

        def sieve(attr: str) -> bool:
            """sieve Checks if attribute should be included in results.

            :param attr: attribute name
            :type attr: str
            :return: True if keeping for setattr
            :rtype: bool
            """
            if kwargs and attr in kwargs["excludes"]:
                return False
            if not includes or attr in includes:
                return True
            return False

        def sui_true_type(anno) -> object:
            """sui_true_type Resolve arguments true type.

            :param anno: The property annotation
            :type anno: type
            :return: True type as object
            :rtype: object
            """
            if "_name" in anno.__dict__ and anno.__dict__["_name"] == "Optional":
                return get_args(anno)[0]
            return anno

        def track_map() -> dict:
            """track_map Setup the mapping of arguments and types.

            :return: Dict of arg_name and none
            :rtype: dict
            """
            if spec.kwonlyargs:
                var_map: dict = {x: None for x in spec.kwonlyargs}
            else:
                var_map: dict = {x: None for x in spec.args[1:]}

            return var_map

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> None:
            """wrapper Wrapper that is called on object __init__.

            :return: The constructed object
            :rtype: Builder
            """
            __var_map = track_map()
            __var_type_map = __var_map.copy()
            # handle default values
            if spec.defaults:
                # if defaults:
                for attr, val in zip(reversed(spec.args), reversed(spec.defaults)):
                    if sieve(attr):
                        __var_map[attr] = val
                        __var_type_map[attr] = sui_true_type(spec.annotations[attr])
            # # handle positional arguments
            positional_attrs = spec.args[1:]
            for attr, val in zip(positional_attrs, args):
                if sieve(attr):
                    __var_map[attr] = val
                    __var_type_map[attr] = sui_true_type(spec.annotations[attr])
                    # __var_type_map[attr] = spec.annotations[attr]

            # handle keyword args
            if kwargs:
                for attr, val in kwargs.items():
                    if sieve(attr):
                        __var_map[attr] = val
                        __var_type_map[attr] = sui_true_type(spec.annotations[attr])
                        # __var_type_map[attr] = spec.annotations[attr]

            # handle keywords with defaults:
            if spec.kwonlydefaults:
                for attr, val in spec.kwonlydefaults.items():
                    if not __var_map[attr] and sieve(attr):
                        __var_map[attr] = val
                        __var_type_map[attr] = sui_true_type(spec.annotations[attr])
                        # __var_type_map[attr] = spec.annotations[attr]

            def my_set_lambda(name, coerce, self, val):
                """my_set_lambda Setter for property on builder.

                :param name: Property Name
                :type name: Any
                :param coerce: Coercion utility
                :type coerce: CallOne
                :param val: The value to set to the property name
                :type val: Any
                :return: self
                :rtype: SuiBaseBuilder
                """
                self.__dict__[name] = coerce(val)
                return self

            def my_get_lambda(name, self):
                """my_get_lambda Return the value of propery.

                :param name: The name of the property
                :type name: Any
                :return: The value of the named property
                :rtype: Any
                """
                return self.__dict__[name]

            # Setup the initializing values
            _instance_dict = self.value_type_validator(__host_class, __var_map, __var_type_map)
            for _new_key, _new_val in _instance_dict.items():
                setattr(self, _new_key, _new_val)
            # Setup the properties (getter, setter)
            myclass = self.__class__
            for _new_key, _new_val in _instance_dict.items():
                coercer = COERCION_FN_MAP.get(__var_type_map[_new_key], lambda x: x)
                setattr(
                    myclass,
                    _new_key,
                    property(
                        functools.partial(my_get_lambda, _new_key), functools.partial(my_set_lambda, _new_key, coercer)
                    ),
                )

            # Call the underlying __host_class __init__ function
            return func(self, *args, **kwargs)

        return wrapper

    return _autoargs


class _NativeTransactionBuilder(SuiBaseBuilder):
    """Builders for simple single parameter transactions."""

    def __init__(self, method: str, handler_cls: Type[SuiBaseType] = None, handler_func: str = None) -> None:
        """Initialize builder."""
        super().__init__(method, False, handler_cls, handler_func)
