#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Json to BCS generator."""

import ast
import argparse
import inspect
import os
import pathlib
from pathlib import Path
import sys

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))

from pysui.sui.sui_common.json_to_bcs import JsonToBcs
from pysui.sui.sui_common.validators import ValidateScrOrDir, ValidateFile

_jtobcs_version = "0.1.0-beta"


def parse_args(
    in_args: list, default_folder: str, input_file_default: str
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [options] command [--command_options]",
        description="Generate python module of BCS classes from JSON.",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Sets flag to show version. Optional.",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="json_input_file",
        required=False,
        action=ValidateFile,
        help=f"The JSON input file to convert to a Python BCS module. Default to '{input_file_default}'",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        dest="target_output_folder",
        required=False,
        action=ValidateScrOrDir,
        help=f"The folder where the Python BCS module is written to. Default to '{default_folder}'",
    )
    return parser.parse_args(in_args)


def main():
    """Main execution for jtobcs."""
    res_path = Path(inspect.getfile(inspect.currentframe())).parent
    input_source: str = str(res_path / "jtobcs_sample.json")
    output_folder: str = str(Path.cwd())
    parsed = parse_args(
        sys.argv[1:].copy(), str(Path.cwd()), res_path / "jtobcs_sample.json"
    )
    if not parsed.version:
        if parsed.json_input_file:
            input_source = parsed.json_input_file
        if parsed.target_output_folder:
            output_folder = parsed.target_output_folder

        json_data = JsonToBcs.validate_json(json_file=input_source)
        module_name = json_data["module"]
        jtobcs = JsonToBcs(module_name)
        ast_module = jtobcs.gen_module(json_data=json_data)

        if output_folder == "con":
            print(ast.unparse(ast_module))
        else:
            fpath = Path(output_folder) / f"{module_name}.py"
            fpath.write_text(ast.unparse(ast_module), encoding="utf8")
    else:
        print(f"jtobcs {_jtobcs_version}")


if __name__ == "__main__":
    main()
