import ast

from personal_python_ast_optimizer.parser.config import (
    ExtrasConfig,
    SectionsConfig,
    SkipConfig,
    TokensConfig,
)
from personal_python_ast_optimizer.parser.minifier import MinifyUnparser
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
    vars_to_fold: dict[str, int | str] | None = None,
    sections_config: SectionsConfig = SectionsConfig(),
    tokens_config: TokensConfig = TokensConfig(),
    extras_config: ExtrasConfig = ExtrasConfig(),
):
    unparser: MinifyUnparser = MinifyUnparser()

    minified_code: str = run_minify_parser(
        unparser,
        before_and_after.before,
        SkipConfig(
            "",
            target_python_version,
            vars_to_fold,
            sections_config,
            tokens_config,
            extras_config,
        ),
    )
    assert python_code_is_valid(minified_code)
    assert (
        before_and_after.after == minified_code
    ), f"{before_and_after.after} != {minified_code}"


def python_code_is_valid(python_code: str) -> bool:
    try:
        ast.parse(python_code)
        return True
    except SyntaxError:
        return False


def _python_version_str_to_int_tuple(python_version: str) -> tuple[int, int]:
    return tuple(int(i) for i in python_version.split("."))[:2]  # type: ignore
