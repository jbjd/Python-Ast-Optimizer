import pytest

from personal_python_ast_optimizer.config import CodeToFoldConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness_old

_binary_op_folding_cases = [
    BeforeAndAfter("a=3+4*2", "a=11"),
    BeforeAndAfter("a=(7-2)//2", "a=2"),
    BeforeAndAfter("a=(7%4)/3", "a=1.0"),
    BeforeAndAfter("a=(1<<3)>>2", "a=2"),
    BeforeAndAfter("a=64|1", "a=65"),
    BeforeAndAfter("a=7&3", "a=3"),
    BeforeAndAfter("a=3^6", "a=5"),
    BeforeAndAfter("a='a' is 'b'", "a=False"),
    BeforeAndAfter("a='a' is not 'b'", "a=True"),
]


@pytest.mark.parametrize("before_and_after", _binary_op_folding_cases)
def test_binary_op_folding(before_and_after: BeforeAndAfter):
    optimize_and_assert_correctness_old(
        before_and_after, code_to_fold=CodeToFoldConfig(fold_constants=True)
    )


def test_string_folding():
    before_and_after = BeforeAndAfter(
        """
a = (
    "a"
    "b"
)""",
        "a='ab'",
    )
    optimize_and_assert_correctness_old(before_and_after)
