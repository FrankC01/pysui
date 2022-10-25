"""Utility functions."""

import base64
import os
from pathlib import Path
from typing import Union

from sui.sui_types import SuiString
from sui.sui_excepts import SuiMiisingBuildFolder, SuiMiisingModuleByteCode


def _module_to_b64(module: Path) -> Union[SuiString, Exception]:
    """Convert modules to base64."""
    with open(module, "rb") as core_file:
        mdata = core_file.read()
        return SuiString(base64.b64encode(mdata).decode())


def package_modules_to_b64(member: Path) -> Union[list[SuiString], Exception]:
    """Convert package modules to base64."""
    expanded_path = Path(os.path.expanduser(member))
    if expanded_path.exists():
        bdir = [x for x in expanded_path.iterdir() if x.is_dir() and x.name == "build"]
        if bdir:
            bmods = [x for x in bdir[0].iterdir() if x.is_dir() and (x / "bytecode_modules").exists()]
            if len(bmods) == 1:
                mod_list = list(bmods[0].glob("*/*.mv"))
                if not mod_list:
                    raise SuiMiisingModuleByteCode(f"{bmods[0]} is empty")
                return [_module_to_b64(x) for x in mod_list]
            raise SuiMiisingBuildFolder(f"No bytecode_modules folder found in {bdir[0]}")
        else:
            raise SuiMiisingBuildFolder(f"No build folder found for {expanded_path}")
