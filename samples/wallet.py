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

sys.path += [
    str(PROJECT_DIR),
    os.path.join(PROJECT_DIR.parent, "samples"),
    os.path.join(PROJECT_DIR.parent, "pysui"),
]


from pysui.sui import SuiConfig

from .cmd_args import build_parser
from .cmds import SUI_CMD_DISPATCH
from .faux_wallet import SuiWallet


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
            cmd_call(SuiWallet(SuiConfig.from_config_file(cfg_file[0])), parsed)
        else:
            cmd_call(SuiWallet(SuiConfig.default()), parsed)
    else:
        print(f"Unable to resolve function for {parsed.subcommand}")


if __name__ == "__main__":
    main()
