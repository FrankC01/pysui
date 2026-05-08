#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Move structure to BCS generator."""

import asyncio
import json
import os
import pathlib
import sys

from pathlib import Path

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui import client_factory
from pysui.sui.sui_common.move_to_bcs import MoveDataType
import pysui.sui.sui_common.mtobcs_types as mtypes
from samples.cmd_argsg import pre_config_pull, build_mtobcs_parser

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


def _fname_from_triple(triple: str) -> str:
    """Form a filename of lower(struct)_module_address.py."""
    addy, module, struct = triple.split("::")
    return f"{struct.lower()}_{module.lower()}_{addy}.py"


async def _execute():
    """."""
    cfg, arg_line = pre_config_pull(sys.argv[1:].copy())
    parsed = build_mtobcs_parser(arg_line, cfg)
    if not parsed.version:
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
        client = client_factory(cfg)
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
