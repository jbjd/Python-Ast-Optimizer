import pytest

from personal_python_ast_optimizer.config import (
    CodeToSkipConfig,
    PerfOptimizationsConfig,
)
from tests.utils import optimize_and_assert_correctness

_example_bool_return: str = """
def a(b, c):
    if c and b in (1,2,3):
        return True
    else:
        return False
"""


def test_no_simplify_conditional_bool_return():
    """Should not change simple conditional return True/False to just a return."""
    optimize_and_assert_correctness(
        _example_bool_return,
        """def a(b,c):
\tif c and b in(1,2,3):return True
\telse:return False""",
        code_to_skip=CodeToSkipConfig(skip_useless_else=False),
        perf_optimizations=PerfOptimizationsConfig(
            simplify_conditional_bool_return=False
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            _example_bool_return,
            "def a(b,c):return c and b in(1,2,3)",
        ),
        (
            """
def a(b):
    if b in (1,2,3):
        return True

    return False
""",
            "def a(b):return b in(1,2,3)",
        ),
        (
            """
def a(b):
    if b:
        some_func()
        return True
    else:
        return False
""",
            """def a(b):
\tif b:some_func();return True
\telse:return False""",
        ),
        (
            """
def a(b):
    if b:
        some_func()
        return True

    return False
        """,
            """def a(b):
\tif b:some_func();return True
\treturn False""",
        ),
    ],
)
def test_simplify_conditional_bool_return(source: str, expected: str):
    """Should change simple conditional return True/False to just a return."""
    optimize_and_assert_correctness(
        source,
        expected,
        code_to_skip=CodeToSkipConfig(skip_useless_else=False),
        perf_optimizations=PerfOptimizationsConfig(
            simplify_conditional_bool_return=True
        ),
    )
