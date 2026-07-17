"""Visitor classes to help optimize Python ASTs."""

import ast

from personal_python_ast_optimizer._optimize.base import AstVisitorBase
from personal_python_ast_optimizer._optimize.typing import AstVisitorProtocol
from personal_python_ast_optimizer._optimize.utils import get_name_or_full_attribute_id


class CallAggregator(AstVisitorBase, AstVisitorProtocol):
    """Visitor that aggregates all Calls."""

    __slots__ = ("calls", "excludes")

    def __init__(self, excludes: set[str]) -> None:
        self._excludes: set[str] = excludes
        self._calls: list[ast.Call] = []

    def visit(self, node: ast.expr) -> list[ast.Call]:
        self._visit(node)
        return self._calls

    def visit_Call(self, node: ast.Call) -> ast.Call:
        if get_name_or_full_attribute_id(node.func) not in self._excludes:
            self._calls.append(node)

        return node


class FunctionFoldableLocalsAggregator(AstVisitorBase, AstVisitorProtocol):
    __slots__ = ("_excludes", "_foldable")

    def __init__(self, excludes: set[str]) -> None:
        self._foldable: dict[str, ast.Constant] = {}
        self._excludes: set[str] = excludes

    def visit(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, ast.Constant]:
        self._traverse_body(node.body)
        return self._foldable

    def visit_Global(self, node: ast.Global) -> None:
        self._handle_global_nonlocal(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self._handle_global_nonlocal(node)

    def _handle_global_nonlocal(self, node: ast.Global | ast.Nonlocal) -> None:
        for name in node.names:
            self._excludes.add(name)
            if name in self._foldable:
                del self._foldable[name]

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._handle_possible_foldable(node.target.id)
        self._generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:

        targets: list[ast.expr]
        value: ast.AST | None
        if isinstance(node.targets[0], ast.Tuple):
            # For now, not considering any of these for folding
            targets = node.targets[0].elts
            value = None
        else:
            targets = node.targets
            value = node.value

        for target in targets:
            if isinstance(target, ast.Name):
                self._handle_possible_foldable(target.id, value)

        self._generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:

        if isinstance(node.target, ast.Name):
            self._handle_possible_foldable(node.target.id, node.value)

        self._generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:

        if isinstance(node.target, ast.Name):
            self._handle_possible_foldable(node.target.id)

        self._generic_visit(node)

    def _handle_possible_foldable(
        self, node_id: str, value: ast.AST | None = None
    ) -> None:
        if node_id in self._foldable:
            del self._foldable[node_id]
        elif (
            value is not None
            and node_id not in self._excludes
            and isinstance(value, ast.Constant)
            and (value.value is None or isinstance(value.value, int))
        ):
            self._foldable[node_id] = value

        self._excludes.add(node_id)
