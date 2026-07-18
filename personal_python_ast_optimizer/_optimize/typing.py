"""Typing for visitors/transformers."""

import ast
from typing import Protocol


class AstVisitorBaseProtocol(Protocol):
    """Protocol for AST visitor base classes. Super classes aren't used
    due to type differences between visitors and transformers."""

    def _visit(self, node: ast.AST): ...  # noqa: ANN202

    def _generic_visit(self, node: ast.AST): ...  # noqa: ANN202


class AstVisitorProtocol(Protocol):
    """Protocol for AST visitors to define a standard visit method to begin parsing."""

    def visit(self, node): ...  # noqa: ANN001, ANN202
