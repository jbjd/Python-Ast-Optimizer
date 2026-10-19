"""Module typing."""

import ast
from types import EllipsisType
from typing import Protocol, TypeVar

type Constant = str | bytes | bool | int | float | complex | EllipsisType | None
type FoldableConstant = Constant | tuple[Constant, ...]

_T = TypeVar("_T", bound=FoldableConstant)


class ConstantCall(Protocol[_T]):
    """A call who's return value can be known at compile time."""

    def __call__(self, *args: _T) -> _T: ...


class Unparser(Protocol):
    def visit(self, node: ast.AST) -> str: ...
