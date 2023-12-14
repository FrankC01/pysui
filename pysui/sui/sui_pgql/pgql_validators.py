#

"""Temporary validations."""

import re
from typing import Union

# Address lengths
SUI_HEX_STRING_LEN: int = 66
"""Length of valid address string with '0x' prefix."""


class TypeValidator:
    """TypeValidator contains validation classmethods."""

    __partstring_pattern: re.Pattern = re.compile(r"[0-9a-fA-F]{1,64}")

    @classmethod
    def check_address(cls, address: str) -> Union[str, ValueError]:
        """."""
        inlen = len(address)
        if inlen < 3 or inlen > SUI_HEX_STRING_LEN:
            raise ValueError("Invalid Sui address")

        if address != "Immutable":
            if address.startswith("0x") or address.startswith("0X"):
                vaddress = address[2:]
            else:
                vaddress = address
            re_res = cls.__partstring_pattern.findall(vaddress)
            if not re_res or len("".join(re_res)) != len(vaddress):
                raise ValueError("Invalid Sui address")

        return address

    @classmethod
    def check_object_id(cls, object_id: str) -> Union[str, ValueError]:
        """."""
        inlen = len(object_id)
        if inlen < 3 or inlen > SUI_HEX_STRING_LEN:
            raise ValueError("Invalid Sui object id")
        if object_id.startswith("0x") or object_id.startswith("0X"):
            vaddress = object_id[2:]
        else:
            raise ValueError("Invalid Sui object id")
        re_res = cls.__partstring_pattern.findall(vaddress)
        if not re_res or len("".join(re_res)) != len(vaddress):
            raise ValueError("Invalid Sui object id")

        return object_id

    @classmethod
    def check_object_ids(cls, object_ids: list[str]) -> Union[list[str], ValueError]:
        """."""
        return [TypeValidator.check_object_id(x) for x in object_ids]
