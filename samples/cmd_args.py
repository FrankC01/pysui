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


"""Argument parsing for samples/wallet."""
import argparse
from cmd_arg_validators import ValidateObjectID, ValidateAddress, ValidatePackageDir, check_positive
from pysui.sui.sui_types.scalars import SuiString, SuiNullType


def _build_read_cmds(subparser) -> None:
    """Read commands."""
    # Address
    subp = subparser.add_parser("active-address", help="Shows active address")
    subp.set_defaults(subcommand="active-address")
    # Addresses
    subp = subparser.add_parser("addresses", help="Shows all addresses")
    subp.set_defaults(subcommand="addresses")
    # New address
    subp = subparser.add_parser("new-address", help="Generate new address and keypair")
    addy_arg_group = subp.add_mutually_exclusive_group(required=True)
    addy_arg_group.add_argument("-e", "--ed25519", help="Generate using ed25519 scheme", action="store_true")
    addy_arg_group.add_argument("-s", "--secp256k1", help="Generate using secp256k1 scheme", action="store_true")
    subp.set_defaults(subcommand="new-address")
    # Gas
    subp = subparser.add_parser("gas", help="Shows gas objects and total mist")
    subp.add_argument("-a", "--address", required=False, help="Gas for address", action=ValidateAddress)
    subp.set_defaults(subcommand="gas")
    # Object
    subp = subparser.add_parser("object", help="Show object by id")
    subp.add_argument("-i", "--id", required=True, action=ValidateObjectID)
    subp.add_argument("-v", "--version", required=False, type=check_positive)
    # subp.add_argument("-j", "--json", required=False, help="Display output as json", action="store_true")
    subp.set_defaults(subcommand="object")
    # Objects
    subp = subparser.add_parser("objects", help="Show all objects")
    subp.add_argument("-a", "--address", required=False, help="Objects for address", action=ValidateAddress)
    subp.add_argument("-j", "--json", required=False, help="Display output as json", action="store_true")
    obj_arg_group = subp.add_mutually_exclusive_group()
    obj_arg_group.add_argument("-d", "--data", help="Only show data objects", action="store_true")
    subp.set_defaults(subcommand="objects")
    # RPC information
    subp = subparser.add_parser("rpcapi", help="Show Sui RPC API information")
    subp.add_argument("-n", "--name", required=False, help="Display details for named Sui RPC API")
    subp.set_defaults(subcommand="rpcapi")
    # Committee info
    subp = subparser.add_parser("committee", help="Show committee info for epoch")
    subp.add_argument(
        "-e",
        "--epoch",
        required=False,
        help="The epoch of interest. If None, default to the latest epoch",
        type=check_positive,
    )
    subp.set_defaults(subcommand="committee")
    # Faucet usage
    subp = subparser.add_parser("faucet", help="Get additional gas from SUI faucet")
    subp.add_argument(
        "-a",
        "--address",
        required=False,
        help="The address to transfer gas to. If None, defaults to the active-address",
        action=ValidateAddress,
    )
    subp.set_defaults(subcommand="faucet")


def _build_transfer_cmds(subparser) -> None:
    """Transfer commands."""
    # Transfer SUI
    subp = subparser.add_parser("transfer-object", help="Transfer an object from one address to another")
    subp.add_argument(
        "-d",
        "--object-id",
        required=True,
        help="Specify sui object being transfered",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-o",
        "--gas",
        required=True,
        help="Specify sui gas object paying for the transaction",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-r",
        "--recipient",
        required=True,
        help="Specify recipient address to send object to",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'transfer-object' transaction budget amount in mists (e.g. 1000)",
        type=check_positive,
    )
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify gas owner address for signing. Default to active address",
        action=ValidateAddress,
    )
    subp.set_defaults(subcommand="transfer-object")
    # Transfer SUI
    subp = subparser.add_parser("transfer-sui", help="Transfer SUI 'mist(s)' to a Sui address")
    subp.add_argument(
        "-a",
        "--amount",
        required=True,
        help="Specify amount of MISTs to transfer.",
        type=check_positive,
    )
    subp.add_argument(
        "-o",
        "--sui-object-id",
        required=True,
        help="Specify sui gas object to transfer from",
        action=ValidateObjectID,
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


def _build_pay_cmds(subparser) -> None:
    """Pay commands."""
    # Pay
    subp = subparser.add_parser("pay", help="Send coin of any type to recipient(s)")
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
    subp.add_argument("-o", "--gas", required=True, help="Specify gas object to transfer from", action=ValidateObjectID)
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'pay' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="pay")
    # PaySui
    subp = subparser.add_parser("paysui", help="Send SUI coins to a list of addresses.")
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
        help="Specify the input sui coins for each <RECEIPIENT>:<AMOUNTS> to send to",
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
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'pay' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="paysui")
    # PayAllSui
    subp = subparser.add_parser("payallsui", help="Send all SUI coin(s) to recipient(s)")
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
        help="Specify the sui coins to use, including transaction payment",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-r",
        "--recipient",
        required=True,
        help="Specify recipient address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify 'pay' transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="payallsui")


def _build_package_cmds(subparser) -> None:
    """Package commands."""
    # Normalized Package
    subp = subparser.add_parser("package", help="Show normalized package information")
    subp.add_argument("-i", "--id", required=True, help="package ID", action=ValidateObjectID)
    subp.set_defaults(subcommand="package")
    # Publish package
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
        help="Specify transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="publish")
    # Move call
    subp = subparser.add_parser("call", help="Call a move contract function")
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify SUI call signer address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-p",
        "--package-object-id",
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
        "--type-arguments",
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
        "-o", "--gas", required=True, help="Specify gas object to pay transaction from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="call")


def _build_coin_cmds(subparser) -> None:
    """Coin commands."""
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
    subp = subparser.add_parser("split-coin", help="Split coin into one or more coins by amount")
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
    # Split coin
    subp = subparser.add_parser("split-coin-equally", help="Split coin into one or more coins equally")
    subp.add_argument(
        "-s",
        "--signer",
        required=False,
        help="Specify split-coin-equally signer address. Default to active address",
        action=ValidateAddress,
    )
    subp.add_argument(
        "-c",
        "--coin_object_id",
        required=True,
        help="Specify the coin ID of the coin being split from.",
        action=ValidateObjectID,
    )
    subp.add_argument(
        "-a",
        "--split_count",
        required=True,
        help="Specify count of coins to split the coin_object_id into.",
        type=check_positive,
    )
    subp.add_argument(
        "-o", "--gas", required=True, help="Specify gas object to pay transaction from", action=ValidateObjectID
    )
    subp.add_argument(
        "-g",
        "--gas-budget",
        required=True,
        help="Specify transaction budget",
        type=check_positive,
    )
    subp.set_defaults(subcommand="split-coin-equally")


def _build_extended_read_commands(subparser) -> None:
    """More Object read commands."""

    def __common_event_opts(eparser) -> None:
        eparser.add_argument(
            "-l",
            "--limit",
            required=False,
            default=SuiNullType(),
            help="limit results by page",
            type=check_positive,
        )
        eparser.add_argument(
            "-c",
            "--cursor",
            required=False,
            help="optional paging cursor, entered as n:n (e.g. 10:0)",
            type=str,
            default=SuiNullType(),
        )
        eparser.add_argument(
            "-d",
            "--descending-order",
            action="store_true",
            default=False,
            help="list results in descending order",
        )

    # Events
    subp = subparser.add_parser(
        "events", help="Show events for types", usage="events subcommand [--subcommand_options]"
    )
    ecmds = subp.add_subparsers(title="subcommand", required=True)
    # All events
    esubp = ecmds.add_parser("all", help="Return all events")
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-all")
    # Module events
    esubp = ecmds.add_parser("module", help="Return events emitted in a specified Move module")
    esubp.add_argument("-p", "--package", required=True, help="the SUI package ID", action=ValidateObjectID)
    esubp.add_argument("-m", "--module", required=True, help="the module name", type=str)
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-module")
    # Structure events
    esubp = ecmds.add_parser("struct", help="Return events with the given move structure name")
    esubp.add_argument("-s", "--struct", required=True, dest="struct_name", type=str)
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-struct")
    # Object events
    esubp = ecmds.add_parser("object", help="Return events associated with the given object")
    esubp.add_argument("-o", "--object", required=True, help="the SUI object ID", action=ValidateObjectID)
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-object")
    # Recipient events
    esubp = ecmds.add_parser("recipient", help="Return events associated with the given recipient")
    esubp.add_argument("-r", "--recipient", required=True, help="the SUI address of recipient", action=ValidateAddress)
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-recipient")
    # Sender events
    esubp = ecmds.add_parser("sender", help="Return events associated with the given sender")
    esubp.add_argument("-s", "--sender", required=True, help="the SUI address of sender", action=ValidateAddress)
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-sender")
    # Time events
    esubp = ecmds.add_parser("time", help="Return events emitted in [start_time, end_time) interval")
    __common_event_opts(esubp)
    esubp.add_argument(
        "-s",
        "--start-time",
        required=True,
        help="left endpoint of time interval, inclusive. This is number of milliseconds since Jan 1 1970",
        type=check_positive,
    )
    esubp.add_argument(
        "-e",
        "--end-time",
        required=True,
        help="right endpoint of time interval, exclusive. This is number of milliseconds since Jan 1 1970",
        type=check_positive,
    )
    esubp.set_defaults(subcommand="event-time")
    # Transaction events
    esubp = ecmds.add_parser("transaction", help="Return events emitted by the given transaction")
    esubp.add_argument(
        "-t", "--txn-digest", dest="digest", required=True, help="the transaction's base64 digest", type=str
    )
    __common_event_opts(esubp)
    esubp.set_defaults(subcommand="event-tx")


def _build_tx_query_commands(subparser) -> None:
    """Transaction information read commands."""

    def __common_txns_opts(eparser) -> None:
        eparser.add_argument(
            "-t", "--transaction-id", dest="digest", required=True, help="transaction digest b64 string", type=str
        )
        eparser.add_argument("-l", "--limit", required=True, help="limit results by page", type=check_positive)
        eparser.add_argument(
            "-d",
            "--descending-order",
            action="store_true",
            default=False,
            help="list results in descending order",
        )

    # Transaction
    subp = subparser.add_parser(
        "txns", help="Show transaction information", usage="txns subcommand [--subcommand_options]"
    )
    tcmds = subp.add_subparsers(title="subcommand", required=True)
    # Total count
    esubp = tcmds.add_parser("count", help="Return total transaction count from server")
    esubp.set_defaults(subcommand="txn-count")
    # Transaction
    esubp = tcmds.add_parser("txn", help="Return transaction information")
    esubp.add_argument("-d", "--digest", required=True, help="the transaction's digest")
    esubp.set_defaults(subcommand="txn-txn")
    # Transactions
    subp = tcmds.add_parser("txnsq", help="Show events for types", usage="txns subcommand [--subcommand_options]")
    ecmds = subp.add_subparsers(title="subcommand", required=True)
    # All transactions
    esubp = ecmds.add_parser("all", help="Return all events")
    __common_txns_opts(esubp)
    esubp.set_defaults(subcommand="txnsq-all")
    # Move function
    esubp = ecmds.add_parser("movefunc", help="Return transaction events for move function.")
    esubp.add_argument("-p", "--package", required=True, help="the SUI package ID", action=ValidateObjectID)
    esubp.add_argument("-m", "--module", required=True, help="the module name", type=str)
    esubp.add_argument("-f", "--function", required=True, help="the function name", type=str)
    __common_txns_opts(esubp)
    esubp.set_defaults(subcommand="txnsq-movefunc")
    # Input object
    esubp = ecmds.add_parser("input", help="Return transaction events for the input object.")
    esubp.add_argument("-i", "--input", required=True, help="the input object ID", action=ValidateObjectID)
    __common_txns_opts(esubp)
    esubp.set_defaults(subcommand="txnsq-input")
    # Mutate object
    esubp = ecmds.add_parser("mutated", help="Return transaction events for the mutate object.")
    esubp.add_argument("-m", "--mutated", required=True, help="the input mutate object ID", action=ValidateObjectID)
    __common_txns_opts(esubp)
    esubp.set_defaults(subcommand="txnsq-mutate")
    # From address
    esubp = ecmds.add_parser("from", help="Return transaction events from sender address.")
    esubp.add_argument(
        "-s", "--sender", dest="froms", required=True, help="the 'from' sender address ID", action=ValidateAddress
    )
    __common_txns_opts(esubp)
    esubp.set_defaults(subcommand="txnsq-from")
    # To address
    esubp = ecmds.add_parser("to", help="Return transaction events from recipient address.")
    esubp.add_argument(
        "-r", "--recipient", dest="to", required=True, help="the 'to' recipient address ID", action=ValidateAddress
    )
    __common_txns_opts(esubp)
    esubp.set_defaults(subcommand="txnsq-to")


def build_parser(in_args: list) -> argparse.Namespace:
    """Build the argument parser structure."""
    # Base menu
    parser = argparse.ArgumentParser(add_help=True, usage="%(prog)s [options] command [--command_options]")
    parser.add_argument("-v", "--version", help="Show pysui SDK version", action="store_true")
    parser.set_defaults(subcommand="version")
    subparser = parser.add_subparsers(title="commands")
    _build_read_cmds(subparser)
    _build_coin_cmds(subparser)
    _build_transfer_cmds(subparser)
    _build_pay_cmds(subparser)
    _build_package_cmds(subparser)
    _build_extended_read_commands(subparser)
    _build_tx_query_commands(subparser)

    return parser.parse_args(in_args if in_args else ["--help"])
