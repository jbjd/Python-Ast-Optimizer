import ast
from collections.abc import Container


def exclude_imports(
    node: ast.Import | ast.ImportFrom, excludes: Container[str]
) -> None:
    if excludes:
        node.names = [
            alias
            for alias in node.names
            if (alias.asname or alias.name) not in excludes
        ]


def filter_imports(node: ast.Import | ast.ImportFrom, includes: Container[str]) -> None:
    node.names = [
        alias for alias in node.names if (alias.asname or alias.name) in includes
    ]


def get_node_name(node: ast.expr) -> str:
    """Returns 'id' or 'attr' attributes or empty string if missing.

    :param node:"""
    if isinstance(node, ast.Starred):
        node = node.value
    return getattr(node, "id", "") or getattr(node, "attr", "")


def is_return_none(node: ast.Return) -> bool:
    return isinstance(node.value, ast.Constant) and node.value.value is None


def skip_decorators(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    decorators_to_ignore: Container[str],
) -> None:
    if decorators_to_ignore:
        node.decorator_list = [
            n
            for n in node.decorator_list
            if get_node_name(n) not in decorators_to_ignore
        ]


def first_occurrence_of_type(data: list, target_type: type) -> int:
    for index, element in enumerate(data):
        if isinstance(element, target_type):
            return index

    return -1
