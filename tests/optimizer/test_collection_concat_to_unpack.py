import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "a = (1,) + (0,0) + b",
            "a=(1,0,0,*b)",
        ),
        (
            "a = [1] + b + [2]",
            "a=[1,*b,2]",
        ),
        (
            "a = b + [2] + [3]",
            "a=[*b,2,3]",
        ),
        (
            "def asdf(im):encoderinfo={**im.a,**e};return encoderinfo",
            "def asdf(im):encoderinfo={**im.a,**e};return encoderinfo",
        ),
    ],
)
def test_collection_concat_to_unpack(source: str, expected: str):

    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(collection_concat_to_unpack=True),
    )
