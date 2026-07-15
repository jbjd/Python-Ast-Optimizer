import sys

import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig, TokensToFold
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("print(not 3)", "print(False)"),
        ("print(not '')", "print(True)"),
        ("print(not a)", "print(not a)"),
        ("if not __debug__:print()", "print()"),
    ],
)
def test_fold_not(source: str, expected: str):
    """Should fold not operations on constant values."""
    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(
            names_to_fold=TokensToFold({"__debug__": False})
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("print(+3)", "print(3)"),
        ("print(+a)", "print(+a)"),
    ],
)
def test_fold_plus(source: str, expected: str):
    """Should fold not operations on constant values."""
    optimize_and_assert_correctness(source, expected)


@pytest.mark.skipif(sys.version_info >= (3, 16), reason="Bitwise not deprected in 3.16")
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("print(~3)", "print(-4)"),
        ("print(~a)", "print(~a)"),
    ],
)
def test_fold_bitwise_not(source: str, expected: str):
    """Should fold bitwise not operations on constant values."""
    optimize_and_assert_correctness(source, expected)
