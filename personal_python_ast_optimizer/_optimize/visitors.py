"""Visitor classes to help optimize Python ASTs."""

import ast
from collections.abc import Iterable

from personal_python_ast_optimizer._optimize.typing import AstNodeVisitorProtocol
from personal_python_ast_optimizer._optimize.utils import get_name_or_full_attribute_id


class CallFinderVisitor(AstNodeVisitorProtocol):
    """Visitor that aggregates all Calls."""

    __slots__ = ("calls", "excludes")

    def __init__(self, excludes: Iterable[str]) -> None:
        self.excludes: Iterable[str] = excludes
        self.calls: list[ast.Call] = []

    def visit(self, node: ast.AST) -> None:
        if (
            isinstance(node, ast.Call)
            and get_name_or_full_attribute_id(node.func) not in self.excludes
        ):
            self.calls.append(node)

        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for sub_value in value:
                    if isinstance(sub_value, ast.AST):
                        self.visit(sub_value)

            elif isinstance(value, ast.AST):
                self.visit(value)
