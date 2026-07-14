import ast

import pytest

from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    OptimizeConfig,
    PerfOptimizationsConfig,
    TokensToSkipConfig,
    TokenTypesToSkipConfig,
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


# TODO: deprecate BeforeAndAfter
def optimize_and_assert_correctness_old(
    before_and_after: BeforeAndAfter,
    code_to_skip: CodeToSkipConfig | None = None,
    token_types_to_skip: TokenTypesToSkipConfig | None = None,
    tokens_to_skip: TokensToSkipConfig | None = None,
    perf_optimizations: PerfOptimizationsConfig | None = None,
):
    optimize_and_assert_correctness(
        before_and_after.before,
        before_and_after.after,
        code_to_skip,
        token_types_to_skip,
        tokens_to_skip,
        perf_optimizations,
    )


def optimize_expect_error(
    source: str,
    error: BaseException,
    expected_message: str,
    code_to_skip: CodeToSkipConfig | None = None,
    token_types_to_skip: TokenTypesToSkipConfig | None = None,
    tokens_to_skip: TokensToSkipConfig | None = None,
    perf_optimizations: PerfOptimizationsConfig | None = None,
):
    with pytest.raises(error, match=expected_message):
        optimize_source_and_minify(
            source,
            OptimizeConfig(
                code_to_skip=code_to_skip,
                tokens_to_skip=tokens_to_skip,
                token_types_to_skip=token_types_to_skip,
                perf_optimizations=perf_optimizations,
            ),
        )


def optimize_and_assert_correctness(
    source: str,
    expected: str,
    code_to_skip: CodeToSkipConfig | None = None,
    token_types_to_skip: TokenTypesToSkipConfig | None = None,
    tokens_to_skip: TokensToSkipConfig | None = None,
    perf_optimizations: PerfOptimizationsConfig | None = None,
):
    optimized_code: str = optimize_source_and_minify(
        source,
        OptimizeConfig(
            code_to_skip=code_to_skip,
            tokens_to_skip=tokens_to_skip,
            token_types_to_skip=token_types_to_skip,
            perf_optimizations=perf_optimizations,
        ),
    )

    _assert_correctness(optimized_code, expected)


def minify_and_assert_correctness(source: str, expected: str) -> None:
    module: ast.Module = ast.parse(source)
    minified_code: str = MinifyUnparser().visit(module)
    _assert_correctness(minified_code, expected)


def _assert_correctness(code_to_check: str, expected_code: str) -> None:
    try:
        ast.parse(code_to_check)
    except SyntaxError as e:
        raise OptimizeOutputError(f"Minified code invalid:\n\n{code_to_check}") from e

    assert code_to_check == expected_code, (
        f"\n\nGot:\n\n{code_to_check}\n\n--------\n\nExpected\n\n{expected_code}"
    )
