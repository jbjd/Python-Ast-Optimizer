import ast

from personal_python_ast_optimizer.parser.config import SkipConfig
from personal_python_ast_optimizer.parser.minifier import MinifyUnparser
from personal_python_ast_optimizer.parser.skipper import AstNodeSkipper


def run_minify_parser(
    source: str,
    unparser: ast._Unparser | None = None,  # type: ignore[name-defined]
    skip_config: SkipConfig | None = None,
) -> str:
    module: ast.Module = ast.parse(source)

    if skip_config is not None:
        AstNodeSkipper(skip_config).visit(module)

    if unparser is None:
        unparser = MinifyUnparser()

    return unparser.visit(module)
