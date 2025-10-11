import ast
from enum import EnumMeta

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


class BeforeAndAfterBasedOnVersion:
    """Input and outputs it may have based on different python versions"""

    __slots__ = ("before", "after")

    def __init__(self, before: str, after: dict[str | None, str]) -> None:
        self.before: str = before
        self.after: dict[str | None, str] = after


def run_minifier_and_assert_correct_multiple_versions(
    source: BeforeAndAfterBasedOnVersion,
):
    target_python_version: tuple[int, int] | None
    for version, expected in source.after.items():
        if version is not None:
            target_python_version = _python_version_str_to_int_tuple(version)
        else:
            target_python_version = version

        version_specific_source = BeforeAndAfter(source.before, expected)

        run_minifier_and_assert_correct(
            version_specific_source, target_python_version=target_python_version
        )


def run_minifier_and_assert_correct(
    before_and_after: BeforeAndAfter,
    target_python_version: tuple[int, int] | None = None,
    vars_to_fold: dict[str, int | str] | None = None,
    enums_to_fold: set[EnumMeta] | None = None,
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
            enums_to_fold,
            sections_config,
            tokens_config,
            extras_config,
        ),
    )
    raise_if_python_code_invalid(minified_code)
    assert (
        before_and_after.after == minified_code
    ), f"{before_and_after.after} != {minified_code}"


def raise_if_python_code_invalid(python_code: str) -> None:
    ast.parse(python_code)


def _python_version_str_to_int_tuple(python_version: str) -> tuple[int, int]:
    return tuple(int(i) for i in python_version.split("."))[:2]  # type: ignore
