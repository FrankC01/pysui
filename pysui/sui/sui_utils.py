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

"""Utility functions."""

import base64
import subprocess
from pathlib import Path
from typing import Union

from .sui_types import SuiString
from .sui_excepts import SuiMiisingBuildFolder, SuiMiisingModuleByteCode, SuiPackageBuildFail

_SUI_BUILD = ["sui", "move", "build", "--path"]


def _module_to_b64(module: Path) -> Union[SuiString, Exception]:
    """Convert modules to base64."""
    with open(module, "rb") as core_file:
        mdata = core_file.read()
        return SuiString(base64.b64encode(mdata).decode())


def _package_modules_to_b64(project: Path) -> Union[list[SuiString], Exception]:
    """Convert package modules to base64."""
    bdir = [x for x in project.iterdir() if x.is_dir() and x.name == "build"]
    if not bdir:
        raise SuiMiisingBuildFolder(f"No build folder found in {project}")
    bmods = [x for x in bdir[0].iterdir() if x.is_dir() and (x / "bytecode_modules").exists()]
    if not bmods:
        raise SuiMiisingBuildFolder(f"No bytecode_modules folder found for {project}/build")
    mod_list = list(bmods[0].glob("*/*.mv"))
    if not mod_list:
        raise SuiMiisingModuleByteCode(f"{bmods[0]} is empty")
    return [_module_to_b64(x) for x in mod_list]


def _compile_project(path_to_package: Path) -> Union[Path, Exception]:
    """Build the move package."""
    args = _SUI_BUILD.copy()
    args.append(str(path_to_package))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode == 0:
        return path_to_package
    raise SuiPackageBuildFail(result.stdout)


def build_b64_modules(path_to_package: Path) -> Union[list[SuiString], Exception]:
    """Build move package and return base64 encoded module list."""
    if path_to_package.exists():
        return _package_modules_to_b64(_compile_project(path_to_package))
    raise SuiMiisingBuildFolder(f"Move project path not found: {path_to_package}")
