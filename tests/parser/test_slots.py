from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_remove_dup_slots():
    before_and_after = BeforeAndAfter(
        "class A:__slots__ = ('a', 'b', 'a')", "class A:__slots__=('a','b')"
    )
    run_minifier_and_assert_correct(before_and_after)
