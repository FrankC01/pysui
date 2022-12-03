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

"""Argparse validators for sample script reuse."""

import sys
import argparse
from pathlib import Path
from typing import Any, Sequence
from pysui.sui.sui_types import ObjectID, SuiInteger, SuiAddress


def check_positive(value: str) -> int:
    """Check for positive integers."""
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return SuiInteger(ivalue)


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
        try:
            if isinstance(values, list):
                values = [SuiAddress.from_hex_string(v) for v in values]
            else:
                values = SuiAddress.from_hex_string(values)
        except ValueError:
            parser.error(f"'{values}' is not valid address.")
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
        try:
            if isinstance(values, list):
                values = [ObjectID(v) for v in values]
            else:
                values = ObjectID(values)
        except ValueError:
            parser.error(f"'{values}' is not valid address.")
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
        if not ppath.exists:
            parser.error(f"{str(ppath)} does not exist.")
        setattr(namespace, self.dest, ppath)
