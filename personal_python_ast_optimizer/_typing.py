import ast
from typing import Protocol

__all__ = ["Unparser"]


class Unparser(Protocol):
    def visit(self, node: ast.AST) -> str: ...
