import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected", "collection_concat_to_unpack"),
    [
        ("a = (1,) + (0,0) + b", "a=(1,0,0)+b", False),
        ("a = (1,) + (0,0) + b", "a=(1,0,0,*b)", True),
        ("a = [1] + b + [2]", "a=[1,*b,2]", True),
        ("a = b + [2] + [3]", "a=[*b,2,3]", True),
        (
            "def asdf(im):encoderinfo={**im.a,**e};return encoderinfo",
            "def asdf(im):encoderinfo={**im.a,**e};return encoderinfo",
            True,
        ),
    ],
)
def test_collection_concat_to_unpack(
    source: str, expected: str, collection_concat_to_unpack: bool
):
    """Should change + to unpack operation."""
    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(
            collection_concat_to_unpack=collection_concat_to_unpack
        ),
    )
