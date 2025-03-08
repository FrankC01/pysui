#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""BCS to Json generator."""

import argparse
import ast
import inspect
import os
import pathlib
import sys

from pathlib import Path

PROJECT_DIR = pathlib.Path(os.path.dirname(__file__))
PARENT = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(os.path.join(PARENT, "pysui")))


import pysui.sui.sui_common.bcs_to_json as ntree
from pysui.sui.sui_common.validators import ValidateScrOrDir, ValidateFile

_bcstoj_version = "0.1.0-beta"


def parse_args(
    in_args: list, default_folder: str, input_file_default: str
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="%(prog)s [options] command [--command_options]",
        description="Generate JSON from BCS classes in python module",
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
        dest="python_input_file",
        required=False,
        action=ValidateFile,
        help=f"The Python input file containing BCS constructs to convert to JSON. Default to '{input_file_default}'",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        dest="target_output_folder",
        action=ValidateScrOrDir,
        required=False,
        help=f"The folder where the JSON output is written to. Default to '{default_folder}'",
    )
    return parser.parse_args(in_args)


def main():
    """Main execution for bcstoj."""
    res_path = Path(inspect.getfile(inspect.currentframe())).parent
    sample_file = res_path / "bcs_samp.py"
    input_source: str = str(sample_file)
    output_folder: str = str(Path.cwd())
    args_parsed = parse_args(sys.argv[1:].copy(), output_folder, input_source)
    if not args_parsed.version:
        if args_parsed.python_input_file:
            input_source = args_parsed.python_input_file
        if args_parsed.target_output_folder:
            output_folder = args_parsed.target_output_folder

        source_module = Path(input_source)
        pre_module: ast.Module = ast.parse(
            source_module.read_text(encoding="utf8"), source_module, "exec"
        )
        parse_tree: ntree.Tree = ntree.Tree("classes")
        decls = ntree.Declarations(parse_tree.root)
        decls.visit(pre_module)
        # Get the name of the tail of the input python module as the 'module' name in json
        fname = source_module.stem
        jstr = parse_tree.emit_json(fname)
        if output_folder == "con":
            print(jstr)
        else:
            fpath = Path(output_folder) / f"{fname}.json"
            fpath.write_text(jstr, encoding="utf8")
    else:
        print(f"bcstoj {_bcstoj_version}")


if __name__ == "__main__":
    main()
