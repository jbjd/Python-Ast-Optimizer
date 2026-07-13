import pytest

from personal_python_ast_optimizer.config import PerfOptimizationsConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness_old

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
        "a,*_=(5,6,7,8)",
    ),
    BeforeAndAfter(
        """
*_,FAVORITE_NUMBER,a=4,5,6,7,8
""",
        "*_,a=(4,6,7,8)",
    ),
    BeforeAndAfter(
        """
FAVORITE_NUMBER,TEST=4,5
""",
        "",
    ),
    BeforeAndAfter(
        "if __name__=='__main__':print()",
        "print()",
    ),
]


@pytest.mark.parametrize("before_and_after", _fold_var_cases)
def test_fold_var(before_and_after: BeforeAndAfter):
    optimize_and_assert_correctness_old(
        before_and_after,
        perf_optimizations=PerfOptimizationsConfig(
            vars_to_fold={"FAVORITE_NUMBER": 6, "TEST": "test", "__name__": "__main__"}
        ),
    )
