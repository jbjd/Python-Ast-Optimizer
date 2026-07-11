import ast
from collections.abc import Iterable, Iterator

from _log import get_logger

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


class _TokensToSkipVisitCounter:
    __slots__ = ("_tokens_to_skip",)

    def __init__(self, tokens_to_skip: Iterable[str]) -> None:
        self._tokens_to_skip: dict[str, int] = dict.fromkeys(tokens_to_skip, 0)

    def __bool__(self) -> bool:
        return bool(self._tokens_to_skip)

    def get_unvisited_tokens(self, tokens_to_ignore: Iterable[str]) -> Iterator[str]:
        for k, v in self._tokens_to_skip.items():
            if v == 0 and k not in tokens_to_ignore:
                yield k

    def should_skip(self, key: object) -> bool:
        if key in self._tokens_to_skip:
            self._tokens_to_skip[key] += 1
            return True

        return False


class TokensToSkipTracker:
    __slots__ = (
        "_no_warn",
        "assignments",
        "classes",
        "decorators",
        "from_imports",
        "functions",
        "module_imports",
    )

    def __init__(
        self,
        assignments: Iterable[str],
        classes: Iterable[str],
        decorators: Iterable[str],
        from_imports: Iterable[str],
        functions: Iterable[str],
        module_imports: Iterable[str],
        no_warn: Iterable[str],
    ) -> None:
        self.assignments = _TokensToSkipVisitCounter(assignments)
        self.classes = _TokensToSkipVisitCounter(classes)
        self.decorators = _TokensToSkipVisitCounter(decorators)
        self.from_imports = _TokensToSkipVisitCounter(from_imports)
        self.functions = _TokensToSkipVisitCounter(functions)
        self.module_imports = _TokensToSkipVisitCounter(module_imports)
        self._no_warn: Iterable[str] = no_warn

    def warn_not_found_skips(self, file_name: str) -> None:
        for attribute in self.__slots__:
            if attribute == "_no_warn":
                continue

            access_counter: _TokensToSkipVisitCounter = getattr(self, attribute)
            not_found: str = ", ".join(
                access_counter.get_unvisited_tokens(self._no_warn)
            )

            if not_found != "":
                _logger.warning(
                    "%s: Asked to skip %s that were not found/needed: %s",
                    f"{file_name}: " if file_name != "" else "",
                    attribute,
                    not_found,
                )
