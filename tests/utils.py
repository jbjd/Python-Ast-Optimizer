import ast

from personal_python_ast_optimizer.parser.config import (
    OptimizationsConfig,
    SkipConfig,
    TokensConfig,
    TokenTypesConfig,
)
from personal_python_ast_optimizer.parser.run import run_minify_parser


class BeforeAndAfter:
    """Input and output after minifying it"""

    __slots__ = ("before", "after")

    def __init__(self, before: str, after: str) -> None:
        self.before: str = before
        self.after: str = after


def run_minifier_and_assert_correct(
    before_and_after: BeforeAndAfter,
    target_python_version: tuple[int, int] | None = None,
    token_types_config: TokenTypesConfig | None = None,
    tokens_config: TokensConfig | None = None,
    optimizations_config: OptimizationsConfig | None = None,
):
    minified_code: str = run_minify_parser(
        before_and_after.before,
        skip_config=SkipConfig(
            "",
            target_python_version=target_python_version,
            tokens_config=tokens_config or TokensConfig(),
            token_types_config=token_types_config or TokenTypesConfig(),
            optimizations_config=optimizations_config or OptimizationsConfig(),
        ),
    )
    raise_if_python_code_invalid(minified_code)
    assert before_and_after.after == minified_code, (
        f"{before_and_after.after} != {minified_code}"
    )


def raise_if_python_code_invalid(python_code: str) -> None:
    ast.parse(python_code)


def _python_version_str_to_int_tuple(python_version: str) -> tuple[int, int]:
    return tuple(int(i) for i in python_version.split("."))[:2]  # type: ignore
