import sys

import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_fold_var_cases = [
    BeforeAndAfter(
        """
from foo import FAVORITE_NUMBER

a = FAVORITE_NUMBER
""",
        "a=6",
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER = 6

a = FAVORITE_NUMBER
""",
        "a=6",
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER: int = 6

a = FAVORITE_NUMBER
""",
        "a=6",
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER=a=6
""",
        "a=6",
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER,a=4,5
""",
        "a=5",
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER,a,*_=4,5,6,7,8
""",
        ("a,*_=(5,6,7,8)" if sys.version_info[:2] > (3, 10) else "(a,*_)=(5,6,7,8)"),
    ),
    BeforeAndAfter(
        """
*_,FAVORITE_NUMBER,a=4,5,6,7,8
""",
        ("*_,a=(4,6,7,8)" if sys.version_info[:2] > (3, 10) else "(*_,a)=(4,6,7,8)"),
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER,TEST=4,5
""",
        "",
    ),
]


@pytest.mark.parametrize("before_and_after", _fold_var_cases)
def test_fold_var(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(
        before_and_after,
        vars_to_fold={"FAVORITE_NUMBER": 6, "TEST": "test"},
    )
