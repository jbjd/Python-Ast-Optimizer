import ast

from personal_python_ast_optimizer.config import (
    CodeToFoldConfig,
    CodeToSkipConfig,
    ExtraOptimizationsConfig,
    OptimizeConfig,
    TokenTypesToSkipConfig,
    UserTokensToSkipConfig,
)
from personal_python_ast_optimizer.run import optimize_source_and_minify


class BeforeAndAfter:
    """Input and output after minifying it"""

    __slots__ = ("after", "before")

    def __init__(self, before: str, after: str) -> None:
        self.before: str = before
        self.after: str = after


def optimize_and_assert_correct(
    before_and_after: BeforeAndAfter,
    code_to_fold_config: CodeToFoldConfig | None = None,
    code_to_skip_config: CodeToSkipConfig | None = None,
    token_types_config: TokenTypesToSkipConfig | None = None,
    tokens_config: UserTokensToSkipConfig | None = None,
    optimizations_config: ExtraOptimizationsConfig | None = None,
):
    minified_code: str = optimize_source_and_minify(
        before_and_after.before,
        OptimizeConfig(
            code_to_fold_config=code_to_fold_config,
            code_to_skip_config=code_to_skip_config,
            tokens_config=tokens_config,
            token_types_config=token_types_config,
            optimizations_config=optimizations_config,
        ),
    )
    raise_if_python_code_invalid(minified_code)
    assert before_and_after.after == minified_code, (
        f"\n\n{before_and_after.after}\n\n--------\n\n{minified_code}"
    )


def raise_if_python_code_invalid(python_code: str) -> None:
    ast.parse(python_code)
