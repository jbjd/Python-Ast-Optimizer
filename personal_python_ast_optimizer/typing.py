"""Module typing."""

import ast
from types import EllipsisType
from typing import Protocol

type Constant = str | bytes | bool | int | float | complex | EllipsisType | None
type FoldableConstant = Constant | tuple[Constant, ...]


class Unparser(Protocol):
    def visit(self, node: ast.AST) -> str: ...
