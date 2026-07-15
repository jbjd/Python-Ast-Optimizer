from unittest.mock import patch

from personal_python_ast_optimizer.config import (
    OptimizeConfig,
    PerfOptimizationsConfig,
    TokensToFold,
    TokensToSkip,
    TokensToSkipConfig,
)
from personal_python_ast_optimizer.run import optimize_source_and_minify


def test_warn_unused_skips() -> None:
    """Should warn when configured and input not found."""
    no_warn_source: str = """
import os

from bar import class_dec

SOME_CONST=1
OTHER_CONST=SOME_CONST

def foo():
    print(1)

@class_dec
class DEF(ABC):a=1
"""

    warn_source: str = "b=1"

    no_warn = set()

    with patch(
        "personal_python_ast_optimizer._optimize.utils._logger.warning"
    ) as mock_logger_warning:
        config = OptimizeConfig(
            tokens_to_skip=TokensToSkipConfig(
                assignments_to_skip=TokensToSkip({"a"}, no_warn),
                classes_to_skip=TokensToSkip({"ABC"}, no_warn),
                decorators_to_skip=TokensToSkip({"class_dec"}, no_warn),
                from_imports_to_skip=TokensToSkip({("bar", "class_dec")}, no_warn),
                functions_to_skip=TokensToSkip({"foo"}, no_warn),
                module_imports_to_skip=TokensToSkip({"os"}, no_warn),
            ),
            perf_optimizations=PerfOptimizationsConfig(
                names_to_fold=TokensToFold({"SOME_CONST": 1}, no_warn)
            ),
        )

        optimize_source_and_minify(no_warn_source, config)
        mock_logger_warning.assert_not_called()

        optimize_source_and_minify(warn_source, config)
        assert mock_logger_warning.call_count == 7
