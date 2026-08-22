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
    def _asdf():print(1)
a = A()._asdf()""",
            """class A:
\tdef _a():print(1)
a=A()._a()""",
        ),
    ],
)
def test_exclude_assign(source: str, expected: str):
    """Should remove assignments when applicable."""

    optimize_and_assert_correctness(
        source, expected, uglify=UglifyConfig(shorten_private_functions=True)
    )
