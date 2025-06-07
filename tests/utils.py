import ast

from personal_python_ast_optimizer.parser import run_minify_parser
from personal_python_ast_optimizer.parser.config import (
    SectionsToSkipConfig,
    SkipConfig,
    TokensToSkipConfig,
)
from personal_python_ast_optimizer.parser.minifier import MinifyUnparser


class BeforeAndAfter:
    """Input and output after minifiying it"""

    __slots__ = ("before", "after")

    def __init__(self, before: str, after: str) -> None:
        self.before: str = before
        self.after: str = after


class BeforeAndAfterBasedOnVersion:
    """Input and outputs it may have based on different python versions"""

    __slots__ = ("before", "after")

    def __init__(self, before: str, after: dict[str | None, str]) -> None:
        self.before: str = before
        self.after: dict[str | None, str] = after


def run_minifiyer_and_assert_correct_multiple_versions(
    source: BeforeAndAfterBasedOnVersion,
):
    target_python_version: tuple[int, int] | None
    for version, expected in source.after.items():
        if version is not None:
            target_python_version = _python_version_str_to_int_tuple(version)
        else:
            target_python_version = version

        version_specific_source = BeforeAndAfter(source.before, expected)

        run_minifiyer_and_assert_correct(
            version_specific_source, target_python_version=target_python_version
        )


def run_minifiyer_and_assert_correct(
    source: BeforeAndAfter,
    target_python_version: tuple[int, int] | None = None,
    constant_vars_to_fold: dict[str, int | str] | None = None,
    sections_to_skip_config: SectionsToSkipConfig = SectionsToSkipConfig(),
    tokens_to_skip_config: TokensToSkipConfig = TokensToSkipConfig(),
):
    unparser: MinifyUnparser = MinifyUnparser(
        constant_vars_to_fold=constant_vars_to_fold
    )

    minified_code: str = run_minify_parser(
        unparser,
        source.before,
        SkipConfig(
            "", target_python_version, sections_to_skip_config, tokens_to_skip_config
        ),
    )
    assert python_code_is_valid(minified_code)
    assert source.after == minified_code


def python_code_is_valid(python_code: str) -> bool:
    try:
        ast.parse(python_code)
        return True
    except SyntaxError:
        return False


def _python_version_str_to_int_tuple(python_version: str) -> tuple[int, int]:
    return tuple(int(i) for i in python_version.split("."))[:2]  # type: ignore
