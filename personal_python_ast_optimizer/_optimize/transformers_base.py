"""Base classes for AST node visitors/transformers."""

import ast
from collections.abc import Iterable

from personal_python_ast_optimizer._optimize.typing import AstNodeVisitorProtocol


class AstNodeTransformerBase(AstNodeVisitorProtocol):
    """Base class for ast node transformers."""

    __slots__ = ()

    def visit(self, node: ast.AST) -> ast.AST | None:
        """Visits `node`."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> ast.AST:
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_values: list[ast.AST] = []
                for value in self._alter_node_list_visit_order(old_value):
                    new_value: ast.AST | None
                    if isinstance(value, ast.AST):
                        new_value = self.visit(value)
                        if new_value is None:
                            continue
                        if not isinstance(new_value, ast.AST):
                            new_values.extend(
                                self._alter_node_list_visit_order(new_value)
                            )
                            continue
                    else:
                        new_value = value

                    self._on_visited_node_add_to_new_values(new_values, new_value)

                if (
                    not isinstance(node, ast.Module)
                    and not new_values
                    and field == "body"  # Kinda hacky, consider a better way to detect
                ):
                    new_values.append(ast.Pass())

                old_value[:] = self._alter_node_list_visit_order(new_values)

            elif isinstance(old_value, ast.AST):
                new_node = self.visit(old_value)
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

    def _on_visited_node_add_to_new_values(
        self, new_nodes: list[ast.AST], node: ast.AST
    ) -> None:
        new_nodes.append(node)

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
