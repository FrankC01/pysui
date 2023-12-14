#

"""Temporary validations."""

import re
from typing import Union
from pysui.sui.sui_constants import SUI_HEX_ADDRESS_STRING_LEN

# owner lengths
"""Length of valid owner string with '0x' prefix."""


class TypeValidator:
    """TypeValidator contains validation classmethods."""

    __partstring_pattern: re.Pattern = re.compile(r"[0-9a-fA-F]{1,64}")

    @classmethod
    def check_owner(cls, owner: str) -> Union[str, ValueError]:
        """."""
        inlen = len(owner)
        if inlen < 3 or inlen > SUI_HEX_ADDRESS_STRING_LEN:
            raise ValueError("Invalid Sui owner")

        if owner != "Immutable":
            if owner.startswith("0x") or owner.startswith("0X"):
                vowner = owner[2:]
            else:
                vowner = owner
            re_res = cls.__partstring_pattern.findall(vowner)
            if not re_res or len("".join(re_res)) != len(vowner):
                raise ValueError("Invalid Sui owner")

        return owner

    @classmethod
    def check_object_id(cls, object_id: str) -> Union[str, ValueError]:
        """."""
        inlen = len(object_id)
        if inlen < 3 or inlen > SUI_HEX_ADDRESS_STRING_LEN:
            raise ValueError("Invalid Sui object id")
        if object_id.startswith("0x") or object_id.startswith("0X"):
            vowner = object_id[2:]
        else:
            raise ValueError("Invalid Sui object id")
        re_res = cls.__partstring_pattern.findall(vowner)
        if not re_res or len("".join(re_res)) != len(vowner):
            raise ValueError("Invalid Sui object id")

        return object_id

    @classmethod
    def check_object_ids(cls, object_ids: list[str]) -> Union[list[str], ValueError]:
        """."""
        return [TypeValidator.check_object_id(x) for x in object_ids]
