import pytest

from personal_python_ast_optimizer.config import (
    OtherOptimizationsConfig,
    TokenTypesToSkipConfig,
    TypeHintsToSkip,
)
from tests.utils import optimize_and_assert_correctness

_FUTURE_IMPORTS_EXAMPLE: str = """
from __future__ import annotations
from __future__ import generator_stop
from __future__ import unicode_literals
from __future__ import with_statement
"""


@pytest.mark.parametrize(
    ("version", "skip_type_hints", "expected"),
    [
        (
            (3, 0),
            TypeHintsToSkip.NONE,
            "from __future__ import annotations,generator_stop",
        ),
        ((3, 7), TypeHintsToSkip.NONE, "from __future__ import annotations"),
        ((3, 7), TypeHintsToSkip.ALL, ""),
    ],
)
def test_futures_imports(
    version: tuple[int, int], skip_type_hints: TypeHintsToSkip, expected: str
):
    """Should remove future imports based on python version where they are mandatory."""

    optimize_and_assert_correctness(
        _FUTURE_IMPORTS_EXAMPLE,
        expected,
        other_optimizations=OtherOptimizationsConfig(target_python_version=version),
        token_types_to_skip=TokenTypesToSkipConfig(skip_type_hints=skip_type_hints),
    )
