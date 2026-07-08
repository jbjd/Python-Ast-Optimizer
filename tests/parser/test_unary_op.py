import pytest

from personal_python_ast_optimizer.config import CodeToFoldConfig
from tests.utils import BeforeAndAfter, optimize_and_assert_correctness

_not_cases = [
    BeforeAndAfter("print(not 3)", "print(False)"),
    BeforeAndAfter("print(not '')", "print(True)"),
    BeforeAndAfter("print(not a)", "print(not a)"),
    BeforeAndAfter("if not __debug__:print()", "print()"),
]


@pytest.mark.parametrize("before_and_after", _not_cases)
def test_not(before_and_after: BeforeAndAfter):
    optimize_and_assert_correctness(
        before_and_after,
        code_to_fold_config=CodeToFoldConfig(vars_to_fold={"__debug__": False}),
    )


_bitwise_not_cases = [
    BeforeAndAfter("print(~3)", "print(-4)"),
    BeforeAndAfter("print(~a)", "print(~a)"),
]


@pytest.mark.parametrize("before_and_after", _bitwise_not_cases)
def test_bitwise_not(before_and_after: BeforeAndAfter):
    optimize_and_assert_correctness(before_and_after)


_plus_cases = [
    BeforeAndAfter("print(+3)", "print(3)"),
    BeforeAndAfter("print(+a)", "print(+a)"),
]


@pytest.mark.parametrize("before_and_after", _plus_cases)
def test_plus(before_and_after: BeforeAndAfter):
    optimize_and_assert_correctness(before_and_after)
