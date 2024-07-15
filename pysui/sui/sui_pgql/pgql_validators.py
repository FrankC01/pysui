#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Temporary validations."""

import re
from typing import Union
from deprecated.sphinx import versionchanged

from pysui import PysuiConfiguration
from pysui.sui.sui_constants import SUI_HEX_ADDRESS_STRING_LEN

# owner lengths
"""Length of valid owner string with '0x' prefix."""


class TypeValidator:
    """TypeValidator contains validation classmethods."""

    __partstring_pattern: re.Pattern = re.compile(r"[0-9a-fA-F]{1,64}")

    @versionchanged(version="0.65.0", reason="BREAKING: Uses PysuiConfiguration")
    @classmethod
    def check_owner(
        cls, owner: str, config: PysuiConfiguration
    ) -> Union[str, ValueError]:
        """check_owner Validates owner is well formed Sui Address.

        Owner may be an alias or a string with 0x prefix and up to 64 hex characters

        :param owner: Input data string to validate
        :type owner: str
        :param config: The active PysuiConfiguraiton for alias checking
        :type config: PysuiConfiguration
        :raises ValueError: If not alias and string length not valid for address
        :raises ValueError: Malformed Sui address string
        :return: Validated owner address string
        :rtype: Union[str, ValueError]
        """
        inlen = len(owner)
        assert isinstance(owner, str), "Owner should be str"
        try:
            return config.address_for_alias(alias_name=owner)
        except ValueError:
            pass
        if inlen < 3 or inlen > SUI_HEX_ADDRESS_STRING_LEN:
            raise ValueError("Invalid Sui address string length")

        if owner != "Immutable":
            if owner.startswith("0x") or owner.startswith("0X"):
                vowner = owner[2:]
            else:
                vowner = owner
            re_res = cls.__partstring_pattern.findall(vowner)
            if not re_res or len("".join(re_res)) != len(vowner):
                raise ValueError("Invalid Sui address string")

        return owner

    @classmethod
    def check_object_id(cls, object_id: str) -> Union[str, ValueError]:
        """check_object_id Validates object id is well formed Sui object id string.

        :param object_id: Input data string to validate
        :type object_id: str
        :raises ValueError: Invalid object id string length
        :raises ValueError: If string does not have 0x or 0X prefix
        :raises ValueError: Malformed Sui address string
        :return: Validated object id string
        :rtype: Union[str, ValueError]
        """
        inlen = len(object_id)
        if inlen < 3 or inlen > SUI_HEX_ADDRESS_STRING_LEN:
            raise ValueError("Invalid Sui object id string length")
        if object_id.startswith("0x") or object_id.startswith("0X"):
            vowner = object_id[2:]
        else:
            raise ValueError("Invalid Sui object id prefix")
        re_res = cls.__partstring_pattern.findall(vowner)
        if not re_res or len("".join(re_res)) != len(vowner):
            raise ValueError("Invalid Sui object id string")

        return object_id

    @classmethod
    def check_object_ids(cls, object_ids: list[str]) -> Union[list[str], ValueError]:
        """check_object_ids Validate a list of object_ids

        :param object_ids: List of object id strings
        :type object_ids: list[str]
        :return: List of validated object id strings
        :rtype: Union[list[str], ValueError]
        """
        return [cls.check_object_id(x) for x in object_ids]

    @classmethod
    def check_target_triplet(
        cls, target: str
    ) -> Union[tuple[str, str, str], ValueError]:
        """."""
        if target.count("::") == 2:
            tpars = target.split("::")
            return cls.check_object_id(tpars[0]), tpars[1], tpars[2]
        raise ValueError(f"Malformed target string {target}")
