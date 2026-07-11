import ast
from collections.abc import Iterator

from personal_python_ast_optimizer._log import get_logger
from personal_python_ast_optimizer.config import TokensToSkip

_logger = get_logger()


def get_name_or_full_attribute(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if not isinstance(node, ast.Attribute):
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

    def should_skip(self, key: object) -> bool:
        if key in self._tokens_to_skip:
            self._tokens_to_skip[key] = _VISITED
            return True

        return False


class TokensToSkipTracker:
    __slots__ = (
        "assignments",
        "classes",
        "decorators",
        "from_imports",
        "functions",
        "module_imports",
    )

    def __init__(
        self,
        assignments: TokensToSkip | None,
        classes: TokensToSkip | None,
        decorators: TokensToSkip | None,
        from_imports: TokensToSkip | None,
        functions: TokensToSkip | None,
        module_imports: TokensToSkip | None,
    ) -> None:
        self.assignments = _TokensToSkipVisitCounter(assignments)
        self.classes = _TokensToSkipVisitCounter(classes)
        self.decorators = _TokensToSkipVisitCounter(decorators)
        self.from_imports = _TokensToSkipVisitCounter(from_imports)
        self.functions = _TokensToSkipVisitCounter(functions)
        self.module_imports = _TokensToSkipVisitCounter(module_imports)

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
