#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""BCS to Json generator."""

import ast
import json
import os
from pathlib import Path
from typing import Any

import bcstoj_tree as ntree


# pylint: disable=invalid-name
class ListFields(ast.NodeVisitor):
    """."""

    _STD_CANOSER_TYPES: dict[str, str] = {
        "Uint8": "u8",
        "Uint16": "u16",
        "Uint32": "u32",
        "Uint64": "u64",
        "Uint128": "u128",
        "Uint256": "u256",
        "str": "string",
    }

    def __init__(self, tree_node: ntree.Node):
        self.current_node: ntree.Node = tree_node

    def visit_List(self, ast_node: ast.List):
        """A list may be the start of field tuples or rhs of an individual tuple."""
        # Root has no parent so it is primary field/enum
        if isinstance(self.current_node, ntree.ClassDeclaration):
            self.current_node = ntree.ListContainer(to_parent=self.current_node)
        # Otherwise we have a list as the tuple value
        else:
            self.current_node = ntree.ListType(
                data={"class_type": "List"}, to_parent=self.current_node
            )

        for lchild in ast_node.elts:
            self.visit(lchild)

        # Reset to parent
        self.current_node = self.current_node.parent_node

    def visit_Tuple(self, ast_node: ast.Tuple):
        """A tuple may be the field assignment tuple or the rhs of the tuple."""
        cnodes: list[ast.AST] = ast_node.elts
        if len(cnodes) > 1:
            # This is the assignment designation for 1 field or enum
            if isinstance(cnodes[0], ast.Constant):
                self.current_node = ntree.TupleAssignmentNode(
                    data={"class_name": cnodes[0].value}, to_parent=self.current_node
                )
                print(f"Tuple for {cnodes[0].value}")
                cnodes = cnodes[1:]
            # The field assignment from above, contains a tuple
            else:
                self.current_node = ntree.TupleType(
                    data={"class_type": "Tuple"}, to_parent=self.current_node
                )
        for gcnode in cnodes:
            self.visit(gcnode)

        self.current_node = self.current_node.parent_node

    def visit_Attribute(self, ast_node: ast.Attribute):
        """Attribute reference handler."""
        att_val = self._STD_CANOSER_TYPES.get(ast_node.attr, ast_node.attr)
        att_src = ast_node.value.id
        ntree.AttributeReference(
            data={"att_src": att_src, "att_val": att_val}, to_parent=self.current_node
        )

    def visit_Name(self, ast_node: ast.Name):
        """Name handling, likely the argument to tuple assignment."""
        ntree.NameType(data={"name_id": ast_node.id}, to_parent=self.current_node)

    def visit_Constant(self, node: ast.Constant):
        """Constant handler for scalars."""

        if node.value is None:
            const_cls = "null"
        elif node.value in [True, False]:
            const_cls = "bool"
        elif isinstance(node.value, int):
            const_cls = "int"
        elif isinstance(node.value, str):
            const_cls = "str"
        else:
            raise NotImplementedError(f"Not handling constant {node.value} types")

        ntree.ConstantType(
            data={"type": const_cls, "value": node.value},
            to_parent=self.current_node,
        )

    def visit_Call(self, ast_node: ast.Call):
        """Commonly for Array but TBD."""
        func_attr: ast.Attribute = ast_node.func
        func_decl_class: str = func_attr.attr
        func_decl_module: str = func_attr.value.id

        if func_decl_module != "canoser":
            raise NotImplementedError(f"Not handling module {func_decl_module} yet")

        match func_decl_class:
            case "ArrayT":
                func_decl_class = "Array"
            case _:
                raise NotImplementedError(f"Not handling type {func_decl_class} yet")
        self.current_node = ntree.ArrayType(
            data={"class_type": "Array"}, to_parent=self.current_node
        )

        for cargs in ast_node.args:
            self.visit(cargs)
        self.current_node = self.current_node.parent_node


class Declarations(ast.NodeVisitor):
    """."""

    _ASSIGN_TYPES: list[str] = ["_fields", "_enums", "_type"]
    _JSON_TYPES: list[str] = ["fields", "enums", "element"]

    def __init__(self, tree_root: ntree.Node):
        self.root_node: ntree.Node = tree_root
        self.tree_node: ntree.Node = None

    def valid_base(self, ast_node: ast.Attribute) -> tuple[str, str, Any]:
        """."""
        if isinstance(ast_node.value, ast.Name) and ast_node.value.id != "canoser":
            return False
        match ast_node.attr:
            case "Struct":
                return ("Structure", "fields", [])
            case "RustEnum":
                return ("Enum", "enums", [])
            case "RustOptional":
                return ("Optional", "element", None)
            case _:
                return False

    def handle_fields(self, ast_node: ast.List) -> ntree.Node:
        """Handles fields for canoser.Sstruct."""
        print(f"Fields for {self.tree_node.node_data['class_name']}")
        list_handler = ListFields(self.tree_node)
        list_handler.visit(ast_node)
        return list_handler.current_node
        # print(ast.dump(node, True, False, indent=2))

    def handle_enums(self, ast_node: ast.List) -> ntree.Node:
        """Handles enums for canoser.RustEnum."""
        print(f"Enums for {self.tree_node.node_data['class_name']}")
        list_handler = ListFields(self.tree_node)
        list_handler.visit(ast_node)
        return list_handler.current_node
        # print(ast.dump(node, True, False, indent=2))

    def handle_element(self, ast_node: ast.AST) -> ntree.Node:
        """Handles element primarily for canoser.RustOptional."""
        print(f"Element for {self.tree_node.node_data['class_name']}")
        list_handler = ListFields(self.tree_node)
        list_handler.visit(ast_node)
        return list_handler.current_node
        # print(ast.dump(node, True, False, indent=2))

    def visit_Assign(self, ast_node: ast.Assign) -> ntree.Node:
        """."""
        if ast_node.targets and ast_node.targets[0].id in self._ASSIGN_TYPES:
            targ = ast_node.targets[0]
            fcont = self._JSON_TYPES[self._ASSIGN_TYPES.index(targ.id)]
            match fcont:
                case "fields":
                    return self.handle_fields(ast_node.value)
                case "enums":
                    return self.handle_enums(ast_node.value)
                case "element":
                    return self.handle_element(ast_node.value)

    def visit_ClassDef(self, ast_node: ast.ClassDef):
        """."""
        class_decl: dict[str, str] = {}
        for base in ast_node.bases:
            if vb := self.valid_base(base):
                clz_name, clz_data, clz_cont = vb
                class_decl["class_name"] = ast_node.name
                class_decl["class_type"] = clz_name
                class_decl[clz_data] = clz_cont
                self.tree_node = ntree.ClassDeclaration(
                    data=class_decl, to_parent=self.root_node
                )
                # self.tree_node = self.root_node.add_child(class_decl)
                if x := list(
                    filter(lambda x: isinstance(x, ast.Assign), ast_node.body)
                ):
                    for assign in x:
                        x = self.visit(assign)
                        print()
                self.tree_node = None
        print()


# pylint: enable=invalid-name


def main():
    """Main execution for jtobcs."""
    res_path = Path(
        os.getcwd()
    )  # Path(inspect.getfile(inspect.currentframe())).parent.parent
    # catalog = create_catalog("2020-12")
    # parsed = parse_args([], os.getcwd(), "jtobcs_sample.json")
    # json_data = validate_json(catalog=catalog, resource_path=res_path)
    pre_file = res_path / "samples/bcs_samp.py"
    # module_name = json_data["module"]
    pre_module: ast.Module = ast.parse(
        pre_file.read_text(encoding="utf8"), "samples/bcs_samp.py", "exec"
    )
    parse_tree: ntree.Tree = ntree.Tree("classes")
    decls = Declarations(parse_tree.root)
    decls.visit(pre_module)
    jstr = json.dumps({"module": "foo", "classes": parse_tree.emit()}, indent=2)
    print(jstr)


if __name__ == "__main__":
    main()
