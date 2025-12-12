import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_not_cases = [
    BeforeAndAfter("print(not 3)", "print(False)"),
    BeforeAndAfter("print(not '')", "print(True)"),
    BeforeAndAfter("print(not a)", "print(not a)"),
]


@pytest.mark.parametrize("before_and_after", _not_cases)
def test_not(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)


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
