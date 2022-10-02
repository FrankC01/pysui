"""Sui Transaction validator."""

import re
from typing import Any
from sui.sui_constants import SUI_ADDRESS_STRING_LEN, SUI_HEX_ADDRESS_STRING_LEN
from sui.sui_excepts import SuiRpcApiInvalidParameter
from sui.sui_builders import BaseBuilder
from sui.sui_apidesc import SuiApi, SuiApiParam

__partstring_pattern = re.compile(r"[0-9a-fA-F]{38}")
__fullstring_pattern = re.compile(r"0[xX][0-9a-fA-F]{40}")


def valid_sui_address(instr: str) -> bool:
    """Verify Sui address string."""
    inlen = len(instr)
    if inlen > SUI_HEX_ADDRESS_STRING_LEN or inlen < SUI_ADDRESS_STRING_LEN:
        return False
    # _kp = keypair_from_keystring(instr)
    if inlen == SUI_HEX_ADDRESS_STRING_LEN and __fullstring_pattern.findall(instr):
        return True
    return __partstring_pattern.findall(instr)


def __identifer_extractor(build_parm: Any, api_parm: SuiApiParam) -> tuple[str, str]:
    """Pull argument type and builder value."""
    return (api_parm.schema.type_path[0], str(build_parm.identifier))


def __validate_parameter(build_parm: Any, api_parm: SuiApiParam) -> tuple[str, str]:
    """Validate the specific parameter."""
    schema_name = type(build_parm).__name__
    if schema_name in api_parm.schema.type_path:
        match schema_name:
            case "ObjectID":
                return (schema_name, str(build_parm))
            case "SuiAddress":
                return __identifer_extractor(build_parm, api_parm)
            case _:
                raise ValueError(f"No validator for {schema_name}")
    return None


def _parameter_check(api_method: SuiApi, builder: BaseBuilder) -> list[tuple[str, str]]:
    """Perform parameter validations."""
    # All calls take at least 1 parameter
    parmlen = len(api_method.params)
    if not builder.params or (len(builder.params) != parmlen):
        raise SuiRpcApiInvalidParameter(
            f"Expected {len(api_method.params)} parameters for {builder.method} but found {parmlen}"
        )

    results = []
    index = 0
    while index < parmlen:
        vres = __validate_parameter(builder.params[index], api_method.params[index])
        if not vres:
            raise SuiRpcApiInvalidParameter(f"{builder.params[index]} => {api_method.params[index]}")
        results.append(vres)
        index = index + 1
    return results


def validate_api(api_method: SuiApi, builder: BaseBuilder) -> list[tuple[str, str]]:
    """Validate the API parameters and arguments."""
    # print(f"Validating against {api_method}")
    return _parameter_check(api_method, builder)
