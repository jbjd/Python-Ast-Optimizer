"""Minifier for Python ASTs."""

import ast
from collections.abc import Generator, Iterable
from contextlib import contextmanager
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

    def _write_many_asts(self, asts: Iterable[ast.AST], delimitor: str) -> None:
        for i, node in enumerate(asts):
            if i > 0:
                self._source.append(delimitor)
            self._visit_node(node)

    def _fill_literal(self, text: LiteralString) -> None:
        match self._get_line_splitter():
            case "\n":
                self._fill_literal_new_line(text)
            case "":
                self._source.append(text)
            case _:
                self._source.append(";")
                self._source.append(text)

    def _fill_literal_new_line(self, text: LiteralString | None = None) -> None:
        self._source.append("\n")
        self._source.append("\t" * self._indent)

        if text is not None:
            self._source.append(text)

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

    @contextmanager
    def _surround(self, start: str, end: str) -> Generator[None, None, None]:
        self._source.append(start)
        yield
        self._source.append(end)

    def visit_Expr(self, node: ast.Expr) -> None:
        self._fill_literal_new_line()
        # TODO: Precedence
        self.traverse(node.value)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # TODO: Precedence
        self._visit_node(node.value)

        # ```1.__abs__()``` is invalid but ```1 .__abs__()``` is valid
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
            self._source.append(" ")

        self._source.append(".")
        self._source.append(node.attr)

    def visit_Name(self, node: ast.Name) -> None:
        self._source.append(node.id)

    def visit_Constant(self, node: ast.Constant) -> None:

        value = node.value

        if isinstance(value, str):
            raise NotImplementedError

        if value is ...:
            self._source.append("...")
        else:
            if node.kind == "u":
                self._source.append("u")
            self._source.append(str(value))

    def visit_List(self, node: ast.List) -> None:
        with self._surround("[", "]"):
            self._write_many_asts(node.elts, ",")

    def visit_Set(self, node: ast.Set) -> None:
        if node.elts:
            with self._surround("{", "}"):
                self._write_many_asts(node.elts, ",")
        else:
            # ```{}``` is a dict, this is a hacky way to make a set
            self._source.append("{*()}")

    def visit_Break(self, _: ast.Break) -> None:
        self._fill_literal("break")

    def visit_Continue(self, _: ast.Continue) -> None:
        self._fill_literal("continue")

    def visit_Pass(self, _: ast.Pass) -> None:
        self._fill_literal("pass")

    def visit_Delete(self, node: ast.Delete) -> None:
        self._fill_literal("del ")
        self._write_many_asts(node.targets, ",")

    def visit_Assert(self, node: ast.Assert) -> None:
        self._fill_literal("assert ")
        self._visit_node(node.test)

        if node.msg is not None:
            self._source.append(",")
            self._visit_node(node.msg)

    def visit_Import(self, node: ast.Import) -> None:
        self._fill_literal("import ")
        self._write_many_asts(node.names, ",")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self._fill_literal("from ")
        if node.level > 0:
            self._source.append("." * node.level)
        if node.module:
            self._source.append(node.module)
        self._source.append(" import ")
        self._write_many_asts(node.names, ",")

    def visit_alias(self, node: ast.alias) -> None:
        self._source.append(node.name)

        if node.asname:
            self._source.append(" as ")
            self._source.append(node.asname)

    def _write_type_params(self, type_params: list[ast.type_param]) -> None:
        if type_params:
            with self._surround("[", "]"):
                self._write_many_asts(type_params, ",")

    def visit_TypeVar(self, node: ast.TypeVar) -> None:
        self._source.append(node.name)

        if node.bound is not None:
            self._source.append(":")
            self._visit_node(node.bound)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> None:
        self._fill_literal("type ")
        self.visit_Name(node.name)

        self._write_type_params(node.type_params)

        self._source.append("=")
        self._visit_node(node.value)

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
