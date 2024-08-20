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

from pysui import PysuiConfiguration, SyncGqlClient

# from pysui.sui.sui_pgql.pgql_clients import SuiGQLClient
from pysui.sui.sui_constants import PYSUI_CLIENT_CONFIG_ENV

from samples.cmd_argsg import build_parser
from samples.cmdsg import SUI_CMD_DISPATCH


def main():
    """Entry point for demonstration."""
    arg_line = sys.argv[1:].copy()
    cfg_local: bool = False
    # Handle a different client.yaml than default
    if arg_line and arg_line[0] == "--local":
        raise ValueError("--local is invalid for GraphQL")
    cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
    parsed = build_parser(arg_line, cfg)
    cmd_call = SUI_CMD_DISPATCH.get(parsed.subcommand, None)
    cfg.make_active(profile_name=parsed.profile_name, persist=False)
    if cmd_call:
        var_args = vars(parsed)
        var_args.pop("subcommand")
        parsed = argparse.Namespace(**var_args)
        cmd_call(SyncGqlClient(pysui_config=cfg), parsed)
    else:
        print(f"Unable to resolve function for {parsed.subcommand}")


if __name__ == "__main__":
    main()
