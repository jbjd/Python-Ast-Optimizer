import pytest

from personal_python_ast_optimizer.config import UglifyConfig
from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """def _asdf():print(1)
a = _asdf()""",
            """def _a():print(1)
a=_a()""",
        ),
        (
            """class A:
    def __init__(self):self.a=1
    def _asdf(self):print(1)
a = A()._asdf()""",
            """class A:
\tdef __init__(self):self.a=1
\tdef _a(self):print(1)
a=A()._a()""",
        ),
        (
            """import _a
def _asdf():print(1)
def _f():print(1)
a = _asdf()""",
            """import _a
def _b():print(1)
def _f():print(1)
a=_b()""",
        ),
        (
            """def _a():print(1)
def _abc():print(1)""",
            """def _a():print(1)
def _b():print(1)""",
        ),
    ],
)
def test_shorten_private_functions(source: str, expected: str):
    """Should shorten private functions without causing global name conflicts."""

    optimize_and_assert_correctness(
        source, expected, uglify=UglifyConfig(shorten_private_functions=True)
    )
