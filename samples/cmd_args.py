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


"""Argument parsing."""
import argparse
import sys
from pathlib import Path
from typing import Any, Sequence
from pysui.sui.sui_types import ObjectID, SuiNumber, SuiAddress, SuiString


def check_positive(value: str) -> int:
    """Check for positive integers."""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return SuiNumber(ivalue)


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


def build_parser(in_args: list) -> argparse.Namespace:
    """Build the argument parser structure."""
    # Base menu
    parser = argparse.ArgumentParser(add_help=True)
    subparser = parser.add_subparsers(title="commands")

    # Address
    subp = subparser.add_parser("active-address", help="Shows active address")
    subp.set_defaults(subcommand="active-address")

    # Addresses
    subp = subparser.add_parser("addresses", help="Shows all addresses")
    subp.set_defaults(subcommand="addresses")
    # Gas
    subp = subparser.add_parser("gas", help="Shows gas objects")
    subp.add_argument("--address", required=False, help="Gas for address", action=ValidateAddress)
    subp.set_defaults(subcommand="gas")
    # New address
    subp = subparser.add_parser("new-address", help="Generate new address and keypair")
    addy_arg_group = subp.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument("-e", "--ed25519", help="Generate using ed25519 scheme", action="store_true")
    addy_arg_group.add_argument("-s", "--secp256k1", help="Generate using secp256k1 scheme", action="store_true")
    subp.set_defaults(subcommand="new-address")
    # Object
    subp = subparser.add_parser("object", help="Show object by id")
    subp.add_argument("--id", required=True, action=ValidateObjectID)
    subp.add_argument("--json", required=False, help="Display output as json", action="store_true")
    subp.set_defaults(subcommand="object")
    # Objects
    subp = subparser.add_parser("objects", help="Show all objects")
    subp.add_argument("--address", required=False, help="Objects for address", action=ValidateAddress)
    subp.add_argument("--json", required=False, help="Display output as json", action="store_true")
    obj_arg_group = subp.add_mutually_exclusive_group()
    obj_arg_group.add_argument("--nft", help="Only show NFT objects", action="store_true")
    obj_arg_group.add_argument("--data", help="Only show data objects", action="store_true")
    subp.set_defaults(subcommand="objects")
    # Package Object
    subp = subparser.add_parser("package-object", help="Get raw package object with Move disassembly")
    subp.add_argument("--id", required=True, help="package ID", action=ValidateObjectID)
    subp.add_argument("--src", required=False, help="Display package module(s) src", action="store_true")
    subp.set_defaults(subcommand="package-object")

    # Normalized Package
    subp = subparser.add_parser("package", help="Get package definition")
    subp.add_argument("--id", required=True, help="package ID", action=ValidateObjectID)
    subp.set_defaults(subcommand="package")
    # RPC information
    subp = subparser.add_parser("rpcapi", help="Display Sui RPC API information")
    subp.add_argument("-n", "--name", required=False, help="Display details for named Sui RPC API")
    subp.set_defaults(subcommand="rpcapi")
    # Transfer SUI
    subp = subparser.add_parser("transfer-sui", help="Transfer SUI gas to recipient")
    subp.add_argument(
        "-a",
        "--amount",
        required=True,
        help="Specify amount of MISTs to transfer.",
        type=check_positive,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to transfer from", action=ValidateObjectID
    )
    subp.add_argument(
        "-r",
        "--recipient",
        required=True,
        help="Specify recipient wallet address to send SUI Mists to",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'transfer-sui' transaction budget amount in Mist (e.g. 1000)",
        type=check_positive,
    )
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify gas owner address for signing. Default to active address",
        action=ValidateAddress,
    )
    subp.set_defaults(subcommand="transfer-sui")
    # Pays
    subp = subparser.add_parser("pay", help="Transfer SUI gas to recipient(s)")
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify pay signer address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-i",
        "--input-coins",
        required=True,
        nargs="+",
        help="Specify the input coins for each <RECEIPIENT>:<AMOUNTS> to send to",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-a",
        "--amounts",
        required=True,
        nargs="+",
        help="Specify amounts of MIST for each <INPUT-COINS> provided.",
        type=check_positive,
    )
    subp.add_argument(
        "-r",
        "--recipients",
        required=True,
        nargs="+",
        help="Specify recipient address for each <AMOUNTS>:<INPUT-COINS> to send to",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to transfer from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'pay' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="pay")
    # Merge coin
    subp = subparser.add_parser("merge-coin", help="Merge two coins together")
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify merge-coin signer address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-p",
        "--primary-coin",
        required=True,
        help="Specify the primary coin ID to merge into",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-c",
        "--coin-to-merge",
        required=True,
        help="Specify the coin ID to merge from.",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to pay transaction from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'merge-coin' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="merge-coin")
    # Split coin
    subp = subparser.add_parser("split-coin", help="Split coin into one or more coins")
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify split-coin signer address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-c",
        "--coin_object_id",
        required=True,
        help="Specify the coin ID the split-amounts are being split from.",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-a",
        "--split_amounts",
        required=True,
        nargs="+",
        help="Specify amounts to split the coin into.",
        type=check_positive,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to pay transaction from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'split-coin' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="split-coin")
    # Move call
    subp = subparser.add_parser("call", help="Call a move contract function")
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify split-coin signer address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-p",
        "--package",
        required=True,
        help="Specify the package ID owner of the move module and function.",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-m",
        "--module",
        required=True,
        help="Specify the module name in the package.",
        type=SuiString,
    )
    subp.add_argument(
        "-f",
        "--function",
        required=True,
        help="Specify the function name in the module.",
        type=SuiString,
    )
    subp.add_argument(
        "-t",
        "--types",
        required=False,
        nargs="+",
        help="Generic types (if any).",
        type=SuiString,
    )
    subp.add_argument(
        "-a",
        "--arguments",
        required=False,
        nargs="+",
        help="Function arguments.",
        type=SuiString,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to pay transaction from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'split-coin' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="call")
    # Publish call
    subp = subparser.add_parser("publish", help="Publish a SUI package")
    subp.add_argument(
        "-s",
        "--sender",
        required=False,
        help="Specify publish sender address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-c",
        "--compiled_modules",
        required=True,
        help="Specify the path to package folder containing compiled modules to publish.",
        action=ValidatePackageDir,
    )
    subp.add_argument(
        "-o", "--gas", required=True, help="Specify gas object to pay transaction from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'split-coin' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="publish")
    return parser.parse_args(in_args if in_args else ["--help"])
