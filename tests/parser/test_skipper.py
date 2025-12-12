import ast
from unittest.mock import patch

from personal_python_ast_optimizer.parser.config import SkipConfig, TokensConfig
from personal_python_ast_optimizer.parser.skipper import AstNodeSkipper

_MODULE_NAME: str = "personal_python_ast_optimizer.parser.skipper"


def test_warn_unused_skips():

    no_warn_module: ast.Module = ast.parse("from here import some_import;a=1")

    warn_module: ast.Module = ast.parse("a=1")

    with patch(f"{_MODULE_NAME}.warnings.warn") as mock_warn:
        skip_config = SkipConfig(
            "some_module",
            tokens_config=TokensConfig(from_imports_to_skip={"some_import"}),
        )
        skipper = AstNodeSkipper(skip_config)
        skipper.visit(no_warn_module)
        mock_warn.assert_not_called()

        skip_config = SkipConfig(
            "some_module",
            tokens_config=TokensConfig(from_imports_to_skip={"some_import"}),
        )
        skipper = AstNodeSkipper(skip_config)
        skipper.visit(warn_module)
        mock_warn.assert_called_once()
