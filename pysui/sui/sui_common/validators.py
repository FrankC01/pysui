#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Validator utilities."""

import re
from deprecated.sphinx import versionadded
from pysui.sui.sui_constants import SUI_HEX_ADDRESS_STRING_LEN


__partstring_pattern: re.Pattern = re.compile(r"[0-9a-fA-F]{1,64}")


@versionadded(
    version="0.76.0",
    reason="Addresses can be between 3 and 66 chars with prefix, 1 and 64 without.",
)
def valid_sui_address(instr: str) -> bool:
    """Verify Sui address string."""
    inlen = len(instr)
    if not instr or inlen > SUI_HEX_ADDRESS_STRING_LEN:
        return False
    match instr:
        case "Immutable":
            return True
        case _:
            if inlen < 3 and (instr.count("x") or instr.count("X")):
                return False
            if instr.count("x") or instr.count("X"):
                instr = instr[2:]
            re_res = __partstring_pattern.findall(instr)
            if re_res:
                if len("".join(re_res)) == len(instr):
                    return True
            return False
