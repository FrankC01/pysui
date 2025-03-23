#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""BCS ast helpers."""

import ast
import copy
from collections import deque
from typing import Any, Optional, Union


class Node:
    """Generic Node."""

    def __init__(self, ident: str, data: Any, children: list[Any]):
        """Node Initializer."""
        self.ident: str = ident
        self.data: Any = data
        self.children: list = children if children else []


class NodeVisitor:
    """A specific visitor for traversing a tree to express python ast."""

    def __init__(self, ast_module: ast.Module):
        self.optional_stub = ast_module.body.pop()
        self.ast_module = ast_module
        self.stack = deque()

    def get(self) -> ast.AST:
        """LIFO pop."""
        return self.stack.pop()

    def put(self, element: ast.AST):
        """LIFO push"""
        self.stack.append(element)

    def peek_last(self) -> ast.AST:
        """LIFO peek last element."""
        return self.stack[0]

    def peek_first(self) -> ast.AST:
        """LIFO peek last element."""
        return self.stack[-1]

    def first_from_top(self, clz_type: ast.AST) -> Union[ast.AST, None]:
        """Finds first of matching type in stack."""
        for ast_type in reversed(self.stack):
            if isinstance(ast_type, clz_type):
                return ast_type
        return None

    def visit(self, node: Node):
        """Visit a node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Node):
        """Called if no explicit visitor function exists for a node."""
        print(f"Skipping {node.__class__.__name__} for '{node.ident}'")
        for value in self._iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, BcsAst.Node):
                        self.visit(item)
            elif isinstance(value, BcsAst.Node):
                self.visit(value)

    def _iter_fields(self, node: Node):
        """
        Yield a Node for each child in ``node.children``
        that is present on *node*.
        """
        for field in node.children:
            try:
                yield field
            except AttributeError:
                pass


class BcsAst:
    """BCS ast type helper class."""

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

    CONSTANT_TRUE = ast.Constant(True)
    CONSTANT_FALSE = ast.Constant(False)
    CONSTANT_NONE = ast.Constant(None)

    @classmethod
    def structure_base(
        clz, name: str, field_expr: ast.AST, class_doc: Optional[str] = None
    ) -> ast.ClassDef:
        """Return a canoser Struct class definition."""
        field_assign = ast.Assign(
            [ast.Name("_fields", ast.Store())],
            field_expr,
            type_comment=None,
            lineno=0,
        )
        if class_doc:
            body = [ast.Expr(ast.Constant(class_doc, str)), field_assign]
        else:
            body = [field_assign]

        return ast.ClassDef(
            name,
            [clz._BCS_STRUCT_BASE],
            [],
            body,
            [],
        )

    @classmethod
    def enum_base(
        clz, name: str, field_expr: ast.AST, class_doc: Optional[str] = None
    ) -> ast.ClassDef:
        """Return a canoser RustEnum class definition."""
        field_assign = ast.Assign(
            [ast.Name("_enums", ast.Store())],
            field_expr,
            type_comment=None,
            lineno=0,
        )
        if class_doc:
            body = [ast.Expr(ast.Constant(class_doc, str)), field_assign]
        else:
            body = [field_assign]

        return ast.ClassDef(
            name,
            [clz._BCS_ENUM_BASE],
            [],
            body,
            [],
        )

    @classmethod
    def optional_base(
        clz, name: str, field_expr: ast.AST, class_doc: Optional[str] = None
    ) -> ast.ClassDef:
        """Return a canoser RustOptional class definition."""

        field_assign = ast.Assign(
            [ast.Name("_type", ast.Store())],
            field_expr,
            type_comment=None,
            lineno=0,
        )
        if class_doc:
            body = [ast.Expr(ast.Constant(class_doc, str)), field_assign]
        else:
            body = [field_assign]

        return ast.ClassDef(
            name,
            [clz._BCS_OPTIONAL_BASE],
            [],
            body,
            [],
        )

    @classmethod
    def optional_type(
        clz,
        walker: NodeVisitor,
        name: str,
        field_expr: ast.AST,
        class_doc: Optional[str] = None,
    ) -> ast.ClassDef:
        """."""
        ocopy: ast.ClassDef = copy.deepcopy(walker.optional_stub)
        tjfn: ast.FunctionDef = ocopy.body.pop()
        field_assign = ast.Assign(
            [ast.Name("_type", ast.Store())],
            field_expr,
            type_comment=None,
            lineno=0,
        )
        if class_doc:
            body = [ast.Expr(ast.Constant(class_doc, str)), field_assign, tjfn]
        else:
            body = [field_assign, tjfn]

        ocopy.name = name
        ocopy.body = body
        return ocopy

    @classmethod
    def generate_nested_vector(
        clz, depth: int, walker: NodeVisitor, node: Node
    ) -> ast.List:
        """Create a BCS list or depth list of lists of data type in node."""
        assert depth > 0
        # Create the root most list and visit the type of list
        walker.put(ast.List([], ast.Load))
        walker.visit(node.data)
        core_list = walker.get()
        core_list.elts.extend([clz.CONSTANT_NONE, clz.CONSTANT_TRUE])
        # If depth > 1 then wrap the root list
        depth -= 1
        while depth:
            core_list = ast.List(
                [core_list, clz.CONSTANT_NONE, clz.CONSTANT_TRUE], ast.Load
            )
            depth -= 1
        return core_list

    @classmethod
    def fully_qualified_reference(clz, fval: dict) -> str:
        """Conjoins package, module, struct/enum from datatype."""
        return "::".join([fval["package"], fval["module"], fval["type"]])
