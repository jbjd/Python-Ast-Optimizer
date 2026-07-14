import ast
from collections.abc import Container


def get_node_name(node: ast.expr) -> str:
    """Returns 'id' or 'attr' attributes or empty string if missing.

    :param node:"""
    if isinstance(node, ast.Starred):
        node = node.value
    return getattr(node, "id", "") or getattr(node, "attr", "")


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
