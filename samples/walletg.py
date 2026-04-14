#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Main driver primarily for demonstrating using Sui GraphQL."""

import argparse
import asyncio
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui import PysuiConfiguration, client_factory
from pysui.sui.sui_constants import PYSUI_CLIENT_CONFIG_ENV

from samples.cmd_argsg import build_parser, pre_config_pull
from samples.cmdsg import SUI_CMD_DISPATCH


async def _run():
    """Async entry point."""
    cfg, arg_line = pre_config_pull(sys.argv[1:].copy())
    parsed = build_parser(arg_line, cfg)
    cmd_call = SUI_CMD_DISPATCH.get(parsed.subcommand, None)
    cfg.make_active(
        group_name=parsed.group_name, profile_name=parsed.profile_name, persist=False
    )
    if cmd_call:
        var_args = vars(parsed)
        var_args.pop("subcommand")
        parsed = argparse.Namespace(**var_args)
        await cmd_call(client_factory(cfg), parsed)
    else:
        print(f"Unable to resolve function for {parsed.subcommand}")


def main():
    """Entry point for demonstration."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
