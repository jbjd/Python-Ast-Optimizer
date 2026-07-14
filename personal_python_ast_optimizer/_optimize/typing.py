"""Typing for visitors/transformers."""

import ast
from typing import Protocol


class AstNodeVisitorProtocol(Protocol):
    """Protocol for AST visitors. Super classes aren't used
    due to type differences between visitors and transformers."""

    def visit(self, node: ast.AST): ...  # noqa: ANN202
