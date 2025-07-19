import ast
from typing import Iterable

from personal_python_ast_optimizer.parser.config import TokensToSkip


def can_skip_annotation_assign(
    node: ast.AnnAssign, within_class: bool, within_function: bool
) -> bool:
    """Returns True if an annotation assign in unneeded in given context.
    Annotations are only needed when assigned in a class outside of a function"""
    return node.value is None and (not within_class or within_function)


def can_skip_if(node: ast.If) -> bool:
    """Returns True if the comparison in an If node cannot
    ever be true"""
    return isinstance(node.test, ast.Constant) and not node.test.value


def if_always_runs(node: ast.If) -> bool:
    """Returns True if the comparison in an If node is always true"""
    return isinstance(node.test, ast.Constant) and node.test.value


def list_or_none_if_only_pass(body: list[ast.stmt]) -> list[ast.stmt] | None:
    """Returns the provided list or None if the list was empty or only
    contained a single Pass node"""
    return None if not body or isinstance(body[0], ast.Pass) else body


def get_node_name(node: object) -> str:
    """Gets id or attr which both can represent var names"""
    if isinstance(node, ast.Call):
        node = node.func
    return getattr(node, "id", "") or getattr(node, "attr", "")


def is_overload_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return (
        len(node.decorator_list) == 1
        and get_node_name(node.decorator_list[0]) == "overload"
    )


def is_return_none(node: ast.Return) -> bool:
    return isinstance(node.value, ast.Constant) and node.value.value is None


def node_inlineable(node: ast.AST) -> bool:
    return node.__class__.__name__ in [
        "Assert",
        "Assign",
        "AugAssign",
        "Break",
        "Continue",
        "Delete",
        "Expr",
        "Import",
        "ImportFrom",
        "Pass",
        "Raise",
        "Return",
    ]


def skip_dangling_expressions(
    node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    """Removes constant dangling expression like doc strings"""
    node.body = [
        element
        for element in node.body
        if not (
            isinstance(element, ast.Expr) and isinstance(element.value, ast.Constant)
        )
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
