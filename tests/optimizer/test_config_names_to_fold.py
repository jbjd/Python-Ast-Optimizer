import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig, TokensToFold
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
from foo import FAVORITE_NUMBER

a = FAVORITE_NUMBER
""",
            "a=6",
        ),
        (
            """
FAVORITE_NUMBER = 6

a = FAVORITE_NUMBER
""",
            "a=6",
        ),
        (
            """
FAVORITE_NUMBER: int = 6

a = FAVORITE_NUMBER
""",
            "a=6",
        ),
        (
            """
FAVORITE_NUMBER=a=6
""",
            "a=6",
        ),
        (
            "if __name__=='__main__':print()",
            "print()",
        ),
        ("print(os.name)", "print('nt')"),
        ("print(foo.os.name)", "print(foo.os.name)"),
        ("print(os.name.foo)", "print(os.name.foo)"),
        (
            """
def get_cpu_count():
    return os.cpu_count() or 1
""",
            "def get_cpu_count():return 12",
        ),
    ],
)
def test_fold_names(source: str, expected: str):
    """Should replace occurrences of name with provided constant."""
    optimize_and_assert_correctness(
        source,
        expected,
        perf_optimizations=PerfOptimizationsConfig(
            calls_to_fold=TokensToFold(
                {
                    "os.cpu_count": 12,
                }
            ),
            name_or_attr_to_fold=TokensToFold(
                {
                    "FAVORITE_NUMBER": 6,
                    "TEST": "test",
                    "__name__": "__main__",
                    "os.name": "nt",
                    "foo": "asdf",
                }
            ),
        ),
    )
