#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Main driver primarily for demonstrating using Sui GraphQL."""

import argparse
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui import SuiConfig
from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_constants import PYSUI_CLIENT_CONFIG_ENV

from samples.cmd_argsg import build_parser
from samples.cmdsg import SUI_CMD_DISPATCH


def main():
    """Entry point for demonstration."""
    arg_line = sys.argv[1:].copy()
    cfg_local: bool = False
    # Handle a different client.yaml than default
    if arg_line and arg_line[0] == "--local":
        cfg_local = True
        arg_line = arg_line[1:]
    parsed = build_parser(arg_line)
    cmd_call = SUI_CMD_DISPATCH.get(parsed.subcommand, None)
    if cmd_call:
        var_args = vars(parsed)
        var_args.pop("subcommand")
        parsed = argparse.Namespace(**var_args)
        if cfg_local:
            raise ValueError("Local not supported for GraphQL commands")
        else:
            cfg = SuiConfig.default_config()
            print(f"Using configuration from {os.environ[PYSUI_CLIENT_CONFIG_ENV]}")

        cmd_call(SuiGQLClient(config=cfg), parsed)
    else:
        print(f"Unable to resolve function for {parsed.subcommand}")


if __name__ == "__main__":
    main()
