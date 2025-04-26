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
from pysui import PysuiConfiguration, AsyncGqlClient
from pysui.sui.sui_common.move_to_bcs import MoveDataType
import pysui.sui.sui_common.mtobcs_types as mtypes
from samples.cmd_argsg import pre_config_pull

_mtobcs_version = "0.1.3-beta"

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
        "--move-target-file",
        dest="move_targets",
        required=True,
        action=ValidateFile,
        help="JSON file of array of maps, each identifies a target for generation",
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


def _fname_from_triple(triple: str) -> str:
    """Form a filename of lower(struct)_module_address.py."""
    addy, module, struct = triple.split("::")
    return f"{struct.lower()}_{module.lower()}_{addy}.py"


async def _execute():
    """."""
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
        json_file: Path = parsed.move_targets
        package_targets: mtypes.Targets = mtypes.Targets.load_declarations(
            json.loads(json_file.read_text(encoding="utf8"))
        )
        output_folder = parsed.target_output_folder
        client = AsyncGqlClient(pysui_config=cfg)
        # Emit python modules for each identified move program structure
        for package in package_targets.targets:
            fname = package.out_file
            # Instantiate the MoveDataType with the target from json
            mst: MoveDataType = MoveDataType(client=client, target=package)
            # Fetch and parse Move struct target to IR and return entry point class name
            _ = await mst.parse_move_target()
            # Compile the BCS from IR and return the namespace
            namespace = await mst.compile_bcs()
            # bcs_entry_class = namespace[entry_point_classname]
            # Execute the deserialization returning the BCS object
            # desered = bcs_entry_class.deserialize(b"0")
            bcs_py = await mst.emit_bcs_source()
            if output_folder == "con":
                print(bcs_py)
            else:
                fpath = Path(output_folder) / fname
                fpath.write_text(bcs_py, encoding="utf8")

    else:
        print(f"mtobcs {_mtobcs_version}")


def main():
    """Main entry point for mtobcs."""
    asyncio.run(_execute())


if __name__ == "__main__":
    main()
