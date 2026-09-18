"""Minifier for Python ASTs."""

import ast
from collections.abc import Generator, Iterable
from contextlib import contextmanager, nullcontext
from typing import TYPE_CHECKING, Literal, LiteralString

from personal_python_ast_optimizer.typing_extensions import Unparser

if TYPE_CHECKING:
    from collections.abc import Callable

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

    def _traverse(self, node: list[ast.stmt]) -> None:
        self.can_write_body_in_one_line = (
            all(self._node_inlineable(sub_node) for sub_node in node) or len(node) == 1
        )
        self.previous_node_in_body = None

        for sub_node in node:
            self._visit_node(sub_node)
            self.can_write_body_in_one_line = False
            self.previous_node_in_body = sub_node

    def _visit_node(self, node: ast.AST) -> None:
        method: str = "visit_" + node.__class__.__name__
        visitor: Callable = getattr(self, method)  # type: ignore[assignment]
        return visitor(node)

    def _maybe_newline(self) -> None:
        if self._source:
            self._source("\n")

    def _write_maybe_lpad(self, to_write: str) -> None:
        if (
            self._source
            and self._source[-1][-1:] not in _chars_that_dont_need_whitespace
        ):
            self._source.append(" ")

        self._source.append(to_write)

    def _write_many(self, *args: tuple[str, ...]) -> None:
        self._source += args

    def _write_many_asts(self, asts: Iterable[ast.AST], delimitor: str) -> None:
        for i, node in enumerate(asts):
            if i > 0:
                self._source.append(delimitor)
            self._visit_node(node)

    def _maybe_write_annotation(self, annotation: ast.expr | None) -> None:
        if annotation is not None:
            self._write_annotation(annotation)

    def _write_annotation(self, annotation: ast.expr) -> None:
        self._source.append(":")
        self._visit_node(annotation)

    def _maybe_write_assign(self, assignment: ast.expr | None) -> None:
        if assignment is not None:
            self._write_assign(assignment)

    def _write_assign(self, assignment: ast.expr) -> None:
        self._source.append("=")
        self._visit_node(assignment)

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
    def block(self) -> Generator[None, None, None]:
        self._source.append(":")

        self._indent += 1
        yield
        self._indent -= 1

    @contextmanager
    def _surround(self, start: str, end: str) -> Generator[None, None, None]:
        self._source.append(start)
        yield
        self._source.append(end)

    def _surround_if(
        self, start: str, end: str, condition: bool
    ) -> Generator[None, None, None]:
        if condition:
            return self._surround(start, end)

        return nullcontext()

    def visit_Expr(self, node: ast.Expr) -> None:
        self._fill_literal_new_line()
        # TODO: Precedence YIELD
        self._visit_node(node.value)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # TODO: Precedence ATOM
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

    def visit_Assign(self, node: ast.Assign) -> None:
        self._fill_literal_new_line()

        for target in node.targets:
            # TODO: Precedence tuple
            self._visit_node(target)
            self._source.append("=")

        self._visit_node(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._fill_literal_new_line()

        with self._surround_if(
            "(", ")", not node.simple and isinstance(node.target, ast.Name)
        ):
            self._visit_node(node.target)

        self._write_annotation(node.annotation)
        self._maybe_write_assign(node.value)

    def visit_arg(self, node: ast.arg) -> None:
        self._source.append(node.arg)
        self._maybe_write_annotation(node.annotation)

    def visit_arguments(self, node: ast.arguments) -> None:
        first: bool = True

        def __maybe_comma() -> None:
            nonlocal first
            if first:
                first = False
            else:
                self._source.append(",")

        positional_args: list[ast.arg] = node.posonlyargs + node.args
        positional_arg_defaults: list[ast.expr | None] = [None] * (
            len(positional_args) - len(node.defaults)
        ) + node.defaults

        index_to_forward_slash: int = len(node.posonlyargs) - 1

        for index, arg in enumerate(positional_args):
            __maybe_comma()
            self._visit_node(arg)

            default: ast.expr | None = positional_arg_defaults[index]
            self._maybe_write_assign(default)

            if index == index_to_forward_slash:
                self._source.append(",/")

        if node.vararg or node.kwonlyargs:
            __maybe_comma()
            self._source.append("*")

            if node.vararg is not None:
                self._source.append(node.vararg.arg)
                self._maybe_write_annotation(node.vararg.annotation)

            if node.kwonlyargs:
                for arg, default in zip(node.kwonlyargs, node.kw_defaults, strict=True):
                    self._source.append(",")
                    self._visit_node(arg)

                    self._maybe_write_assign(default)

        if node.kwarg:
            __maybe_comma()
            self._write_many("**", node.kwarg.arg)
            self._maybe_write_annotation(node.kwarg.annotation)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self._source.append(" async for " if node.is_async else " for ")

        # TODO: Precedence tuple

        self._visit_node(node.target)
        self._source.append(" in ")

        # TODO: Precedence test

        self._visit_node(node.iter)

        for if_clause in node.ifs:
            self._write_maybe_lpad("if ")
            self._visit_node(if_clause)

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

    def visit_SetComp(self, node: ast.SetComp) -> None:
        with self._surround("{", "}"):
            self._visit_node(node.elt)
            for gen in node.generators:
                self._visit_node(gen)

    def visit_Break(self, _: ast.Break) -> None:
        self._fill_literal("break")

    def visit_Continue(self, _: ast.Continue) -> None:
        self._fill_literal("continue")

    def visit_Pass(self, _: ast.Pass) -> None:
        self._fill_literal("pass")

    def visit_Return(self, node: ast.Return) -> None:
        self._fill_literal("return")

        if node.value is not None:
            self._source.append(" ")
            self._visit_node(node.value)

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
        self._maybe_write_annotation(node.bound)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> None:
        self._fill_literal("type ")
        self.visit_Name(node.name)

        self._write_type_params(node.type_params)

        self._write_assign(node.value)

    def _write_decorators(
        self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        for decorator in node.decorator_list:
            self._fill_literal_new_line("@")
            self._visit_node(decorator)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function_helper(node, "def")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function_helper(node, "async def")

    def _function_helper(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, suffix: str
    ) -> None:
        self._write_decorators(node)
        self._fill_literal_new_line(suffix + " " + node.name)

        if hasattr(node, "type_params"):
            self._write_type_params(node.type_params)

        with self._surround("(", ")"):
            self._visit_node(node.args)

        if node.returns:
            self._source.append("->")
            self._visit_node(node.returns)

        with self.block():
            # TODO: doc string
            self._traverse(node.body)

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
