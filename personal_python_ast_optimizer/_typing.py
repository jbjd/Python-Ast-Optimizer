import ast
from typing import Protocol


class Unparser(Protocol):
    def visit(self, node: ast.AST) -> str: ...
