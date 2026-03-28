import ast


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
