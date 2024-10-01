#
"""QueryNode doc table generator."""

import ast
import os
from pathlib import Path


class PrintNodeVisitor(ast.NodeVisitor):
    def __init__(self, qpath: str):
        self.qpath = qpath
        self.title: str = ""
        self.py_clz: str = " :py:class:"
        self.py_clz_quote_sym = "`"
        self.row_sep_sym: str = "-"
        self.tit_sep_sym: str = "="
        self.row_corn_sym: str = "+"
        self.row_vert_sym: str = "|"
        self.qnodes: list[str] = []
        self.max_inner_str_len: int = 0
        self.max_max_len: int = 0
        self.single_bar: str = ""
        self.double_bar: str = ""

    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.ClassDef):
            self.qnodes.append(self.qpath + "." + node.name)
        return super().visit(node)

    def max_clzname_len(self) -> int:
        """Maximum length string."""
        return len(max(self.qnodes, key=len))

    def dump(self):
        """Dumps class list only."""
        for qnode in self.qnodes:
            print(qnode)

    def centered_sting(self, value: str) -> str:
        """Centers a string in available space"""
        buffer = self.max_max_len - len(value)
        buffer = int(buffer / 2)
        result = " " * buffer + value + " " * buffer
        # Adjust for odd number fill
        if fill := self.max_max_len - len(result):
            result = result + " " * fill
        return result

    def link_string(self, value: str) -> str:
        """Left justifies string in available space."""
        value = self.py_clz + self.py_clz_quote_sym + value + self.py_clz_quote_sym
        buffer = self.max_max_len - len(value)
        return self.row_vert_sym + value + " " * buffer + self.row_vert_sym

    @property
    def one_single_bar(self) -> str:
        """Straight single bar."""
        return self.row_corn_sym + self.single_bar + self.row_corn_sym

    @property
    def one_double_bar(self) -> str:
        """Straight single bar."""
        return self.row_corn_sym + self.double_bar + self.row_corn_sym

    def table_row(self, value: str) -> str:
        """Generate a table row"""
        return self.row_vert_sym + self.centered_sting(value) + self.row_vert_sym

    def format_table(self) -> str:
        """Generate the table string."""
        # calc max lengths
        self.max_inner_str_len = (
            self.max_clzname_len()
            + len(self.py_clz_quote_sym) * 2
            + len(self.py_clz)
            + 1
        )
        self.max_max_len = 2 + self.max_inner_str_len
        self.single_bar = self.row_sep_sym * self.max_max_len
        self.double_bar = self.tit_sep_sym * self.max_max_len
        table_rows: list[str] = []

        table_rows.append(self.one_single_bar)
        table_rows.append(self.table_row("Name"))
        table_rows.append(self.one_double_bar)
        for qnode in self.qnodes:
            table_rows.append(self.link_string(qnode))
            table_rows.append(self.one_single_bar)
        return "\n" + "\n".join(table_rows)


def generate_qnode_doc(template: Path, target: Path, data: str):
    """Create the table documentation."""
    if template.exists():
        if target.exists():
            os.remove(target)
        output_str = template.read_text(encoding="utf8") + data
        target.write_text(output_str, encoding="utf8")


if __name__ == "__main__":
    target = Path("./pysui/sui/sui_pgql/pgql_query.py")
    if target.exists():
        tree = target.read_text()
        pnv = PrintNodeVisitor("pysui.sui.sui_pgql.pgql_query")
        pnv.visit(ast.parse(tree))
        table = pnv.format_table()
        print(table)
        generate_qnode_doc(
            Path("./doc/source/_qnode_base.rst"),
            Path("./doc/source/graphql_qnodes.rst"),
            table,
        )
