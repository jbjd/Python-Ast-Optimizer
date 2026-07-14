"""Utilities for AST optimization."""

import ast
from collections.abc import Iterator

from personal_python_ast_optimizer._log import get_logger
from personal_python_ast_optimizer.config import TokensToSkip
from personal_python_ast_optimizer.typing import FoldableConstant

_logger = get_logger()


def is_return_literal_none(node: ast.Return) -> bool:
    return isinstance(node.value, ast.Constant) and node.value.value is None


def get_name_or_full_attribute_id(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if not isinstance(node, ast.Attribute):
        return None

    return get_full_attribute_id(node)


def get_full_attribute_id(node: ast.Attribute) -> str:
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

    def __init__(self, tokens_to_skip: TokensToSkip[T] | None) -> None:
        self._tokens_to_skip: dict[T, int]

        if tokens_to_skip is None:
            self._tokens_to_skip = {}
        elif tokens_to_skip.no_warn is None:
            self._tokens_to_skip = {t: _UNVISITED for t in tokens_to_skip.tokens}
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

    def has(self, key: object) -> bool:
        if key in self._tokens_to_skip:
            self._tokens_to_skip[key] = _VISITED
            return True

        return False


class _TokensToFoldVisitCounter(_TokensToSkipVisitCounter):
    def __init__(
        self, tokens_to_skip: TokensToSkip[dict[str, FoldableConstant]]
    ) -> None:
        super().__init__(tokens_to_skip)
        self.map: dict[str, FoldableConstant] = tokens_to_skip.tokens

    def get(self, key: str) -> FoldableConstant:
        return self.map[key]


class TokensTracker:
    __slots__ = (
        "assignments_to_skip",
        "classes_to_skip",
        "decorators_to_skip",
        "from_imports_to_skip",
        "functions_to_skip",
        "module_imports_to_skip",
        "names_to_fold",
    )

    def __init__(
        self,
        assignments_to_skip: TokensToSkip | None,
        classes_to_skip: TokensToSkip | None,
        decorators_to_skip: TokensToSkip | None,
        from_imports_to_skip: TokensToSkip | None,
        functions_to_skip: TokensToSkip | None,
        module_imports_to_skip: TokensToSkip | None,
        names_to_fold: TokensToSkip[dict[str, FoldableConstant]] | None,
    ) -> None:
        self.assignments_to_skip = _TokensToSkipVisitCounter(assignments_to_skip)
        self.classes_to_skip = _TokensToSkipVisitCounter(classes_to_skip)
        self.decorators_to_skip = _TokensToSkipVisitCounter(decorators_to_skip)
        self.from_imports_to_skip = _TokensToSkipVisitCounter(from_imports_to_skip)
        self.functions_to_skip = _TokensToSkipVisitCounter(functions_to_skip)
        self.module_imports_to_skip = _TokensToSkipVisitCounter(module_imports_to_skip)
        self.names_to_fold = _TokensToFoldVisitCounter(names_to_fold)

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
