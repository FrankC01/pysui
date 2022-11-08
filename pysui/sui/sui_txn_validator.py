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


"""Sui Transaction validator."""

import re
from typing import Any, Union
from ..abstracts import Builder
from .sui_constants import SUI_ADDRESS_STRING_LEN, SUI_HEX_ADDRESS_STRING_LEN
from .sui_excepts import SuiRpcApiInvalidParameter
from .sui_apidesc import SuiApi, SuiApiParam

__partstring_pattern = re.compile(r"[0-9a-fA-F]{38}")
__fullstring_pattern = re.compile(r"0[xX][0-9a-fA-F]{40}")


def valid_sui_address(instr: str) -> bool:
    """Verify Sui address string."""
    inlen = len(instr)
    if instr == "0x2":
        return True
    if instr == "Immutable":
        return True
    if inlen > SUI_HEX_ADDRESS_STRING_LEN or inlen < SUI_ADDRESS_STRING_LEN:
        return False
    # _kp = keypair_from_keystring(instr)
    if inlen == SUI_HEX_ADDRESS_STRING_LEN and __fullstring_pattern.findall(instr):
        return True
    return __partstring_pattern.findall(instr)


def __validate_parameter(build_parm: Any, api_parm: SuiApiParam) -> Union[tuple[str, str], SuiRpcApiInvalidParameter]:
    """Validate the specific parameter."""
    from .sui_types import SuiArray

    schema_name = type(build_parm).__name__
    att = getattr(build_parm, api_parm.name)
    if isinstance(build_parm, SuiArray):
        att = [getattr(x, api_parm.name) for x in att]

    # print(f"att {api_parm.name} = {att}")
    if att is None:
        raise SuiRpcApiInvalidParameter(f"builder {build_parm} does not have attribute {api_parm.name}")
    return (schema_name, att)


def _parameter_check(api_method: SuiApi, builder: Builder) -> Union[tuple[str, str], SuiRpcApiInvalidParameter]:
    """Perform parameter validations."""
    # All calls take at least 1 parameter
    parmlen = len(api_method.params)
    build_parms = builder.params
    if len(build_parms) != parmlen:
        raise SuiRpcApiInvalidParameter(
            f"API Expected {parmlen} parameters for {builder.method} but found {len(build_parms)}"
        )

    results = []
    index = 0
    while index < parmlen:
        vres = __validate_parameter(build_parms[index], api_method.params[index])
        results.append(vres)
        index = index + 1
    return results


def validate_api(api_method: SuiApi, builder: Builder) -> Union[tuple[str, str], SuiRpcApiInvalidParameter]:
    """Validate the API parameters and arguments."""
    return _parameter_check(api_method, builder)
