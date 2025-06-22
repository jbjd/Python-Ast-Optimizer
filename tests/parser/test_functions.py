from tests.utils import BeforeAndAfter, run_minifier_and_assert_correct


def test_function_dangling_constants():
    before_and_after = BeforeAndAfter(
        """
def foo(bar: str) -> None:
    '''Some Doc String'''

    3  # This is some dangling constant
    a: int
    return
""",
        "def foo(bar):return",  # TODO: Skip empty returns at end of body
    )
    run_minifier_and_assert_correct(before_and_after)


def test_function_with_many_args():
    before_and_after = BeforeAndAfter(
        """
def foo(bar, spam, eggs):
    a: int = 1
    return a
""",
        "def foo(bar,spam,eggs):a=1;return a",
    )
    run_minifier_and_assert_correct(before_and_after)


def test_function_with_many_returns():
    before_and_after = BeforeAndAfter(
        """
def foo(bar):
    if bar:
        return None
    return 1
""",
        """
def foo(bar):
\tif bar:return
\treturn 1
""".strip(),
    )
    run_minifier_and_assert_correct(before_and_after)


def test_function_call_same_line():
    before_and_after = BeforeAndAfter(
        """
if a==b:
    a()
    b()
    c()
""",
        "if a==b:a();b();c()",
    )
    run_minifier_and_assert_correct(before_and_after)
