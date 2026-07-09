import ast


class AstNodeVisitorBase:
    """Base class for ast node visitors. Intended for internal use."""

    __slots__ = ()

    def visit(self, node: ast.AST) -> ast.AST:
        """Visits `node`."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> ast.AST:
        """Visits all ASTs within `node`."""
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in self.alter_node_list_before_visit(value):
                    if isinstance(item, ast.AST):
                        self.visit(item)

            elif isinstance(value, ast.AST):
                self.visit(value)

        return node

    # Start - Nodes that do not need to be fully visited

    def visit_alias(self, node: ast.alias) -> ast.alias:
        return node

    def visit_Break(self, node: ast.Break) -> ast.Break:
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        return node

    def visit_Continue(self, node: ast.Continue) -> ast.Continue:
        return node

    def visit_Pass(self, node: ast.Pass) -> ast.Pass:
        return node

    def visit_Global(self, node: ast.Global) -> ast.Global:
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        return node

    # End - Nodes that do not need to be fully visited

    @staticmethod
    def _alter_node_list_visit_order(ast_list: list[ast.AST]) -> list[ast.AST]:
        """Allows the list of nodes to be altered so orderings other then first to last
        can be done by sub-classes.

        :param ast_list: List of ASTs to visit
        :returns: List of the same ASTs but with the order possibly altered"""
        return ast_list


class AstNodeTransformerBase(AstNodeVisitorBase):
    """Base class for ast node transformers. Intended for internal use."""

    def visit(self, node: ast.AST) -> ast.AST | None:  # type: ignore[override]
        return super().visit(node)

    def generic_visit(self, node: ast.AST) -> ast.AST:
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                for value in self._alter_node_list_visit_order(old_value):
                    if isinstance(value, ast.AST):
                        value = self.visit(value)  # noqa: PLW2901
                        if value is None:
                            continue
                        if not isinstance(value, ast.AST):
                            new_values.extend(self._alter_node_list_visit_order(value))
                            continue

                    self._on_visited_node_add_to_new_values(new_values, value)

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
    def _on_visited_node_add_to_new_values(
        new_nodes: list[ast.AST], node: ast.AST
    ) -> None:
        new_nodes.append(node)
