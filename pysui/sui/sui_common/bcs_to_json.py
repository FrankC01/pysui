#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-


"""BCS to Json generator."""

import ast

# pylint: disable=too-few-public-methods
from functools import reduce
import json
from pathlib import Path
from typing import Any, Optional, TypeVar
import inspect

from jsonschema import validate

T = TypeVar("T", bound="Node")


class Node:
    """Generic Node has data and potential children."""

    def __init__(self, *, data: Optional[Any] = None, parent: Optional[T] = None):
        self.node_data: Any = data
        self.children: list[T] = []
        self.parent_node = None
        if parent:
            parent.children.append(self)
            self.parent_node = parent

    def add_child(self, data: Optional[Any] = None) -> T:
        """Add a child to this node and return the new node."""
        n = Node(data=data, parent=self)
        self.children.append(n)
        return n


class ClassDeclaration(Node):
    """A node that is a container of field tuples or expression."""

    def __init__(self, *, to_parent: T, data: Optional[Any] = None):
        """For ListContainer with parent typlically being a Class definition node"""
        super().__init__(data=data, parent=to_parent)


class ListContainer(Node):
    """A node that is a container of tuples when for a Structure or Enum."""

    def __init__(self, *, to_parent: T, data: Optional[Any] = None):
        """For ListContainer with parent typlically being a Class definition node"""
        super().__init__(data=data, parent=to_parent)


class TupleAssignmentNode(Node):
    """A tuple with assignment node."""

    def __init__(self, *, data: Any, to_parent: T):
        """For TupleAssignment with parent typlically being a ListContainer node"""
        super().__init__(data=data, parent=to_parent)


class TupleType(Node):
    """A tuple construct."""

    def __init__(self, *, data: Any, to_parent: T):
        """For Tuple type with parent typlically being another type"""
        super().__init__(data=data, parent=to_parent)


class ListType(Node):
    """A list construct."""

    def __init__(self, *, data: Any, to_parent: T):
        """For List type with parent typlically being another type"""
        super().__init__(data=data, parent=to_parent)


class MapType(Node):
    """A Map (dict) type construct."""

    def __init__(self, *, data: Any, to_parent: T):
        """For Map (dict) type with parent typlically being construct of field/enum tuple."""
        super().__init__(data=data, parent=to_parent)


class ArrayType(Node):
    """A array construct."""

    def __init__(self, *, data: Any, to_parent: T):
        """For Array type with parent typlically being another type"""
        super().__init__(data=data, parent=to_parent)


class ConstantType(Node):
    """A constant value."""

    def __init__(self, *, data: Any, to_parent: T):
        """For scalar constants."""
        super().__init__(data=data, parent=to_parent)


class NameType(Node):
    """A Name constant value."""

    def __init__(self, *, data: Any, to_parent: T):
        """For named assignments. Likley referring to some other class."""
        super().__init__(data=data, parent=to_parent)


class AttributeReference(Node):
    """An attribute used in container types."""

    def __init__(self, *, data: Any, to_parent: T):
        """For a reference attribute from explicit module."""
        super().__init__(data=data, parent=to_parent)


class TreeVisitor:
    """A specific visitor for traversing a tree."""

    def visit(self, node: Node):
        """Visit a node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Node):
        """Called if no explicit visitor function exists for a node."""
        print(f"Skipping {node.__class__.__name__}")
        for value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, Node):
                        self.visit(item)
            elif isinstance(value, Node):
                self.visit(value)


def iter_fields(node: Node):
    """
    Yield a Node for each child in ``node.children``
    that is present on *node*.
    """
    for field in node.children:
        try:
            yield field
        except AttributeError:
            pass


# pylint: disable=invalid-name
class Tree(TreeVisitor):
    """Generic n-ary tree as IR to json."""

    def __init__(self, name):
        """."""
        self.root_node: Node = Node(data=name)

    @property
    def root(self) -> Node:
        """."""
        return self.root_node

    def visit_ConstantType(self, node: ConstantType) -> dict:
        """."""
        if node.node_data["type"] == "null":
            return {
                "class_type": "Constant",
                "element": {
                    "constant_type": node.node_data["type"],
                },
            }
        return {
            "class_type": "Constant",
            "element": {
                "constant_type": node.node_data["type"],
                "constant_value": node.node_data["value"],
            },
        }
        # pass

    def visit_NameType(self, node: NameType) -> dict:
        """."""
        return {"class_type": "Reference", "element": node.node_data["name_id"]}

    def visit_AttributeReference(self, node: AttributeReference) -> dict:
        """."""
        if node.node_data["att_src"] == "canoser":
            return {"class_type": "Reference", "element": node.node_data["att_val"]}
        concat = f"{node.node_data['att_src']}.{node.node_data['att_val']}"
        return {"class_type": "Reference", "element": concat}

    def visit_TupleType(self, node: TupleType) -> dict:
        """An inner type of some TupleAssignmentNode hierarchy."""
        return {
            "class_type": "Tuple",
            "elements": [self.visit(x) for x in node.children],
        }

    def visit_TupleAssignmentNode(self, node: TupleAssignmentNode) -> dict:
        """A tuple has a identifier and an expression"""
        # print()
        return reduce(
            lambda a, b: a | b, [self.visit(x) for x in node.children], node.node_data
        )

    def visit_MapType(self, node: MapType) -> dict:
        """A maptype has a key/value declaration."""
        ugga = [self.visit(x) for x in node.children]
        mt_key = node.children[0].node_data
        return {
            "class_type": "Map",
            "map_definition": {"map_key": ugga[0], "map_value": ugga[1]},
        }

    def visit_ArrayType(self, node: ArrayType) -> dict:
        """."""
        parms = [self.visit(x) for x in node.children]
        array_definition: dict = {
            "element": None,
            "fixed_length": None,
            "encode_length": True,
        }
        for parm in parms:
            if parm["class_type"] == "Reference":
                array_definition["element"] = parm["element"]
            elif (
                parm["class_type"] == "Constant"
                and parm["element"]["constant_type"] == "int"
            ):
                array_definition["fixed_length"] = parm["element"]["constant_value"]
            elif (
                parm["class_type"] == "Constant"
                and parm["element"]["constant_type"] == "bool"
            ):
                array_definition["encode_length"] = parm["element"]["constant_value"]

        return {"class_type": "Array", "array_definition": array_definition}
        # print()

    def visit_ListType(self, node: ListType) -> dict:
        """."""
        x = self.visit(node.children[0])
        return x | node.node_data

    def visit_ListContainer(self, node: ListContainer) -> list:
        """."""
        return [self.visit(x) for x in node.children]

    def visit_ClassDeclaration(self, node: ClassDeclaration):
        """."""
        x = self.visit(node.children[0])
        if node.node_data["class_type"] == "Structure":
            node.node_data["fields"] = x
        elif node.node_data["class_type"] == "Enum":
            node.node_data["enums"] = x
        elif node.node_data["class_type"] == "Optional":
            node.node_data["element"] = x
        return node.node_data

    @classmethod
    def validate_json_data(clz, *, json_data: dict) -> dict:
        """Validate the JSON data with schema."""
        resource_path = Path(inspect.getfile(inspect.currentframe())).parent
        schema_json = resource_path / "jtobcs_spec.json"
        schema = json.loads(schema_json.read_text(encoding="utf8"))
        validate(json_data, schema)
        return json_data

    def emit_json(self, module_name: str) -> str:
        """Emit the class constructs in tree to json."""
        res = [self.visit(x) for x in self.root_node.children]
        json_data = {"module": module_name, "classes": res}
        return json.dumps(self.validate_json_data(json_data=json_data), indent=2)


# pylint: disable=invalid-name
class ListFields(ast.NodeVisitor):
    """A tree visitor of the python AST for `_fields` or `_enums` resolution."""

    _STD_CANOSER_TYPES: dict[str, str] = {
        "Uint8": "u8",
        "Uint16": "u16",
        "Uint32": "u32",
        "Uint64": "u64",
        "Uint128": "u128",
        "Uint256": "u256",
        "str": "string",
    }

    def __init__(self, tree_node: Node):
        self.current_node: Node = tree_node

    def visit_List(self, ast_node: ast.List):
        """A list may be the start of field tuples or rhs of an individual tuple."""
        # Root has no parent so it is primary field/enum
        if isinstance(self.current_node, ClassDeclaration):
            self.current_node = ListContainer(to_parent=self.current_node)
        # Otherwise we have a list as the tuple value
        else:
            self.current_node = ListType(
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
                self.current_node = TupleAssignmentNode(
                    data={"class_name": cnodes[0].value}, to_parent=self.current_node
                )
                # print(f"Tuple for {cnodes[0].value}")
                cnodes = cnodes[1:]
            # The field assignment from above, contains a tuple
            else:
                self.current_node = TupleType(
                    data={"class_type": "Tuple"}, to_parent=self.current_node
                )
        for gcnode in cnodes:
            self.visit(gcnode)

        self.current_node = self.current_node.parent_node

    def visit_Dict(self, ast_node: ast.Dict):
        self.current_node = MapType(
            data={"class_type": "Map"}, to_parent=self.current_node
        )
        self.visit(ast_node.keys[0])
        for mvalue in ast_node.values:
            self.visit(mvalue)

        print()

    def visit_Attribute(self, ast_node: ast.Attribute):
        """Attribute reference handler."""
        att_val = self._STD_CANOSER_TYPES.get(ast_node.attr, ast_node.attr)
        att_src = ast_node.value.id
        AttributeReference(
            data={"att_src": att_src, "att_val": att_val}, to_parent=self.current_node
        )

    def visit_Name(self, ast_node: ast.Name):
        """Name handling, likely the argument to tuple assignment."""
        NameType(data={"name_id": ast_node.id}, to_parent=self.current_node)

    def visit_Constant(self, node: ast.Constant):
        """Constant handler for scalars."""

        if node.value is None:
            const_cls = "null"
        elif node.value in [True, False]:
            const_cls = "boolean"
        elif isinstance(node.value, int):
            const_cls = "int"
        elif isinstance(node.value, str):
            const_cls = "str"
        else:
            raise NotImplementedError(f"Not handling constant {node.value} types")

        ConstantType(
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
        self.current_node = ArrayType(
            data={"class_type": "Array"}, to_parent=self.current_node
        )

        for cargs in ast_node.args:
            self.visit(cargs)
        self.current_node = self.current_node.parent_node


class Declarations(ast.NodeVisitor):
    """A tree visitor of the python AST for `Structure`,`RustEnum` or `RustOptional` resolution."""

    _ASSIGN_TYPES: list[str] = ["_fields", "_enums", "_type"]
    _JSON_TYPES: list[str] = ["fields", "enums", "element"]

    def __init__(self, tree_root: Node):
        self.root_node: Node = tree_root
        self.tree_node: Node = None

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

    def handle_fields(self, ast_node: ast.List) -> Node:
        """Handles fields for canoser.Sstruct."""
        # print(f"Fields for {self.tree_node.node_data['class_name']}")
        list_handler = ListFields(self.tree_node)
        list_handler.visit(ast_node)
        return list_handler.current_node
        # print(ast.dump(node, True, False, indent=2))

    def handle_enums(self, ast_node: ast.List) -> Node:
        """Handles enums for canoser.RustEnum."""
        # print(f"Enums for {self.tree_node.node_data['class_name']}")
        list_handler = ListFields(self.tree_node)
        list_handler.visit(ast_node)
        return list_handler.current_node
        # print(ast.dump(node, True, False, indent=2))

    def handle_element(self, ast_node: ast.AST) -> Node:
        """Handles element primarily for canoser.RustOptional."""
        # print(f"Element for {self.tree_node.node_data['class_name']}")
        list_handler = ListFields(self.tree_node)
        list_handler.visit(ast_node)
        return list_handler.current_node
        # print(ast.dump(node, True, False, indent=2))

    def visit_Assign(self, ast_node: ast.Assign) -> Node:
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
                self.tree_node = ClassDeclaration(
                    data=class_decl, to_parent=self.root_node
                )
                # self.tree_node = self.root_node.add_child(class_decl)
                if x := list(
                    filter(lambda x: isinstance(x, ast.Assign), ast_node.body)
                ):
                    for assign in x:
                        x = self.visit(assign)

                self.tree_node = None
