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
import base64
import binascii
import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union
from deprecated.sphinx import versionchanged, versionadded
import base58
from pysui.sui.sui_common.instrumentation import instrumented, sync_instrumented


_SUI_BUILD2: list[str] = ["move", "build", "--dump", "-e"]



@dataclass
@versionadded(version="0.96.0", reason="New package manager approach.")
class CompiledPackage:
    """Ease of compilation information dataclass."""

    project_source_digest: bytes = None
    dependencies: list[str] = None
    compiled_modules: list[bytes] = None
    package_digest: list[int] = None




@versionadded(version="0.96.0", reason="New package manager approach.")
@sync_instrumented("pysui.sui.sui_utils._compile_projectg2")
def _compile_projectg2(
    sui_bin_str: str, path_to_package: Path, args_list: list[str], build_env: str
) -> CompiledPackage:
    """_compile_projectg Compiles a sui move project in GraohQL environment."""
    mbs = _SUI_BUILD2.copy()
    mbs.append(build_env)
    mbs.extend(args_list)
    mbs.append("-p")
    mbs.append(path_to_package)

    mbs.insert(0, sui_bin_str)
    result = subprocess.run(mbs, capture_output=True, text=True)
    if result.returncode == 0:
        jsonb = json.loads(result.stdout)
        return CompiledPackage(
            dependencies=jsonb["dependencies"],
            compiled_modules=[list(base64.b64decode(x)) for x in jsonb["modules"]],
            project_source_digest=jsonb["digest"],
        )
    raise RuntimeError(result.stdout)







@versionadded(version="0.96.0", reason="New package manager approach.")
@sync_instrumented("pysui.sui.sui_utils.publish_buildg2")
def publish_buildg2(
    sui_bin_path_str: str, path_to_package: Path, args_list: list[str], build_env: str
) -> Union[CompiledPackage, Exception]:
    """Build and collect module base64 strings and dependencies ObjectIDs."""
    # Compile the package
    cpackage = _compile_projectg2(
        sui_bin_path_str, path_to_package, args_list, build_env
    )

    cpackage.package_digest = bytes(cpackage.project_source_digest)

    # _package_digestg2(cpackage)
    return cpackage



# Serialize helper
@sync_instrumented("pysui.sui.sui_utils.serialize_uint32_as_uleb128")
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


@sync_instrumented("pysui.sui.sui_utils.partition")
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


@sync_instrumented("pysui.sui.sui_utils.hexstring_to_sui_id")
def hexstring_to_sui_id(indata: str, default_fill_length: int = 64) -> str:
    """Convert hexstring to valid full length sui address/object id."""

    if len(indata) < default_fill_length:
        if indata.count("x") or indata.count("X"):
            indata = indata[2:]
        indata = f"0x{indata.zfill(default_fill_length)}"
    return indata


@versionchanged(version="0.19.0", reason="Account for > 3 and < 66 size hex string")
@sync_instrumented("pysui.sui.sui_utils.hexstring_to_list")
def hexstring_to_list(indata: str, default_fill_length: int = 64) -> list[int]:
    """hexstring_to_list convert a hexstr (e.g. 0x...) into a list of ints.

    :param indata: Data to conver to list of ints
    :type indata: str
    :return: converted indata to int list
    :rtype: list[int]
    """
    return [int(x) for x in binascii.unhexlify(hexstring_to_sui_id(indata)[2:])]



@sync_instrumented("pysui.sui.sui_utils.from_list_to_b58str")
def from_list_to_b58str(indata: list) -> str:
    """From list to b58 string."""
    return base58.b58encode(bytearray(indata)).decode("utf-8")


@sync_instrumented("pysui.sui.sui_utils.b58str_to_list")
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





if __name__ == "__main__":
    pass
