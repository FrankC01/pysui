#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confidential Transfer (private funds) example command-line tool.

Exercises pysui private-transfer support (configuration, id derivation, and — as
they are added — registration and rekey) for validation and clarification ahead
of a live Confidential Transfer deployment.  Commands are added incrementally;
the first, ``validate_config``, resolves and validates a
:class:`PrivateFundsConfig` against the active ``PysuiConfiguration`` profile.
"""

import argparse
import asyncio
import sys

from pysui import PysuiConfiguration
from pysui.private_transfer.config import PrivateFundsConfig


def validate_config(
    *, args: argparse.Namespace, pysui_config: PysuiConfiguration
) -> None:
    """Validate a PrivateFundsConfig against the active PysuiConfiguration profile.

    :param args: Parsed command arguments (uses ``args.path``)
    :type args: argparse.Namespace
    :param pysui_config: The shared pysui configuration driving group resolution
    :type pysui_config: PysuiConfiguration
    """
    try:
        pfconfig = PrivateFundsConfig(
            pysui_config=pysui_config, from_cfg_path=args.path
        )
    except ValueError as exc:
        print(f"PrivateFundsConfig validation FAILED: {exc}")
        return
    group = pfconfig.active_group
    print(f"PrivateFundsConfig validated for profile '{pysui_config.active_profile}':")
    print(f"  group name:      {group.name}")
    print(f"  packageId:       {group.package_id}")
    print(f"  tokenRegistry:   {group.token_registry}")
    print(f"  accountRegistry: {group.account_registry}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser and register all subcommands.

    :returns: The configured argument parser
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ucs_private_funds_example",
        description="Confidential Transfer (private funds) example commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser(
        "validate_config",
        help="Validate PrivateFundsConfig against the active PysuiConfiguration profile.",
    )
    validate.add_argument(
        "--path",
        default=None,
        help="Optional directory containing PrivateFundsConfig.json (default: ~/.pysui).",
    )
    return parser


async def main(*, pysui_config: PysuiConfiguration) -> None:
    """Parse arguments and dispatch to the selected command.

    :param pysui_config: The shared pysui configuration
    :type pysui_config: PysuiConfiguration
    """
    args = build_parser().parse_args()
    if args.command == "validate_config":
        validate_config(args=args, pysui_config=pysui_config)
    # Future async commands dispatch with await, e.g.:
    # elif args.command == "register":
    #     await register(args=args, pysui_config=pysui_config)


if __name__ == "__main__":
    # Optionally force a specific command + arguments (uncomment one):
    # sys.argv = ["ucs_private_funds_example.py", "validate_config"]
    sys.argv = [
        "ucs_private_funds_example.py",
        "validate_config",
        "--path",
        "~/.pwallet",
    ]

    _pysui_config = PysuiConfiguration(
        # Uncomment one group:
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        # group_name=PysuiConfiguration.SUI_GRPC_GROUP,
        # profile_name="devnet",
        profile_name="testnet",
        # profile_name="mainnet",
    )
    asyncio.run(main(pysui_config=_pysui_config))
