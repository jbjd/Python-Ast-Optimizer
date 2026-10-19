import pytest

from personal_python_ast_optimizer.config import UglifyConfig
from tests.utils import optimize_and_assert_correctness


def test_uglify_name():
    """Should uglify name without touching private function"""
    source: str = """
class A:
    def _asdf(self):print(1)"""

    expected: str = """class A:
\tdef _asdf(a):print(1)"""

    optimize_and_assert_correctness(
        source,
        expected,
        uglify=UglifyConfig(names_to_uglify=["self"]),
    )


@pytest.mark.parametrize(
    ("source", "expected", "to_uglify"),
    [
        (
            """def _asdf():print(1)
a = _asdf()""",
            """def _a():print(1)
a=_a()""",
            None,
        ),
        (
            """class A:
    def __init__(self):self.a=1
    def _asdf(self):print(1)
a = A()._asdf()""",
            """class A:
\tdef __init__(b):b.a=1
\tdef _a(b):print(1)
a=A()._a()""",
            ["self"],
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
            None,
        ),
        (
            """def _a():print(1)
def _abc():print(1)""",
            """def _a():print(1)
def _b():print(1)""",
            None,
        ),
    ],
)
def test_shorten_private_functions(
    source: str, expected: str, to_uglify: dict[str, str] | None
):
    """Should shorten private functions without causing global name conflicts."""

    optimize_and_assert_correctness(
        source,
        expected,
        uglify=UglifyConfig(names_to_uglify=to_uglify, shorten_private_functions=True),
    )
