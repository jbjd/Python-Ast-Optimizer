import ast
from collections.abc import Iterable
from enum import Enum
from typing import override

from personal_python_ast_optimizer._optimize._base import AstNodeTransformerBase
from personal_python_ast_optimizer.config import TypeHintsToSkip


class _NodeContext(Enum):
    NONE = 0
    CLASS = 1
    FUNCTION = 2


class FirstPassOptimizer(AstNodeTransformerBase):
    """Removes All nodes that only need to be removed once and can't be
    optimized into removal later. Intened to be called once as a first pass."""

    __slots__ = (
        "_node_context",
        "skip_asserts",
        "skip_dangling_expressions",
        "skip_generics",
        "skip_overload_functions",
        "skip_type_hints",
        "skip_typing_cast",
    )

    def __init__(
        self,
        skip_dangling_expressions: bool,
        skip_type_hints: TypeHintsToSkip,
        skip_generics: bool,
        skip_asserts: bool,
        skip_typing_cast: bool,
        skip_overload_functions: bool,
    ) -> None:
        self.skip_dangling_expressions: bool = skip_dangling_expressions
        self.skip_type_hints: TypeHintsToSkip = skip_type_hints
        self.skip_generics: bool = skip_generics and bool(skip_type_hints)
        self.skip_asserts: bool = skip_asserts
        self.skip_typing_cast: bool = skip_typing_cast
        self.skip_overload_functions: bool = skip_overload_functions
        self._node_context: _NodeContext = _NodeContext.NONE

    def visit_AsyncFunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._handle_function(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._handle_function(node)

    def _handle_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.AST | None:
        if self.skip_overload_functions and self._is_overload_function(node):
            return None

        if self.skip_type_hints:
            node.returns = None

        return self._visit_with_context(node, _NodeContext.FUNCTION)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        return self._visit_with_context(node, _NodeContext.CLASS)

    def visit_arg(self, node: ast.arg) -> ast.arg:
        if self.skip_type_hints:
            node.annotation = None

        return node

    def visit_Call(self, node: ast.Call) -> ast.AST | None:
        if (
            self.skip_typing_cast
            and isinstance(node.func, ast.Name)
            and node.func.id == "cast"
            and len(node.args) == 2  # noqa: PLR2004
        ):
            return self.generic_visit(node.args[1])

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        if self.skip_type_hints == TypeHintsToSkip.ALL or (
            self.skip_type_hints == TypeHintsToSkip.ALL_BUT_CLASS_VARS
            and self._node_context != _NodeContext.CLASS
        ):
            return (
                None
                if node.value is None
                else self.generic_visit(ast.Assign([node.target], node.value))
            )

        return self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> ast.AST | None:
        return None if self.skip_asserts else self.generic_visit(node)

    def visit_TypeVar(self, node: ast.TypeVar) -> ast.TypeVar | None:
        return None if self.skip_generics else self.generic_visit(node)

    def visit_ParamSpec(self, node: ast.ParamSpec) -> ast.ParamSpec | None:
        return None if self.skip_generics else self.generic_visit(node)

    def visit_TypeVarTuple(self, node: ast.TypeVarTuple) -> ast.TypeVarTuple | None:
        return None if self.skip_generics else self.generic_visit(node)

    def visit_TypeAlias(self, node: ast.TypeAlias) -> ast.TypeAlias | None:
        return None if self.skip_generics else self.generic_visit(node)

    @override
    def _has_work(self) -> bool:
        return (
            self.skip_dangling_expressions
            or bool(self.skip_type_hints)
            or self.skip_generics
            or self.skip_asserts
            or self.skip_typing_cast
        )

    def _visit_with_context(self, node: ast.AST, context: _NodeContext) -> ast.AST:
        previous_value: _NodeContext = self._node_context
        self._node_context = context
        try:
            return self.generic_visit(node)
        finally:
            self._node_context = previous_value

    @staticmethod
    def _is_overload_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return (
            len(node.decorator_list) == 1
            and isinstance(node.decorator_list[0], ast.Name)
            and node.decorator_list[0].id == "overload"
        )


class UnusedImportSkipper(AstNodeTransformerBase):
    """Removes unused import nodes from AST."""

    __slots__ = ("_names_and_attrs", "skip_unused_imports")

    def __init__(
        self, skip_unused_imports: bool, imports_to_preserve: Iterable[str]
    ) -> None:
        self.skip_unused_imports: bool = skip_unused_imports
        self._names_and_attrs: set[str] = set(imports_to_preserve)

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        self._filter_imports(node)

        return node if node.names else None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        if node.module != "__future__":
            self._filter_imports(node)

        return node if node.names else None

    def visit_Name(self, node: ast.Name) -> ast.Name:
        self._names_and_attrs.add(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self._names_and_attrs.add(node.attr)
        return self.generic_visit(node)

    def _filter_imports(self, node: ast.Import | ast.ImportFrom) -> None:
        node.names = [
            alias
            for alias in node.names
            if (alias.asname or alias.name) in self._names_and_attrs
        ]

    @override
    def _has_work(self) -> bool:
        return self.skip_unused_imports

    @override
    @staticmethod
    def _alter_node_list_visit_order(ast_list: list[ast.AST]) -> list[ast.AST]:
        return reversed(ast_list)
