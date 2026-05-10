#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Argument parsing for samples/walletg."""

import argparse
from pathlib import Path
from typing import Optional
from pysui import PysuiConfiguration
from pysui.sui.sui_common.config.confgroup import GroupProtocol
import pysui.sui.sui_common.validators as validator
from pysui.sui.sui_types.scalars import SuiString


def _add_owner_args(subp, required: bool = False) -> None:
    """Add mutually exclusive owner/alias arguments to a subparser."""
    addy_arg_group = subp.add_mutually_exclusive_group(required=required)
    addy_arg_group.add_argument(
        "-o",
        "--owner",
        required=False,
        help="Sui address of owner. Optional.",
        action=validator.ValidateAddress,
    )
    addy_arg_group.add_argument(
        "-a",
        "--alias",
        required=False,
        help="Alias of owner address. Optional.",
        action=validator.ValidateAlias,
    )


def _build_chain_cmds(subparser) -> None:
    """Chain information commands."""
    # chain-id
    subp = subparser.add_parser("chain-id", help="Show current chain identifier")
    subp.set_defaults(subcommand="chain-id")
    # txns (nested subparser)
    subp = subparser.add_parser(
        "txns",
        help="Show transaction information",
        usage="txns subcommand [--subcommand_options]",
    )
    tcmds = subp.add_subparsers(title="subcommand", required=True)
    esubp = tcmds.add_parser("count", help="Return total transaction count from server")
    esubp.set_defaults(subcommand="txn-count")
    esubp = tcmds.add_parser("txn", help="Return transaction information")
    esubp.add_argument("-d", "--digest", required=True, help="the transaction's digest")
    esubp.set_defaults(subcommand="txn-txn")


def _build_read_cmds(subparser) -> None:
    """Read commands."""
    # gas
    subp = subparser.add_parser(
        "gas",
        help="Shows gas objects and total mist. If owner or alias not provided, defaults to active-address.",
    )
    _add_owner_args(subp)
    subp.add_argument(
        "-i",
        "--include-pruned",
        required=False,
        help="Include pruned and deleted results. Optional.",
        action="store_true",
    )
    subp.set_defaults(subcommand="gas")
    # coins
    subp = subparser.add_parser(
        "coins",
        help="Shows coin type balances. If owner or alias not provided, defaults to active-address.",
    )
    _add_owner_args(subp)
    subp.set_defaults(subcommand="coins")
    # object
    subp = subparser.add_parser("object", help="Show object by id")
    subp.add_argument("-i", "--id", required=True, action=validator.ValidateObjectID)
    subp.set_defaults(subcommand="object")
    # objects
    subp = subparser.add_parser(
        "objects",
        help="Show all objects. If owner or alias not provided, defaults to active-address.",
    )
    _add_owner_args(subp)
    subp.add_argument(
        "-i",
        "--include-pruned",
        required=False,
        help="Include pruned and deleted results. Optional.",
        action="store_true",
    )
    subp.add_argument(
        "-j",
        "--json",
        required=False,
        help="Display output as json",
        action="store_true",
    )
    subp.set_defaults(subcommand="objects")
    # package
    subp = subparser.add_parser("package", help="Show normalized package information")
    subp.add_argument(
        "-i",
        "--id",
        required=True,
        help="package ID",
        action=validator.ValidateObjectID,
    )
    subp.set_defaults(subcommand="package")


def _build_account_cmds(subparser) -> None:
    """Account and address management commands."""
    # active-address
    subp = subparser.add_parser("active-address", help="Shows active address")
    subp.set_defaults(subcommand="active-address")
    # addresses
    subp = subparser.add_parser("addresses", help="Shows all addresses")
    subp.add_argument(
        "-d",
        "--details",
        required=False,
        help="Show additional information.",
        action="store_true",
    )
    subp.set_defaults(subcommand="addresses")
    # new-address
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
    # aliases (nested subparser)
    subp = subparser.add_parser(
        "aliases",
        help="Sui Address alias management",
        usage="aliases subcommand [--subcommand_options]",
    )
    acmds = subp.add_subparsers(title="subcommand", required=True)
    asubp = acmds.add_parser("list", help="List aliases and associated Sui addresses")
    asubp.set_defaults(subcommand="list-aliases")
    asubp = acmds.add_parser("rename", help="Rename aliases for associated Sui addresses")
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


def _build_operations_cmds(subparser) -> None:
    """Transaction operation commands (PTB-building)."""
    # transfer-object
    subp = subparser.add_parser(
        "transfer-object",
        help="Transfer an object from one address to another. If owner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-t",
        "--transfer",
        required=True,
        help="Specify object ID of sui object being transferred",
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
    _add_owner_args(subp)
    subp.set_defaults(subcommand="transfer-object")
    # transfer-sui
    subp = subparser.add_parser(
        "transfer-sui",
        help="Transfer SUI 'mist(s)' to a Sui address. If owner or alias not provided, defaults to active-address.",
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
    _add_owner_args(subp)
    subp.set_defaults(subcommand="transfer-sui")
    # pay
    subp = subparser.add_parser(
        "pay",
        help="Send coin of any type to recipient(s). If owner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-i",
        "--input-coins",
        required=True,
        nargs="+",
        help="Specify the input coins for each <RECIPIENT>:<AMOUNTS> to send to",
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
        help="Specify 'pay' transaction budget. Optional.",
        type=str,
    )
    _add_owner_args(subp)
    subp.set_defaults(subcommand="pay")
    # merge-coin
    subp = subparser.add_parser(
        "merge-coin",
        help="Merge two coins together. If owner or alias not provided, defaults to active-address. If you want to merge all coins to one: use 'smash'",
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
        help="Specify 'merge-coin' transaction budget. Optional.",
        type=str,
    )
    _add_owner_args(subp)
    subp.set_defaults(subcommand="merge-coin")
    # split-coin
    subp = subparser.add_parser(
        "split-coin",
        help="Split coin into one or more coins by amount. If owner or alias not provided, defaults to active-address.",
    )
    subp.add_argument(
        "-c",
        "--coin_object_id",
        required=False,
        help="Specify the coin ID the split-amounts are being split from. Optional, will choose coin.",
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
    _add_owner_args(subp)
    subp.set_defaults(subcommand="split-coin")
    # split-coin-equally
    subp = subparser.add_parser(
        "split-coin-equally",
        help="Split coin into one or more coins equally. If owner or alias not provided, defaults to active-address.",
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
    _add_owner_args(subp)
    subp.set_defaults(subcommand="split-coin-equally")
    # publish
    subp = subparser.add_parser(
        "publish",
        help="Publish a SUI package. If owner or alias not provided, defaults to active-address.",
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
    _add_owner_args(subp)
    subp.set_defaults(subcommand="publish")
    # call
    subp = subparser.add_parser(
        "call",
        help="Call a move contract function. If owner or alias not provided, defaults to active-address.",
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
    _add_owner_args(subp)
    subp.set_defaults(subcommand="call")


def _build_transaction_cmds(subparser) -> None:
    """Transaction byte commands (simulate and execute)."""
    # simulate
    subp = subparser.add_parser(
        "simulate",
        help="Simulate a transaction (TransactionData base64 bytes).",
    )
    subp.add_argument(
        "-t",
        "--txb",
        required=True,
        help="The base64 TransactionData bytes.",
        action=validator.ValidateB64,
    )
    subp.add_argument(
        "--checks-enabled",
        dest="checks_enabled",
        required=False,
        default=True,
        help="Enable transaction checks. Default True.",
        action=argparse.BooleanOptionalAction,
    )
    subp.add_argument(
        "--gas-selection",
        dest="gas_selection",
        required=False,
        default=True,
        help="Enable gas selection. Default True.",
        action=argparse.BooleanOptionalAction,
    )
    subp.set_defaults(subcommand="simulate")
    # execute-tx
    subp = subparser.add_parser(
        "execute-tx",
        help="Execute a signed transaction on blockchain.",
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


def _build_info_cmds(subparser) -> None:
    """Info commands."""
    subp = subparser.add_parser("version", help="Show pysui SDK version.")
    subp.set_defaults(subcommand="version")


def _base_parser(
    pconfig: PysuiConfiguration,
    desc: Optional[str] = None,
    group_protocols: Optional[list[GroupProtocol]] = None,
) -> argparse.ArgumentParser:
    """Basic parser setting for all commands."""
    parser = argparse.ArgumentParser(
        add_help=True,
        usage=desc or "%(prog)s [options] command [--command_options]",
        description="",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        dest="config_name",
        default=pconfig.config,
        required=False,
        help=f"The Pysui Configuration folder to use. Default to '{pconfig.config}'",
    )
    _group_choices = (
        pconfig.group_names_for_protocol(protocols=group_protocols)
        if group_protocols
        else pconfig.group_names()
    )
    parser.add_argument(
        "--group",
        dest="group_name",
        choices=_group_choices,
        default=pconfig.active_group.group_name,
        required=False,
        help=f"The active group to use. Default to '{pconfig.active_group_name}'",
    )
    parser.add_argument(
        "--profile",
        dest="profile_name",
        choices=pconfig.profile_names(),
        default=pconfig.active_profile,
        required=False,
        help=f"The profile node to use. Default to '{pconfig.active_profile}' from '{pconfig.active_group_name}'",
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
    parser = _base_parser(pconfig)
    subparser = parser.add_subparsers(title="commands")
    _build_chain_cmds(subparser)
    _build_read_cmds(subparser)
    _build_account_cmds(subparser)
    _build_operations_cmds(subparser)
    _build_transaction_cmds(subparser)
    _build_info_cmds(subparser)
    return parser.parse_args(in_args if in_args else ["--help"])


def build_async_gas_parser(
    in_args: list, pconfig: PysuiConfiguration
) -> argparse.Namespace:
    """Build the argument parser for async-gas."""
    parser = _base_parser(
        pconfig,
        group_protocols=[GroupProtocol.GRAPHQL, GroupProtocol.GRPC],
    )
    parser.add_help = True
    parser.usage = "%(prog)s [options]"
    parser.description = "Report SUI gas for active address. Supports GRAPHQL and GRPC groups."
    return parser.parse_args(in_args)


def build_mtobcs_parser(
    in_args: list, pconfig: PysuiConfiguration
) -> argparse.Namespace:
    """Build the argument parser for mtobcs."""
    parser = _base_parser(
        pconfig,
        group_protocols=[GroupProtocol.GRAPHQL, GroupProtocol.GRPC],
    )
    parser.add_help = True
    parser.usage = "%(prog)s [options]"
    parser.description = (
        "Generate python module of BCS classes from JSON. Supports GRAPHQL and GRPC groups."
    )
    parser.add_argument(
        "-m",
        "--move-target-file",
        dest="move_targets",
        required=True,
        action=validator.ValidateFile,
        help="JSON file of array of maps, each identifies a target for generation",
    )
    _default_folder = str(Path.cwd())
    parser.add_argument(
        "-o",
        "--output-folder",
        dest="target_output_folder",
        required=False,
        default=_default_folder,
        action=validator.ValidateScrOrDir,
        help=f"The folder where the Python BCS module is written to. Default to '{_default_folder}'",
    )
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
    parser = _base_parser(
        pconfig,
        "splay [options].\n\n" + build_splay_parser.__doc__,
        group_protocols=[GroupProtocol.GRAPHQL, GroupProtocol.GRPC],
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
        help="merges all or -o owner coins then splays into 'n' coins to itself. Mutually exclusive with '-r/--recipients",
        action=validator.ValidatePositive,
    )
    dest_arg_group.add_argument(
        "-r",
        "--recipients",
        nargs="+",
        help="merges all or -o owner coins then splays evenly to these recipients. Mutually exclusive with '-n/--number",
        action=validator.ValidateAddress,
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        required=False,
        help="Parse and display routing decision without executing. Optional.",
        action="store_true",
    )
    return parser.parse_args(in_args if in_args else ["--help"])


def _group_pull(cli_arg: list, config: PysuiConfiguration) -> list:
    """Check for group and set accordingly."""
    if cli_arg.count("--group"):
        ndx = cli_arg.index("--group")
        nvl: str = cli_arg[ndx + 1]
        config.make_active(group_name=nvl)
        cli_arg = [n for n in cli_arg if n not in [cli_arg[ndx], cli_arg[ndx + 1]]]
    return cli_arg


def pre_config_pull(cli_arg: list) -> tuple[PysuiConfiguration, list]:
    """Check for a configuration path to use."""
    cfg = None
    removals: list = []
    if cli_arg.count("--config"):
        ndx = cli_arg.index("--config")
        nvl: str = cli_arg[ndx + 1]
        cfg = PysuiConfiguration(from_cfg_path=nvl)
        removals.append(cli_arg[ndx])
        removals.append(cli_arg[ndx + 1])
        cli_arg = _group_pull(cli_arg, cfg)
        cli_arg = [n for n in cli_arg if n not in removals]
    else:
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    return cfg, cli_arg
