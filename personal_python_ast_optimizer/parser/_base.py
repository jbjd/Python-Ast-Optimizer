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
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)

            elif isinstance(value, ast.AST):
                self.visit(value)

        return node


class AstNodeTransformerBase(AstNodeVisitorBase):
    """Base class for ast node transformers. Intended for internal use."""

    __slots__ = ("reverse",)

    def __init__(self, reverse: bool = False) -> None:
        self.reverse = reverse

    def visit(self, node: ast.AST) -> ast.AST | None:  # type: ignore[override]
        return super().visit(node)

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
