from personal_python_ast_optimizer.parser.config import ExtrasConfig
from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_remove_dup_slots_tuple():
    before_and_after = BeforeAndAfter(
        "class A:__slots__ = ('a', 'b', 'a')", "class A:__slots__=('a','b')"
    )
    run_minifier_and_assert_correct(
        before_and_after, extras_config=ExtrasConfig(warn_unusual_code=False)
    )


def test_remove_dup_slots__list_annotation():
    before_and_after = BeforeAndAfter(
        "class A:__slots__: list = ['a', 'b', 'a']", "class A:__slots__=['a','b']"
    )
    run_minifier_and_assert_correct(
        before_and_after, extras_config=ExtrasConfig(warn_unusual_code=False)
    )


def test_remove_dup_slots_set():
    before_and_after = BeforeAndAfter(
        "class A:__slots__ = {'a', 'b', 'a'}", "class A:__slots__={'a','b'}"
    )
    run_minifier_and_assert_correct(
        before_and_after, extras_config=ExtrasConfig(warn_unusual_code=False)
    )
