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
from pysui.abstracts import Builder

from pysui.sui.sui_excepts import SuiRpcApiInvalidParameter
from pysui.sui.sui_apidesc import SuiApi, SuiApiParam
from pysui.sui.sui_types import SuiArray

__partstring_pattern = re.compile(r"[0-9a-fA-F]{38}")
__fullstring_pattern = re.compile(r"0[xX][0-9a-fA-F]{40}")


def __validate_parameter(build_parm: Any, api_parm: SuiApiParam) -> Union[tuple[str, str], SuiRpcApiInvalidParameter]:
    """Validate the specific parameter."""
    # from .sui_types import SuiArray

    schema_name = type(build_parm).__name__
    att = getattr(build_parm, api_parm.name)
    match api_parm.schema.type:
        case "array":
            if isinstance(att, SuiArray):
                att = [getattr(x, api_parm.name) for x in att.array]
            elif isinstance(att, list) and api_parm.name != "single_transaction_params":
                att = [getattr(x, api_parm.name) for x in att]
            elif isinstance(att, list) and api_parm.name == "single_transaction_params":
                pass
            else:
                raise ValueError(f"{api_parm.name} requires SuiArray")
        case _:
            pass
    # if isinstance(att, list) and api_parm.name != "single_transaction_params":
    #     att = [getattr(x, api_parm.name) for x in att]

    # print(f"att {api_parm.name} = {att}")
    if att is None and api_parm.required:
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
