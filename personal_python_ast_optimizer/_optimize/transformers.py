import ast
from collections.abc import Iterable
from typing import override

from personal_python_ast_optimizer._optimize._base import AstNodeTransformerBase


class UnusedImportSkipper(AstNodeTransformerBase):
    __slots__ = ("names_and_attrs",)

    def __init__(self, imports_to_preserve: Iterable[str]) -> None:
        self.names_and_attrs: set[str] = set(imports_to_preserve)

    @override
    @staticmethod
    def alter_node_list_visit_order(ast_list: list[ast.AST]) -> list[ast.AST]:
        return reversed(ast_list)

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        self.filter_imports(node, self.names_and_attrs)

        return node if node.names else None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        if node.module != "__future__":
            self.filter_imports(node, self.names_and_attrs)

        return node if node.names else None

    def filter_imports(self, node: ast.Import | ast.ImportFrom) -> None:
        node.names = [
            alias
            for alias in node.names
            if (alias.asname or alias.name) in self.names_and_attrs
        ]

    def visit_Name(self, node: ast.Name) -> ast.Name:
        self.names_and_attrs.add(node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.names_and_attrs.add(node.attr)
        return self.generic_visit(node)
