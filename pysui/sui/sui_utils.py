#    Copyright 2022 Franctype_key V. Castellucci
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

"""Utility functions."""

import base64
import binascii
import subprocess
from pathlib import Path
from types import NoneType
from typing import Any, Optional, Type, Union, get_args
from dataclasses_json import DataClassJsonMixin

from pysui.sui.sui_types.scalars import (
    SuiString,
    ObjectID,
    SuiInteger,
    SuiNullType,
    SuiBoolean,
    SuiTransactionDigest,
    SuiTxBytes,
    SuiSignature,
)
from pysui.sui.sui_types.address import SuiAddress, valid_sui_address
from pysui.sui.sui_types.collections import SuiArray, SuiMap
from pysui.sui.sui_excepts import (
    SuiException,
    SuiMiisingBuildFolder,
    SuiMiisingModuleByteCode,
    SuiPackageBuildFail,
)
from pysui.sui.sui_txresults.single_tx import ObjectRead, ObjectReadData


_SUI_BUILD = ["sui", "move", "build", "-p"]


def _module_to_b64(module: Path) -> Union[SuiString, OSError]:
    """_module_to_b64 Convert binary modules to base64.

    :param module: Fully qualified path to move compiled module
    :type module: Path
    :return: A base64 encoded string of tile content or OSError
    :rtype: Union[SuiString, OSError]
    """
    with open(module, "rb") as core_file:
        mdata = core_file.read()
        return SuiString(base64.b64encode(mdata).decode())


def _package_modules_to_b64(project: Path) -> Union[list[SuiString], Union[OSError, SuiException]]:
    """_package_modules_to_b64 Converts found sui move binary modules to base64 strings.

    :param project: Path to the project folder
    :type project: Path
    :raises SuiMiisingBuildFolder: If project folder does not contain 'build' subfolder
    :raises SuiMiisingBuildFolder: If project/build folder does not contain 'bytecode_modules' subfolder
    :raises SuiMiisingModuleByteCode: If there are no '*.mv' files to convert
    :return: List of base64 encoded SuiStrings for each module found
    :rtype: Union[list[SuiString], Union[OSError, SuiException]]
    """
    bdir = [x for x in project.iterdir() if x.is_dir() and x.name == "build"]
    if not bdir:
        raise SuiMiisingBuildFolder(f"No build folder found in {project}")
    bmods = [x for x in bdir[0].iterdir() if x.is_dir() and (x / "bytecode_modules").exists()]
    if not bmods:
        raise SuiMiisingBuildFolder(f"No bytecode_modules folder found for {project}/build")
    mod_list = list(bmods[0].glob("*/*.mv"))
    if not mod_list:
        raise SuiMiisingModuleByteCode(f"{bmods[0]} is empty")
    return [_module_to_b64(x) for x in mod_list]


def _compile_project(path_to_package: Path) -> Union[Path, SuiException]:
    """_compile_project Compiles a sui move project.

    This can be called prior to using the Publish builder to ensure
    that the compiled move code is free of test bytes which would fail
    the `sui_publish` RPC call.

    :param path_to_package: Qualified path to SUI move project.
    :type path_to_package: Path
    :raises SuiPackageBuildFail: If the `sui move build` fails.
    :return: The path_to_package Path
    :rtype: Union[Path, SuiException]
    """
    args = _SUI_BUILD.copy()
    args.append(str(path_to_package))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode == 0:
        return path_to_package
    raise SuiPackageBuildFail(result.stdout)


def build_b64_modules(path_to_package: Path) -> Union[list[SuiString], Union[OSError, SuiException]]:
    """build_b64_modules Builds and encoedes a sui move package for publishing.

    :param path_to_package: Qualified path to SUI move project.
    :type path_to_package: Path
    :raises SuiMiisingBuildFolder: If path does not exist
    :return: List of base64 encoded SuiStrings, each representing a compiled sui module.
    :rtype: Union[list[SuiString], Union[OSError, SuiException]]
    """
    if path_to_package.exists():
        return _package_modules_to_b64(_compile_project(path_to_package))
    raise SuiMiisingBuildFolder(f"Move project path not found: {path_to_package}")


# Coercion utilities


def as_sui_address(in_data: Any) -> Union[SuiAddress, ValueError]:
    """as_sui_address coerces `in_data` to a SuiAddress.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If the data is not a valid SuiAddress form
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiAddress
    :rtype: Union[SuiAddress, ValueError]
    """
    if isinstance(in_data, SuiAddress):
        result = in_data
    elif isinstance(in_data, (ObjectID, SuiString)):
        if valid_sui_address(in_data.value):
            result = SuiAddress(in_data.value)
        else:
            raise ValueError(f"Type {in_data.__class__.__name__}: {in_data.value} is not a valid SuiAddress form.")
    elif isinstance(in_data, str):
        if valid_sui_address(in_data):
            result = SuiAddress(in_data)
        else:
            raise ValueError(f"str {in_data} is not a valid SuiAddress form.")
    if not result:
        raise ValueError(f"Can not get SuiInteger from {in_data} with type {type(in_data)}")
    return result


def as_object_id(in_data: Any) -> Union[ObjectID, ValueError]:
    """as_object_id coerces `in_data` to an ObjectID.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: if indata type not a suitable subtype of SuiScalarType
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: An ObjectID
    :rtype: Union[ObjectID, Union[ValueError, AttributeError]]
    """
    result = SuiNullType()
    # object_id: ObjectID = None
    if isinstance(in_data, ObjectID):
        result = in_data
    elif isinstance(in_data, str):
        result = ObjectID(in_data)
    elif isinstance(in_data, (ObjectRead, ObjectReadData)):
        result = in_data.identifier
    elif isinstance(in_data, SuiString):
        result = ObjectID(in_data.value)
    elif issubclass(type(in_data), SuiAddress):
        result = ObjectID(in_data.identifier.value)
    elif issubclass(type(in_data), DataClassJsonMixin):
        if hasattr(in_data, "identifier"):
            result = in_data.identifier
            if isinstance(result, str):
                result = ObjectID(result)
    if not result:
        raise ValueError(f"Can not get ObjectID from {in_data} with type {type(in_data)}")
    return result


def as_sui_string(in_data: Any) -> Union[SuiString, ValueError]:
    """as_sui_string coerces `in_data` to a SuiString.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiString
    :rtype: Union[SuiString, ValueError]
    """
    if isinstance(in_data, SuiString):
        result = in_data
    elif isinstance(in_data, str):
        result = SuiString(in_data)
    elif isinstance(in_data, int):
        result = SuiString(str(in_data))
    elif issubclass(type(in_data), SuiAddress):
        result = SuiString(in_data.identifier.value)
    if not result:
        raise ValueError(f"Can not get SuiString from {in_data} with type {type(in_data)}")
    return result


def as_sui_integer(in_data: Any) -> Union[SuiInteger, ValueError]:
    """as_sui_integer coerces `in_data` to a SuiInteger.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiInteger
    :rtype: Union[SuiInteger, ValueError]
    """
    if isinstance(in_data, SuiInteger):
        result = in_data
    elif isinstance(in_data, int):
        result = SuiInteger(in_data)
    elif isinstance(in_data, str):
        int_only = in_data.split(".")[0]
        result = SuiInteger(int(int_only))
    if not result:
        raise ValueError(f"Can not get SuiInteger from {in_data} with type {type(in_data)}")
    return result


def as_sui_array(in_data: Any) -> Union[SuiArray, ValueError]:
    """as_sui_array coerces `in_data` to a SuiArray.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiArray
    :rtype: Union[SuiArray, ValueError]
    """
    if isinstance(in_data, SuiArray):
        result = in_data
    elif isinstance(in_data, list):
        result = SuiArray(in_data)
    elif isinstance(in_data, tuple):
        result = SuiArray(list(in_data))
    if not result:
        raise ValueError(f"Can not get SuiArray from {in_data} with type {type(in_data)}")
    return result


def as_sui_map(in_data: Any) -> Union[SuiMap, ValueError]:
    """as_sui_map coerces `in_data` to a SuiMap.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiMap
    :rtype: Union[SuiMap, ValueError]
    """
    if isinstance(in_data, SuiMap):
        result = in_data
    elif isinstance(in_data, dict):
        result = SuiMap("", "")
        result.map = in_data
    if not result:
        raise ValueError(f"Can not get SuiMap from {in_data} with type {type(in_data)}")
    return result


def as_sui_boolean(in_data: Any) -> Union[SuiBoolean, ValueError]:
    """as_sui_boolean coerces `in_data` to a SuiBoolean.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiBoolean
    :rtype: Union[SuiBoolean, ValueError]
    """
    if isinstance(in_data, SuiBoolean):
        result = in_data
    elif isinstance(in_data, bool):
        result = SuiBoolean(in_data)
    elif isinstance(in_data, int):
        result = SuiBoolean(False) if in_data == 0 else SuiBoolean(True)
    else:
        result = SuiBoolean(True) if in_data else SuiBoolean(False)
    if not result:
        raise ValueError(f"Can not get SuiBoolean from {in_data} with type {type(in_data)}")
    return result


def is_base_64(str_or_bytes: Union[str, bytes, bytearray]) -> bool:
    """is_base_64 validate str_or_bytes if valid base64 construct.

    :param str_or_bytes: In data
    :type str_or_bytes: Union[str, bytes, bytearray]
    :raises ValueError: Invalid input type
    :return: True if is valid base64
    :rtype: bool
    """
    try:
        if isinstance(str_or_bytes, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(str_or_bytes, "ascii")
        elif isinstance(str_or_bytes, (bytes, bytearray)):
            sb_bytes = str_or_bytes
        else:
            raise ValueError("Argument must be string, bytes or bytearray")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except binascii.Error:
        return False


def to_base_64(in_data: Any, clz: Any) -> Union[Any, ValueError]:
    """to_base_64 Coerce str,bytes or bytearray to base64.

    :param in_data: Data to coerce
    :type in_data: Any
    :param clz: Result class that can construct with single argument
    :type clz: Any
    :raises ValueError: If `in_data` type not support for coercion
    :return: `clz` object instance
    :rtype: Union[Any, ValueError]
    """
    if isinstance(in_data, clz):
        result = in_data
    elif is_base_64(in_data):
        result = clz(in_data)
    elif isinstance(in_data, (str, bytes, bytearray)):
        in_data = in_data if not isinstance(in_data, str) else bytes(in_data, "utf-16")
        result = clz(base64.b64encode(in_data))
    if not result:
        raise ValueError(f"Can not get {clz.__class__.__name__} from {in_data} with type {type(clz)}")
    return result


def as_sui_txbytes(in_data: Any) -> Union[SuiTxBytes, ValueError]:
    """as_sui_txbytes coerces `in_data` to a SuiTxBytes.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiTxBytes
    :rtype: Union[SuiTxBytes, ValueError]
    """
    return to_base_64(in_data, SuiTxBytes)


def as_sui_signature(in_data: Any) -> Union[SuiSignature, ValueError]:
    """as_sui_signature coerces `in_data` to a SuiSignature.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiSignature
    :rtype: Union[SuiSignature, ValueError]
    """
    return to_base_64(in_data, SuiSignature)


def as_sui_txdigest(in_data: Any) -> Union[SuiTransactionDigest, ValueError]:
    """."""
    if isinstance(in_data, SuiTransactionDigest):
        result = in_data
    elif isinstance(in_data, SuiString):
        result = SuiTransactionDigest(in_data.value)
    elif isinstance(in_data, str):
        result = SuiTransactionDigest(in_data)
    if not result:
        raise ValueError(f"Can not get SuiTransactionDigest from {in_data} with type {type(in_data)}")
    return result


#: Keys are the end product pysui type and the value (set) are the types it can convert from.

COERCION_TO_FROM_SETS = {
    ObjectID: {str, SuiAddress, DataClassJsonMixin},
    SuiAddress: {str, ObjectID, SuiString},
    SuiString: {str, int, ObjectID, SuiAddress},
    SuiInteger: {str, int},
    SuiArray: {list, tuple},
    SuiMap: {dict},
    SuiSignature: {str, bytes, bytearray},
    SuiTxBytes: {str, bytes, bytearray},
    SuiTransactionDigest: {str, SuiString},
    SuiBoolean: {bool, int, str},
}
#: Keys are the inbound types that can be represented in SUI types in the value (set).
COERCION_FROM_TO_SETS = {
    str: {SuiAddress, ObjectID, SuiString, SuiInteger, SuiBoolean, SuiTxBytes, SuiSignature, SuiTransactionDigest},
    int: {SuiInteger, SuiString, SuiBoolean},
    bytes: {SuiTxBytes, SuiSignature},
    bytearray: {SuiTxBytes, SuiSignature},
    list: {SuiArray},
    tuple: {SuiArray},
    dict: {SuiMap},
    bool: {SuiBoolean},
    SuiString: {SuiAddress, ObjectID, SuiBoolean},
    NoneType: {SuiNullType},
}

#: Keys are the types and value is the converter function.

COERCION_FN_MAP = {
    SuiAddress: as_sui_address,
    ObjectID: as_object_id,
    SuiString: as_sui_string,
    SuiInteger: as_sui_integer,
    SuiArray: as_sui_array,
    SuiMap: as_sui_map,
    SuiBoolean: as_sui_boolean,
    SuiSignature: as_sui_signature,
    SuiTxBytes: as_sui_txbytes,
    SuiTransactionDigest: as_sui_txdigest,
    NoneType: lambda x: SuiNullType(),
}

if __name__ == "__main__":
    import inspect
    import functools

    def builder_init(*includes, **kwargs):
        """."""

        def _autoargs(func):
            __host_class, __host_func = func.__qualname__.split(".")
            if __host_func != "__init__":
                raise ValueError(f"@builder_init is decorator for class __init__, found {__host_func}")
            spec = inspect.getfullargspec(func)
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

            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                __var_map: dict = {}
                __var_type_map: dict = {}
                # handle default values
                if spec.defaults:
                    # if defaults:
                    for attr, val in zip(reversed(spec.args), reversed(spec.defaults)):
                        if sieve(attr):
                            __var_map[attr] = val
                            __var_type_map[attr] = spec.annotations[attr]
                            # setattr(self, attr, val)
                # # handle positional arguments
                positional_attrs = spec.args[1:]
                for attr, val in zip(positional_attrs, args):
                    if sieve(attr):
                        __var_map[attr] = val
                        __var_type_map[attr] = spec.annotations[attr]

                # handle keyword args
                if kwargs:
                    for attr, val in kwargs.items():
                        if sieve(attr):
                            __var_map[attr] = val
                            __var_type_map[attr] = spec.annotations[attr]

                # handle keywords with defaults:
                if spec.kwonlydefaults:
                    for attr, val in spec.kwonlydefaults.items():
                        if sieve(attr):
                            __var_map[attr] = val
                            __var_type_map[attr] = spec.annotations[attr]

                # Setup the self parameter properties
                for _new_key, _new_val in self.value_type_validator(__host_class, __var_map, __var_type_map).items():
                    setattr(self, _new_key, _new_val)
                # Call the underlying __host_class __init__ function
                return func(self, *args, **kwargs)

            return wrapper

        return _autoargs

    class Moopy:
        """Faux SuiBaseBuilder."""

        def __init__(
            self,
            method: str,
            handler_cls: Type[DataClassJsonMixin] = None,
            handler_func: str = None,
        ) -> None:
            """."""
            self._method = method
            self._handler_cls: Type[DataClassJsonMixin] = handler_cls
            self._handler_func: str = handler_func

        @property
        def method(self) -> str:
            """."""
            return self._method

        def pull_vars(self) -> list[Any]:
            """Filter out private/protected var elements."""
            return [val for _var_key, val in vars(self).items() if _var_key[0] != "_"]

        @classmethod
        def value_type_validator(cls, base_class_name: str, args: dict, builder_types: dict) -> Union[dict, TypeError]:
            """."""
            result_dict = {}
            for ctype_key, ctype_value in builder_types.items():
                # Get the type of value from args of same name
                has_type = type(args[ctype_key])
                # print(f"args {ctype_key} has type {has_type} and expects {ctype_value}")
                # if hastype is equal to expected type (ctype_value)
                if has_type == ctype_value:
                    result_dict[ctype_key] = args[ctype_key]
                # if intype has cross-reference, call the converter
                elif has_type in COERCION_FROM_TO_SETS and ctype_value in COERCION_FROM_TO_SETS[has_type]:
                    result_dict[ctype_key] = COERCION_FN_MAP[ctype_value](args[ctype_key])
                # If no value in argument but type supports Optional
                elif not args[ctype_key]:
                    if "_name" in ctype_value.__dict__ and ctype_value.__dict__["_name"] == "Optional":
                        result_dict[ctype_key] = COERCION_FN_MAP[has_type](ctype_key)
                    else:
                        raise TypeError(f"{ctype_key} has no value but missing type hint 'Optional'")
                # If value in argument and type can be optional Optional
                elif (
                    args[ctype_key] and "_name" in ctype_value.__dict__ and ctype_value.__dict__["_name"] == "Optional"
                ):
                    true_type = get_args(ctype_value)[0]
                    if (
                        true_type in COERCION_TO_FROM_SETS
                        and has_type in COERCION_TO_FROM_SETS[true_type]
                        and true_type in COERCION_FN_MAP
                    ):
                        result_dict[ctype_key] = COERCION_FN_MAP[true_type](args[ctype_key])
                    else:
                        raise ValueError(f"Unable to handle {ctype_key} attribute assignment")
                else:
                    # We get here if we can't coerce type
                    raise ValueError(
                        f"{ctype_key} expects {ctype_value} but args {ctype_key} is  {type(args[ctype_key])}"
                    )
            return result_dict

    class WithSpec(Moopy):
        """."""

        # _builder_types: dict = {"package": ObjectID, "module_name": Optional[SuiString]}

        @builder_init()
        def __init__(self, *, package: ObjectID, module_name: Optional[SuiString] = "Flimpy") -> None:
            """."""
            super().__init__("sui_getObject", handler_cls=ObjectRead, handler_func="from_dict")

    # monk = WithSpec(package="0x2", module_name=None)
    monk = WithSpec(package="foofuckingbar", module_name=None)
    print(monk.pull_vars())
    # faux = Faux("0x2", "base")
    # print(faux.pull_vars())
