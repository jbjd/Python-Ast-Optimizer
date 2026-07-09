import ast
from collections.abc import Iterable

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


class _TokensToSkipAccessCounter:
    __slots__ = ("tokens_to_skip",)

    def __init__(self, tokens_to_skip: Iterable[str]) -> None:
        self.tokens_to_skip: dict[str, int] = dict.fromkeys(tokens_to_skip, 0)

    def should_skip(self, key: str) -> bool:
        if key in self.tokens_to_skip:
            self.tokens_to_skip[key] += 1
            return True

        return False


class UserTokensToSkipTracker:
    __slots__ = (
        "_no_warn",
        "assignments",
        "classes",
        "decorators",
        "dict_keys",
        "from_imports",
        "functions",
        "module_imports",
    )

    def __init__(
        self,
        assignments: Iterable[str],
        classes: Iterable[str],
        decorators: Iterable[str],
        dict_keys: Iterable[str],
        from_imports: Iterable[str],
        functions: Iterable[str],
        module_imports: Iterable[str],
        no_warn: Iterable[str],
    ) -> None:
        self.assignments = _TokensToSkipAccessCounter(assignments)
        self.classes = _TokensToSkipAccessCounter(classes)
        self.decorators = _TokensToSkipAccessCounter(decorators)
        self.dict_keys = _TokensToSkipAccessCounter(dict_keys)
        self.from_imports = _TokensToSkipAccessCounter(from_imports)
        self.functions = _TokensToSkipAccessCounter(functions)
        self.module_imports = _TokensToSkipAccessCounter(module_imports)
        self._no_warn: Iterable[str] = no_warn

    def warn_not_found_skips(self) -> None:
        for attribute in self.__slots__:
            if attribute == "no_warn":
                continue

            access_counter: _TokensToSkipAccessCounter = getattr(self, attribute)
            not_found: str = ", ".join(
                k
                for k, v in access_counter.tokens_to_skip
                if v <= 0 and k not in self._no_warn
            )

            if not_found != "":
                _logger.warning(
                    "Asked to skip %s that were not found/needed: %s",
                    attribute,
                    not_found,
                )
