#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""BCS ast helpers."""

import ast
from collections import deque
from typing import Any, Union


class Node:
    """Generic Node."""

    def __init__(self, ident: str, data: Any, fields: list[Any]):
        """Node Initializer."""
        self.ident: str = ident
        self.data: Any = data
        self.fields: list = fields if fields else []


class NodeVisitor:
    """A specific visitor for traversing a tree to express python ast."""

    def __init__(self, ast_module: ast.Module):
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
        for field in node.fields:
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
    def structure_base(clz, name: str, field_expr: ast.AST):
        """Return a canoser Struct class definition."""
        return ast.ClassDef(
            name,
            [clz._BCS_STRUCT_BASE],
            [],
            [
                ast.Assign(
                    [ast.Name("_fields", ast.Store())],
                    field_expr,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )

    @classmethod
    def enum_base(clz, name: str, field_expr: ast.AST):
        """Return a canoser RustEnum class definition."""
        return ast.ClassDef(
            name,
            [clz._BCS_ENUM_BASE],
            [],
            [
                ast.Assign(
                    [ast.Name("_enums", ast.Store())],
                    field_expr,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )

    @classmethod
    def optional_base(clz, name: str, field_expr: ast.AST):
        """Return a canoser RustOptional class definition."""
        return ast.ClassDef(
            name,
            [clz._BCS_OPTIONAL_BASE],
            [],
            [
                ast.Assign(
                    [ast.Name("_type", ast.Store())],
                    field_expr,
                    type_comment=None,
                    lineno=0,
                )
            ],
            [],
        )
