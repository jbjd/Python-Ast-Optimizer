import pytest

from personal_python_ast_optimizer.parser.config import OptimizationsConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_not_cases = [
    BeforeAndAfter("print(not 3)", "print(False)"),
    BeforeAndAfter("print(not '')", "print(True)"),
    BeforeAndAfter("print(not a)", "print(not a)"),
    BeforeAndAfter("if not __debug__:print()", "print()"),
]


@pytest.mark.parametrize("before_and_after", _not_cases)
def test_not(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(
        before_and_after,
        optimizations_config=OptimizationsConfig(vars_to_fold={"__debug__": False}),
    )


_bitwise_not_cases = [
    BeforeAndAfter("print(~3)", "print(-4)"),
    BeforeAndAfter("print(~a)", "print(~a)"),
]


@pytest.mark.parametrize("before_and_after", _bitwise_not_cases)
def test_bitwise_not(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)


_plus_cases = [
    BeforeAndAfter("print(+3)", "print(3)"),
    BeforeAndAfter("print(+a)", "print(+a)"),
]


@pytest.mark.parametrize("before_and_after", _plus_cases)
def test_plus(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)
