"""Base classes for AST node visitors/transformers."""

import ast
from collections.abc import Iterable, Sequence

from personal_python_ast_optimizer._optimize.typing import AstVisitorBaseProtocol


class AstVisitorBase(AstVisitorBaseProtocol):
    """Base class for ast node visitors."""

    __slots__ = ()

    def _visit(self, node: ast.AST) -> None:
        """Visits `node`."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self._generic_visit)
        visitor(node)

    def _generic_visit(self, node: ast.AST) -> None:
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                self._traverse_body(value)
            elif isinstance(value, ast.AST):
                self._visit(value)

    def _traverse_body(self, body: Sequence[ast.AST]) -> None:
        for item in body:
            if isinstance(item, ast.AST):
                self._visit(item)


class AstTransformerBase(AstVisitorBaseProtocol):
    """Base class for ast node transformers."""

    __slots__ = ()

    def _visit(self, node: ast.AST) -> ast.AST | None:
        """Visits `node`."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> ast.AST:  # noqa: C901
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_nodes: list[ast.AST] = []
                for value in self._alter_node_list_visit_order(old_value):
                    new_node: ast.AST | None
                    if isinstance(value, ast.AST):
                        new_node = self._visit(value)
                        if new_node is None:
                            continue
                        if not isinstance(new_node, ast.AST):
                            new_nodes.extend(
                                self._alter_node_list_visit_order(new_node)
                            )
                            continue
                    else:
                        new_node = value

                    if self._should_add_node_to_body(new_nodes, new_node):
                        new_nodes.append(new_node)

                if (
                    not isinstance(node, ast.Module)
                    and not new_nodes
                    and field == "body"  # Kinda hacky, consider a better way to detect
                ):
                    new_nodes.append(ast.Pass())

                old_value[:] = self._alter_node_list_visit_order(new_nodes)

            elif isinstance(old_value, ast.AST):
                new_node = self._visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)

        return node

    @staticmethod
    def _alter_node_list_visit_order(ast_list: list[ast.AST]) -> Iterable[ast.AST]:
        """Allows the list of nodes to be altered so orderings other then first to last
        can be done by sub-classes.

        :param ast_list: List of ASTs to visit
        :returns: List of the same ASTs but with the order possibly altered"""
        return ast_list

    def _should_add_node_to_body(self, new_nodes: list[ast.AST], node: ast.AST) -> bool:  # noqa: ARG002
        return True

    # Start - Nodes that do not need to be fully visited

    def visit_alias(self, node: ast.alias) -> ast.AST | None:
        return node

    def visit_Break(self, node: ast.Break) -> ast.AST | None:
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST | None:
        return node

    def visit_Continue(self, node: ast.Continue) -> ast.AST | None:
        return node

    def visit_Pass(self, node: ast.Pass) -> ast.AST | None:
        return node

    def visit_Global(self, node: ast.Global) -> ast.AST | None:
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.AST | None:
        return node

    # End - Nodes that do not need to be fully visited
