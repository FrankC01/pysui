"""Argument parsing."""
import argparse
import pathlib
import sys
from typing import Any, Sequence
from pysui.sui.sui_types import ObjectID, SuiNumber, SuiAddress


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
            sys.exit(-1)
        setattr(namespace, self.dest, values)


class ValidateFile(argparse.Action):
    """File validator."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = ...,
    ) -> None:
        """Validate."""
        fpath = pathlib.Path(values)

        if fpath.exists():
            setattr(namespace, self.dest, fpath)
        else:
            parser.error(f"{values} does not exist")
            sys.exit(-1)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser structure."""
    # Base menu
    parser = argparse.ArgumentParser(add_help=True)
    # parser.add_argument("--client", required=False, help="Set client.yaml configuration path", action=ValidateFile)
    subparser = parser.add_subparsers(title="commands")

    # Address
    subp = subparser.add_parser("active-address", help="Shows active address", parents=[parser], add_help=False)
    subp.set_defaults(subcommand="active-address")

    # Addresses
    subp = subparser.add_parser("addresses", help="Shows all addresses", parents=[parser], add_help=False)
    subp.set_defaults(subcommand="addresses")
    # Gas
    subp = subparser.add_parser("gas", help="Shows gas objects", parents=[parser], add_help=False)
    subp.add_argument("--address", required=False, help="Gas for address", action=ValidateAddress)
    subp.set_defaults(subcommand="gas")
    # New address
    subp = subparser.add_parser(
        "new-address", help="Generate new address and keypair", parents=[parser], add_help=False
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument("-e", "--ed25519", help="Generate using ed25519 scheme", action="store_true")
    addy_arg_group.add_argument("-s", "--secp256k1", help="Generate using secp256k1 scheme", action="store_true")
    subp.set_defaults(subcommand="new-address")
    # Object
    subp = subparser.add_parser("object", help="Show object by id", parents=[parser], add_help=False)
    subp.add_argument("--id", required=True, action=ValidateObjectID)
    subp.add_argument("--json", required=False, help="Display output as json", action="store_true")
    subp.set_defaults(subcommand="object")
    # Objects
    subp = subparser.add_parser("objects", help="Show all objects", parents=[parser], add_help=False)
    subp.add_argument("--address", required=False, help="Objects for address", action=ValidateAddress)
    subp.add_argument("--json", required=False, help="Display output as json", action="store_true")
    obj_arg_group = subp.add_mutually_exclusive_group()
    obj_arg_group.add_argument("--nft", help="Only show NFT objects", action="store_true")
    obj_arg_group.add_argument("--data", help="Only show data objects", action="store_true")
    subp.set_defaults(subcommand="objects")
    # Package Object
    subp = subparser.add_parser(
        "package-object", help="Get raw package object with Move disassembly", parents=[parser], add_help=False
    )
    subp.add_argument("--id", required=True, help="package ID", action=ValidateObjectID)
    subp.add_argument("--src", required=False, help="Display package module(s) src", action="store_true")
    subp.set_defaults(subcommand="package-object")

    # Normalized Package
    subp = subparser.add_parser("package", help="Get package definition", parents=[parser], add_help=False)
    subp.add_argument("--id", required=True, help="package ID", action=ValidateObjectID)
    subp.set_defaults(subcommand="package")
    # RPC information
    subp = subparser.add_parser("rpcapi", help="Display Sui RPC API information", parents=[parser], add_help=False)
    subp.add_argument("-n", "--name", required=False, help="Display details for named Sui RPC API")
    subp.set_defaults(subcommand="rpcapi")
    # Transfer SUI
    subp = subparser.add_parser("transfer-sui", help="Transfer SUI gas to recipient", parents=[parser], add_help=False)
    subp.add_argument(
        "-a",
        "--amount",
        required=True,
        help="Specify amount of MIST to transfer.",
        type=check_positive,
    )
    subp.add_argument(
        "-o", "--gas-object", required=True, help="Specify gas object to transfer from", action=ValidateObjectID
    )
    subp.add_argument(
        "-r",
        "--recipient",
        required=True,
        help="Specify recipient address to send gas to",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'transfer-sui' transaction budget",
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
    subp = subparser.add_parser("pay", help="Transfer SUI gas to recipient(s)", parents=[parser], add_help=False)
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
    subp = subparser.add_parser("merge-coin", help="Merge two coins together", parents=[parser], add_help=False)
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
    subp = subparser.add_parser(
        "split-coin", help="Split coin into one or more coins", parents=[parser], add_help=False
    )
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

    return parser
