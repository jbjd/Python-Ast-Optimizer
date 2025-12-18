import ast

from personal_python_ast_optimizer.parser.config import SkipConfig
from personal_python_ast_optimizer.parser.minifier import MinifyUnparser
from personal_python_ast_optimizer.parser.skipper import AstNodeSkipper


def run_minify_parser(
    parser: MinifyUnparser, source: str, skip_config: SkipConfig | None = None
) -> str:
    module: ast.Module = ast.parse(source)

    if skip_config is not None:
        AstNodeSkipper(skip_config).visit(module)

    return parser.visit(module)
