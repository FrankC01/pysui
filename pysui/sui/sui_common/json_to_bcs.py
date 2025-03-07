#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Json to BCS generator."""

import ast
import json
import inspect
from pathlib import Path
from typing import Any, Union
from jsonschema import validate


class JsonToBcs:
    """JSON to BCS generator class."""

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
        "bytes": "bytes",
    }

    def __init__(self, module_name: str):
        """."""
        resource_path = Path(inspect.getfile(inspect.currentframe())).parent
        self.python_stub = resource_path / "jtobcs_pre.py"
        self.ast_module: ast.Module = ast.parse(
            self.python_stub.read_text(encoding="utf8"), module_name, "exec"
        )

    def _class_def(
        self, name: str, base: ast.Attribute, field_name: str, field_expr: ast.AST
    ) -> ast.ClassDef:
        """Class definition framework."""
        return ast.ClassDef(
            name,
            [base],
            [],
            [
                ast.Assign(
                    [ast.Name(field_name, ast.Store())],
                    field_expr,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )

    def _gen_structure(
        self, *, name: str, ast_module: Union[ast.AST, ast.Module], spec: dict
    ) -> ast.ClassDef:
        """Generate a BCS canoser Struct."""

        field_targets: ast.List = ast.List([], ast.Load)
        if fields := spec.get("fields"):
            for field in fields:
                self._process_json(field_targets, field)
        cdef = self._class_def(name, self._BCS_STRUCT_BASE, "_fields", field_targets)
        if isinstance(ast_module, ast.Module):
            ast_module.body.append(cdef)
        return cdef

    def _gen_enum(
        self, *, name: str, ast_module: Union[ast.AST, ast.Module], spec: dict
    ) -> ast.ClassDef:
        """Generate a BCS canoser RustEnum."""
        field_targets: ast.List = ast.List([], ast.Load)
        if fields := spec.get("enums"):
            for field in fields:
                self._process_json(field_targets, field)

        cdef = self._class_def(name, self._BCS_ENUM_BASE, "_enums", field_targets)
        if isinstance(ast_module, ast.Module):
            ast_module.body.append(cdef)
        return cdef

    def _gen_option(
        self, *, name: str, ast_module: Union[ast.AST, ast.Module], spec: dict
    ) -> ast.ClassDef:
        """Generate a BCS canoser RustOptional."""

        if element := spec.get("element"):
            if element and isinstance(element, dict):
                if element["class_type"] == "Reference":
                    atype = self._BCS_COMMON_TYPES.get(
                        element["element"], element["element"]
                    )
                else:
                    raise NotImplementedError(
                        f"Not supporting {element['class_type']} yet."
                    )
        else:
            atype = None

        expr: ast.Expr = ast.parse(f"_type={atype}").body[0]
        cdef = self._class_def(name, self._BCS_OPTIONAL_BASE, "_type", expr.value)

        if isinstance(ast_module, ast.Module):
            ast_module.body.append(cdef)

        return cdef

    def _gen_array_field(self, *, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
        """Generate an array of type."""
        adef = spec.get("array_definition")
        aelement = adef.get("element")
        if isinstance(aelement, str):
            atype = self._BCS_COMMON_TYPES.get(aelement, aelement)
        else:
            raise NotImplementedError("Non-string element for array")
        sstr = f"('{name}',canoser.ArrayT({atype},{adef.get('fixed_length', None)},{adef.get('encode_length', True)}))"
        expr: ast.Expr = ast.parse(sstr).body[0]
        ast_field.elts.append(expr.value)

    def _gen_list_field(self, *, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
        """Generate an list of type."""
        atype = self._BCS_COMMON_TYPES.get(spec["element"], spec["element"])
        sstr = f"('{name}',[{atype}])" if name else f"[{atype}]"
        expr: ast.Expr = ast.parse(sstr).body[0]
        ast_field.elts.append(expr.value)

    def _gen_map_field(self, *, name, ast_field: ast.List, spec: dict) -> ast.Dict:
        """Generate a dict type."""
        # To hold map and key
        field_targets: ast.Tuple = ast.Tuple([], ast.Load)
        self._process_json(field_targets, spec["map_definition"]["map_key"])
        self._process_json(field_targets, spec["map_definition"]["map_value"])
        mdict: ast.Dict = ast.Dict([], [])
        mdict.keys.append(field_targets.elts[0])
        mdict.values.append(field_targets.elts[1])
        ast_field.elts.append(ast.Tuple([ast.Constant(name, str), mdict], ast.Load()))

    def _gen_tuple_field(self, *, name, ast_field: ast.List, spec: dict) -> ast.Tuple:
        """."""
        field_targets: ast.Tuple = ast.Tuple([], ast.Load)
        for field in spec["elements"]:
            self._process_json(field_targets, field)
        cname = ast.Constant(name, str)
        ast_field.elts.append(ast.Tuple([cname, field_targets], ast.Load()))

    def _gen_reference_field(
        self, *, name, ast_field: ast.List, spec: dict
    ) -> ast.Tuple:
        """."""
        atype = self._BCS_COMMON_TYPES.get(spec["element"], spec["element"])
        sstr = f"('{name}',{atype})" if name else atype
        expr: ast.Expr = ast.parse(sstr).body[0]
        ast_field.elts.append(expr.value)

    def _gen_constant_field(
        self, *, name, ast_field: ast.List, spec: dict
    ) -> ast.Tuple:
        """."""
        ispec = spec.get("element", None)
        if ispec and isinstance(ispec, dict):
            if atype := self._BCS_COMMON_TYPES.get(ispec["constant_type"]):
                sstr = f"('{name}',{ispec['constant_value']})"
                expr: ast.Expr = ast.parse(sstr).body[0]
                ast_field.elts.append(expr.value)
                return expr.value
        raise ValueError(f"Constant {ispec} not recognized")

    def _process_json(self, ast_module: Any, spec: dict) -> Any:
        """."""
        match spec["class_type"]:
            case "Structure":
                return self._gen_structure(
                    name=spec["class_name"], ast_module=ast_module, spec=spec
                )
            case "Enum":
                return self._gen_enum(
                    name=spec["class_name"], ast_module=ast_module, spec=spec
                )
            case "Optional":
                return self._gen_option(
                    name=spec["class_name"], ast_module=ast_module, spec=spec
                )
            case "Array":
                return self._gen_array_field(
                    name=spec["class_name"], ast_field=ast_module, spec=spec
                )
            case "List":
                return self._gen_list_field(
                    name=spec.get("class_name"), ast_field=ast_module, spec=spec
                )
            case "Map":
                return self._gen_map_field(
                    name=spec["class_name"], ast_field=ast_module, spec=spec
                )
            case "Tuple":
                return self._gen_tuple_field(
                    name=spec["class_name"], ast_field=ast_module, spec=spec
                )
            case "Reference":
                return self._gen_reference_field(
                    name=spec.get("class_name"), ast_field=ast_module, spec=spec
                )
            case "Constant":
                return self._gen_constant_field(
                    name=spec["class_name"], ast_field=ast_module, spec=spec
                )

    def gen_module(self, *, json_data: dict) -> ast.Module:
        """Generates the python BCS from json data."""
        for spec in json_data["classes"]:
            self._process_json(self.ast_module, spec)
        return self.ast_module

    @classmethod
    def validate_json(clz, *, json_file: str) -> dict:
        """Validate the JSON file with schema."""
        resource_path = Path(inspect.getfile(inspect.currentframe())).parent
        schema_json = resource_path / "jtobcs_spec.json"
        schema = json.loads(schema_json.read_text(encoding="utf8"))
        json_data = json.loads(Path(json_file).read_text(encoding="utf8"))
        validate(json_data, schema)
        return json_data
