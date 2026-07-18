import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("a=1+100*2+1", "a=202"),
        ("a=(7-2)//2", "a=2"),
        ("a=(7%4)/3", "a=1.0"),
        ("a=(1<<3)>>2", "a=2"),
        ("a=64|1", "a=65"),
        ("a=7&3", "a=3"),
        ("a=3^6", "a=5"),
        ("a=2**3", "a=8"),
    ],
)
def test_fold_binary_op(source: str, expected: str):
    """Should fold constants in binary operations."""
    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(fold_constants=True),
    )
