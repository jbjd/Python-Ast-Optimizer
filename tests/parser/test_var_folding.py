import pytest

from personal_python_ast_optimizer.parser.config import OptimizationsConfig
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
    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(
            vars_to_fold={"FAVORITE_NUMBER": 6, "TEST": "test", "__name__": "__main__"}
        ),
    )
