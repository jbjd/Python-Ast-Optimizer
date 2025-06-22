import pytest

from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct

_constant_folding_cases = [
    BeforeAndAfter("a=3+4*2", "a=11"),
    BeforeAndAfter("a=(7-2)//2", "a=2"),
    BeforeAndAfter("a=(7%4)/3", "a=1.0"),
    BeforeAndAfter("a=(1<<3)>>2", "a=2"),
    BeforeAndAfter("a=64|1", "a=65"),
    BeforeAndAfter("a=7&3", "a=3"),
    BeforeAndAfter("a=3^6", "a=5"),
]


@pytest.mark.parametrize("before_and_after", _constant_folding_cases)
def test_constant_folding(before_and_after: BeforeAndAfter):
    run_minifier_and_assert_correct(before_and_after)
