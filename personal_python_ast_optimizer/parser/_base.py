import ast
from collections.abc import Iterable


class AstNodeTransformerBase(ast.NodeTransformer):
    """Base class for ast node transformers. Intended for internal use."""

    __slots__ = ()

    # Nodes that do not need to be fully visited
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


class UnusedNodeSkipperBase(AstNodeTransformerBase):
    """Base class for ast node transformers that will skip over unused
    nodes such as unused imports."""

    __slots__ = ("depth", "names")

    def __init__(self, imports_to_preserve: Iterable[str] | None = None) -> None:
        self.names: set[str] = (
            set(imports_to_preserve) if imports_to_preserve is not None else set()
        )
        self.depth = 0

    def generic_visit(self, node: ast.AST) -> ast.AST:
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                self.depth += 1
                new_values = []
                ast_removed: bool = False
                for value in reversed(old_value):
                    if isinstance(value, ast.AST):
                        value = self.visit(value)  # noqa: PLW2901
                        if value is None:
                            ast_removed = True
                            continue

                    new_values.append(value)

                if not isinstance(node, ast.Module) and not new_values and ast_removed:
                    new_values.append(ast.Pass())

                old_value[:] = reversed(new_values)
                self.depth -= 1

            elif isinstance(old_value, ast.AST):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)

        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        self.names.add(node.id)
        return node
