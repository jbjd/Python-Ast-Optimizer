"""Module typing."""

import ast
from types import EllipsisType
from typing import Protocol

type FoldableConstant = str | bytes | bool | int | float | complex | None | EllipsisType


class Unparser(Protocol):
    def visit(self, node: ast.AST) -> str: ...
