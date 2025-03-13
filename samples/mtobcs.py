#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move structure to BCS generator."""

import argparse
import asyncio
import os
import pathlib
import sys

from pathlib import Path

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui.sui.sui_common.validators import ValidateScrOrDir, ValidateSuiTriple
from pysui import PysuiConfiguration
from pysui.sui.sui_common.move_to_bcs import MoveStructureTree
from samples.cmd_argsg import pre_config_pull

_mtobcs_version = "0.1.0-beta"

import logging

logger = logging.getLogger()
logging.basicConfig(
    filename="mtobcs.log",
    filemode="a",
    encoding="utf-8",
    format="%(asctime)s %(module)s %(levelname)s %(message)s",
    level=logging.INFO,
)


def parse_args(
    pconfig: PysuiConfiguration, in_args: list, default_folder: str
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [options] command [--command_options]",
        description="Generate python module of BCS classes from JSON.",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        default=pconfig.config,
        required=False,
        help=f"The Pysui Configuration folder to use. Default to '{pconfig.config}'",
    )
    parser.add_argument(
        "--group",
        dest="group_name",
        choices=pconfig.group_names(),
        required=False,
        help=f"The GraphQL groups. Default to '{pconfig.active_group_name}'",
    )
    parser.add_argument(
        # "-p",
        "--profile",
        dest="profile_name",
        choices=pconfig.profile_names(),
        required=False,
        help=f"The GraphQL profile node. Default to '{pconfig.active_profile}' from '{pconfig.active_group_name}'",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Sets flag to show version. Optional.",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--move_struct",
        dest="move_structure",
        required=True,
        action=ValidateSuiTriple,
        help="The address::module::struct type",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        dest="target_output_folder",
        required=False,
        default=default_folder,
        action=ValidateScrOrDir,
        help=f"The folder where the Python BCS module is written to. Default to '{default_folder}'",
    )
    return parser.parse_args(in_args)


# Build the structure tree
# 1. Fetch an objects structure
# 2. For each field
# 3. if scalar (ie. u64, string, address, digest) return
# 4. else go to 1
#
# Setup the basic module
# Walk the tree bottom up
# Generate the classes


async def main():
    """Main entry point for mtobcs."""
    cfg, arg_line = pre_config_pull(sys.argv[1:].copy())
    output_folder: str = str(Path.cwd())
    parsed = parse_args(cfg, arg_line, output_folder)
    if not parsed.version:
        if parsed.group_name or parsed.profile_name:
            cfg.make_active(
                group_name=parsed.group_name,
                profile_name=parsed.profile_name,
                persist=False,
            )
    else:
        print(f"mtobcs {_mtobcs_version}")


async def faux_main():
    pcfg: PysuiConfiguration = PysuiConfiguration(
        group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP,
        profile_name="devnet",
        # profile_name="testnet",
        # profile_name="mainnet",
        # persist=True,
    )
    starg: str = (
        "0x78f2d481065d62e4aac902a8453d3529d48efb2001f307993240239df965fc96::parms::ParmObject"
    )
    logger.info(f"Processing {starg}")
    mst: MoveStructureTree = MoveStructureTree(cfg=pcfg, target=starg)
    await mst.build()
    # await mst.emit()
    logger.info(f"Complete processing {starg}")


if __name__ == "__main__":
    asyncio.run(faux_main())
    # asyncio.run(main())
