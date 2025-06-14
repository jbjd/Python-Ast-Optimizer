from tests.utils import BeforeAndAfter, run_minifiyer_and_assert_correct


def test_function_dangling_constants():
    before_and_after = BeforeAndAfter(
        """
def foo(bar: str) -> None:
    '''Some Doc String'''

    3  # This is some dangling constant
    a: int
    return "Hello World"
""",
        "def foo(bar):return 'Hello World'",
    )
    run_minifiyer_and_assert_correct(before_and_after)


def test_function_with_many_args():
    before_and_after = BeforeAndAfter(
        """
def foo(bar, spam, eggs):
    a: int = 1
    return a
""",
        "def foo(bar,spam,eggs):\n\ta=1;return a",
    )
    run_minifiyer_and_assert_correct(before_and_after)


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
    run_minifiyer_and_assert_correct(before_and_after)


def test_function_call_same_line():
    before_and_after = BeforeAndAfter(
        """
if a==b:
    a()
    b()
    c()
""",
        "if a==b:\n\ta();b();c()",
    )
    run_minifiyer_and_assert_correct(before_and_after)
