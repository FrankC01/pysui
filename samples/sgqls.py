#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Sui GraphQL Schemas Persist."""

import argparse
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui import PysuiConfiguration, GqlProtocolClient as AsyncGqlClient
from pysui.sui.sui_common.config.confgroup import GroupProtocol


def build_parser(in_args: list, pconfig: PysuiConfiguration) -> argparse.Namespace:
    """Build the argument parser structure."""
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [options] command [--command_options]",
        description="Persist Sui GraphQL schemas",
    )
    parser.add_argument(
        "--group",
        dest="group_name",
        choices=pconfig.group_names_for_protocol(protocols=[GroupProtocol.GRAPHQL]),
        default=pconfig.active_group.group_name,
        required=False,
        help=f"The GraphQL group. Only GRAPHQL groups are listed. Default to '{pconfig.active_group.group_name}'",
    )
    schema_targets = pconfig.profile_names()
    schema_targets.insert(0, "all")
    parser.add_argument(
        "--profile",
        dest="profile_name",
        choices=schema_targets,
        default=["all"],
        required=False,
        nargs="+",
        help="GraphQL profile(s) to generate schemas for. Defaults to 'all'",
    )
    return parser.parse_args(in_args)


def gen_schemas(prf_list: list[str], cfg: PysuiConfiguration):
    """Generate and persist a schema for each."""
    current_profile = cfg.active_profile
    for prf in prf_list:
        cfg.make_active(profile_name=prf, persist=False)
        AsyncGqlClient(pysui_config=cfg, write_schema=True)
    cfg.make_active(profile_name=current_profile)


def main():
    """Entry point for demonstration."""
    try:
        arg_line = sys.argv[1:].copy()
        cfg = PysuiConfiguration(group_name=PysuiConfiguration.SUI_GQL_RPC_GROUP)
        parsed = build_parser(arg_line, cfg)
        cfg.make_active(group_name=parsed.group_name, persist=False)
        if "all" in parsed.profile_name:
            gen_schemas(cfg.profile_names(), cfg)
        else:
            gen_schemas(parsed.profile_name, cfg)
    except ValueError as ve:
        print(ve.args)


if __name__ == "__main__":
    main()
