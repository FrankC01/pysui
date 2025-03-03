#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Validator utilities."""

import argparse
import base64
import binascii
import re
from pathlib import Path
from typing import Any, Sequence
from deprecated.sphinx import versionadded
from pysui.sui.sui_constants import (
    SUI_HEX_ADDRESS_STRING_LEN,
    SUI_MIN_ALIAS_LEN,
    SUI_MAX_ALIAS_LEN,
)


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


class ValidateAlias(argparse.Action):
    """Alias string validator."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        vlen: int = len(values)
        if SUI_MIN_ALIAS_LEN <= vlen <= SUI_MAX_ALIAS_LEN:
            setattr(namespace, self.dest, values)
        else:
            parser.error(
                f"Invalid alias string length, must be betwee {SUI_MIN_ALIAS_LEN} and {SUI_MAX_ALIAS_LEN} characters."
            )
            sys.exit(-1)


class ValidateAddress(argparse.Action):
    """Address validator."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        if isinstance(values, list):
            for va in values:
                if not valid_sui_address(va):
                    parser.error(f"'{values}' contains invlaid Sui address.")
                    sys.exit(-1)
        else:
            if not valid_sui_address(values):
                parser.error(f"'{values}' is not a valid Sui address.")
                sys.exit(-1)
        setattr(namespace, self.dest, values)


class ValidateObjectID(argparse.Action):
    """ObjectID validator."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        if isinstance(values, list):
            for va in values:
                if not valid_sui_address(va):
                    parser.error(f"'{values}' contains invlaid Sui object id format.")
                    sys.exit(-1)
        else:
            if not valid_sui_address(values):
                parser.error(f"'{values}' is not a valid Sui object id format.")
                sys.exit(-1)
        setattr(namespace, self.dest, values)


class ValidatePackageDir(argparse.Action):
    """Validate package directory."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        ppath = Path(values)
        if not ppath.exists():
            parser.error(f"{str(ppath)} does not exist.")
        setattr(namespace, self.dest, ppath)


class ValidateFile(argparse.Action):
    """Validate package directory."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        ppath = Path(values)
        if not ppath.exists():
            parser.error(f"{str(ppath)} does not exist.")
        elif not ppath.is_file():
            parser.error(f"{str(ppath)} is not a file.")
        setattr(namespace, self.dest, ppath)


class ValidateScrOrDir(argparse.Action):
    """Validate package directory."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        if values and values == "con":
            setattr(namespace, self.dest, values)
        else:
            ppath = Path(values)
            if not ppath.exists():
                parser.error(f"{str(ppath)} does not exist.")
            elif not ppath.is_dir():
                parser.error(f"{str(ppath)} is not a folder.")
            setattr(namespace, self.dest, values)


class ValidatePositive(argparse.Action):
    """Validate a positive integer."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        try:
            ivalue = int(values)
            if ivalue >= 0:
                setattr(namespace, self.dest, ivalue)
                return
            parser.error(f"{values} invalid positive int")
        except ValueError as ve:
            parser.error(f"{ve.args[0]}")


class ValidateB64(argparse.Action):
    """Validate base64 string."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        try:
            if isinstance(values, list):
                res = [base64.b64decode(x, validate=True) for x in values]
            else:
                res = base64.b64decode(values, validate=True)
            setattr(namespace, self.dest, values)
        except binascii.Error as bae:
            parser.error(f"{values} invalide base64 string")
