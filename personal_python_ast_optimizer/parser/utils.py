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
