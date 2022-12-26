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

"""Main driver primarily for demonstrating."""

import argparse
import os
import pathlib
import sys


PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_clients.sync_client import SuiClient

from samples.cmd_args import build_parser
from samples.cmds import SUI_CMD_DISPATCH


def main():
    """Entry point for demonstration."""
    arg_line = sys.argv[1:].copy()
    cfg_file = None
    # Handle a different client.yaml than default
    if arg_line and arg_line[0] == "--local":
        cfg_file = arg_line[1:2]
        arg_line = arg_line[2:]
    parsed = build_parser(arg_line)
    cmd_call = SUI_CMD_DISPATCH.get(parsed.subcommand, None)
    if cmd_call:
        var_args = vars(parsed)
        var_args.pop("subcommand")
        parsed = argparse.Namespace(**var_args)
        if cfg_file:
            cfg = SuiConfig.from_config_file(cfg_file[0])
        else:
            cfg = SuiConfig.default()
        print(f"Using configuration from {cfg.configuration_path}")
        cmd_call(SuiClient(cfg), parsed)
    else:
        print(f"Unable to resolve function for {parsed.subcommand}")


if __name__ == "__main__":
    main()
