import ast


class AstNodeVisitorBase:
    """Base class for ast node visitors. Intended for internal use."""

    __slots__ = ()

    def visit(self, node: ast.AST) -> ast.AST | None:
        """Visits `node`."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> ast.AST:
        """Visits all ASTs within `node`."""
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
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


class AstNodeTransformerBase(AstNodeVisitorBase):
    """Base class for ast node transformers. Intended for internal use."""

    __slots__ = ("reverse",)

    def __init__(self, reverse: bool = False) -> None:
        self.reverse = reverse

    def generic_visit(self, node: ast.AST) -> ast.AST:
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                to_visit = reversed(old_value) if self.reverse else old_value
                new_values = []
                ast_removed: bool = False
                for value in to_visit:
                    if isinstance(value, ast.AST):
                        value = self.visit(value)  # noqa: PLW2901
                        if value is None:
                            ast_removed = True
                            continue
                        if not isinstance(value, ast.AST):
                            new_values.extend(
                                reversed(value) if self.reverse else value
                            )
                            continue
                    new_values.append(value)

                if not isinstance(node, ast.Module) and not new_values and ast_removed:
                    new_values.append(ast.Pass())

                old_value[:] = reversed(new_values) if self.reverse else new_values

            elif isinstance(old_value, ast.AST):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)

        return node
