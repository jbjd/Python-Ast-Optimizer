import ast
import warnings
from typing import Iterable

from personal_python_ast_optimizer.parser.config import TokensToSkip


def exclude_imports(node: ast.Import | ast.ImportFrom, exlcudes: Iterable[str]) -> None:
    node.names = [
        alias for alias in node.names if (alias.asname or alias.name) not in exlcudes
    ]


def filter_imports(node: ast.Import | ast.ImportFrom, filter: Iterable[str]) -> None:
    node.names = [
        alias for alias in node.names if (alias.asname or alias.name) in filter
    ]


def get_node_name(node: ast.AST | None) -> str:
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


def remove_duplicate_slots(
    node: ast.Assign | ast.AnnAssign, warn_duplicates: bool = True
) -> None:
    if isinstance(node.value, (ast.Tuple, ast.List, ast.Set)):
        found_values: set[str] = set()
        unique_objects: list[ast.expr] = []
        for const_value in node.value.elts:
            if not isinstance(const_value, ast.Constant) or not isinstance(
                const_value.value, str
            ):
                raise ValueError(
                    f"Invalid slots value {const_value.__class__.__name__}"
                )
            if const_value.value not in found_values:
                unique_objects.append(const_value)
                found_values.add(const_value.value)

        if len(node.value.elts) != len(unique_objects):
            if warn_duplicates:
                warnings.warn(f"Duplicate entries found in __slots__: {found_values}")
            node.value.elts = unique_objects


def first_occurrence_of_type(data: list, target_type: type) -> int:
    for index, element in enumerate(data):
        if isinstance(element, target_type):
            return index

    return -1
