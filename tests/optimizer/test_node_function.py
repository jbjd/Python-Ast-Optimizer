from tests.utils import optimize_and_assert_correctness


def test_function_returns_literal_none():
    """Should replace 'return None' with 'return' or remove."""

    source: str = """
def foo(bar):
    if bar:
        return None
    print(1)
    return None
def asdf():
    return None
"""

    expected: str = """def foo(bar):
\tif bar:return
\tprint(1)
def asdf():pass"""

    optimize_and_assert_correctness(source, expected)
