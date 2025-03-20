#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move structure to BCS generator."""

import argparse
import asyncio
import json
import os
import pathlib
import sys

from pathlib import Path
from typing import Union

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui.sui.sui_common.validators import (
    ValidateScrOrDir,
    ValidateFile,
    valid_sui_address,
)
from pysui import PysuiConfiguration
from pysui.sui.sui_common.move_to_bcs import MoveDataType
from samples.cmd_argsg import pre_config_pull

_mtobcs_version = "0.1.0-beta"

import logging

logger = logging.getLogger()
logging.basicConfig(
    filename="mtobcs.log",
    filemode="w",
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
        "--move-struct-file",
        dest="move_structure",
        required=True,
        action=ValidateFile,
        help="JSON file of string array, each row identifies a program structure (e.g. 0x2::coin::Coin)",
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


def _validate_structs(slist: list[str]) -> Union[None, ValueError]:
    """Ensure structs are well formed."""
    for package in slist:
        if package.count("::") == 2:
            addy, module, tail = package.split("::")
            if not valid_sui_address(addy):
                raise ValueError(f"Invalid Sui address '{addy}' in '{package}'.")
        else:
            raise ValueError(f"Invalid Sui move triple '{package}'.")


def _fname_from_triple(triple: str) -> str:
    """Form a filename of lower(struct)_module_address.py."""
    addy, module, struct = triple.split("::")
    return f"{struct.lower()}_{module.lower()}_{addy}.py"


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
        # Load the move structure json file
        json_file: Path = parsed.move_structure
        package_structs: list[str] = json.loads(json_file.read_text(encoding="utf8"))
        _validate_structs(package_structs)
        output_folder = parsed.target_output_folder
        # Emit python modules for each identified move program structure
        for package in package_structs:
            fname = _fname_from_triple(package)
            mst: MoveDataType = MoveDataType(cfg=cfg, target=package)
            await mst.build()
            bcs_py = await mst.emit()
            if output_folder == "con":
                print(bcs_py)
            else:
                fpath = Path(output_folder) / fname
                fpath.write_text(bcs_py, encoding="utf8")

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
    # Devnet
    starg: str = (
        "0xd64180a00db195a116aabcdc68ff6095b28a6592cb33af6e434bac717e760f9a::parms::ParmObject"
    )
    # Testnet
    # starg: str = (
    #     "0x0c7ae833c220aa73a3643a0d508afa4ac5d50d97312ea4584e35f9eb21b9df12::pool::Pool"
    # )
    mst: MoveDataType = MoveDataType(cfg=pcfg, target=starg)
    await mst.build()

    bcs_py = await mst.emit()
    print(bcs_py)
    logger.info(f"Complete processing {starg}")


if __name__ == "__main__":
    # asyncio.run(faux_main())
    asyncio.run(main())
