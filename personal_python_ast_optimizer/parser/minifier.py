import ast
from ast import _Unparser  # type: ignore
from typing import Literal

from personal_python_ast_optimizer.python_info import (
    chars_that_dont_need_whitespace,
    comparison_and_conjunctions,
    operators_and_separators,
)


class MinifyUnparser(_Unparser):

    __slots__ = ("is_last_node_in_body", "previous_node_in_body")

    def __init__(self) -> None:
        self._source: list[str]  # type: ignore
        self._indent: int  # type: ignore
        super().__init__()

        self.previous_node_in_body: ast.stmt | None = None
        self.is_last_node_in_body: bool = False

    def fill(self, text: str = "", splitter: Literal["", "\n", ";"] = "\n") -> None:
        """Overrides super fill to use tabs over spaces and different line splitters"""
        if text == "" and (splitter == "" or not self._source):
            return

        match splitter:
            case "\n":
                self.maybe_newline()
                self.write("\t" * self._indent + text)
            case "":
                self.write(text)
            case _:
                self.write(f";{text}")

    def write(self, *text: str) -> None:
        """Write text, with some mapping replacements"""
        if len(text) == 0:
            return

        text = tuple(map(self._update_text_to_write, text))

        first_letter_to_write: str = text[0][:1]
        if (
            first_letter_to_write in chars_that_dont_need_whitespace
            and self._last_char_is(" ")
        ):
            self._source[-1] = self._source[-1][:-1]

        self._source.extend(text)

    def _update_text_to_write(self, text: str) -> str:
        """Give text to be written, replace some specific occurrences"""
        if text in operators_and_separators:
            return text.strip()

        if text in comparison_and_conjunctions:
            return self._get_space_before_write() + text[1:]

        return text

    def maybe_newline(self) -> None:
        if self._source and self._source[-1] != "\n":
            self.write("\n")

    def visit_node(
        self,
        node: ast.AST,
        is_last_node_in_body: bool = False,
        last_visited_node: ast.stmt | None = None,
    ) -> None:
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)

        self.is_last_node_in_body = is_last_node_in_body
        self.previous_node_in_body = last_visited_node

        return visitor(node)  # type: ignore

    def traverse(self, node: list[ast.stmt] | ast.AST) -> None:
        if isinstance(node, list):
            last_visited_node: ast.stmt | None = None
            last_index = len(node) - 1
            for index, item in enumerate(node):
                is_last_node_in_body: bool = index == last_index
                self.visit_node(item, is_last_node_in_body, last_visited_node)
                last_visited_node = item
        else:
            self.visit_node(node)

    def visit_Break(self, _: ast.Break) -> None:
        self.fill("break", splitter=self._get_line_splitter())

    def visit_Pass(self, _: ast.Pass | None = None) -> None:
        self.fill("pass", splitter=self._get_line_splitter())

    def visit_Continue(self, _: ast.Continue) -> None:
        self.fill("continue", splitter=self._get_line_splitter())

    def visit_Assert(self, node: ast.Assert) -> None:
        self.fill("assert ", splitter=self._get_line_splitter())
        self.traverse(node.test)
        if node.msg:
            self.write(", ")
            self.traverse(node.msg)

    def visit_Return(self, node: ast.Return) -> None:
        self.fill("return", splitter=self._get_line_splitter())
        if node.value:
            self.write(" ")
            self.traverse(node.value)

    def visit_Raise(self, node: ast.Raise) -> None:
        self.fill("raise", splitter=self._get_line_splitter())

        if not node.exc:
            if node.cause:
                raise ValueError("Node can't use cause without an exception.")
            return

        self.write(" ")
        self.traverse(node.exc)

        if node.cause:
            self.write(" from ")
            self.traverse(node.cause)

    def visit_Expr(self, node: ast.Expr) -> None:
        self.fill(splitter=self._get_line_splitter())
        self.set_precedence(ast._Precedence.YIELD, node.value)  # type: ignore
        self.traverse(node.value)

    def visit_Import(self, node: ast.Import) -> None:
        self.fill("import ", splitter=self._get_line_splitter())
        self.interleave(lambda: self.write(","), self.traverse, node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.fill("from ", splitter=self._get_line_splitter())
        self.write("." * (node.level or 0))
        if node.module:
            self.write(node.module)
        self.write(" import ")
        self.interleave(lambda: self.write(","), self.traverse, node.names)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.fill(splitter=self._get_line_splitter())
        for target in node.targets:
            self.set_precedence(ast._Precedence.TUPLE, target)  # type: ignore
            self.traverse(target)
            self.write("=")
        self.traverse(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.fill(splitter=self._get_line_splitter())
        self.traverse(node.target)
        self.write(self.binop[node.op.__class__.__name__] + "=")
        self.traverse(node.value)

    def _last_char_is(self, char_to_check: str) -> bool:
        return len(self._source) > 0 and self._source[-1][-1:] == char_to_check

    def _get_space_before_write(self) -> str:
        if not self._source:
            return ""
        most_recent_token: str = self._source[-1]
        return "" if most_recent_token[-1:] in chars_that_dont_need_whitespace else " "

    def _get_line_splitter(self) -> Literal["", "\n", ";"]:
        """Get character that starts the next line of code with the shortest
        possible whitespace. Either a new line, semicolon, or nothing."""
        if (
            len(self._source) > 0
            and self._source[-1] == ":"
            and self.is_last_node_in_body
        ):
            return ""

        previous_node_class: str = self.previous_node_in_body.__class__.__name__
        if self._indent > 0 and previous_node_class in [
            "Assert",
            "Assign",
            "AugAssign",
            "Expr",
            "Import",
            "ImportFrom",
        ]:
            return ";"

        return "\n"
