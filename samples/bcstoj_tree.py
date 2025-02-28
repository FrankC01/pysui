#
"""."""

# pylint: disable=too-few-public-methods
from functools import reduce
from typing import Any, Optional, TypeVar


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
    """A node that is a container of tuples."""

    def __init__(self, *, to_parent: T, data: Optional[Any] = None):
        """For ListContainer with parent typlically being a Class definition node"""
        super().__init__(data=data, parent=to_parent)


class ListContainer(Node):
    """A node that is a container of tuples."""

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
    """."""

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
    """Generic n-ary tree."""

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

    def emit(self) -> list:
        """Emit the class constructs in tree."""
        res = [self.visit(x) for x in self.root_node.children]
        return res


if __name__ == "__main__":
    t = Tree("foo")
