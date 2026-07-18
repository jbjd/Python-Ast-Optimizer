"""Utilities for AST optimization."""

import ast
from collections.abc import Iterator
from enum import Enum
from typing import Any, override

from personal_python_ast_optimizer._log import get_logger
from personal_python_ast_optimizer.config import TokensToFold, TokensToSkip
from personal_python_ast_optimizer.typing import FoldableConstant

_logger = get_logger()


class NodeContext(Enum):
    NONE = 0
    CLASS = 1
    FUNCTION = 2


def is_return_literal_none(node: ast.Return) -> bool:
    """Checks if node is returning a literal None.

    :param node: A return node to check
    :returns: True if node returns literal None"""
    return isinstance(node.value, ast.Constant) and node.value.value is None


def get_name_or_full_attribute_id(node: ast.AST) -> str | None:
    """Returns id of Name nodes or full id of Attribute nodes.

    :param node: An AST node to check
    :returns: id or None if not a Name/Attribute"""
    if isinstance(node, ast.Name):
        return node.id

    if not isinstance(node, ast.Attribute):
        return None

    return get_full_attribute_id(node)


def get_full_attribute_id(node: ast.Attribute) -> None:
    """Returns full id of Attribute node.

    :param node: An Attribute node to check
    :returns: full id of Attribute or None if its value is not a Name/Attributes"""
    if not isinstance(node.value, (ast.Name, ast.Attribute)):
        return None

    all_attributes: list[ast.Attribute | ast.Name] = [node]

    child: ast.expr = node.value
    while isinstance(child, (ast.Name, ast.Attribute)):
        all_attributes.append(child)
        if isinstance(child, ast.Attribute):
            child = child.value
        else:
            break

    return ".".join(
        n.attr if isinstance(n, ast.Attribute) else n.id
        for n in reversed(all_attributes)
    )


_UNVISITED = 0
_VISITED = 1


class _TokensToSkipVisitCounter[T]:
    __slots__ = ("_tokens_to_skip",)

    def __init__(
        self, tokens_to_skip: TokensToSkip[T] | TokensToFold[T, Any] | None
    ) -> None:
        self._tokens_to_skip: dict[T, int]

        if tokens_to_skip is None:
            self._tokens_to_skip = {}
        elif tokens_to_skip.no_warn == "*":
            self._tokens_to_skip = {t: _VISITED for t in tokens_to_skip.tokens}
        else:
            self._tokens_to_skip = {
                t: _VISITED if t in tokens_to_skip.no_warn else _UNVISITED
                for t in tokens_to_skip.tokens
            }

    def __bool__(self) -> bool:
        return bool(self._tokens_to_skip)

    def get_unvisited_tokens(self) -> Iterator[str]:
        for k, v in self._tokens_to_skip.items():
            if v == 0:
                yield str(k)

    def add(self, key: T, already_visitied: bool) -> None:
        self._tokens_to_skip[key] = already_visitied

    def has(self, key: object) -> bool:
        if key in self._tokens_to_skip:
            self._tokens_to_skip[key] = _VISITED
            return True

        return False


class _TokensToFoldVisitCounter(_TokensToSkipVisitCounter[str]):
    def __init__(
        self, tokens_to_fold: TokensToFold[str, FoldableConstant] | None
    ) -> None:
        super().__init__(tokens_to_fold)
        self.map: dict[str, FoldableConstant] = (
            {} if tokens_to_fold is None else tokens_to_fold.tokens
        )

    @override
    def add(self, key: str, already_visitied: bool) -> None:
        raise NotImplementedError  # pragma: no cover

    def get(self, key: str) -> FoldableConstant:
        return self.map[key]


class TokensTracker:
    __slots__ = (
        "assignments_to_skip",
        "calls_to_fold",
        "classes_to_skip",
        "decorators_to_skip",
        "from_imports_to_skip",
        "functions_to_skip",
        "module_imports_to_skip",
        "name_or_attr_to_fold",
    )

    def __init__(
        self,
        assignments_to_skip: TokensToSkip[str] | None,
        classes_to_skip: TokensToSkip[str] | None,
        decorators_to_skip: TokensToSkip[str] | None,
        from_imports_to_skip: TokensToSkip[tuple[str, str]] | None,
        functions_to_skip: TokensToSkip[str] | None,
        module_imports_to_skip: TokensToSkip[str] | None,
        calls_to_fold: TokensToFold[str, FoldableConstant] | None,
        name_or_attr_to_fold: TokensToFold[str, FoldableConstant] | None,
    ) -> None:
        self.assignments_to_skip = _TokensToSkipVisitCounter(assignments_to_skip)
        self.classes_to_skip = _TokensToSkipVisitCounter(classes_to_skip)
        self.decorators_to_skip = _TokensToSkipVisitCounter(decorators_to_skip)
        self.from_imports_to_skip = _TokensToSkipVisitCounter(from_imports_to_skip)
        self.functions_to_skip = _TokensToSkipVisitCounter(functions_to_skip)
        self.module_imports_to_skip = _TokensToSkipVisitCounter(module_imports_to_skip)
        self.calls_to_fold = _TokensToFoldVisitCounter(calls_to_fold)
        self.name_or_attr_to_fold = _TokensToFoldVisitCounter(name_or_attr_to_fold)

    def warn_not_found_skips(self, file_name: str) -> None:
        for attribute in self.__slots__:
            access_counter: _TokensToSkipVisitCounter = getattr(self, attribute)
            not_found: str = ", ".join(access_counter.get_unvisited_tokens())

            if not_found != "":
                _logger.warning(
                    "%sAsked to skip %s that were not found/needed: %s",
                    f"{file_name}: " if file_name != "" else "",
                    attribute,
                    not_found,
                )
