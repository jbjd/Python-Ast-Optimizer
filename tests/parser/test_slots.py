from tests.utils import BeforeAndAfter, optimize_and_assert_correctness


def test_remove_dup_slots_tuple():
    before_and_after = BeforeAndAfter(
        "class A:__slots__ = ('a', 'b', 'a')", "class A:__slots__=('a','b')"
    )
    optimize_and_assert_correctness(before_and_after)


def test_remove_dup_slots_list_annotation():
    before_and_after = BeforeAndAfter(
        "class A:__slots__: list = ['a', 'b', 'a']", "class A:__slots__:list=['a','b']"
    )
    optimize_and_assert_correctness(before_and_after)


def test_remove_dup_slots_set():
    before_and_after = BeforeAndAfter(
        "class A:__slots__ = {'a', 'b', 'a'}", "class A:__slots__={'a','b'}"
    )
    optimize_and_assert_correctness(before_and_after)
