import ast
from typing import Iterable

from personal_python_ast_optimizer.parser.config import TokensToSkip


def can_skip_annotation_assign(
    node: ast.AnnAssign, within_class: bool, within_function: bool
) -> bool:
    """Returns True if an annotation assign in unneeded in given context.
    Annotations are only needed when assigned in a class outside of a function"""
    return node.value is None and (not within_class or within_function)


def get_node_name(node: object) -> str:
    """Gets id or attr which both can represent var names"""
    if isinstance(node, ast.Call):
        node = node.func
    return getattr(node, "id", "") or getattr(node, "attr", "")


def is_name_equals_main_node(node: ast.expr) -> bool:
    if not isinstance(node, ast.Compare):
        return False

    return (
        getattr(node.left, "id", "") == "__name__"
        and isinstance(node.ops[0], ast.Eq)
        and getattr(node.comparators[0], "value", "") == "__main__"
    )


def is_return_none(node: ast.Return) -> bool:
    return isinstance(node.value, ast.Constant) and node.value.value is None


def skip_dangling_expressions(
    node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    """Removes constant daggling expression like doc strings"""
    node.body = [
        element
        for element in node.body
        if not (
            isinstance(element, ast.Expr) and isinstance(element.value, ast.Constant)
        )
    ]


def remove_empty_annotations(node: ast.FunctionDef) -> None:
    node.body = [
        element
        for element in node.body
        if not (isinstance(element, ast.AnnAssign) and not element.value)
    ]


def skip_base_classes(
    node: ast.ClassDef, classes_to_ignore: Iterable[str] | TokensToSkip
) -> None:
    node.bases = [
        base for base in node.bases if getattr(base, "id", "") not in classes_to_ignore
    ]


def skip_decorators(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    decorators_to_ignore: Iterable[str] | TokensToSkip,
) -> None:
    node.decorator_list = [
        n for n in node.decorator_list if get_node_name(n) not in decorators_to_ignore
    ]


def first_occurrence_of_type(data: list, target_type) -> int:
    for index, element in enumerate(data):
        if isinstance(element, target_type):
            return index
    return -1
