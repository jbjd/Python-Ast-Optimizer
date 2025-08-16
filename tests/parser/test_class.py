from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_class_only_docstring():
    before_and_after = BeforeAndAfter(
        """
class Foo():
    '''Some Class'''
""",
        "class Foo:pass",
    )
    run_minifier_and_assert_correct(before_and_after)


def test_tuple_class():
    before_and_after = BeforeAndAfter(
        """
class SomeTuple():
    '''A tuple, wow!'''
    thing1: str
    thing2: int
""",
        "class SomeTuple:thing1:int;thing2:int",
    )
    run_minifier_and_assert_correct(before_and_after)
