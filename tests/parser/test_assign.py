import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_assign_cases = [
    BeforeAndAfter(
        """
if a > 6:
    b = 3
c = 4
""",
        "if a>6:b=3\nc=4",
    ),
    BeforeAndAfter(
        """
if a > 6:
    b = 3
    c = 4
""",
        "if a>6:b=3;c=4",
    ),
    BeforeAndAfter(
        """
if a > 6:
    b += 3
    c += 4
""",
        "if a>6:b+=3;c+=4",
    ),
    BeforeAndAfter(
        """
if a > 6:
    b = 3
""",
        "if a>6:b=3",
    ),
    BeforeAndAfter(
        """
if a > 6:
    b = 3
else:
    c = 6
""",
        "if a>6:b=3\nelse:c=6",
    ),
]


@pytest.mark.parametrize("before_and_after", _assign_cases)
def test_assign(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)
