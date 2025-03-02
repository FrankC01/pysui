#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Json to BCS generator."""

import ast
import argparse
import inspect
import os
import pathlib
import sys

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui.sui.sui_common.json_to_bcs import JsonToBcs
from pathlib import Path


def parse_args(
    in_args: list, default_folder: str, input_file_default: str
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [options] command [--command_options]",
        description="",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="json_input_file",
        required=False,
        default=input_file_default,
        help=f"The JSON input file to convert to a Python BCS module. Default to '{input_file_default}'",
    )
    parser.add_argument(
        "-t",
        "--target-folder",
        dest="target_output_folder",
        default=default_folder,
        required=False,
        help=f"The folder where the Python BCS module is written to. Default to '{default_folder}'",
    )
    return parser.parse_args(in_args)


def main():
    """Main execution for jtobcs."""
    res_path = Path(inspect.getfile(inspect.currentframe())).parent
    parsed = parse_args([], str(Path.cwd()), res_path / "jtobcs_sample.json")
    json_data = JsonToBcs.validate_json(json_file=parsed.json_input_file)
    module_name = json_data["module"]
    jtobcs = JsonToBcs(module_name)
    ast_module = jtobcs.gen_module(json_data=json_data)

    print(ast.unparse(ast_module))
    # fpath = Path(parsed.target_output_folder) / f"{module_name}.py"
    # fpath.write_text(ast.unparse(ast_module), encoding="utf8")


if __name__ == "__main__":
    main()
