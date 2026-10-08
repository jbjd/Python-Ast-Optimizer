import pytest

from tests.utils import optimize_and_assert_correctness


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
for a in range(7):
    print(a)
""",
            "for a in range(7):print(a)",
        ),
        (
            "for a in zip([1,2],[3,4]):pass",
            "",
        ),
        (
            "for a in some_func():pass",
            "some_func()",
        ),
    ],
)
def test_for(source: str, expected: str):
    """Should remove dead for nodes and preserve functions with side-effects."""

    optimize_and_assert_correctness(source, expected)
