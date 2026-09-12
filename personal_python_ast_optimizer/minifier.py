"""Minifier for Python ASTs."""

import ast
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Literal, LiteralString

from personal_python_ast_optimizer.typing import Unparser

if TYPE_CHECKING:
    from collections.abc import Callable


class MinifyUnparser(Unparser):
    """Turns a Python AST into source code in a minfied format."""

    __slots__ = (
        "_indent",
        "_source",
        "can_write_body_in_one_line",
        "previous_node_in_body",
    )

    def __init__(self) -> None:
        self._indent: int = 0
        self._source: list[str] = []
        self.previous_node_in_body: ast.stmt | None = None
        self.can_write_body_in_one_line: bool = False

    def visit(self, node: ast.Module) -> str:
        for n in node.body:
            self._visit_node(n)

        return "".join(self._source)

    def traverse(self, node: list[ast.stmt] | ast.AST) -> None:
        if isinstance(node, list):
            self.can_write_body_in_one_line = (
                all(self._node_inlineable(sub_node) for sub_node in node)
                or len(node) == 1
            )
            self.previous_node_in_body = None

            for sub_node in node:
                self._visit_node(sub_node)
                self.can_write_body_in_one_line = False
                self.previous_node_in_body = sub_node
        else:
            self._visit_node(node)

    def _visit_node(self, node: ast.AST) -> None:
        method: str = "visit_" + node.__class__.__name__
        visitor: Callable = getattr(self, method)  # type: ignore[assignment]
        return visitor(node)

    def _write_iterable(self, body: Iterable[str], deliminator: LiteralString) -> None:
        for i, b in enumerate(body):
            if i > 0:
                self._source.append(deliminator)
            self._source.append(b)

    def _write_alias(self, aliases: list[ast.alias]) -> Iterator[str]:
        self._write_iterable(iter(n.name for n in aliases), ",")

    def _fill_literal(self, text: LiteralString) -> None:
        match self._get_line_splitter():
            case "\n":
                self._fill_literal_new_line(text)
            case "":
                self._source.append(text)
            case _:
                self._source.append(";")
                self._source.append(text)

    def _fill_literal_new_line(self, text: LiteralString) -> None:
        self._source.append("\n")
        self._source.append("\t" * self._indent + text)

    def _get_line_splitter(self) -> Literal["", "\n", ";"]:
        if not self._source or (
            self._source[-1] == ":" and self.can_write_body_in_one_line
        ):
            return ""

        if (
            self._indent > 0
            and self.previous_node_in_body is not None
            and self._node_inlineable(self.previous_node_in_body)
        ):
            return ";"

        return "\n"

    def visit_Break(self, _: ast.Break) -> None:
        self._fill_literal("break")

    def visit_Continue(self, _: ast.Continue) -> None:
        self._fill_literal("continue")

    def visit_Pass(self, _: ast.Pass) -> None:
        self._fill_literal("pass")

    def visit_Import(self, node: ast.Import) -> None:
        self._fill_literal("import ")
        self._write_alias(node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self._fill_literal("from ")
        if node.level > 0:
            self._source.append("." * node.level)
        if node.module:
            self._source.append(node.module)
        self._source.append(" import ")
        self._write_alias(node.names)

    @staticmethod
    def _node_inlineable(node: ast.AST) -> bool:
        return node.__class__.__name__ in [
            "Assert",
            "AnnAssign",
            "Assign",
            "AugAssign",
            "Break",
            "Continue",
            "Delete",
            "Expr",
            "Global",
            "Import",
            "ImportFrom",
            "Nonlocal",
            "Pass",
            "Raise",
            "Return",
        ]
