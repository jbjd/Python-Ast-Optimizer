"""Minifier for Python ASTs."""

import ast
from ast import _Precedence  # type: ignore[attr-defined]
from collections.abc import Callable, Iterable, Iterator
from typing import Literal, LiteralString

_chars_that_dont_need_whitespace: list[str] = [
    "'",
    '"',
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "*",
]

_ast_comparisons: dict[str, str] = {
    "Eq": "==",
    "NotEq": "!=",
    "Lt": "<",
    "LtE": "<=",
    "Gt": ">",
    "GtE": ">=",
    "Is": " is ",
    "IsNot": " is not ",
    "In": " in ",
    "NotIn": " not in ",
}


_ast_operators_to_strip: list[str] = [
    ", ",
    ": ",
    " + ",
    " - ",
    " * ",
    " ** ",
    " @ ",
    " / ",
    " // ",
    " % ",
    " << ",
    " >> ",
    " | ",
    " & ",
    " ^ ",
]


class MinifyUnparser(ast._Unparser):  # type: ignore[misc, name-defined]
    """Turns a Python AST into source code in a minfied format."""

    __slots__ = ("can_write_body_in_one_line", "previous_node_in_body")

    def __init__(self) -> None:
        self._source: list[str]  # type: ignore[misc]
        self._indent: int  # type: ignore[misc]
        super().__init__()

        self.previous_node_in_body: ast.stmt | None = None
        self.can_write_body_in_one_line: bool = False

    def visit(self, node: ast.AST) -> str:
        """Outputs a source code string that, if converted back to an ast
        (using ast.parse) will generate an AST equivalent to *node*"""
        self.traverse(node)
        return "".join(self._source)

    def fill(self, text: str = "", splitter: Literal["", "\n", ";"] = "\n") -> None:
        """Overrides super fill to use tabs over spaces and different line splitters."""
        match splitter:
            case "\n":
                self.maybe_newline()
                self.write("\t" * self._indent + text)
            case "":
                self.write(text)
            case _:
                self.write(";" + text)

    def fill_literal(self, text: LiteralString) -> None:
        """Adds text to source without an additional parsing. Only use when text is
        known to contain no extra whitespace."""
        match self._get_line_splitter():
            case "\n":
                self.fill_literal_new_line(text)
            case "":
                self._source.append(text)
            case _:
                self._source.append(";" + text)

    def fill_literal_new_line(self, text: LiteralString) -> None:
        self.maybe_newline()
        self._source.append("\t" * self._indent + text)

    def fill_splitter(self) -> None:
        """Adds splitter to source based on previous node."""
        splitter: str = self._get_line_splitter()

        if splitter == ";":
            self._source.append(";")
        elif splitter == "\n":
            self.maybe_newline()
            if self._indent > 0:
                self._source.append("\t" * self._indent)

    def _get_line_splitter(self) -> Literal["", "\n", ";"]:
        """Get character that starts the next line of code with the shortest
        possible whitespace. Either a new line, semicolon, or nothing."""
        if self._source and self._source[-1] == ":" and self.can_write_body_in_one_line:
            return ""

        if (
            self._indent > 0
            and self.previous_node_in_body is not None
            and self._node_inlineable(self.previous_node_in_body)
        ):
            return ";"

        return "\n"

    def write(self, *text: str) -> None:
        """Write text, with some mapping replacements"""
        text = tuple(self._yield_updated_text(text))

        if not text:
            return

        first_letter_to_write: str = text[0][:1]
        if (
            first_letter_to_write in _chars_that_dont_need_whitespace
            and self._source
            and self._source[-1][-1] == " "
        ):
            self._source[-1] = self._source[-1][:-1]

        self._source.extend(text)

    def _yield_updated_text(self, text_iter: Iterable[str]) -> Iterator[str]:
        """Give text to be written, replace some specific occurrences
        and yield new results if not empty strings"""
        for text in text_iter:
            if text in _ast_operators_to_strip:
                yield text.strip()
                continue

            if text[:1] == " " and (
                not self._source
                or self._source[-1][-1] in _chars_that_dont_need_whitespace
            ):
                text = text[1:]  # noqa: PLW2901

            if text != "":
                yield text

    def _traverse_node(self, node: ast.AST) -> None:
        method: str = "visit_" + node.__class__.__name__
        visitor: Callable = getattr(self, method, self.generic_visit)  # type: ignore[assignment]
        return visitor(node)

    def traverse(self, node: list[ast.stmt] | ast.AST) -> None:
        if isinstance(node, list):
            self.can_write_body_in_one_line = (
                all(self._node_inlineable(sub_node) for sub_node in node)
                or len(node) == 1
            )
            self.previous_node_in_body = None

            for sub_node in node:
                self._traverse_node(sub_node)
                self.can_write_body_in_one_line = False
                self.previous_node_in_body = sub_node
        else:
            self._traverse_node(node)

    def visit_Break(self, _: ast.Break) -> None:
        self.fill_literal("break")

    def visit_Pass(self, _: ast.Pass | None = None) -> None:
        self.fill_literal("pass")

    def visit_Continue(self, _: ast.Continue) -> None:
        self.fill_literal("continue")

    def visit_Assert(self, node: ast.Assert) -> None:
        self.fill_literal("assert ")
        self.traverse(node.test)
        if node.msg:
            self._source.append(",")
            self.traverse(node.msg)

    def visit_Global(self, node: ast.Global) -> None:
        self._write_scope("global ", node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self._write_scope("nonlocal ", node.names)

    def _write_scope(self, scope: LiteralString, names: list[str]) -> None:
        self.fill_literal(scope)
        self.interleave(lambda: self._source.append(","), self._source.append, names)

    def visit_Delete(self, node: ast.Delete) -> None:
        self.fill_literal("del ")
        self._traverse_comma_delimitated_body(node.targets)

    def visit_Return(self, node: ast.Return) -> None:
        self.fill_literal("return")
        if node.value:
            self._source.append(" ")
            self.traverse(node.value)

    def visit_Raise(self, node: ast.Raise) -> None:
        if not node.exc:
            self.fill_literal("raise")
            return

        self.fill_literal("raise ")
        self.traverse(node.exc)

        if node.cause:
            self.write(" from ")
            self.traverse(node.cause)

    def visit_Expr(self, node: ast.Expr) -> None:
        self.fill_splitter()
        self.set_precedence(_Precedence.YIELD, node.value)
        self.traverse(node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        with self.require_parens(_Precedence.NAMED_EXPR, node):
            self.set_precedence(_Precedence.ATOM, node.target, node.value)
            self.traverse(node.target)
            self._source.append(":=")
            self.traverse(node.value)

    def visit_Import(self, node: ast.Import) -> None:
        self.fill_literal("import ")
        self._traverse_comma_delimitated_body(node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.fill_literal("from ")
        if node.level > 0:
            self._source.append("." * node.level)
        if node.module:
            self._source.append(node.module)
        self._source.append(" import ")
        self._traverse_comma_delimitated_body(node.names)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.fill_splitter()
        with self.delimit_if(
            "(", ")", not node.simple and isinstance(node.target, ast.Name)
        ):
            self.traverse(node.target)

        self._source.append(":")
        self.traverse(node.annotation)

        if node.value is not None:
            self._source.append("=")
            self._traverse_node(node.value)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.fill_splitter()

        for target in node.targets:
            self.set_precedence(_Precedence.TUPLE, target)  # type: ignore[attr-defined]
            self._traverse_node(target)
            self._source.append("=")

        self._traverse_node(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.fill_splitter()

        self._traverse_node(node.target)
        self._source.append(self.binop[node.op.__class__.__name__] + "=")
        self._traverse_node(node.value)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._write_decorators(node)
        self.fill_literal_new_line("class " + node.name)

        if hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)

        with self.delimit_if("(", ")", condition=node.bases or node.keywords):
            self._traverse_comma_delimitated_body(node.bases)
            self._traverse_comma_delimitated_body(node.keywords)

        with self.block():
            self._write_docstring_and_traverse_body(node)

    def _function_helper(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        fill_suffix: Literal["def", "async def"],
    ) -> None:
        self._write_decorators(node)
        self.fill_literal_new_line(f"{fill_suffix} {node.name}")

        if hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)

        with self.delimit("(", ")"):
            self._traverse_node(node.args)

        if node.returns:
            self._source.append("->")
            self._traverse_node(node.returns)

        with self.block(extra=self.get_type_comment(node)):
            self._write_docstring_and_traverse_body(node)

    def _write_decorators(
        self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        for deco in node.decorator_list:
            self.fill_literal_new_line("@")
            self.traverse(deco)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> None:
        self.fill("type ")
        self.traverse(node.name)
        self._type_params_helper(node.type_params)
        self.write("=")
        self.traverse(node.value)

    def visit_List(self, node: ast.List) -> None:
        with self.delimit("[", "]"):
            self._traverse_comma_delimitated_body(node.elts)

    def visit_Set(self, node: ast.Set) -> None:
        if node.elts:
            with self.delimit("{", "}"):
                self._traverse_comma_delimitated_body(node.elts)
        else:
            self._source.append("set()")

    def visit_Compare(self, node: ast.Compare) -> None:
        with self.require_parens(_Precedence.CMP, node):
            self.set_precedence(_Precedence.CMP.next(), node.left, *node.comparators)
            self.traverse(node.left)
            for op, comparator in zip(node.ops, node.comparators, strict=True):
                self.write(_ast_comparisons[op.__class__.__name__])
                self.traverse(comparator)

    def _traverse_comma_delimitated_body(
        self, body: list[ast.alias] | list[ast.expr] | list[ast.keyword]
    ) -> None:
        """Writes ast expr objects with comma delimitation"""
        self.interleave(lambda: self._source.append(","), self.traverse, body)

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
