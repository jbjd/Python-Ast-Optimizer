import pytest

from personal_python_ast_optimizer._optimize.utils import UglyNameGenerator
from personal_python_ast_optimizer.config import (
    OptimizeConfig,
    TokensToSkip,
    TokensToSkipConfig,
)
from personal_python_ast_optimizer.minifier import MinifyUnparser
from personal_python_ast_optimizer.run import optimize_source


def test_ugly_name_generator():
    """Should handle moving between names of different lengths."""
    name_generator = UglyNameGenerator()

    assert name_generator.get_ugly_name() == "a"
    assert name_generator.get_ugly_name() == "b"

    for _ in range(50):
        name_generator.get_ugly_name()

    assert name_generator.get_ugly_name() == "aa"


def test_warn_not_found_skips(caplog: pytest.LogCaptureFixture):
    """Should warn when skip was not found."""

    config = OptimizeConfig(
        tokens_to_skip=TokensToSkipConfig(
            assignments_to_skip=TokensToSkip(["asdf"], [])
        )
    )

    optimize_source("print(1)", MinifyUnparser(), config)

    assert len(caplog.messages) == 1
    assert (
        caplog.messages[0]
        == "Asked to skip assignments_to_skip that were not found/needed: asdf"
    )
