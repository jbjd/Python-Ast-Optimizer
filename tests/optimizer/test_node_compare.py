import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("a='a' is 'b'", "a=False"),
        ("a='a' is not 'b'", "a=True"),
        ("a=3>=2", "a=True"),
        ("a=2<=2", "a=True"),
        ("a=1<2", "a=True"),
        ("a=1!=1", "a=False"),
    ],
)
def test_fold_comparisons(source: str, expected: str):
    """Should fold comparisons between constant values."""
    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(fold_constants=True),
    )
