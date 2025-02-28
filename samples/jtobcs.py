#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Json to BCS generator."""

import ast
import argparse
import inspect

import json
import os

from pathlib import Path
from typing import Any, Optional

from jsonschema import validate

_BCS_STRUCT_BASE = ast.Attribute(
    ast.Name("canoser", ast.Load()),
    "Struct",
    ast.Load(),
)
_BCS_ENUM_BASE = ast.Attribute(
    ast.Name("canoser", ast.Load()),
    "RustEnum",
    ast.Load(),
)
_BCS_OPTIONAL_BASE = ast.Attribute(
    ast.Name("canoser", ast.Load()),
    "RustOptional",
    ast.Load(),
)

_BCS_COMMON_TYPES: dict[str, str] = {
    "u8": "bcs.U8",
    "u16": "bcs.U16",
    "u32": "bcs.U32",
    "u64": "bcs.U64",
    "u128": "bcs.U1128",
    "u256": "bcs.U256",
    "string": "str",
    "boolean": "bool",
}


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
    # return parser.parse_args(in_args if in_args else ["--help"])


def gen_structure(*, name: str, ast_module: ast.AST, spec: dict) -> ast.ClassDef:
    """Generate a BCS canoser Struct."""

    field_targets: ast.List = ast.List([], ast.Load)
    if fields := spec.get("fields"):
        for field in fields:
            process_json(field_targets, field)

    ast_module.body.append(
        ast.ClassDef(
            name,
            [_BCS_STRUCT_BASE],
            [],
            [
                ast.Assign(
                    [ast.Name("_fields", ast.Store())],
                    field_targets,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )
    )


def gen_enum(*, name: str, ast_module: ast.AST, spec: dict) -> ast.ClassDef:
    """Generate a BCS canoser RustEnum."""
    field_targets: ast.List = ast.List([], ast.Load)
    if fields := spec.get("enums"):
        for field in fields:
            process_json(field_targets, field)

    ast_module.body.append(
        ast.ClassDef(
            name,
            [_BCS_ENUM_BASE],
            [],
            [
                ast.Assign(
                    [ast.Name("_enums", ast.Store())],
                    field_targets,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )
    )


def gen_option(*, name: str, ast_module: ast.AST, spec: dict) -> ast.ClassDef:
    """Generate a BCS canoser RustOptional."""

    if element := spec.get("element"):
        if element and isinstance(element, dict):
            if element["class_type"] == "Reference":
                atype = _BCS_COMMON_TYPES.get(element["element"], element["element"])
            else:
                raise NotImplementedError(f"No supporting {element['class_type']} yet.")
    else:
        atype = None

    expr: ast.Expr = ast.parse(f"_type={atype}").body[0]

    ast_module.body.append(
        ast.ClassDef(
            name,
            [_BCS_OPTIONAL_BASE],
            [],
            [
                ast.Assign(
                    [ast.Name("_type", ast.Store())],
                    expr.value,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )
    )


def gen_array_field(*, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
    """Generate an array of type."""
    adef = spec.get("array_definition")
    aelement = adef.get("element")
    if isinstance(aelement, str):
        atype = _BCS_COMMON_TYPES.get(aelement, aelement)
    else:
        raise NotImplementedError("Non-string element for array")
    sstr = f"('{name}',canoser.ArrayT({atype},{adef.get('fixed_length', None)},{adef.get('encode_length', True)}))"
    expr: ast.Expr = ast.parse(sstr).body[0]
    ast_field.elts.append(expr.value)


def gen_list_field(*, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
    """Generate an array of type."""
    atype = _BCS_COMMON_TYPES.get(spec["element"], spec["element"])
    sstr = f"('{name}',[{atype}])"
    expr: ast.Expr = ast.parse(sstr).body[0]
    ast_field.elts.append(expr.value)


def gen_tuple_field(*, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
    """."""
    field_targets: ast.Tuple = ast.Tuple([], ast.Load)
    for field in spec["elements"]:
        process_json(field_targets, field)
    cname = ast.Constant(name, str)
    ast_field.elts.append(ast.Tuple([cname, field_targets], ast.Load()))


def gen_inner_reference(*, ast_field: ast.Tuple, spec: dict) -> ast.Tuple:
    """."""
    atype = _BCS_COMMON_TYPES.get(spec["element"], spec["element"])
    expr: ast.Expr = ast.parse(atype).body[0]
    ast_field.elts.append(expr.value)


def gen_reference_field(*, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
    """."""
    atype = _BCS_COMMON_TYPES.get(spec["element"], spec["element"])
    sstr = f"('{name}',{atype})"
    expr: ast.Expr = ast.parse(sstr).body[0]
    ast_field.elts.append(expr.value)


def gen_constant_field(*, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
    """."""
    ispec = spec.get("element", None)
    if ispec and isinstance(ispec, dict):
        if atype := _BCS_COMMON_TYPES.get(ispec["constant_type"]):
            sstr = f"('{name}',{ispec['constant_value']})"
            expr: ast.Expr = ast.parse(sstr).body[0]
            ast_field.elts.append(expr.value)
            return expr.value
    raise ValueError(f"Constant {ispec} not recognized")


def process_json(ast_module: Any, spec: dict) -> Any:
    """."""
    match spec["class_type"]:
        case "Structure":
            return gen_structure(
                name=spec["class_name"], ast_module=ast_module, spec=spec
            )
        case "Enum":
            return gen_enum(name=spec["class_name"], ast_module=ast_module, spec=spec)
        case "Optional":
            return gen_option(name=spec["class_name"], ast_module=ast_module, spec=spec)
        case "Array":
            return gen_array_field(
                name=spec["class_name"], ast_field=ast_module, spec=spec
            )
        case "List":
            return gen_list_field(
                name=spec["class_name"], ast_field=ast_module, spec=spec
            )
        case "Tuple":
            return gen_tuple_field(
                name=spec["class_name"], ast_field=ast_module, spec=spec
            )
        case "Reference":
            if c_name := spec.get("class_name", None):
                return gen_reference_field(name=c_name, ast_field=ast_module, spec=spec)
            else:
                return gen_inner_reference(ast_field=ast_module, spec=spec)
        case "Constant":
            return gen_constant_field(
                name=spec["class_name"], ast_field=ast_module, spec=spec
            )

    return None


def validate_json(*, resource_path: Path, json_file: str) -> dict:
    """Validate the JSON file with our schema."""
    schema_json = resource_path / "jtobcs_spec.json"
    schema = json.loads(schema_json.read_text(encoding="utf8"))
    json_data = json.loads(Path(json_file).read_text(encoding="utf8"))
    validate(json_data, schema)
    return json_data


def main():
    """Main execution for jtobcs."""
    res_path = Path(inspect.getfile(inspect.currentframe())).parent
    parsed = parse_args([], os.getcwd(), res_path / "jtobcs_sample.json")
    json_data = validate_json(resource_path=res_path, json_file=parsed.json_input_file)
    pre_file = res_path / "jtobcs_pre.py"
    module_name = json_data["module"]
    pre_module: ast.Module = ast.parse(
        pre_file.read_text(encoding="utf8"), module_name, "exec"
    )
    for spec in json_data["classes"]:
        _ = process_json(pre_module, spec)
    print(ast.unparse(pre_module))
    # if parsed.target_output_folder == "con":
    #     print(ast.unparse(pre_module))
    # else:
    #     fpath = Path(parsed.target_output_folder) / f"{module_name}.py"
    #     fpath.write_text(ast.unparse(pre_module), encoding="utf8")


if __name__ == "__main__":
    main()
