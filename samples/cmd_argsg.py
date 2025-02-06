#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Argument parsing for samples/walletg."""

import argparse
from typing import Optional
from pysui import PysuiConfiguration
import pysui.sui.sui_common.validators as validator
from pysui.sui.sui_types.scalars import SuiString


def _build_read_cmds(subparser) -> None:
    """Read commands."""
    # Address
    subp = subparser.add_parser("active-address", help="Shows active address")
    subp.set_defaults(subcommand="active-address")
    # Addresses
    subp = subparser.add_parser("addresses", help="Shows all addresses")
    subp.add_argument(
        "-d",
        "--details",
        required=False,
        help="Show additional information.",
        action="store_true",
    )

    subp.set_defaults(subcommand="addresses")
    # New address
    subp = subparser.add_parser("new-address", help="Generate new address and keypair")
    addy_arg_group = subp.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument(
        "-e",
        "--ed25519",
        help="Generate using ed25519 scheme",
        action="store_true",
    )
    addy_arg_group.add_argument(
        "-s",
        "--secp256k1",
        help="Generate using secp256k1 scheme",
        action="store_true",
    )
    addy_arg_group.add_argument(
        "-r",
        "--secp256r1",
        help="Generate using secp256r1 scheme",
        action="store_true",
    )
    subp.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias name for new address. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="new-address")
    # Gas
    subp = subparser.add_parser(
        "gas",
        help="Shows gas objects and total mist. If owwner or alias not provided, defaults to active-address.",
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address of gas owner. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of owner address. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="gas")
    # Object
    subp = subparser.add_parser("object", help="Show object by id")
    subp.add_argument("-i", "--id", required=True, action=validator.ValidateObjectID)
    subp.add_argument("-v", "--version", required=False, type=str)
    # subp.add_argument("-j", "--json", required=False, help="Display output as json", action="store_true")
    subp.set_defaults(subcommand="object")
    # Objects
    subp = subparser.add_parser(
        "objects",
        help="Show all objects. If owwner or alias not provided, defaults to active-address.",
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address of objects owner. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of owner address. Optional.",
        action=validator.ValidateAlias,
    )
    subp.add_argument(
        "-j",
        "--json",
        required=False,
        help="Display output as json",
        action="store_true",
    )
    subp.set_defaults(subcommand="objects")


def _build_transfer_cmds(subparser) -> None:
    """Transfer commands."""
    # Transfer SUI
    subp = subparser.add_parser(
        "transfer-object",
        help="Transfer an object from one address to another. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-t",
        "--transfer",
        required=True,
        help="Specify object ID of sui object being transfered",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-r",
        "--recipient",
        required=True,
        help="Specify recipient address to send object to",
        action=validator.ValidateAddress,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify 'transfer-object' transaction budget amount in mists (e.g. 1000). Optional.",
        type=str,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify sui gas object used to pay for the transaction. Optional.",
        action=validator.ValidateObjectID,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="transfer-object")
    # Transfer SUI
    subp = subparser.add_parser(
        "transfer-sui",
        help="Transfer SUI 'mist(s)' to a Sui address. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-t",
        "--takes",
        required=True,
        help="Specify sui gas object to take mists from",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-m",
        "--mists",
        required=True,
        help="Specify amount of MISTs to transfer.",
        type=str,
    )
    subp.add_argument(
        "-r",
        "--recipient",
        required=True,
        help="Specify recipient wallet address to send SUI Mists to",
        action=validator.ValidateAddress,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify 'transfer-sui' transaction budget amount in Mist (e.g. 1000). Optional.",
        type=str,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify sui gas object used to pay for the transaction. Optional.",
        action=validator.ValidateObjectID,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="transfer-sui")


def _build_pay_cmds(subparser) -> None:
    """Pay commands."""
    # Pay
    subp = subparser.add_parser(
        "pay",
        help="Send coin of any type to recipient(s). If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-i",
        "--input-coins",
        required=True,
        nargs="+",
        help="Specify the input coins for each <RECEIPIENT>:<AMOUNTS> to send to",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-m",
        "--mists",
        required=True,
        nargs="+",
        help="Specify amounts of MIST for each <INPUT-COINS> provided.",
        type=str,
    )
    subp.add_argument(
        "-r",
        "--recipients",
        required=True,
        nargs="+",
        help="Specify recipient address for each <AMOUNTS>:<INPUT-COINS> to send to",
        action=validator.ValidateAddress,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify sui gas object used to pay for the transaction. Optional.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify 'pay' transaction budget.Optional.",
        type=str,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="pay")


def _build_coin_cmds(subparser) -> None:
    """Coin commands."""
    # Merge coin
    subp = subparser.add_parser(
        "merge-coin",
        help="Merge two coins together. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-p",
        "--primary-coin",
        required=True,
        help="Specify the primary coin ID to merge into",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-c",
        "--coin-to-merge",
        required=True,
        help="Specify the coin ID to merge from.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify gas object to pay transaction from. Optional.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify 'merge-coin' transaction budget.Optional.",
        type=str,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="merge-coin")
    # Split coin
    subp = subparser.add_parser(
        "split-coin",
        help="Split coin into one or more coins by amount. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-c",
        "--coin_object_id",
        required=True,
        help="Specify the coin ID the split-amounts are being split from.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-m",
        "--mists",
        required=True,
        nargs="+",
        help="Specify mist amounts to split the coin into.",
        type=str,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify gas object to pay transaction from. Optional.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify 'split-coin' transaction budget. Optional.",
        type=str,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="split-coin")
    # Split coin
    subp = subparser.add_parser(
        "split-coin-equally",
        help="Split coin into one or more coins equally. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-c",
        "--coin_object_id",
        required=True,
        help="Specify the coin ID of the coin being split from.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-s",
        "--split_count",
        required=True,
        help="Specify count of coins to split the coin_object_id into.",
        type=str,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify gas object to pay transaction from. Optional.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify transaction budget. Optional.",
        type=str,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="split-coin-equally")


def _build_gql_cmds(subparser) -> None:
    """GraphQL Text file execution."""
    # Query
    subp = subparser.add_parser(
        "gql-query",
        help="Execute a GraphQL query.",
    )
    subp.add_argument(
        "-q",
        "--query-file",
        required=True,
        help="The file containing the query to execute. ",
        action=validator.ValidatePackageDir,
    )
    print_group = subp.add_mutually_exclusive_group(required=False)
    print_group.add_argument(
        "-j",
        "--json",
        required=False,
        help="Output as json",
        action="store_true",
    )
    print_group.add_argument(
        "-p",
        "--pretty",
        required=False,
        help="Output dictionary to pretty print",
        action="store_true",
    )

    subp.set_defaults(subcommand="query")

    # Dry Run Data
    subp = subparser.add_parser(
        "tx-dryrun-data",
        help="Dry run a transaction block (TransactionData).",
    )
    subp.add_argument(
        "-t",
        "--txb",
        required=True,
        help="The base64 transaction block data bytes.",
        action=validator.ValidateB64,
    )
    subp.set_defaults(subcommand="dryrun-data")

    # Dry Run Kind
    subp = subparser.add_parser(
        "tx-dryrun-kind",
        help="Dry run a transaction block kind (TransactionKind).",
    )
    subp.add_argument(
        "-t",
        "--txb",
        required=True,
        help="The base64 transaction block kind bytes. ",
        action=validator.ValidateB64,
    )
    subp.add_argument(
        "--sender",
        required=False,
        help="Optionally set the sender's sui address",
        action=validator.ValidateAddress,
    )
    subp.add_argument(
        "--gas-price",
        required=False,
        help="Optionally set the transaction gas price (in mists)",
        type=int,
    )
    subp.add_argument(
        "--gas-objects",
        required=False,
        nargs="+",
        help="Optionally set the transaction gas objects to use",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "--budget",
        required=False,
        help="Optionally set the transactions budget (in mists)",
        type=int,
    )

    subp.add_argument(
        "--sponsor",
        required=False,
        help="Optionally set the sponsor's sui address",
        action=validator.ValidateAddress,
    )
    subp.set_defaults(subcommand="dryrun-kind")

    # Execute transaction
    subp = subparser.add_parser(
        "execute-signed-tx",
        help="Dry run a transaction block (TransactionData).",
    )
    subp.add_argument(
        "-t",
        "--txb",
        required=True,
        help="The base64 transaction block data bytes.",
        action=validator.ValidateB64,
    )
    subp.add_argument(
        "--signatures",
        required=True,
        nargs="+",
        help="A list of Base64 encoded signatures `flag || signature || pubkey` in base64",
        action=validator.ValidateB64,
    )

    subp.set_defaults(subcommand="execute-tx")


def _build_package_cmds(subparser) -> None:
    """Package commands."""
    # Normalized Package
    subp = subparser.add_parser("package", help="Show normalized package information")
    subp.add_argument(
        "-i",
        "--id",
        required=True,
        help="package ID",
        action=validator.ValidateObjectID,
    )
    subp.set_defaults(subcommand="package")
    # Publish package
    subp = subparser.add_parser(
        "publish",
        help="Publish a SUI package. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-p",
        "--package",
        required=True,
        help="Specify the path to package folder to publish.",
        action=validator.ValidatePackageDir,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify gas object to pay transaction from. Optional.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify transaction budget. Optional.",
        type=str,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )

    subp.set_defaults(subcommand="publish")
    # Move call
    subp = subparser.add_parser(
        "call",
        help="Call a move contract function. If owwner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-p",
        "--package-object-id",
        required=True,
        help="Specify the package ID owner of the move module and function.",
        action=validator.ValidateObjectID,
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
        "--type-arguments",
        required=False,
        nargs="+",
        help="Generic types (if any).",
        type=SuiString,
    )
    subp.add_argument(
        "--args",
        required=False,
        nargs="+",
        help="Function arguments.",
        type=SuiString,
    )
    subp.add_argument(
        "-g",
        "--gas",
        required=False,
        help="Specify gas object to pay transaction from. Optional.",
        action=validator.ValidateObjectID,
    )
    subp.add_argument(
        "-b",
        "--budget",
        required=False,
        help="Specify transaction budget. Optional.",
        type=str,
    )
    addy_arg_group = subp.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address to send/sign with. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of Sui owner. Optional.",
        action=validator.ValidateAlias,
    )
    subp.set_defaults(subcommand="call")


def _build_tx_query_commands(subparser) -> None:
    """Transaction information read commands."""

    # Transaction
    subp = subparser.add_parser(
        "txns",
        help="Show transaction information",
        usage="txns subcommand [--subcommand_options]",
    )
    tcmds = subp.add_subparsers(title="subcommand", required=True)
    # Total count
    esubp = tcmds.add_parser("count", help="Return total transaction count from server")
    esubp.set_defaults(subcommand="txn-count")
    # Transaction
    esubp = tcmds.add_parser("txn", help="Return transaction information")
    esubp.add_argument("-d", "--digest", required=True, help="the transaction's digest")
    esubp.set_defaults(subcommand="txn-txn")


def _build_aliases_cmds(subparser) -> None:
    """Address aliases commands."""
    # Transaction
    subp = subparser.add_parser(
        "aliases",
        help="Sui Address alias management",
        usage="aliases subcommand [--subcommand_options]",
    )
    acmds = subp.add_subparsers(title="subcommand", required=True)
    asubp = acmds.add_parser("list", help="List aliases and associated Sui addresses")
    asubp.set_defaults(subcommand="list-aliases")
    asubp = acmds.add_parser(
        "rename", help="Rename aliases for associated Sui addresses"
    )
    asubp.add_argument(
        "-e",
        "--existing",
        required=True,
        help="Existing alias name",
        action=validator.ValidateAlias,
    )
    asubp.add_argument(
        "-t",
        "--to",
        required=True,
        help="Alias to name",
        action=validator.ValidateAlias,
    )
    asubp.set_defaults(subcommand="rename-aliases")


def _base_parser(
    pconfig: PysuiConfiguration, desc: Optional[str] = None
) -> argparse.ArgumentParser:
    """Basic parser setting for all commands."""
    parser = argparse.ArgumentParser(
        add_help=True,
        usage=desc or "%(prog)s [options] command [--command_options]",
        description="",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--group",
        dest="group_name",
        choices=pconfig.group_names(),
        default=pconfig.active_group.group_name,
        required=False,
        help=f"The GraphQL groups. Default to '{pconfig.active_group_name}'",
    )
    parser.add_argument(
        # "-p",
        "--profile",
        dest="profile_name",
        choices=pconfig.profile_names(),
        default=pconfig.active_profile,
        required=False,
        help=f"The GraphQL profile node. Default to '{pconfig.active_profile}' from '{pconfig.active_group_name}'",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Sets flag to show version. Optional.",
        action="store_true",
    )
    parser.set_defaults(subcommand="version")

    return parser


def build_parser(in_args: list, pconfig: PysuiConfiguration) -> argparse.Namespace:
    """Build the argument parser structure."""
    # Base menu
    parser = _base_parser(pconfig)

    subparser = parser.add_subparsers(title="commands")
    _build_aliases_cmds(subparser)
    _build_read_cmds(subparser)
    _build_coin_cmds(subparser)
    _build_transfer_cmds(subparser)
    _build_pay_cmds(subparser)
    _build_gql_cmds(subparser)
    _build_package_cmds(subparser)
    _build_tx_query_commands(subparser)

    return parser.parse_args(in_args if in_args else ["--help"])


def build_async_gas_parser(
    in_args: list, pconfig: PysuiConfiguration
) -> argparse.Namespace:
    """Build the argument parser structure."""
    # Base menu
    parser = _base_parser(pconfig)
    parser.add_help = True
    parser.usage = "%(prog)s [options]"
    parser.description = "Gather all gas for all objects"
    return parser.parse_args(in_args)


def build_smash_parser(
    in_args: list, pconfig: PysuiConfiguration
) -> argparse.Namespace:
    """smash merges all of an addresses Sui coins to one."""
    parser = _base_parser(pconfig, "smash [options].\n\n" + build_smash_parser.__doc__)
    parser.add_argument(
        "-i",
        "--include",
        nargs="+",
        help="Includes these coins explicitly to smash together",
        action=validator.ValidateAddress,
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        help="Exclude these coins from smash list",
        action=validator.ValidateAddress,
    )
    addy_arg_group = parser.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        help="Sui address of gas owner. Mutually exclusive with '-a/--alias",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        help="Alias of owner address.Mutually exclusive with '-o/--owner",
        action=validator.ValidateAlias,
    )
    parser.add_argument(
        "-w",
        "--wait",
        required=False,
        help="Sets flag to wait for transaction commitment. Optional.",
        action="store_true",
    )

    return parser.parse_args(in_args if in_args else ["--help"])


def build_splay_parser(
    in_args: list, pconfig: PysuiConfiguration
) -> argparse.Namespace:
    """splay spreads all, selected coins or count evenly to itself or other addresses."""
    parser = _base_parser(pconfig, "splay [options].\n\n" + build_splay_parser.__doc__)
    addy_arg_group = parser.add_mutually_exclusive_group(required=False)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        help="Sui address of gas owner. Mutually exclusive with '-a/--alias",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        help="Alias of owner address.Mutually exclusive with '-o/--owner",
        action=validator.ValidateAlias,
    )
    parser.add_argument(
        "-i",
        "--include",
        nargs="+",
        help="Includes these coins explicitly for smashing step before splaying",
        action=validator.ValidateAddress,
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        help="Excludes these coins from smashing step before splaying",
        action=validator.ValidateAddress,
    )

    parser.add_argument(
        "-m",
        "--mist",
        help="Amount of mist per split. Either expresses as mists `nnn` or Sui `1S`, `1s`",
    )
    dest_arg_group = parser.add_mutually_exclusive_group(required=False)
    dest_arg_group.add_argument(
        "-n",
        "--number",
        help="marges all or -c owner coins then splays into 'n' coins to itself. Mutually exclusive with '-r/--recipients",
        action=validator.ValidatePositive,
    )
    dest_arg_group.add_argument(
        "-r",
        "--recipients",
        nargs="+",
        help="merges all or -c owner coins then splays evenly to these recipients. Mutually exclusive with '-n/--number",
        action=validator.ValidateAddress,
    )
    parser.add_argument(
        "-b",
        "--budget",
        required=False,
        default=10_000_000,
        help="Budget reserved to execute splay. Optional - defaults to 10_000_000 mists.",
        action=validator.ValidatePositive,
    )
    parser.add_argument(
        "-w",
        "--wait",
        required=False,
        help="Sets flag to wait for transaction commitment. Optional.",
        action="store_true",
    )
    return parser.parse_args(in_args if in_args else ["--help"])
