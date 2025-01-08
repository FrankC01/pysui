#    Copyright Frank V. Castellucci
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

import itertools
import math
import os
import base64
import binascii
import subprocess
import hashlib
from dataclasses import dataclass
from pathlib import Path
from types import NoneType
from typing import Any, Iterable, Union
from deprecated.sphinx import versionchanged, deprecated
import base58
import yaml
from dataclasses_json import DataClassJsonMixin
from deprecated.sphinx import versionchanged, versionadded
from pysui.sui.sui_common.validators import valid_sui_address
from pysui.sui.sui_constants import (
    DEFAULT_ALIAS_PATH_STRING,
    DEFAULT_DEVNET_PATH_STRING,
    EMPEHMERAL_PATH,
    PYSUI_EXEC_ENV,
    SUI_BASE_ACTIVE,
    SUI_BASE_EXEC_PATH,
    DEFAULT_SUI_BINARY_PATH,
)

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
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import BatchParameter, SuiArray, SuiMap
from pysui.sui.sui_excepts import (
    SuiException,
    SuiMiisingBuildFolder,
    SuiPackageBuildFail,
)
from pysui.sui.sui_txresults.single_tx import ObjectRead, ObjectReadData


# _SUI_BUILD: list[str] = ["sui", "move", "build", "-p"]
# _SUI_BUILD_SKIP_GIT: list[str] = ["sui", "move", "build", "--skip-fetch-latest-git-deps", "-p"]
_UNPUBLISHED: str = "0000000000000000000000000000000000000000000000000000000000000000"

_SUI_BUILD: list[str] = ["move", "build"]


@dataclass
@versionadded(
    version="0.66.0",
    reason="Uses raw bytes from modules.",
)
class CompiledPackageRaw:
    """Ease of compilation information dataclass."""

    project_name: str
    project_id: str
    project_source_digest: bytes
    dependencies: list[str]
    compiled_modules: list[bytes] = None
    package_digest: bytes = None


def _compile_project(
    path_to_package: Path, args_list: list[str]
) -> Union[Path, SuiException]:
    """_compile_project Compiles a sui move project.

    This can be called prior to using the Publish builder to ensure
    that the compiled move code is free of test bytes which would fail
    the `sui_publish` RPC call.

    :param path_to_package: Qualified path to SUI move project.
    :type path_to_package: Path
    :param skip_git_dependencie: Skip sui move buikd checking git dependencies.
    :type skip_git_dependencie: bool
    :raises SuiPackageBuildFail: If the `sui move build` fails.
    :return: The path_to_package Path
    :rtype: Union[Path, SuiException]
    """
    mbs = _SUI_BUILD.copy()
    mbs.extend(args_list)
    mbs.append("-p")
    mbs.append(path_to_package)
    # return " ".join(mbs)

    mbs.insert(0, os.environ[PYSUI_EXEC_ENV])
    result = subprocess.run(mbs, capture_output=True, text=True)
    if result.returncode == 0:
        return path_to_package
    raise SuiPackageBuildFail(result.stdout)


def _compile_projectg(
    sui_bin_str: str, path_to_package: Path, args_list: list[str]
) -> Union[Path, SuiException]:
    """_compile_projectg Compiles a sui move project in GraohQL environment."""
    mbs = _SUI_BUILD.copy()
    mbs.extend(args_list)
    mbs.append("-p")
    mbs.append(path_to_package)

    mbs.insert(0, sui_bin_str)
    result = subprocess.run(mbs, capture_output=True, text=True)
    if result.returncode == 0:
        return path_to_package
    raise SuiPackageBuildFail(result.stdout)


def _build_dep_info(build_path: str) -> Union[CompiledPackageRaw, Exception]:
    """Fetch details about build."""
    build_info = Path(build_path).joinpath("BuildInfo.yaml")
    if build_info.exists():
        build_info_dict = yaml.safe_load(build_info.read_text(encoding="utf-8"))[
            "compiled_package_info"
        ]
        pname = build_info_dict["package_name"].lower()
        inner_dep = build_info_dict["address_alias_instantiation"]
        pindent = f"0x{inner_dep[pname]}"
        dep_ids: list[ObjectID] = []
        for key, value in inner_dep.items():
            if key != pname:
                dep_ids.append(f"0x{value}")
        return CompiledPackageRaw(
            pname,
            pindent,
            binascii.unhexlify(build_info_dict["source_digest"]),
            dep_ids,
        )
    raise ValueError("Corrupt publish build information")


def _package_digestg(package: CompiledPackageRaw, module_path: Path) -> None:
    """Captures compiled module bytes for publishing and digest calculation."""

    mod_bytes: list[bytes] = []
    all_digests: list[bytes] = []

    mod_list = list(module_path.glob("*.mv"))
    if not mod_list:
        raise ValueError(f"{module_path} is empty")
    for mmod in mod_list:
        binfile = mmod.read_bytes()
        hasher = hashlib.blake2b(digest_size=32)
        hasher.update(binfile)
        all_digests.append(hasher.digest())
        mod_bytes.append(list(binfile))
    for dep_str in package.dependencies:
        all_digests.append(binascii.unhexlify(dep_str[2:]))
    all_digests.sort()
    hasher = hashlib.blake2b(digest_size=32)
    for bblock in all_digests:
        hasher.update(bblock)
    package.package_digest = hasher.digest()
    package.compiled_modules = mod_bytes


@versionchanged(
    version="0.17.0",
    reason="Added the package digest that matches chain digest.",
)
def publish_build(
    path_to_package: Path,
    args_list: list[str],
) -> Union[CompiledPackageRaw, Exception]:
    """Build and collect module base64 strings and dependencies ObjectIDs."""
    if os.environ[PYSUI_EXEC_ENV] == EMPEHMERAL_PATH:
        raise ValueError(f"Configuration does not support publishing")
    # Compile the package
    path_to_package = _compile_project(path_to_package, args_list)
    # Find the build folder
    build_path = path_to_package.joinpath("build")
    if not build_path.exists():
        raise SuiMiisingBuildFolder(f"No build folder found in {path_to_package}")
    # Get the project folder
    build_subdir = [
        x for x in os.scandir(build_path) if x.is_dir() and x.name != "locks"
    ]
    if len(build_subdir) > 1:
        raise SuiMiisingBuildFolder(f"No build folder found in {path_to_package}")
    # Finally, get the module(s) bytecode folder
    move_modules = Path(build_subdir[0]).joinpath("bytecode_modules")
    if not move_modules.exists():
        raise SuiMiisingBuildFolder(
            f"No bytecode_modules folder found for {path_to_package}/build"
        )

    # Construct initial package
    cpackage = _build_dep_info(build_subdir[0].path)
    # Set module bytes as base64 strings and generate package digest
    _package_digestg(cpackage, move_modules)
    return cpackage


def publish_buildg(
    sui_bin_path_str: str,
    path_to_package: Path,
    args_list: list[str],
) -> Union[CompiledPackageRaw, Exception]:
    """Build and collect module base64 strings and dependencies ObjectIDs."""
    # Compile the package
    path_to_package = _compile_projectg(sui_bin_path_str, path_to_package, args_list)
    # Find the build folder
    build_path = path_to_package.joinpath("build")
    if not build_path.exists():
        raise SuiMiisingBuildFolder(f"No build folder found in {path_to_package}")
    # Get the project folder
    build_subdir = [
        x for x in os.scandir(build_path) if x.is_dir() and x.name != "locks"
    ]
    if len(build_subdir) > 1:
        raise SuiMiisingBuildFolder(f"No build folder found in {path_to_package}")
    # Finally, get the module(s) bytecode folder
    byte_modules = Path(build_subdir[0]).joinpath("bytecode_modules")
    if not byte_modules.exists():
        raise SuiMiisingBuildFolder(
            f"No bytecode_modules folder found for {path_to_package}/build"
        )

    # Construct initial package
    cpackage = _build_dep_info(build_subdir[0].path)
    # Set module bytes as base64 strings and generate package digest
    _package_digestg(cpackage, byte_modules)
    return cpackage


@versionchanged(version="0.41.0", reason="Sui aliases configuration feature added")
def sui_base_get_config() -> tuple[Path, Path, Union[Path, None]]:
    """sui_base_get_config Load a sui-base configuration.

    :raises ValueError: client.yaml not found
    :raises ValueError: sui binary not found
    :return: Fully qualified paths to client.yaml and sui binary
    :rtype: tuple[Path, Path]
    """
    # Have the system expand path and resolve symlinks
    active_path = Path(os.readlink(os.path.expanduser(SUI_BASE_ACTIVE)))
    astem = active_path.stem
    match astem:
        case "localnet" | "devnet" | "testnet":
            # client yaml
            local_cfg = Path(os.readlink(active_path.joinpath("config"))).joinpath(
                "client.yaml"
            )
            if not local_cfg.exists():
                raise ValueError(f"client.yaml not found {local_cfg}")
            # alias json
            alias_file = Path(os.readlink(active_path.joinpath("config"))).joinpath(
                "sui.aliases"
            )
            # Sui binary
            sui_exec_path = Path(
                os.readlink(active_path.joinpath("sui-repo"))
            ).joinpath(SUI_BASE_EXEC_PATH)
            if not sui_exec_path.exists():
                raise ValueError(f"sui binary not found {sui_exec_path}")
        case _:
            # default client yaml
            local_cfg = Path(os.path.expanduser(DEFAULT_DEVNET_PATH_STRING))
            if not local_cfg.exists():
                raise ValueError(f"client.yaml not found {local_cfg}")
            # alias json
            alias_file = Path(os.path.expanduser(DEFAULT_ALIAS_PATH_STRING))
            # Default Sui binary
            sui_exec_path = Path(os.path.expanduser(DEFAULT_SUI_BINARY_PATH))
            if not sui_exec_path.exists():
                raise ValueError(f"sui binary not found {sui_exec_path}")
    return local_cfg, sui_exec_path, alias_file


# Serialize helper
def serialize_uint32_as_uleb128(value: int) -> bytes:
    """."""
    ret = bytearray()
    while value >= 0x80:
        # Write 7 (lowest) bits of data and set the 8th bit to 1.
        byte = value & 0x7F
        ret.append(byte | 0x80)
        value >>= 7

    # Write the remaining bits of data and set the highest bit to 0.
    ret.append(value)
    return bytes(ret)


# Iteration helpers - lists


def partition(ilist: Iterable, chunk_size: int):
    """Partition a list with max paritiion size.

    Lazy generation of list partitions with size <= chunk_size

    :param ilist: A flat list to partition
    :type ilist: Iterable
    :param chunk_size: Max elements per partition
    :type chunk_size: int
    :yield: a list of size N where N <= chunk_size
    :rtype: list
    """
    it = iter(ilist)
    while item := list(itertools.islice(it, chunk_size)):
        yield item


# Conversion utilities


def hexstring_to_sui_id(indata: str, default_fill_length: int = 64) -> str:
    """Convert hexstring to valid full length sui address/object id."""

    if len(indata) < default_fill_length:
        if indata.count("x") or indata.count("X"):
            indata = indata[2:]
        indata = f"0x{indata.zfill(default_fill_length)}"
    return indata


@versionchanged(version="0.19.0", reason="Account for > 3 and < 66 size hex string")
def hexstring_to_list(indata: str, default_fill_length: int = 64) -> list[int]:
    """hexstring_to_list convert a hexstr (e.g. 0x...) into a list of ints.

    :param indata: Data to conver to list of ints
    :type indata: str
    :return: converted indata to int list
    :rtype: list[int]
    """
    return [int(x) for x in binascii.unhexlify(hexstring_to_sui_id(indata)[2:])]


def b64str_to_list(indata: str) -> list[int]:
    """b64str_to_list convert a base64 string into a list of ints.

    :param indata: Base64 encoded string
    :type indata: str
    :return: converted indata to int list
    :rtype: list[int]
    """
    b64bytes = base64.b64decode(indata)
    return [int(x) for x in b64bytes]


def from_list_to_b58str(indata: list) -> str:
    """From list to b58 string."""
    return base58.b58encode(bytearray(indata)).decode("utf-8")


def b58str_to_list(indata: str) -> list[int]:
    """b58str_to_list convert a base58 string into a list of ints.

    :param indata: Base58 encoded string
    :type indata: str
    :return: converted indata to int list
    :rtype: list[int]
    """
    try:
        decode_bytes = base58.b58decode(indata)
    # Fall back if invalid base58 str
    except ValueError:
        decode_bytes = base64.b64decode(indata)
    return [int(x) for x in decode_bytes]


def int_to_listu8(byte_count: int, in_el: int) -> list[int]:
    """int_to_listu8 converts integer to array of u8 bytes.

    :param byte_count: Expected byte count of integer
    :type byte_count: int
    :param in_el: The integer elements
    :type in_el: int
    :raises ValueError: If mismatch on expected and actual byte count
    :return: the integer value converted to list of int (u8)
    :rtype: list[int]
    """
    byte_res = math.ceil(in_el.bit_length() / 8)
    if byte_res == byte_count:
        return list(in_el.to_bytes(byte_res, "little"))
    raise ValueError(f"Expected byte count {byte_count} found byte count {byte_res}")


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
            raise ValueError(
                f"Type {in_data.__class__.__name__}: {in_data.value} is not a valid SuiAddress form."
            )
    elif isinstance(in_data, str):
        if valid_sui_address(in_data):
            result = SuiAddress(in_data)
        else:
            raise ValueError(f"str {in_data} is not a valid SuiAddress form.")
    if not result:
        raise ValueError(
            f"Can not get SuiInteger from {in_data} with type {type(in_data)}"
        )
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
        raise ValueError(
            f"Can not get ObjectID from {in_data} with type {type(in_data)}"
        )
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
    elif isinstance(in_data, SuiNullType):
        result = in_data
    if not result:
        raise ValueError(
            f"Can not get SuiString from {in_data} with type {type(in_data)}"
        )
    return result


def as_sui_integer(in_data: Any) -> Union[SuiInteger, ValueError]:
    """as_sui_integer coerces `in_data` to a SuiInteger.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiInteger
    :rtype: Union[SuiInteger, ValueError]
    """
    result = SuiNullType()
    if isinstance(in_data, SuiInteger):
        result = in_data
    elif isinstance(in_data, int):
        result = SuiInteger(in_data)
    elif isinstance(in_data, str):
        int_only = in_data.split(".")[0]
        result = SuiInteger(int(int_only))
    if not result:
        raise ValueError(
            f"Can not get SuiInteger from {in_data} with type {type(in_data)}"
        )
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
        raise ValueError(
            f"Can not get SuiArray from {in_data} with type {type(in_data)}"
        )
    return result


def as_sui_map(in_data: Any) -> Union[SuiMap, ValueError]:
    """as_sui_map coerces `in_data` to a SuiMap.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiMap
    :rtype: Union[SuiMap, ValueError]
    """
    result = None
    if isinstance(in_data, SuiMap):
        result = in_data
    elif isinstance(in_data, dict):
        result = SuiMap("", "")
        result.map = in_data
    elif isinstance(in_data, SuiNullType):
        result = SuiMap("", "")
        result.map = {}
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
        raise ValueError(
            f"Can not get SuiBoolean from {in_data} with type {type(in_data)}"
        )
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
        raise ValueError(
            f"Can not get {clz.__class__.__name__} from {in_data} with type {type(clz)}"
        )
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
    """as_sui_txdigest coerces `in_data` to a SuiTransactionDigest.

    :param in_data: Data to attempt coercion with
    :type in_data: Any
    :raises ValueError: If `in_data` type is not handled by this utility.
    :return: A SuiTransactionDigest
    :rtype: Union[SuiTransactionDigest, ValueError]
    """
    if isinstance(in_data, SuiTransactionDigest):
        result = in_data
    elif isinstance(in_data, SuiString):
        result = SuiTransactionDigest(in_data.value)
    elif isinstance(in_data, str):
        result = SuiTransactionDigest(in_data)
    if not result:
        raise ValueError(
            f"Can not get SuiTransactionDigest from {in_data} with type {type(in_data)}"
        )
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
    str: {
        SuiAddress,
        ObjectID,
        SuiString,
        SuiInteger,
        SuiBoolean,
        SuiTxBytes,
        SuiSignature,
        SuiTransactionDigest,
    },
    int: {SuiInteger, SuiString, SuiBoolean},
    bytes: {SuiTxBytes, SuiSignature},
    bytearray: {SuiTxBytes, SuiSignature},
    list: {
        SuiArray,
        SuiArray[SuiString],
        SuiArray[SuiAddress],
        SuiArray[BatchParameter],
        SuiArray[ObjectID],
        SuiArray[SuiInteger],
    },
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
    SuiArray[ObjectID]: as_sui_array,
    SuiArray[SuiInteger]: as_sui_array,
    SuiArray[SuiString]: as_sui_array,
    SuiArray[BatchParameter]: as_sui_array,
    SuiArray[SuiAddress]: as_sui_array,
    SuiMap: as_sui_map,
    SuiBoolean: as_sui_boolean,
    SuiSignature: as_sui_signature,
    SuiTxBytes: as_sui_txbytes,
    SuiTransactionDigest: as_sui_txdigest,
    NoneType: lambda x: SuiNullType(),
    Any: lambda x: x,
}

if __name__ == "__main__":
    pass
