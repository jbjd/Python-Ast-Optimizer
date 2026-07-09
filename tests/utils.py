import ast

from personal_python_ast_optimizer.config import (
    CodeToFoldConfig,
    CodeToSkipConfig,
    OptimizeConfig,
    OtherOptimizationsConfig,
    TokenTypesToSkipConfig,
    UserTokensToSkipConfig,
)
from personal_python_ast_optimizer.minifier import MinifyUnparser
from personal_python_ast_optimizer.run import optimize_source_and_minify


class BeforeAndAfter:
    """Input and output after minifying it"""

    __slots__ = ("after", "before")

    def __init__(self, before: str, after: str) -> None:
        self.before: str = before
        self.after: str = after


class OptimizeOutputError(Exception):
    pass


def optimize_and_assert_correctness(
    before_and_after: BeforeAndAfter,
    code_to_fold: CodeToFoldConfig | None = None,
    code_to_skip: CodeToSkipConfig | None = None,
    token_types_to_skip: TokenTypesToSkipConfig | None = None,
    tokens_to_skip: UserTokensToSkipConfig | None = None,
    other_optimizations: OtherOptimizationsConfig | None = None,
):
    optimized_code: str = optimize_source_and_minify(
        before_and_after.before,
        OptimizeConfig(
            code_to_fold=code_to_fold,
            code_to_skip=code_to_skip,
            tokens_to_skip=tokens_to_skip,
            token_types_to_skip=token_types_to_skip,
            other_optimizations=other_optimizations,
        ),
    )

    _validate_correctness(optimized_code, before_and_after.after)


def minify_and_validate_syntax(before: str, after: str) -> None:
    module: ast.Module = ast.parse(before)
    minified_code: str = MinifyUnparser().visit(module)
    _validate_correctness(minified_code, after)


def _validate_correctness(code_to_check: str, expected_code: str) -> None:
    try:
        ast.parse(code_to_check)
    except SyntaxError as e:
        raise OptimizeOutputError(f"Minified code invalid:\n\n{code_to_check}") from e

    assert code_to_check == expected_code, (
        f"\n\nGot:\n\n{code_to_check}\n\n--------\n\nExpected\n\n{expected_code}"
    )
